"""Ejecuta las transiciones reales del visor con Node y un DOM mínimo."""
from pathlib import Path
import re
import shutil
import subprocess
import unittest

HTML = Path(__file__).with_name('interfaz.html').read_text(encoding='utf-8')
SCRIPT = re.search(r'<script>(.*?)</script>', HTML, re.S).group(1)
HARNESS = r"""
const assert=require('node:assert/strict');
const elements=new Map();
class Element {
  constructor(){this.hidden=false;this.disabled=false;this.value='';this.listeners={};this.attrs={};this.options=[];this.classList={add(){},remove(){}}}
  set innerHTML(value){this.html=value;if(value.includes('<option')){this.options=[...value.matchAll(/<option value="([^"]+)">([^<]*)<\/option>/g)].map(m=>({value:m[1],textContent:m[2]}));this.value=this.options[0]?.value||''}}
  get innerHTML(){return this.html||''}
  get selectedOptions(){return this.options.filter(o=>o.value===this.value)}
  addEventListener(type,handler){this.listeners[type]=handler}
  setAttribute(key,value){this.attrs[key]=value}
  removeAttribute(key){delete this[key];delete this.attrs[key]}
  focus(){document.activeElement=this}
  scrollIntoView(){}
}
global.document={getElementById(id){if(!elements.has(id))elements.set(id,new Element());return elements.get(id)},querySelector(selector){return this.getElementById(selector)}};
global.window={addEventListener(){}};
global.matchMedia=()=>({matches:false});
global.URL.createObjectURL=()=> 'blob:original';global.URL.revokeObjectURL=()=>{};
document.getElementById('edge-view').innerHTML='<option value="occupancy_image_url">Mapa de señal</option><option value="filtered_edges_image_url">Bordes dentro de los niveles</option><option value="edges_image_url">Bordes de la foto</option>';
const fixtures=[{id:'YOLO11-1',name:'YOLO11-1'},{id:'YOLO26-1',name:'YOLO26-1'},
 {id:'V2-YOLO11',name:'V2-YOLO11',states:[{key:'reponer',label:'Reponer',color:'#f00'},{key:'suficiente',label:'Suficiente',color:'#080'}]},
 {id:'V2-YOLO26',name:'V2-YOLO26',states:[{key:'reponer',label:'Reponer',color:'#f00'},{key:'suficiente',label:'Suficiente',color:'#080'}]}];
global.fetch=async()=>({ok:true,json:async()=>({models:fixtures})});
function prediction(edges=true){return {counts:{reponer:1,suficiente:0},detections:[{id:1,label:'Reponer',confidence:.9}],model:'V2-YOLO26',device:'cpu',seconds:1,image_url:'data:levels',...(edges?{occupancy:{},occupancy_image_url:'data:signal',edges_image_url:'data:edges',filtered_edges_image_url:'data:filtered'}:{})}}
"""


class VisionInterfaceTests(unittest.TestCase):
    def js(self, body):
        code = HARNESS + SCRIPT + '\nsetImmediate(async()=>{try{' + body + "\n}catch(error){console.error(error);process.exitCode=1}});"
        result = subprocess.run([shutil.which('node') or 'node', '-e', code], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_version_filters_models_and_changes_the_states(self):
        self.js("""
        assert.equal($('version').value,'v2');assert.equal($('model').value,'V2-YOLO26');
        assert.deepEqual($('model').options.map(o=>o.value),['V2-YOLO11','V2-YOLO26']);
        assert.deepEqual(states.map(s=>s[0]),['reponer','suficiente']);
        $('version').value='v1';$('version').listeners.change();
        assert.deepEqual($('model').options.map(o=>o.value),['YOLO11-1','YOLO26-1']);
        assert.equal(states.length,4);assert.equal($('view-result').disabled,true);
        """)

    def test_compare_and_edge_maps_use_the_same_current_photo(self):
        self.js("""
        choose({name:'foto.jpg',size:100,type:'image/jpeg'});show(prediction());
        view('compare');assert.equal($('photo').hidden,true);assert.equal($('comparison').hidden,false);
        assert.equal($('compare-original').src,'blob:original');assert.equal($('compare-result').src,'data:levels');
        view('edges');assert.equal($('photo').src,'data:signal');assert.equal($('edge-controls').hidden,false);
        $('edge-view').value='filtered_edges_image_url';$('edge-view').listeners.change();
        assert.equal($('photo').src,'data:filtered');
        assert.equal($('viewport').attrs['aria-labelledby'],'view-edges');
        """)

    def test_parameter_changes_clear_old_results_and_pure_yolo_has_no_edges(self):
        self.js("""
        choose({name:'foto.jpg',size:100,type:'image/jpeg'});
        for(const control of ['model','method','confidence','version']){
          show(prediction());view('compare');
          if(control==='confidence'){$('confidence').value='.5';$('confidence').listeners.input()}
          else $(''+control).listeners.change();
          assert.equal(result,null);assert.equal($('view-edges').disabled,true);
          assert.equal($('comparison').hidden,true);assert.equal($('compare-result').src,undefined);
          assert.equal($('photo').src,'blob:original');assert.equal($('download').href,undefined);
        }
        show(prediction(false));assert.equal($('view-edges').disabled,true);
        view('edges');assert.equal($('photo').src,'data:levels');
        choose({name:'otra.png',size:120,type:'image/png'});assert.equal(result,null);
        """)

    def test_keyboard_skips_unavailable_tabs_and_wraps(self):
        self.js("""
        choose({name:'foto.jpg',size:100,type:'image/jpeg'});show(prediction(false));
        $('view-result').focus();let prevented=false;
        document.querySelector('[role=tablist]').listeners.keydown({key:'ArrowRight',preventDefault(){prevented=true}});
        assert.equal(prevented,true);assert.equal(document.activeElement,$('view-compare'));
        assert.equal($('view-compare').tabIndex,0);assert.equal($('view-result').tabIndex,-1);
        document.querySelector('[role=tablist]').listeners.keydown({key:'ArrowRight',preventDefault(){}});
        assert.equal(document.activeElement,$('view-original'));
        """)

    def test_summary_attributes_predictions_to_the_model_without_claiming_accuracy(self):
        self.js("""
        choose({name:'foto.jpg',size:100,type:'image/jpeg'});show(prediction());
        assert.match($('summary').innerHTML,/El modelo V2-YOLO26 encontró 1 nivel/);
        assert.match($('summary').innerHTML,/no tiene anotaciones de referencia/);
        show({...prediction(false),detections:[],counts:{}});
        assert.match($('summary').innerHTML,/El modelo V2-YOLO26 no encontró niveles/);
        """)


if __name__ == '__main__':
    unittest.main()
