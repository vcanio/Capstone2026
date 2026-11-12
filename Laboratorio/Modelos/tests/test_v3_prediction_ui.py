"""Flujo real del componente V3 con DOM mínimo y solicitud controlada."""
from pathlib import Path
import shutil
import subprocess
import unittest


class V3PredictionUITests(unittest.TestCase):
    def test_prediction_comparison_reset_and_no_availability_states(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('Node.js no disponible')
        source = (Path(__file__).resolve().parents[1] / 'static/v3-prediction.js').read_text(encoding='utf-8')
        prelude = """
        const assert=require('node:assert/strict'),nodes=new Map();
        const document={getElementById:id=>{
          if(!nodes.has(id))nodes.set(id,{value:'',innerHTML:'',textContent:'',hidden:false,events:{},dataset:{},
            classList:{toggle(){}},addEventListener(k,fn){this.events[k]=fn},setAttribute(k,v){this[k]=v},
            getAttribute(k){return this[k]||null}});return nodes.get(id);
        }};
        const get=id=>document.getElementById(id),ImageNavigation={mount(){}},runName=String;
        let jobs=[],busy=false,request;
        const updateAvailability=()=>{},poll=async()=>{};
        const api=async(path,config)=>{request=config;return {id:'job',state:'running',config}};
        const model='Experimentos/v3_run/entrenamiento/weights/best.pt';
        get('v3-predict-model').value=model;get('v3-predict-source').value='validation';
        get('v3-predict-photo').value='real.png';get('v3-predict-conf').value='.6';get('v3-predict-nms').value='.7';
        """
        assertions = """
        (async()=>{
          const catalog={models:[{id:model,run:'v3_run',checkpoint:'best',imgsz:640}],
            runs:[{id:'v3_run',photos:[{name:'real.png',origin:'real',scene:'scene'}]}]};
          V3Prediction.setActive(true,true,catalog,[],false);
          assert.equal(get('v3-predict-submit').disabled,false);
          assert.match(get('v3-predict-original').src,/development-image/);
          await get('v3-predict-form').events.submit({preventDefault(){}});
          assert.equal(request.pipeline,'geometria_nivel_v3');assert.equal(request.photo,'real.png');
          assert.equal(request.source_mode,'validation');assert.equal(request.imgsz,640);assert.equal(request.occupancy,undefined);
          assert.equal(request.conf,.6);
          const done={id:'job',state:'done',image_url:'/prediction.jpg',result:{
            detecciones:[{id:1,confianza:.9,contorno_valido:true}],
            metricas:{anotados:2,aciertos:1,omitidos:1,extras:0}}};
          V3Prediction.setActive(true,true,catalog,[done],false);
          assert.match(get('v3-predict-summary').textContent,/1 de 2/);
          assert.doesNotMatch(get('v3-predict-summary').textContent,/Suficiente|Reponer/);
          assert.equal(get('v3-predict-result').src,'/prediction.jpg');
          assert.equal(get('v3-predict-download').hidden,false);
          get('v3-predict-view-compare').events.click();
          assert.equal(get('v3-predict-original-figure').hidden,false);assert.equal(get('v3-predict-result-figure').hidden,false);
          get('v3-predict-conf').events.change();assert.equal(get('v3-predict-download').hidden,true);
          assert.equal(get('v3-predict-result-figure').hidden,true);
          get('v3-predict-source').value='upload';get('v3-predict-source').events.change();
          assert.equal(get('v3-predict-submit').disabled,true);assert.equal(get('v3-predict-original-figure').hidden,true);
        })().catch(error=>{console.error(error);process.exitCode=1});
        """
        result = subprocess.run([node], input=prelude + source + assertions, text=True,
                                encoding='utf-8', capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
