"""Continuidad del ensayo y registro explícito de revisión, sin inferencia ni GPU."""
from pathlib import Path
import shutil
import subprocess
import unittest


class V3ResultsUITests(unittest.TestCase):
    def test_review_is_manual_preserves_draft_and_targets_selected_run(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node no disponible')
        source=(Path(__file__).resolve().parents[1]/'static/v3-results.js').read_text(encoding='utf-8')
        prelude="""
        const assert=require('node:assert/strict'),nodes=new Map();
        const document={getElementById:id=>{
          if(!nodes.has(id))nodes.set(id,{value:'',innerHTML:'',textContent:'',hidden:false,dataset:{},events:{},
            addEventListener(k,fn){this.events[k]=fn}});return nodes.get(id);
        }};
        const get=id=>document.getElementById(id),runName=String,liveChart=()=>'<svg></svg>';
        let requests=[];const api=async(path,config)=>requests.push({path,config}),refresh=async()=>{};
        get('v3-result-run').value='first';
        const catalog={v3_training:{exports:[{author:'Vicente'}],runs:[
          {id:'first',ready:true,metrics:{sets:{val_real:{'metrics/mAP50(M)':.9}}}},
          {id:'second',ready:true,decision:{status:'candidato',author:'Vicente',reason:'Revisión previa'}}]},
          v3_prediction:{models:[{run:'first',id:'first/best.pt',checkpoint:'best'},
            {run:'second',id:'second/best.pt',checkpoint:'best'}]}};
        """
        assertions="""
        (async()=>{
          V3Results.setActive(true,true,catalog,false);
          assert.equal(requests.length,0);assert.match(get('v3-result-decision').textContent,/Falta tu revisión/);
          assert.equal(get('v3-result-content').hidden,false);
          get('v3-result-reason').value='Hay superiores que corregir';
          V3Results.setActive(true,true,catalog,false);
          assert.equal(get('v3-result-reason').value,'Hay superiores que corregir');
          get('v3-result-status').value='seguir_ajustando';
          await get('v3-result-form').events.submit({preventDefault(){}});
          assert.equal(requests.length,1);assert.equal(requests[0].config.run,'first');
          assert.equal(requests[0].config.status,'seguir_ajustando');
          V3Results.chooseRun('second');assert.equal(get('v3-result-status').value,'candidato');
          assert.match(get('v3-result-next').textContent,/no reemplaza el modelo oficial/);
          V3Results.setActive(true,false,catalog,false);assert.equal(get('v3-result-fields').disabled,true);
          catalog.v3_training.vision_release={run:'second',accepted_by:'Vicente'};
          V3Results.setActive(true,true,catalog,false);
          assert.equal(get('v3-result-form').hidden,true);
          assert.equal(get('v3-result-fields').disabled,true);
          assert.match(get('v3-result-decision').textContent,/Aceptado por Vicente/);
          await get('v3-result-form').events.submit({preventDefault(){}});
          assert.equal(requests.length,1);
          V3Results.setActive(false,true,catalog,false);assert.equal(get('results-legacy').hidden,false);
        })().catch(error=>{console.error(error);process.exitCode=1});
        """
        result=subprocess.run([node],input=prelude+source+assertions,text=True,encoding='utf-8',capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
