"""Regresiones controladas; no son una evaluación de precisión en fotos reales."""
from copy import deepcopy
from io import BytesIO
import json
from http.server import ThreadingHTTPServer
import threading
from types import SimpleNamespace
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import numpy as np
from PIL import Image
from app import Handler
from inferencia import analyze_edges
from ocupacion_basal import compute_cell_maps, score_level_from_features, feature_bounds, POLICY
from ocupacion_linea_a import score_level_from_features as old_score, gondola_feature_bounds
from presentacion_niveles import occupancy_estimate
import test_vision_ui as ui


def feature(rows=None):
    shape = (20, 40)
    f = dict(valid=True, valid_cells=800, usable=np.ones(shape, bool),
             observed_coverage=np.ones(shape, np.float32), mask_coverage=np.ones(shape, np.float32))
    for key, low, high in [('density', .001, .07), ('gradient', 3, 42),
                           ('color_density', 0, .45), ('deviation', 1.5, 20)]:
        f[key] = np.full(shape, low, np.float32)
        if rows is not None:
            f[key][rows, :] = high
    return f


class BasalTests(unittest.TestCase):
    def test_low_products_keep_horizontal_coverage(self):
        low, tall = feature(slice(14, 19)), feature(slice(4, 19))
        bounds = feature_bounds([low, tall])
        self.assertEqual(old_score(low, gondola_feature_bounds([low, tall]))['state'], 'reponer')
        for f in (low, tall):
            r = score_level_from_features(f, bounds)
            self.assertEqual((r['pct'], r['state']), (100, 'suficiente'))

    def test_empty_and_one_row_rail_do_not_become_product(self):
        for f in (feature(), feature(slice(18, 19))):
            r = score_level_from_features(f, feature_bounds([f]))
            self.assertEqual((r['pct'], r['state']), (0, 'reponer'))

    def test_unknown_base_abstains_instead_of_reporting_empty(self):
        f = feature()
        f['observed_coverage'][13:19] = 0
        r = score_level_from_features(f, feature_bounds([f]))
        self.assertEqual(r['state'], 'revisar')
        self.assertIsNone(occupancy_estimate(r, 'v2')['pct'])

    def test_unknown_columns_do_not_join_gaps_or_inflate_empty_width(self):
        f = feature()
        f['observed_coverage'][:, 18:22] = 0
        r = score_level_from_features(f, feature_bounds([f]))
        self.assertEqual(r['observed_width_pct'], 90)
        self.assertEqual(r['max_gap_pct'], 45)
        self.assertEqual(r['state'], 'reponer')

    def test_unknown_area_that_could_cross_threshold_requires_review(self):
        f = feature()
        occupied = feature(slice(13, 19))
        for key in ('density', 'gradient', 'color_density', 'deviation'):
            f[key][:, :10] = occupied[key][:, :10]
        f['observed_coverage'][:, 36:] = 0
        r = score_level_from_features(f, feature_bounds([f]))
        self.assertEqual(r['coverage_lower_pct'], 25)
        self.assertEqual(r['coverage_upper_pct'], 35)
        self.assertEqual(r['state'], 'revisar')

    def test_supported_narrow_product_survives(self):
        f = feature()
        full = feature(slice(13, 19))
        for key in ('density', 'gradient', 'color_density', 'deviation'):
            f[key][:, 20] = full[key][:, 20]
        r = score_level_from_features(f, feature_bounds([f]))
        self.assertEqual(r['pct'], 2.5)
        self.assertEqual(r['max_gap_pct'], 50)

    def test_band_follows_sloped_mask_without_modifying_it(self):
        f = feature(slice(0, 20))
        f['usable'][10:, :20] = False
        saved = f['usable'].copy()
        maps = compute_cell_maps(f, feature_bounds([f]))
        self.assertLess(np.flatnonzero(maps['band'][:, 5]).max(), np.flatnonzero(maps['band'][:, 30]).min())
        np.testing.assert_array_equal(saved, f['usable'])

    def test_too_small_band_and_missing_masks_are_not_sufficient(self):
        f = feature()
        f['usable'][3:] = False
        self.assertEqual(score_level_from_features(f, feature_bounds([f]))['state'], 'revisar')
        self.assertEqual(score_level_from_features(None)['status'], 'sin_medicion')

    def test_switching_estimator_preserves_yolo_masks_and_default_output(self):
        rgb = np.full((400, 700, 3), 60, np.uint8)
        rgb[220:330, 40:650] = (230, 30, 30)
        mask = np.zeros((1, 400, 700), np.uint8)
        mask[:, 40:350, 30:670] = 1
        saved = mask.copy()
        result = SimpleNamespace(names={0: 'Nivel'}, masks=SimpleNamespace(data=SimpleNamespace(cpu=lambda:SimpleNamespace(numpy=lambda:mask))), boxes=None)
        detections = [{'id':1,'state':'detectado'}]
        analyze_edges(rgb, result, detections, 'v2')
        original = deepcopy(detections)
        output = analyze_edges(rgb, result, detections, 'v2', occupancy_algorithm='basal')
        self.assertEqual(detections[0]['occupancy']['interpretation_policy'], POLICY)
        self.assertEqual(detections[0]['state'], 'detectado')
        self.assertFalse(output['occupancy']['calibrated'])
        analyze_edges(rgb, result, detections, 'v2')
        self.assertEqual(detections, original)
        np.testing.assert_array_equal(saved, mask)


class BasalHttpTests(unittest.TestCase):
    def test_selection_reaches_runner_and_receipt_and_rejects_unknown(self):
        calls = []
        def analyze(body, model, confidence, method, **options):
            calls.append(options)
            return {'image':Image.new('RGB',(20,20)), 'detections':[], 'occupancy':{'revision':'test'}}
        server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
        server.runner = SimpleNamespace(analyze=analyze, manifest={'default_model':'fixture'})
        thread = threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            for algorithm in ('linea_a','basal'):
                request = Request(f'http://127.0.0.1:{server.server_port}/api/predict?ocupacion={algorithm}',data=b'photo',headers={'Content-Type':'image/jpeg'})
                with urlopen(request) as response:
                    data=json.load(response)
                self.assertEqual(data['analysis_context']['occupancy_algorithm'],algorithm)
            self.assertEqual(calls,[{}, {'occupancy_algorithm':'basal'}])
            with self.assertRaises(HTTPError) as error:
                urlopen(Request(f'http://127.0.0.1:{server.server_port}/api/predict?ocupacion=invalid',data=b'x',headers={'Content-Type':'image/jpeg'}))
            self.assertEqual(error.exception.code,400)
        finally:
            server.shutdown();server.server_close();thread.join()


class BasalUITests(unittest.TestCase):
    js = ui.VisionInterfaceTests.js

    def test_session_restores_both_algorithms_and_their_reviews(self):
        self.js(r'''
        currentModel={id:'V3',geometry_only:true,occupancy_method:'old',occupancy_revision:'a',occupancy_algorithms:[{id:'linea_a',name:'Actual',method:'old',revision:'a'},{id:'basal',name:'Basal',method:'new',revision:'b'}]};availableModels=[currentModel];modelContext();
        chooseBatch([{name:'a.jpg',type:'image/jpeg',size:1}]);
        batch[0].result={...prediction(),model:'V3',occupancy:{method:'old',revision:'a'}};ReviewDesk.correct(batch[0],'QA');
        changeAlgorithm('basal');batch[0].result={...prediction(),model:'V3',occupancy:{method:'new',revision:'b'}};
        ReviewDesk.addIssue(batch[0],{reason:'Otro',note:'basal'},'QA');
        let stored;window.indexedDB={};
        sessionDB=async()=>({close(){},transaction(){const tx={objectStore:()=>({put(value){stored=structuredClone(value);queueMicrotask(()=>tx.oncomplete())},get(){const req={result:structuredClone(stored)};queueMicrotask(()=>req.onsuccess());return req}})};return tx}});
        saveSession();await saveQueue;clearBatch();occupancyAlgorithm='linea_a';
        await restoreSession();assert.equal(occupancyAlgorithm,'basal');assert.equal(batch[0].issues[0].note,'basal');
        changeAlgorithm('linea_a');assert.equal(ReviewDesk.status(batch[0]),'correcta');assert.equal(batch[0].result.occupancy.method,'old');
        await saveQueue;
        ''')

    def test_zip_keeps_variants_with_separate_review_records(self):
        self.js(r'''
        global.File=class extends Blob{constructor(parts,name,options){super(parts,options);this.name=name}};
        const data={...prediction(false),width:100,height:80,image_url:'data:image/jpeg;base64,AA=='};
        const item={file:new File([new Uint8Array([1,2,3])],'foto.jpg',{type:'image/jpeg'}),result:data};
        ReviewDesk.correct(item,'QA');
        const variants={[variantKey(data.model,'linea_a')]:{result:data,review:ReviewDesk.snapshot(item)},[variantKey(data.model,'basal')]:{result:{...data,occupancy:{revision:'basal'}},review:{issues:[],reviewEvents:[],marked:false,correct:false}}};
        const record=ReviewDesk.exportRecord(item,{archivo:'originales/001_foto.jpg',resultado:'resultados/001.json',variantes:'variantes/001.json'});
        const encode=value=>new TextEncoder().encode(JSON.stringify(value));
        const blob=zipSelected([{name:record.archivo,bytes:new Uint8Array([1,2,3])},{name:record.resultado,bytes:encode(data)},{name:record.variantes,bytes:encode(variants)},{name:'revision.json',bytes:encode({schema_version:2,fotos:[record]})}]);
        const restored=ReviewDesk.importRecords(ReviewDesk.readZip(await blob.arrayBuffer()),{id:data.model});
        assert.equal(Object.keys(restored[0].variantResults).length,2);
        assert.equal(restored[0].variantResults[variantKey(data.model,'linea_a')].review.correct,true);
        assert.equal(restored[0].variantResults[variantKey(data.model,'basal')].review.correct,false);
        assert.deepEqual([...new Uint8Array(await restored[0].file.arrayBuffer())],[1,2,3]);
        ''')

    def test_switch_restores_results_and_reviews_and_keeps_default(self):
        self.js(r'''
        const a={id:'linea_a',name:'Línea A',method:'old',revision:'a'},b={id:'basal',name:'Basal',method:'new',revision:'b'};
        currentModel={id:'V3',geometry_only:true,occupancy_method:'old',occupancy_revision:'a',occupancy_algorithms:[a,b]};availableModels=[currentModel];modelContext();
        assert.equal(occupancyAlgorithm,'linea_a');
        chooseBatch([{name:'a.jpg',type:'image/jpeg',size:1}]);
        const original={...prediction(),model:'V3',occupancy:{method:'old',revision:'a'}};
        batch[0].result=original;ReviewDesk.correct(batch[0],'QA');
        changeAlgorithm('basal');assert.equal(batch[0].result,null);assert.equal(ReviewDesk.status(batch[0]),'sin_revisar');
        const newer={...prediction(),model:'V3',occupancy:{method:'new',revision:'b'}};
        ReviewDesk.accept(batch[0],newer,.6);ReviewDesk.addIssue(batch[0],{reason:'Otro',note:'basal'},'QA');
        changeAlgorithm('linea_a');assert.equal(batch[0].result,original);assert.equal(ReviewDesk.status(batch[0]),'correcta');assert.equal(batch[0].issues.length,0);
        changeAlgorithm('basal');assert.equal(batch[0].result,newer);assert.equal(batch[0].issues[0].note,'basal');
        running=true;changeAlgorithm('linea_a');assert.equal(occupancyAlgorithm,'basal');running=false;
        batchRunning=true;changeAlgorithm('linea_a');assert.equal(occupancyAlgorithm,'basal');
        ''')

    def test_basal_render_and_request_are_distinct(self):
        self.js(r'''
        currentModel={id:'V3',geometry_only:true,occupancy_algorithms:[{id:'linea_a',name:'Actual',method:'old',revision:'a'},{id:'basal',name:'Basal',method:'basal_v1_observable_columns',revision:'b'}]};availableModels=[currentModel];modelContext();
        chooseBatch([{name:'a.jpg',type:'image/jpeg',size:1}]);changeAlgorithm('basal');
        const data={...prediction(),model:'V3',geometry_only:true,occupancy:{method:'basal_v1_observable_columns',revision:'b',interpretation_policy:{name:'basal_visible_width_v1',threshold_pct:30}}};
        data.detections[0].occupancy={pct:80,observed_width_pct:90,max_gap_pct:10,status:'medido'};
        let requested='';global.fetch=async(url)=>{requested=url;return {ok:true,json:async()=>data}};
        await analyzePhoto();assert.match(requested,/ocupacion=basal/);assert.match($('algorithm-result-label').textContent,/basal.*experimental/i);
        assert.match($('edge-columns').innerHTML,/Ancho observable/);assert.match($('occupancy-help').textContent,/calibración/);
        assert.equal(resultMatchesAlgorithm(data),true);assert.equal(resultMatchesAlgorithm(data,currentModel,'linea_a'),false);
        ''')
