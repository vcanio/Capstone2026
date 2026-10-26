"""Orientación, continuidad de IDs y decisiones humanas, sin GPU ni CVAT."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import panel_modelos as panel

HERE = Path(__file__).resolve().parents[1]


class WorkspaceStateTests(unittest.TestCase):
    def js(self, code):
        node = shutil.which('node')
        if not node:
            self.skipTest('Node.js no disponible')
        script = (HERE / 'static/lab-logic.js').read_text(encoding='utf-8')
        result = subprocess.run([node], input=script + "\nconst assert=require('node:assert/strict');\n" + code,
                                text=True, encoding='utf-8', capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_new_copy_does_not_invalidate_historical_model(self):
        self.js("""
        const copy={id:'new',state:'pendiente_revision',report:{bloqueos_entrenamiento:0}};
        const run={id:'old',ready:true,config:{source:'old-copy'},comparisons:[{split:'val'}]};
        const data={datasets:[copy],runs:[run],models:[{id:'old/best.pt',run:'old'}]};
        const connection={phase:'ready',activityKnown:true};
        let s=Lab.workspaceState(data,'new','old',[],connection,'v2');
        assert.equal(s.kind,'review');assert.equal(s.model.id,'old/best.pt');assert.equal(s.evaluation,'disponible');
        copy.report.bloqueos_entrenamiento=2;s=Lab.workspaceState(data,'new','old',[],connection,'v2');
        assert.equal(s.kind,'blocked');assert.equal(s.model.run,'old');
        copy.report.bloqueos_entrenamiento=0;copy.state='lista_niveles';
        assert.equal(Lab.workspaceState(data,'new','old',[],connection,'v2').kind,'ready');
        run.config.source='new';assert.equal(Lab.workspaceState(data,'new','old',[],connection,'v2').kind,'results');
        assert.equal(Lab.workspaceState(data,'new','old',[],{...connection,activityError:'falló'},'v2').kind,'error');
        """)

    def test_active_failure_missing_evaluation_and_v3_are_separate(self):
        self.js("""
        const copy={id:'copy',state:'lista_niveles',report:{}},run={id:'run',ready:true,config:{source:'copy'}};
        const data={datasets:[copy],runs:[run],models:[{id:'run/best.pt',run:'run'}]},c={phase:'ready',activityKnown:true};
        const job={id:'job',state:'running',config:{action:'train',run:'run'},progress:{stage:'evaluating'}};
        let s=Lab.workspaceState(data,'copy','run',[job],c,'v2');assert.equal(s.kind,'active');assert.equal(s.trialState,'evaluando');
        job.state='interrupted';job.error='reinicio';s=Lab.workspaceState(data,'copy','run',[job],c,'v2');
        assert.equal(s.kind,'failed');assert.match(s.reason,/reinicio/);assert.equal(s.job.id,'job');
        job.config.run='unrelated';assert.equal(Lab.workspaceState(data,'copy','run',[job],c,'v2').kind,'evaluation');
        assert.equal(Lab.workspaceState(data,'copy','run',[],c,'v3').kind,'v3');
        assert.equal(Lab.versionOf({manifest:{clases:['Nivel']}}),'v3');
        assert.equal(Lab.workspaceState({datasets:[],runs:[],models:[]},'', '',[],c,'v2').kind,'empty');
        """)

    def test_contextual_prediction_keeps_exact_weights_and_missing_id_does_not_fallback(self):
        source = (HERE / 'static/panel.js').read_text(encoding='utf-8')
        action = source[source.index('function contextAction('):source.index('function renderReviewReceipt(')]
        self.js("""
        const nodes=new Map(),$=id=>{if(!nodes.has(id))nodes.set(id,{value:'',checked:false});return nodes.get(id)};
        const data={datasets:[],runs:[{id:'run'}],models:[{id:'run/last.pt',run:'run',imgsz:960}]};
        const pendingChoices=new Set(['model','run']);let view='',problem='';
        const renderModelOptions=()=>{},resetPrediction=()=>{},renderOriginal=()=>{},modelHelp=()=>{},
          renderWorkspace=()=>{},saveUiPreferences=()=>{},switchTab=id=>view=id,error=text=>problem=text;
        """ + action + """
        contextAction('predict','run/last.pt');assert.equal($('model').value,'run/last.pt');
        assert.equal($('predict-size').value,'960');assert.equal(view,'predict');assert.equal(pendingChoices.has('model'),false);
        contextAction('predict','missing/best.pt');assert.match(problem,/ya no están disponibles/);
        assert.equal($('model').value,'run/last.pt');contextAction('results','run');assert.equal($('run').value,'run');
        """)


class DecisionTests(unittest.TestCase):
    def test_training_keeps_purpose_and_reference_and_rejects_unintegrated_v3(self):
        run={'id':'source','ready':True,'manifest':{'clases':['Nivel_reponer','Nivel_suficiente']}}
        data={'runs':[run],'datasets':[],'models':[{'id':'general.pt'}]}
        config=dict(action='train',model='general.pt',source='source',name='fixture',epochs=1,batch=1,
                    lr=0.001,seed=42,imgsz=640,purpose='Comparar bordes',reference_run='source')
        result=panel.validate(config,data)
        self.assertEqual(result['purpose'],'Comparar bordes')
        self.assertEqual(result['reference_run'],'source')
        with self.assertRaises(ValueError):panel.validate({**config,'purpose':'x'*1001},data)
        with self.assertRaises(ValueError):panel.validate({**config,'reference_run':'missing'},data)
        run['manifest']['clases']=['Nivel']
        with self.assertRaisesRegex(ValueError,'V3 requiere'):panel.validate(config,data)

    def test_decision_history_is_atomic_and_does_not_change_metrics(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);run=root/'Laboratorio/Experimentos'/'fixture';run.mkdir(parents=True)
            (run/'manifest.json').write_text('{}');metrics=run/'metricas_validacion.json';metrics.write_text('{"score": 0.6}')
            config={'run':'fixture','status':'candidato','reason':'Revisar escenas nuevas','author':'Vicente'}
            with patch.object(panel,'ROOT',root),patch.object(panel,'invalidate_catalog'):
                panel.record_decision(config)
                panel.record_decision({**config,'status':'seguir_ajustando','reason':'Faltan casos críticos'})
                for invalid in ({**config,'run':'../otro'},{**config,'reason':''},{**config,'author':'x'},{**config,'status':'validado'}):
                    with self.assertRaises(ValueError):panel.record_decision(invalid)
            saved=json.loads((run/'decision_modelo.json').read_text(encoding='utf-8'))
            self.assertEqual(len(saved['history']),2)
            self.assertEqual(saved['current']['status'],'seguir_ajustando')
            self.assertEqual(metrics.read_text(),'{"score": 0.6}')


if __name__=='__main__':unittest.main()
