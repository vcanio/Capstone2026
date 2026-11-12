"""Paridad de presentación con Walmart Visión, sin inferencia ni datos reales."""
from pathlib import Path
import shutil
import subprocess
import unittest
from presentacion_niveles import occupancy_estimate
from panel_source import read_panel


class VisionParityTests(unittest.TestCase):
    def test_shared_reading_keeps_threshold_and_missing_measurements(self):
        for value, label in ((0, 'Reponer'), (29.99, 'Reponer'), (30, 'Suficiente'), (100, 'Suficiente')):
            reading = occupancy_estimate({'status': 'medido', 'combined_signal_pct': value}, 'v2')
            self.assertEqual(reading['pct'], value)
            self.assertEqual(reading['label'], label)
        for value in (None, True, float('nan'), -1, 101):
            self.assertIsNone(occupancy_estimate({'status': 'medido', 'combined_signal_pct': value}, 'v2')['pct'])
        self.assertIsNone(occupancy_estimate({'status': 'sin_medicion', 'combined_signal_pct': 0}, 'v2')['pct'])

    def js(self, body):
        node = shutil.which('node')
        if not node:
            self.skipTest('Se necesita Node.js.')
        logic = (Path(__file__).parents[1] / 'static/prediction-demo-logic.js').read_text(encoding='utf-8')
        result = subprocess.run([node], input="const assert=require('node:assert/strict');\n" + logic + body,
                                text=True, encoding='utf-8', capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_occupancy_uses_measurement_instead_of_yolo_class_or_confidence(self):
        self.js("""
        const detections=[0,29.99,30,100,null].map((pct,i)=>({id:i+1,clase:'Nivel_suficiente',
          confianza:.99,occupancy_estimate:{pct}}));
        const summary=PredictionDemo.occupancySummary(detections);
        assert.match(summary.title,/2 niveles necesitan reposición/);
        assert.match(summary.detail,/1 sin medición/);
        assert.deepEqual(summary.rows.map(r=>r.tone),['low','low','enough','enough','unknown']);
        const missing=PredictionDemo.occupancySummary([{clase:'Nivel_suficiente',confianza:.99}]);
        assert.equal(missing.rows[0].pct,null);
        assert.match(missing.title,/No se pudo estimar/);
        assert.match(PredictionDemo.occupancySummary([]).title,/No se detectaron/);
        const historic=PredictionDemo.occupancySummary([{occupancy:{status:'medido',
          combined_signal_pct:44,area_signal_pct:10}}],'paulo_mascara_v2_combinacion_ponderada');
        assert.equal(historic.rows[0].pct,44);
        """)

    def test_result_download_and_compare_use_occupancy_image_then_clear_on_reset(self):
        html = read_panel()
        start = html.index('function showPrediction(job)')
        show = html[start:html.index('function schedulePoll()', start)]
        start = html.index('function resetPrediction()')
        reset = html[start:html.index('function renderOriginal()', start)]
        self.js("""
        const nodes=new Map(),$=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',hidden:false,
          removeAttribute(key){delete this[key]},setAttribute(){}});return nodes.get(id)};
        const document={querySelector:selector=>$(selector),querySelectorAll:()=>[]};
        const ImageNavigation={release(){},mount(){}},setHTML=(node,html)=>node.innerHTML=html;
        const esc=String,data={models:[]},currentView='predict',matchMedia=()=>({matches:false});
        const renderEdgeViews=()=>{},demoView=()=>{},renderEdgeLayer=()=>{},updateAvailability=()=>{};
        let edgeLayers=[],predictJob='fixture';
        """ + show + reset + """
        const job={id:'fixture',image_url:'yolo.jpg',occupancy_result_url:'occupancy.jpg',result:{
          config:{scope:'Nivel_estados',image_source:'upload',conf:.25,imgsz:640},
          occupancy:{method:'paulo_mascara_v2_combinacion_ponderada'},
          detecciones:[{id:1,clase:'Nivel_suficiente',confianza:.99,occupancy_estimate:{pct:15}}]}};
        showPrediction(job);
        assert.match($('prediction-output').innerHTML,/src="occupancy.jpg"/);
        assert.equal($('download-prediction').href,'occupancy.jpg');
        assert.match($('prediction-summary').innerHTML,/necesita reposición/);
        assert.match($('prediction-occupancy').innerHTML,/15 %/);
        assert.match($('prediction-detections').innerHTML,/Suficiente/);
        assert.equal($('prediction-occupancy').hidden,false);
        assert.equal($('prediction-measurements').hidden,false);
        resetPrediction();
        assert.equal($('prediction-occupancy').hidden,true);
        assert.equal($('prediction-measurements').innerHTML,'');
        assert.equal($('download-prediction').href,undefined);
        assert.equal($('prediction-tools').hidden,true);
        delete job.result.occupancy;delete job.occupancy_result_url;showPrediction(job);
        assert.match($('prediction-output').innerHTML,/src="yolo.jpg"/);
        assert.equal($('prediction-occupancy').hidden,true);
        assert.equal($('prediction-measurements').hidden,true);
        """)
