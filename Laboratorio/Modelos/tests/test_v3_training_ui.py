"""El seguimiento V3 usa el historial real para curvas, tabla y mejor época."""
from pathlib import Path
import shutil
import subprocess
import unittest

HERE = Path(__file__).resolve().parents[1]


class V3TrainingUITests(unittest.TestCase):
    def test_stable_defaults_without_planned_selection_and_poll_preserves_user_draft(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('Node.js no disponible')
        script = """
        const assert=require('node:assert/strict'),nodes=new Map();
        const document={getElementById(id){
          if(!nodes.has(id))nodes.set(id,{value:'',innerHTML:'',events:{},addEventListener(k,f){this.events[k]=f}});
          return nodes.get(id);
        }};
        const get=id=>document.getElementById(id),submit=()=>{throw Error('Must not auto train')};
        get('v3-train-source').value='active';
        """ + (HERE/'static/v3-training.js').read_text(encoding='utf-8') + """
        const model='Experimentos/stable/entrenamiento/weights/best.pt';
        const data={v3_training:{supported:true,exports:[{id:'active',counts:{train:336}}],selections:[],
          initial_models:[{id:model,label:'Estable'}],defaults:{model,name:'v3_refuerzo_actual',epochs:40,patience:10,lr:.0001}}};
        V3Training.setActive(true,true,data,[],false);
        for(const [key,value] of Object.entries(data.v3_training.defaults))assert.equal(get('v3-train-'+key).value,String(value));
        get('v3-train-name').value='mi_refuerzo';get('v3-train-lr').value='0.0002';
        V3Training.setActive(true,true,data,[],false);
        assert.equal(get('v3-train-name').value,'mi_refuerzo');assert.equal(get('v3-train-lr').value,'0.0002');
        """
        result = subprocess.run([node], input=script, capture_output=True, text=True, encoding='utf-8', timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_reduced_selection_updates_counts_preserves_draft_and_submits_only_on_click(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node.js no disponible')
        ui=(HERE/'static/v3-training.js').read_text(encoding='utf-8')
        prelude="""
        const assert=require('node:assert/strict'),nodes=new Map(),document={getElementById:id=>{
          if(!nodes.has(id))nodes.set(id,{value:'',innerHTML:'',textContent:'',dataset:{},events:{},addEventListener(k,fn){this.events[k]=fn}});
          return nodes.get(id)}};
        const get=id=>document.getElementById(id);let requests=[];
        const submit=async c=>requests.push(c),updateAvailability=()=>{};
        get('v3-train-source').value='export';get('v3-train-purpose').value='base';get('v3-train-model').value='yolo26n';
        for(const [key,value] of Object.entries({epochs:100,batch:2,lr:.001,seed:42,patience:20,imgsz:640}))get('v3-train-'+key).value=String(value);
        """
        assertions="""
        (async()=>{
          const selection={id:'reduced',source:'export',label:'Originales y vacía',trial_name:'v3_niveles_una_vacia',purpose:'Comparación controlada',development_counts:{train:166,val_real:28,val_sintetica:40}};
          const data={v3_training:{supported:true,defaults:{imgsz:640,batch:2},exports:[{id:'export',copy:'copy',author:'Vicente',counts:{train:326,val_real:28,val_sintetica:40,test_real:27,test_sintetica:36},excluded:1}],selections:[selection]}};
          V3Training.setActive(true,true,data,[],false);
          assert.equal(requests.length,0);assert.equal(get('v3-train-selection').value,'reduced');
          assert.match(get('v3-train-data').textContent,/166 fotos/);assert.match(get('v3-train-data').textContent,/63 fotos/);
          assert.match(get('v3-train-gallery').href,/selection=reduced/);assert.match(get('v3-train-gallery').textContent,/166/);assert.equal(get('v3-train-gallery').hidden,false);
          get('v3-train-name').value='mi_nombre';V3Training.setActive(true,true,data,[],false);assert.equal(get('v3-train-name').value,'mi_nombre');
          get('v3-train-selection').value='';get('v3-train-selection').events.change();assert.match(get('v3-train-data').textContent,/326 fotos/);
          assert.equal(get('v3-train-gallery').hidden,true);
          get('v3-train-imgsz').value='960';get('v3-train-batch').value='4';
          V3Training.chooseSelection('reduced');assert.equal(get('v3-train-name').value,'v3_niveles_una_vacia');assert.equal(get('v3-train-imgsz').value,'640');assert.equal(get('v3-train-batch').value,'2');
          await get('v3-train-form').events.submit({preventDefault(){}});
          assert.equal(requests.length,1);assert.equal(requests[0].selection,'reduced');assert.equal(requests[0].imgsz,640);
          const parent='Experimentos/parent/entrenamiento/weights/best.pt';
          data.v3_training.initial_models=[{id:'Modelos/preentrenados/yolo26n-seg.pt',label:'General'},{id:parent,label:'Actual best.pt'}];
          data.v3_training.selections.push({id:'fine',source:'export',label:'Afinado con repaso',trial_name:'v3_afinado',purpose:'Afinado',required_initial_model:parent,
            training_defaults:{model:parent,epochs:40,patience:10,lr:.0001,batch:2,imgsz:640,seed:42},development_counts:{train:113,val_real:22,val_sintetica:47}});
          V3Training.setActive(true,true,data,[],false);V3Training.chooseSelection('fine');
          assert.equal(get('v3-train-model').value,parent);assert.match(get('v3-train-model').innerHTML,/Actual best.pt/);
          assert.equal(get('v3-train-epochs').value,'40');assert.equal(get('v3-train-patience').value,'10');assert.equal(get('v3-train-lr').value,'0.0001');
          assert.match(get('v3-train-data').textContent,/113 fotos/);assert.equal(requests.length,1);
          get('v3-train-lr').value='0.00005';V3Training.setActive(true,true,data,[],false);assert.equal(get('v3-train-lr').value,'0.00005');
          V3Training.chooseSelection('fine');assert.equal(get('v3-train-lr').value,'0.0001');assert.equal(get('v3-train-model').value,parent);
        })().catch(error=>{console.error(error);process.exitCode=1});
        """
        result=subprocess.run([node],input=prelude+ui+assertions,text=True,encoding='utf-8',capture_output=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_history_updates_curves_best_epoch_table_and_empty_state_without_starting_jobs(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('Node.js no disponible')
        panel = (HERE / 'static/panel.js').read_text(encoding='utf-8-sig')
        helpers = panel[panel.index('function duration('):panel.index('let monitorDisplayState=')]
        logic = (HERE / 'static/lab-logic.js').read_text(encoding='utf-8-sig')
        ui = (HERE / 'static/v3-training.js').read_text(encoding='utf-8-sig')
        prelude = """
        const assert=require('node:assert/strict'),nodes=new Map();
        const document={getElementById:id=>{
          if(!nodes.has(id))nodes.set(id,{value:'',textContent:'',innerHTML:'',hidden:false,
            addEventListener(){},getAttribute(){return null},prepend(node){this.firstElementChild=node}});
          return nodes.get(id);
        }};
        const ImageNavigation={mount(){}},submit=()=>{throw Error('No iniciar entrenamiento')};
        const updateAvailability=()=>{},esc=String;
        """
        assertions = """
        const row=(epoch,map,train,val)=>({epoch,'metrics/mAP50-95(M)':map,'train/seg_loss':train,'val/seg_loss':val});
        const history=[row(1,.4,1.2,1.5)],run={id:'v3_run',history};
        const catalog={v3_training:{supported:true,exports:[],runs:[run]}};
        const job={id:'job',state:'running',config:{action:'train',pipeline:'geometria_nivel_v3',run:'v3_run',epochs:100},
          progress:{stage:'training',completed_epochs:1,current_epoch:2},started_at:new Date().toISOString()};
        const text=id=>document.getElementById(id).textContent,html=id=>document.getElementById(id).innerHTML;
        V3Training.setActive(true,true,catalog,[job],true);
        assert.match(html('v3-live-quality'),/<svg/);assert.match(html('v3-live-loss'),/stroke-dasharray/);
        assert.equal(text('v3-training-best'),'0.400');assert.match(text('v3-training-best-epoch'),/época 1/);
        assert.match(html('v3-training-history'),/1.500/);
        assert.equal(document.getElementById('v3-training').firstElementChild,document.getElementById('v3-training-monitor'));
        history.push(row(2,.7,.8,1.1));job.progress.completed_epochs=2;job.progress.current_epoch=3;
        V3Training.setActive(true,true,catalog,[job],true);
        assert.equal(text('v3-training-map'),'0.700');assert.equal(text('v3-training-loss'),'0.800');
        assert.match(text('v3-training-best-epoch'),/época 2/);assert.match(html('v3-training-history'),/1.100/);
        assert.match(text('v3-training-count'),/Época 3 de 100 en curso/);
        V3Training.setActive(true,true,catalog,[{id:'prediction',state:'running',config:{action:'predict',pipeline:'geometria_nivel_v3'}},job],true);
        assert.equal(text('v3-training-map'),'0.700');assert.match(text('v3-training-count'),/Época 3 de 100/);
        run.history=[];job.id='empty';job.progress.completed_epochs=0;
        V3Training.setActive(true,true,catalog,[job],true);
        assert.equal(text('v3-training-map'),'—');assert.doesNotMatch(html('v3-live-quality'),/<svg/);
        assert.match(html('v3-live-quality'),/primeras métricas/);
        """
        result = subprocess.run([node], input=prelude + logic + helpers + ui + assertions,
            capture_output=True, text=True, encoding='utf-8', timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
