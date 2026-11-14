"""Pruebas de comparación simultánea Línea A vs Basal y etiquetado por nivel."""
from http.server import ThreadingHTTPServer
from io import BytesIO
import json
import threading
from types import SimpleNamespace
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import numpy as np
from PIL import Image

from app import Handler
from inferencia import ModelRunner
import test_vision_ui as ui


def _jpeg_bytes(width=320, height=240):
    img = Image.new('RGB', (width, height), (75, 75, 75))
    buf = BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()


def _tensor(values):
    return SimpleNamespace(cpu=lambda: SimpleNamespace(tolist=lambda: values, numpy=lambda: values))


class DualAnalysisBackendTests(unittest.TestCase):
    def test_runner_ambos_runs_yolo_once_and_builds_both_variants(self):
        runner = ModelRunner()
        calls = []
        masks = np.zeros((2, 240, 320), np.uint8)
        masks[0, 20:100, 20:300] = 1
        masks[1, 130:215, 20:300] = 1
        boxes = _tensor([[20.0, 20.0, 300.0, 100.0], [20.0, 130.0, 300.0, 215.0]])
        confs = _tensor([0.92, 0.88])
        clss = _tensor([0.0, 0.0])
        xy = [np.array([[20, 20], [300, 20], [300, 100], [20, 100]], dtype=np.float32),
              np.array([[20, 130], [300, 130], [300, 215], [20, 215]], dtype=np.float32)]

        class FakeModel:
            def predict(self, *args, **kwargs):
                calls.append(kwargs)
                return [SimpleNamespace(
                    names={0: 'Nivel'},
                    masks=SimpleNamespace(data=_tensor(masks), xy=xy),
                    boxes=SimpleNamespace(xyxy=boxes, conf=confs, cls=clss),
                )]

        runner._load_model = lambda model_id: (FakeModel(), 'cpu')
        default_model = runner.manifest['default_model']
        out = runner.analyze(_jpeg_bytes(), default_model, 0.6, 'yolo_paulo_v2',
                             occupancy_algorithm='ambos', primary_algorithm='basal', quality_check=False)
        self.assertEqual(len(calls), 1)
        self.assertIn('variant_results', out)
        self.assertEqual(set(out['variant_results']), {'linea_a', 'basal'})
        self.assertEqual(out['occupancy']['interpretation_policy']['name'], 'basal_visible_width_v1')
        self.assertEqual(out['variant_results']['linea_a']['occupancy']['interpretation_policy']['name'], 'body_fill_gap_v1')
        self.assertIn('edges_image', out)
        self.assertNotIn('edges_image', out['variant_results']['linea_a'])

    def test_http_ambos_returns_encoded_variants_and_rejects_bad_primary(self):
        calls = []

        def analyze(body, model, confidence, method, **options):
            calls.append(options)
            a = {'image': Image.new('RGB', (20, 20)), 'occupancy_image': Image.new('RGB', (20, 20)),
                 'detections': [], 'occupancy': {'revision': 'rev_a'}}
            b = {'image': Image.new('RGB', (20, 20)), 'occupancy_image': Image.new('RGB', (20, 20)),
                 'edges_image': Image.new('RGB', (20, 20)), 'detections': [], 'occupancy': {'revision': 'rev_b'}}
            return {**b, 'variant_results': {'linea_a': a, 'basal': b}}

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.runner = SimpleNamespace(analyze=analyze, manifest={'default_model': 'fixture'})
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            req = Request(
                f'http://127.0.0.1:{server.server_port}/api/predict?ocupacion=ambos&primario=basal',
                data=b'photo', headers={'Content-Type': 'image/jpeg'})
            with urlopen(req) as resp:
                data = json.load(resp)
            self.assertEqual(calls, [{'occupancy_algorithm': 'ambos', 'primary_algorithm': 'basal'}])
            self.assertEqual(data['analysis_context']['occupancy_algorithm'], 'basal')
            self.assertEqual(set(data['variants']), {'linea_a', 'basal'})
            self.assertEqual(data['variants']['linea_a']['analysis_context']['occupancy_algorithm'], 'linea_a')
            self.assertEqual(data['variants']['basal']['analysis_context']['occupancy_algorithm'], 'basal')
            self.assertTrue(data['variants']['linea_a']['edges_image_url'].startswith('data:image/png;base64,'))
            with self.assertRaises(HTTPError) as err:
                urlopen(Request(
                    f'http://127.0.0.1:{server.server_port}/api/predict?ocupacion=ambos&primario=otro',
                    data=b'x', headers={'Content-Type': 'image/jpeg'}))
            self.assertEqual(err.exception.code, 400)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


class DualCompareAndLabelUITests(unittest.TestCase):
    js = ui.VisionInterfaceTests.js

    def test_dual_analysis_populates_both_variants_and_compare_views(self):
        self.js(r'''
        const a={id:'linea_a',name:'Línea A',method:'linea_a_v1_gondola_anchorage',revision:'ra'};
        const b={id:'basal',name:'Basal',method:'basal_v1_observable_columns',revision:'rb'};
        currentModel={id:'V3',geometry_only:true,occupancy_method:'linea_a_v1_gondola_anchorage',occupancy_revision:'ra',occupancy_algorithms:[a,b]};
        availableModels=[currentModel]; modelContext();
        chooseBatch([{name:'gondola.jpg',type:'image/jpeg',size:10}]);
        $('analyze-both').checked=true;
        const resA={...prediction(),model:'V3',geometry_only:true,image_url:'data:image/jpeg;base64,A1',occupancy_image_url:'data:image/png;base64,SA',
          occupancy:{method:'linea_a_v1_gondola_anchorage',revision:'ra',interpretation_policy:{name:'body_fill_gap_v1',threshold_pct:52}},
          detections:[{id:1,confidence:.9,occupancy:{pct:68,status:'medido'},occupancy_estimate:{pct:68,state:'suficiente',label:'Suficiente'}}]};
        const resB={...prediction(),model:'V3',geometry_only:true,image_url:'data:image/jpeg;base64,B1',occupancy_image_url:'data:image/png;base64,SB',
          occupancy:{method:'basal_v1_observable_columns',revision:'rb',interpretation_policy:{name:'basal_visible_width_v1',threshold_pct:30}},
          detections:[{id:1,confidence:.9,occupancy:{pct:40,observed_width_pct:50,status:'medido',review_required:true},occupancy_estimate:{pct:null,state:'revisar',label:'Revisar'}}]};
        let requested='';
        global.fetch=async(url)=>{requested=url;return {ok:true,json:async()=>({...resA,variants:{linea_a:resA,basal:resB}})}};
        await analyzePhoto();
        assert.match(requested,/ocupacion=ambos/);
        assert.match(requested,/primario=linea_a/);
        assert.equal(batch[0].result.variants,undefined);
        assert.ok(batch[0].variantResults[variantKey('V3','basal')].result);
        assert.match($('occupancy-rows').innerHTML,/compare-alt-row is-diff/);
        assert.match($('occupancy-rows').innerHTML,/Discrepan/);
        assert.match($('batch-compare-summary').innerHTML,/Discrepancias: 1 niveles/);
        view('compare');
        assert.equal($('compare-mode').hidden,false);
        $('compare-mode').value='linea_a_vs_basal'; view('compare');
        assert.equal($('compare-original').src,'data:image/jpeg;base64,A1');
        assert.equal($('compare-result').src,'data:image/jpeg;base64,B1');
        $('compare-mode').value='edges_linea_a_vs_basal'; view('compare');
        assert.equal($('compare-original').src,'data:image/png;base64,SA');
        assert.equal($('compare-result').src,'data:image/png;base64,SB');
        ''')

    def test_level_labels_metrics_filters_and_zip_roundtrip(self):
        self.js(r'''
        global.File=class extends Blob{constructor(parts,name,options){super(parts,options);this.name=name}};
        global.confirm=()=>true; global.setTimeout=()=>0;
        const a={id:'linea_a',name:'Línea A',method:'linea_a_v1_gondola_anchorage',revision:'ra'};
        const b={id:'basal',name:'Basal',method:'basal_v1_observable_columns',revision:'rb'};
        currentModel={id:'V3',geometry_only:true,occupancy_method:'linea_a_v1_gondola_anchorage',occupancy_revision:'ra',occupancy_algorithms:[a,b]};
        availableModels=[currentModel]; modelContext();
        chooseBatch([
          new File([new Uint8Array([1,2])],'f1.jpg',{type:'image/jpeg'}),
          new File([new Uint8Array([3,4])],'f2.jpg',{type:'image/jpeg'}),
        ]);
        const makeA=(id,pct,st)=>({...prediction(false),width:100,height:80,image_url:'data:image/jpeg;base64,AA==',model:'V3',geometry_only:true,
          occupancy:{method:'linea_a_v1_gondola_anchorage',revision:'ra',interpretation_policy:{name:'body_fill_gap_v1',threshold_pct:52}},
          detections:[{id,confidence:.9,display_polygon:[[10,10],[90,10],[90,70],[10,70]],occupancy:{pct,status:'medido'},occupancy_estimate:{pct,state:st}}]});
        const makeB=(id,pct,st)=>({...prediction(false),width:100,height:80,image_url:'data:image/jpeg;base64,BB==',model:'V3',geometry_only:true,
          occupancy:{method:'basal_v1_observable_columns',revision:'rb',interpretation_policy:{name:'basal_visible_width_v1',threshold_pct:30}},
          detections:[{id,confidence:.9,display_polygon:[[10,10],[90,10],[90,70],[10,70]],occupancy:{pct,observed_width_pct:90,status:'medido'},occupancy_estimate:{pct,state:st}}]});
        batch[0].result=makeA(1,20,'reponer');
        batch[0].variantResults={[variantKey('V3','linea_a')]:{result:batch[0].result,review:ReviewDesk.snapshot(batch[0])},
          [variantKey('V3','basal')]:{result:makeB(1,70,'suficiente'),review:ReviewDesk.snapshot(batch[0])}};
        batch[1].result=makeA(1,80,'suficiente');
        batch[1].variantResults={[variantKey('V3','linea_a')]:{result:batch[1].result,review:ReviewDesk.snapshot(batch[1])},
          [variantKey('V3','basal')]:{result:makeB(1,80,'suficiente'),review:ReviewDesk.snapshot(batch[1])}};
        await selectBatch(0);
        $('batch-filter').value='discrepancies'; $('batch-filter').listeners.change();
        assert.deepEqual(filteredBatchIndices(),[0]);
        $('batch-filter').value='all'; $('batch-filter').listeners.change();
        $('reviewer-name').value='Vicente';
        // Etiquetar nivel 1 de foto 1 como vacio mediante clic delegado.
        $('occupancy-rows').listeners.click({target:{closest:sel=>sel==='[data-occ-level]'?{dataset:{occLevel:'1',occLabel:'vacio'}}:null}});
        assert.equal(batch[0].levelLabels['1'].label,'vacio');
        undoReview();
        assert.equal(batch[0].levelLabels['1'],undefined);
        $('occupancy-rows').listeners.click({target:{closest:sel=>sel==='[data-occ-level]'?{dataset:{occLevel:'1',occLabel:'vacio'}}:null}});
        await selectBatch(1);
        $('occupancy-rows').listeners.click({target:{closest:sel=>sel==='[data-occ-level]'?{dataset:{occLevel:'1',occLabel:'suficiente'}}:null}});
        $('batch-filter').value='labeled'; $('batch-filter').listeners.change();
        assert.deepEqual(filteredBatchIndices(),[0,1]);
        const stats=ReviewDesk.computeComparisonMetrics(batch,'V3','linea_a');
        assert.equal(stats.metrics.linea_a.f1,100);
        assert.equal(stats.metrics.basal.tp,0);
        assert.equal(stats.metrics.basal.fn,1);
        assert.match($('batch-compare-summary').innerHTML,/Etiquetas: 2 niveles/);
        // Exportar ZIP y verificar etiquetas_ocupacion.json / csv + reimportación.
        global.createImageBitmap=async()=>({width:100,height:80,close(){}});
        const ctx={drawImage(){},beginPath(){},moveTo(){},lineTo(){},closePath(){},stroke(){}};
        let exportedBlob=null;
        global.URL.createObjectURL=blob=>{exportedBlob=blob;return 'blob:zip'};
        const origCreate=document.createElement;
        document.createElement=tag=>tag==='canvas'?{width:0,height:0,getContext:()=>ctx,toBlob:cb=>cb(new Blob([new Uint8Array([9])]))}:{href:'',download:'',click(){}};
        await exportReviewLot();
        document.createElement=origCreate;
        const files=ReviewDesk.readZip(await exportedBlob.arrayBuffer());
        assert.ok(files.has('etiquetas_ocupacion.json'));
        assert.ok(files.has('etiquetas_ocupacion.csv'));
        const labelsJson=JSON.parse(new TextDecoder().decode(files.get('etiquetas_ocupacion.json')));
        assert.equal(labelsJson.length,2);
        assert.equal(labelsJson[0].label,'vacio');
        assert.equal(labelsJson[0].alerta_humana,1);
        assert.equal(labelsJson[0].basal.state,'suficiente');
        const restored=ReviewDesk.importRecords(files,algorithmModel());
        assert.equal(restored[0].levelLabels['1'].label,'vacio');
        assert.equal(restored[1].levelLabels['1'].label,'suficiente');
        ''')

    def test_side_by_side_auto_compare_persistence_and_batch_fill(self):
        self.js(r'''
        const a={id:'linea_a',name:'Línea A',method:'linea_a_v1_gondola_anchorage',revision:'ra'};
        const b={id:'basal',name:'Basal',method:'basal_v1_observable_columns',revision:'rb'};
        currentModel={id:'V3',geometry_only:true,occupancy_method:'linea_a_v1_gondola_anchorage',occupancy_revision:'ra',occupancy_algorithms:[a,b]};
        availableModels=[currentModel]; modelContext();
        chooseBatch([
          {name:'p1.jpg',type:'image/jpeg',size:10},
          {name:'p2.jpg',type:'image/jpeg',size:10},
        ]);
        const makeA=(suf,pct,st)=>({...prediction(),model:'V3',geometry_only:true,
          image_url:'data:image/jpeg;base64,A'+suf,occupancy_image_url:'data:image/png;base64,SA'+suf,
          occupancy:{method:'linea_a_v1_gondola_anchorage',revision:'ra',interpretation_policy:{name:'body_fill_gap_v1',threshold_pct:52}},
          detections:[{id:1,confidence:.9,occupancy:{pct,status:'medido'},occupancy_estimate:{pct,state:st,label:st==='reponer'?'Reponer':'Suficiente'}}]});
        const makeB=(suf,pct,st)=>({...prediction(),model:'V3',geometry_only:true,
          image_url:'data:image/jpeg;base64,B'+suf,occupancy_image_url:'data:image/png;base64,SB'+suf,
          occupancy:{method:'basal_v1_observable_columns',revision:'rb',interpretation_policy:{name:'basal_visible_width_v1',threshold_pct:30}},
          detections:[{id:1,confidence:.9,occupancy:{pct,observed_width_pct:50,status:'medido',review_required:st==='revisar'},occupancy_estimate:{pct:st==='revisar'?null:pct,state:st,label:st==='revisar'?'Revisar':'Suficiente'}}]});
        $('analyze-both').checked=true;
        let idxReq=0;
        global.fetch=async(url)=>{
          const tag=++idxReq===1?'1':'2';
          const resA=makeA(tag,68,'suficiente');
          const resB=makeB(tag,40,'revisar');
          return {ok:true,json:async()=>({...resA,variants:{linea_a:resA,basal:resB}})};
        };
        await analyzePhoto();
        assert.equal(currentViewMode,'compare');
        assert.equal($('compare-mode').value,'linea_a_vs_basal');
        assert.equal($('compare-original').src,'data:image/jpeg;base64,A1');
        assert.equal($('compare-result').src,'data:image/jpeg;base64,B1');
        assert.equal($('view-compare').textContent,'Línea A vs Basal');
        assert.equal($('dual-algo-summary').hidden,false);
        assert.match($('dual-algo-summary').innerHTML,/Línea A/);
        assert.match($('dual-algo-summary').innerHTML,/Basal/);
        assert.match($('compare-left-stats').innerHTML,/Suficiente/i);
        assert.match($('compare-right-stats').innerHTML,/Revisar/i);

        // Segunda foto con solo Línea A, luego completar par faltante desde resumen del lote.
        $('analyze-both').checked=false;
        batch[1].result=makeA('2_solo',25,'reponer');
        batch[1].variantResults={[variantKey('V3','linea_a')]:{result:batch[1].result,review:ReviewDesk.snapshot(batch[1])}};
        await selectBatch(1);
        assert.equal(currentViewMode,'compare');
        assert.equal($('compare-mode').value,'original_vs_result');
        assert.match($('batch-compare-summary').innerHTML,/data-analyze-missing-pair/);

        $('batch-compare-summary').listeners.click({target:{closest:sel=>sel==='[data-analyze-missing-pair]'?{dataset:{analyzeMissingPair:'1'}}:null}});
        await new Promise(r=>setTimeout(r,20));
        assert.equal(currentViewMode,'compare');
        assert.equal($('compare-mode').value,'linea_a_vs_basal');
        assert.equal($('compare-original').src,'data:image/jpeg;base64,A2');
        assert.equal($('compare-result').src,'data:image/jpeg;base64,B2');

        // Cambiar a bordes con las píldoras y alternar algoritmo activo conservando vista dual.
        $('compare-mode-pills').listeners.click({target:{closest:sel=>sel==='[data-compare-mode]'?{dataset:{compareMode:'edges_linea_a_vs_basal'}}:null}});
        assert.equal($('compare-original').src,'data:image/png;base64,SA2');
        assert.equal($('compare-result').src,'data:image/png;base64,SB2');
        $('dual-algo-summary').listeners.click({target:{closest:sel=>sel==='[data-switch-algo]'?{dataset:{switchAlgo:'basal'}}:null}});
        assert.equal(occupancyAlgorithm,'basal');
        assert.equal(currentViewMode,'compare');

        // Alternar zoom de comparación 150% / 100%.
        let zoomedToggle=null;
        $('comparison').classList.toggle=(cls,force)=>{if(cls==='is-zoomed')zoomedToggle=force};
        $('compare-zoom').value='150';
        $('compare-zoom').listeners.input();
        assert.equal($('compare-zoom-value').textContent,'150 %');
        assert.equal($('comparison').style['--compare-zoom'],'150%');
        assert.equal(zoomedToggle,true);
        $('compare-zoom').value='100';
        $('compare-zoom').listeners.input();
        assert.equal($('compare-zoom-value').textContent,'100 %');
        assert.equal($('comparison').style['--compare-zoom'],'100%');
        assert.equal(zoomedToggle,false);
        ''')
