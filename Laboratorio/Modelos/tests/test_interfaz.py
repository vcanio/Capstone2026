"""Casos de estados del panel: Node ejecuta las funciones reales sin DOM ni ML."""
from pathlib import Path
from panel_source import read_panel
import re
import shutil
import subprocess
import unittest

HERE = Path(__file__).resolve().parents[1]


class InterfaceTests(unittest.TestCase):
    def test_decision_uses_the_expanded_evaluation_when_available(self):
        self.js("""
        const assert=require('node:assert/strict');
        const run={id:'base',ready:true,manifest:{scope:'Nivel_estados',clases:['Nivel_reponer','Nivel_suficiente'],imagenes:[]},
          availability:{val:{alertas:{reales:1,acertadas:1,falsas:0}}},
          development_evaluation:{metrics:{fotos:40,alertas:{reales:69,acertadas:66,falsas:15}}}};
        assert.match(Lab.resultDecision(run,'YOLO26').title,/YOLO26 reconoció 66 de 69 niveles/);
        assert.match(Lab.resultDecision(run).detail,/Omitió 3 niveles/);
        assert.match(Lab.resultDecision(run).detail,/anotaciones revisadas de 40 fotos/);
        assert.match(Lab.evaluationContext(run),/40 fotos/);
        """)

    def test_prediction_photos_follow_selected_model_without_changing_other_catalogs(self):
        self.js("""
        const assert=require('node:assert/strict');
        const catalog={images:[{id:'train'},{id:'val'},{id:'new'}],models:[
          {id:'a',training_images:['train']},{id:'b',training_images:['val']},
          {id:'all',training_images:['train','val','new']},{id:'general',run:null}]};
        assert.deepEqual(Lab.predictionImages(catalog,'a').map(i=>i.id),['val','new']);
        assert.deepEqual(Lab.predictionImages(catalog,'b').map(i=>i.id),['train','new']);
        assert.deepEqual(Lab.predictionImages(catalog,'all'),[]);
        assert.deepEqual(Lab.predictionImages(catalog,'missing'),[]);
        assert.equal(Lab.predictionImages(catalog,'general').length,3);
        assert.equal(catalog.images.length,3);
        """)

    def test_paulo_percentages_do_not_change_yolo_alerts_or_turn_missing_into_zero(self):
        self.js("""
        const assert=require('node:assert/strict');
        const detections=[{id:1,clase:'Nivel_reponer',occupancy:{area_signal_pct:95,width_signal_pct:100}},
          {id:2,clase:'Nivel_suficiente',occupancy:{area_signal_pct:null,width_signal_pct:null}}];
        assert.equal(PredictionDemo.summary(detections,'Nivel_estados',['reponer','suficiente']).alerts,1);
        const rows=PredictionDemo.occupancyRows(detections);
        assert.match(PredictionDemo.occupancyRevision('paulo_mascara_v2_color_textura'),/Revisión 2/);
        assert.match(PredictionDemo.occupancyRevision('paulo_mascara_v1'),/Revisión 1/);
        assert.match(PredictionDemo.occupancyRevision('paulo_mascara_v2_combinacion_ponderada'),/Bordes V2/);
        assert.deepEqual(PredictionDemo.methodConfig('yolo_paulo_v2'),{occupancy:true,occupancy_version:'v2'});
        assert.deepEqual(PredictionDemo.methodConfig('yolo_paulo'),{occupancy:true,occupancy_version:'v1'});
        assert.deepEqual(PredictionDemo.methodConfig('yolo'),{occupancy:false,occupancy_version:'v1'});
        assert.match(PredictionDemo.methodHelp('yolo_paulo_v2'),/70 %/);
        assert.equal(PredictionDemo.occupancyRows([{occupancy:{combined_signal_pct:0}}])[0].combined,'0.0 %');
        assert.equal(rows[1].combined,'Sin medición');
        assert.equal(rows[0].width,'100.0 %');assert.equal(rows[1].area,'Sin medición');
        assert.equal(rows[0].state,'Reponer');
        """)

    def test_project_versions_filter_datasets_models_and_archives_together(self):
        self.js("""
        const assert=require('node:assert/strict');
        const old={id:'old',scope:'Nivel_estados',manifest:{clases:['Nivel_vacio','Nivel_suficiente']}};
        const base={id:'base',report:{clases:['Nivel_reponer','Nivel_suficiente']},state:'lista_niveles'};
        const later={id:'later',manifest:{clases:['Nivel_reponer','Nivel_suficiente','Nivel_no_evaluable']}};
        old.manifest.imagenes=[{imagen_id:'real_old',split:'train'}];
        const catalog={runs:[old,later],datasets:[base],images:[{name:'real_old'},{name:'base_photo',project_version:'v2'}],models:[{id:'general.pt'},{id:'old/best.pt',run:'old'},{id:'later/best.pt',run:'later'}],archived_datasets:[base],archived_models:[{id:'old/last.pt',run:'old'}]};
        const v2=Lab.versionCatalog(catalog,'v2');
        assert.deepEqual(v2.runs.map(r=>r.id),['later']);
        assert.deepEqual(v2.datasets.map(r=>r.id),['base']);
        assert.deepEqual(v2.models.map(m=>m.id),['general.pt','later/best.pt']);
        assert.equal(v2.archived_models.length,0);
        assert.equal(v2.archived_datasets.length,1);
        assert.deepEqual(v2.images.map(i=>i.name),['base_photo']);
        const v1=Lab.versionCatalog(catalog,'v1');
        assert.deepEqual(v1.runs.map(r=>r.id),['old']);
        assert.equal(v1.datasets.length,0);
        assert.equal(v1.archived_models.length,1);
        assert.deepEqual(v1.images.map(i=>i.name),['real_old']);
        assert.equal(catalog.models.length,3);
        """)

    def test_version_status_distinguishes_ready_data_from_a_trained_model(self):
        self.js("""
        const assert=require('node:assert/strict');
        const dataset={id:'base',report:{clases:['Nivel_reponer','Nivel_suficiente']},state:'lista_niveles'};
        const run={id:'train_v2',ready:true,manifest:{clases:dataset.report.clases}};
        const catalog={runs:[],datasets:[dataset],models:[{id:'general.pt'}]};
        assert.match(Lab.versionStatus(catalog,'v2'),/Datos preparados/);
        assert.match(Lab.versionStatus(catalog,'v1'),/Sin datos/);
        catalog.runs.push(run);catalog.models.push({id:'train_v2/best.pt',run:run.id});
        assert.match(Lab.versionStatus(catalog,'v2'),/Modelo disponible/);
        assert.match(Lab.versionStatus(catalog,'v2',[{state:'running',config:{action:'train',run:run.id}}]),/Entrenando/);
        assert.match(Lab.versionStatus(catalog,'v2',[{state:'running',config:{action:'train',run:'new_run',source:run.id}}]),/Entrenando/);
        """)

    def test_cvat_sources_follow_criterion_and_keep_visibility_in_v2(self):
        self.js("""
        const assert=require('node:assert/strict');
        assert.equal(Lab.versionOf({task_id:16}),'v1');
        assert.equal(Lab.versionOf({task_id:19}),'v2');
        assert.equal(Lab.versionOf({task_id:22}),'v2');
        assert.equal(Lab.versionOf({criterion_version:'disponibilidad_visual_nivel_v2_reponer'}),'v2');
        assert.equal(Lab.versionOf({scope:'Modulo'}),'otros');
        """)

    def test_schema_profiles_follow_dataset_metadata(self):
        self.js("""
        const assert=require('node:assert/strict');
        const v1={scope:'Nivel_estados',report:{clases:['Nivel_vacio','Nivel_baja_disponibilidad','Nivel_suficiente','Nivel_no_evaluable']}};
        const base={report:{clases:['Nivel_reponer','Nivel_suficiente']}};
        const complete={manifest:{clases:['Nivel_reponer','Nivel_suficiente','Nivel_no_evaluable']}};
        assert.equal(Lab.profile(v1).label,'v1 · 4 estados');
        assert.equal(Lab.profile(base).id,'v2_base');
        assert.equal(Lab.profile(complete).id,'v2_visibilidad');
        assert.deepEqual(Lab.profile(base).states,['reponer','suficiente']);
        assert.deepEqual(Lab.profile({}).states,[]);
        """)

    def test_new_criterion_does_not_hide_v1_demo_weights(self):
        self.js("""
        const assert=require('node:assert/strict');
        const catalog={runs:[
          {id:'v1',ready:true,manifest:{scope:'Nivel_estados',clases:['Nivel_vacio','Nivel_baja_disponibilidad','Nivel_suficiente','Nivel_no_evaluable']},config:{model:'general.pt'}},
          {id:'v2',ready:true,manifest:{scope:'Nivel_estados',clases:['Nivel_reponer','Nivel_suficiente']},config:{model:'general.pt'}}],
          models:[{id:'v1/best.pt',run:'v1'},{id:'v2/best.pt',run:'v2'}]};
        assert.deepEqual(Lab.modelChoices(catalog).map(m=>m.run).sort(),['v1','v2']);
        const [v1,v2]=catalog.runs.map(r=>({...r,signature:'same',evaluation_protocol:{confidence:0.25,iou:0.5}}));
        assert.equal(Lab.comparable(v1,v2),false);
        assert.equal(Lab.comparable(v1,{...v1,id:'v1b'}),true);
        """)

    def test_v2_prediction_uses_restock_and_binary_model_classes(self):
        self.js("""
        const assert=require('node:assert/strict');
        const result=PredictionDemo.summary([{clase:'Nivel_reponer'},{clase:'Nivel_suficiente'}],
          'Nivel_estados',['reponer','suficiente']);
        assert.equal(result.alerts,1);
        assert.equal(result.counts.reponer,1);
        assert.equal(result.counts.suficiente,1);
        assert.deepEqual(result.states.map(s=>s.key),['reponer','suficiente']);
        assert.equal(PredictionDemo.summary([{clase:'Nivel_suficiente'}],'Nivel_estados').alerts,0);
        """)

    def test_results_start_with_a_recent_evaluated_run_of_the_current_scope(self):
        self.js("""
        const assert=require('node:assert/strict');
        const catalog={runs:[{id:'piloto_20261009_054145_0441',ready:true},
          {id:'niveles_yolo11_20261013_050854_b679',ready:true,scope:'Nivel_estados'},
          {id:'niveles_yolo26_20261013_052316_6893',ready:true,scope:'Nivel_estados'},
          {id:'niveles_20261014_100000_abcd',ready:false,scope:'Nivel_estados'},
          {id:'verificacion_panel_20261014_110000_abcd',ready:true,scope:'Nivel_estados'}]};
        assert.equal(Lab.defaultRun(catalog,'Nivel_estados'),'niveles_yolo26_20261013_052316_6893');
        assert.equal(Lab.defaultRun(catalog,'Modulo'),'piloto_20261009_054145_0441');
        assert.equal(Lab.defaultRun({runs:catalog.runs.slice(0,1)},'Nivel_estados'),'');
        """)

    def test_alert_decision_does_not_confuse_localization_with_correct_states(self):
        self.js("""
        const assert=require('node:assert/strict');
        const run={id:'niveles_ensayo',ready:true,scope:'Nivel_estados',
          comparisons:[{split:'val',aciertos:50,anotados:50}],
          availability:{val:{alertas:{reales:4,acertadas:0,falsas:2}}}};
        const decision=Lab.resultDecision(run);
        assert.equal(decision.kind,'attention');
        assert.match(decision.title,/0 de 4 niveles/);
        assert.match(decision.detail,/Omitió 4 niveles/);
        assert.match(decision.detail,/2 falsas alertas/);
        run.availability.val.alertas.acertadas=4;
        assert.equal(Lab.resultDecision(run).kind,'observed');
        assert.match(Lab.resultDecision(run).detail,/2 falsas alertas/);
        """)

    def test_missing_alert_evidence_is_not_reported_as_success(self):
        self.js("""
        const assert=require('node:assert/strict');
        const run={id:'niveles_ensayo',ready:true,manifest:{scope:'Nivel_estados'}};
        assert.equal(Lab.resultDecision(run).kind,'limited');
        assert.match(Lab.resultDecision(run).title,/no hay métricas/);
        run.availability={val:{alertas:{reales:0,acertadas:0,falsas:0}}};
        assert.match(Lab.resultDecision(run).title,/no tiene niveles anotados/);
        assert.equal(Lab.resultDecision({...run,ready:false}).kind,'limited');
        const technical={...run,id:'verificacion_panel_1'};
        assert.match(Lab.resultDecision(technical).title,/funcionamiento del panel/);
        assert.match(Lab.resultDecision({id:'modulos',ready:true,
          comparisons:[{split:'train',aciertos:10,anotados:10},
                       {split:'val',aciertos:2,anotados:3}]}).title,/2 de 3 módulos/);
        """)

    def test_prediction_recommends_weights_for_the_selected_scope(self):
        self.js("""
        const assert=require('node:assert/strict');
        const catalog={runs:[{id:'piloto_01_a',ready:true,scope:'Modulo'},
          {id:'niveles_20261013_050000_abcd',ready:true,manifest:{scope:'Nivel_estados'}}],
          models:[{id:'pilot/best.pt',run:'piloto_01_a'},
          {id:'level/last.pt',run:'niveles_20261013_050000_abcd'},
          {id:'level/best.pt',run:'niveles_20261013_050000_abcd'},
          {id:'general.pt',run:null}]};
        assert.equal(Lab.defaultModel(catalog,'predict','Nivel_estados'),'level/best.pt');
        assert.equal(Lab.defaultModel(catalog,'predict','Modulo'),'pilot/best.pt');
        assert.equal(Lab.defaultModel(catalog,'train','Nivel_estados'),'general.pt');
        catalog.models=catalog.models.filter(m=>!m.id.startsWith('level/'));
        assert.equal(Lab.defaultModel(catalog,'predict','Nivel_estados'),'general.pt');
        """)

    def test_training_progress_uses_completed_epochs_and_handles_early_stop(self):
        self.js("""
        const assert=require('node:assert/strict');
        const job={state:'running',config:{epochs:100},progress:{stage:'evaluating',current_epoch:19,
          started_at:'2026-10-13T12:00:00Z',updated_at:'2026-10-13T12:18:00Z'}};
        const run={history:[{epoch:1,'metrics/mAP50-95(M)':0.5},
          {epoch:18,'metrics/mAP50-95(M)':0.4}]};
        const state=Lab.trainingState(job,run,Date.parse('2026-10-13T12:19:00Z'));
        assert.equal(state.completed,18);assert.equal(state.percent,18);assert.equal(state.stage,'evaluating');
        assert.equal(state.best.epoch,1);assert.equal(state.elapsed,1140);
        job.state='done';const done=Lab.trainingState(job,run,Date.parse('2026-10-13T14:00:00Z'));
        assert.equal(done.stage,'done');assert.equal(done.completed,18);assert.equal(done.percent,18);
        assert.equal(done.elapsed,1080);assert.equal(done.terminal,true);
        """)

    def test_training_without_telemetry_does_not_invent_measurements(self):
        self.js("""
        const assert=require('node:assert/strict');
        const job={state:'running',config:{}};
        const state=Lab.trainingState(job,null);
        assert.equal(state.stage,'unknown');assert.equal(state.total,null);
        assert.equal(state.percent,null);assert.equal(state.elapsed,null);assert.equal(state.best,null);
        const failed=Lab.trainingState({...job,state:'error',progress:{stage:'preparing'}},null);
        assert.equal(failed.stage,'preparing');assert.equal(failed.terminal,true);
        """)

    def test_levels_ready_and_geometry_blocking_are_independent_of_modules(self):
        self.js("""
        const assert=require('node:assert/strict');
        const ready={id:'levels',scope:'Nivel_estados',state:'lista_niveles',report:{bloqueos_modulos:0,bloqueos_entrenamiento:0}};
        const broken={...ready,id:'broken',state:'pendiente_revision',report:{bloqueos_modulos:0,bloqueos_entrenamiento:1}};
        const connection={phase:'ready',activityKnown:true};
        assert.equal(Lab.homeState({datasets:[ready]},'levels',[],connection).kind,'ready');
        assert.equal(Lab.homeState({datasets:[ready,broken]},'broken',[],connection).kind,'blocked');
        const groups=Lab.reportGroups({incidencias:[{bloquea_entrenamiento:true,bloquea_modulos:false,categoria:'niveles'}]});
        assert.equal(groups.blocks.length,1);assert.equal(groups.levels.length,0);
        """)

    def test_level_history_does_not_hide_module_copy_of_same_people(self):
        self.js("""
        const assert=require('node:assert/strict');
        const sources=[{job_id:33,assignee:{username:'vi.canio'}}];
        const groups=Lab.copiesByPerson([{id:'a',scope:'Modulo',sources,created_at:'2026-10-01'},
          {id:'b',scope:'Nivel_estados',sources,created_at:'2026-10-13'}]);
        assert.equal(groups.length,2);assert.equal(groups[0].person,'Vicente');
        """)

    def test_task_16_does_not_hide_task_15_of_same_people(self):
        self.js("""
        const assert=require('node:assert/strict');
        const copies=[{id:'old',scope:'Nivel_estados',sources:[{job_id:33,assignee:{username:'vi.canio'}}]},
          {id:'new',scope:'Nivel_estados',sources:[{job_id:36,assignee:{username:'vi.canio'}}]}];
        assert.equal(Lab.copiesByPerson(copies).length,2);
        """)
    @classmethod
    def setUpClass(cls):
        cls.node = shutil.which('node')
        if not cls.node:
            raise RuntimeError('Se necesita Node.js para comprobar los estados de la interfaz.')
        cls.html = read_panel()
        cls.logic = re.search(r'<script id="lab-logic">(.*?)</script>', cls.html, re.S).group(1)
        cls.logic += '\n' + re.search(r'<script id="prediction-demo-logic">(.*?)</script>', cls.html, re.S).group(1)

    def test_photo_demo_distinguishes_critical_non_evaluable_and_empty_results(self):
        self.js("""
        const assert=require('node:assert/strict');
        const mixed=PredictionDemo.summary([{clase:'Nivel_vacio'},{clase:'Nivel_baja_disponibilidad'},
          {clase:'Nivel_suficiente'},{clase:'Nivel_no_evaluable'}],'Nivel_estados');
        assert.equal(mixed.alerts,2);assert.equal(mixed.total,4);
        assert.match(mixed.title,/posibles faltantes/);
        const obscured=PredictionDemo.summary([{clase:'Nivel_no_evaluable'}],'Nivel_estados');
        assert.equal(obscured.alerts,0);assert.match(obscured.title,/no son evaluables/);
        assert.doesNotMatch(obscured.title,/suficientes/);
        const empty=PredictionDemo.summary([],'Nivel_estados');
        assert.match(empty.title,/No se detectaron niveles/);
        assert.doesNotMatch(empty.title,/suficientes/);
        const generic=PredictionDemo.summary([{clase:'person'}]);
        assert.equal(generic.levels,false);assert.match(generic.detail,/modelo general/);
        """)

    def js(self, assertions):
        result = subprocess.run([self.node], input=self.logic + '\n' + assertions,
                                capture_output=True, text=True, encoding='utf-8', timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selected_blocked_copy_beats_old_ready_copy(self):
        self.js("""
        const assert=require('node:assert/strict');
        const old={id:'old',created_at:'2026-10-01',state:'lista_modulos',report:{bloqueos_modulos:0}};
        const fresh={id:'fresh',created_at:'2026-10-06',state:'pendiente_revision',report:{bloqueos_modulos:2}};
        const data={datasets:[old,fresh]},connection={phase:'ready',activityKnown:true};
        const state=Lab.homeState(data,'fresh',[],connection);
        assert.equal(state.kind,'blocked');assert.equal(state.copy.id,'fresh');assert.equal(state.alternative.id,'old');
        assert.equal(Lab.currentCopy(data,null).id,'fresh');
        assert.equal(Lab.homeState(data,'old',[],connection).kind,'ready');
        """)

    def test_copies_are_grouped_by_person_and_latest_is_not_an_approval(self):
        self.js("""
        const assert=require('node:assert/strict');
        const copies=[
          {id:'vi-old',created_at:'2026-10-01',state:'lista_modulos',sources:[{job_id:28}]},
          {id:'pau',created_at:'2026-10-04',sources:[{job_id:29}]},
          {id:'vi-new',created_at:'2026-10-06',state:'pendiente_revision',sources:[{job_id:28}]}];
        const groups=Lab.copiesByPerson(copies),vi=groups.find(g=>g.person==='Vilches');
        assert.equal(groups.length,2);assert.equal(vi.latest.id,'vi-new');
        assert.equal(vi.latest.state,'pendiente_revision');assert.equal(vi.history[0].id,'vi-old');
        assert.equal(copies[0].id,'vi-old');
        """)

    def test_other_jobs_use_assignee_or_explicit_job_name(self):
        self.js("""
        const assert=require('node:assert/strict');
        const groups=Lab.copiesByPerson([
          {id:'a',created_at:'2026-10-06',sources:[{job_id:30,assignee:{username:'vi.canio'}}]},
          {id:'b',created_at:'2026-10-07',sources:[{job_id:31}]}]);
        assert.ok(groups.some(g=>g.person==='Vicente'));assert.ok(groups.some(g=>g.person==='Trabajo 31'));
        """)

    def test_loading_error_and_active_do_not_imply_empty_data(self):
        self.js("""
        const assert=require('node:assert/strict'),data={datasets:[]};
        assert.equal(Lab.homeState(data,null,[],{phase:'loading'}).kind,'loading');
        assert.equal(Lab.homeState(data,null,[],{phase:'error',error:'offline'}).kind,'error');
        assert.equal(Lab.homeState(data,null,[],{phase:'ready',activityKnown:false}).kind,'loading');
        assert.equal(Lab.homeState(data,null,[],{phase:'ready',activityKnown:false,activityError:'offline'}).kind,'error');
        assert.equal(Lab.homeState(data,null,[{state:'running',config:{action:'train'}}],{phase:'ready',activityKnown:true}).kind,'active');
        assert.equal(Lab.homeState(data,null,[],{phase:'ready',activityKnown:true}).kind,'empty');
        """)

    def test_human_review_still_required_after_technical_checks(self):
        self.js("""
        const assert=require('node:assert/strict');
        const copy={id:'copy',created_at:'2026-10-06',state:'pendiente_revision',report:{bloqueos_modulos:0}};
        const data={datasets:[copy]},connection={phase:'ready',activityKnown:true};
        assert.equal(Lab.homeState(data,'copy',[],connection).kind,'review');
        copy.state='lista_modulos';assert.equal(Lab.homeState(data,'copy',[],connection).kind,'ready');
        copy.report.bloqueos_modulos=1;assert.equal(Lab.homeState(data,'copy',[],connection).kind,'blocked');
        """)

    def test_optional_attributes_are_separate_and_do_not_skip_human_review(self):
        self.js("""
        const assert=require('node:assert/strict');
        const optional={bloquea_modulos:false,categoria:'atributos',problema:'Integridad pendiente'};
        const level={bloquea_modulos:false,categoria:'niveles',problema:'Límite superior pendiente'};
        const report={bloqueos_modulos:0,incidencias:[optional,level]};
        assert.deepEqual(Lab.reportGroups(report),{blocks:[],attributes:[optional],levels:[level]});
        const copy={id:'copy',state:'pendiente_revision',report};
        const data={datasets:[copy]},connection={phase:'ready',activityKnown:true};
        assert.equal(Lab.homeState(data,'copy',[],connection).kind,'review');
        copy.state='lista_modulos';assert.equal(Lab.homeState(data,'copy',[],connection).kind,'ready');
        assert.match(Lab.issueAdvice({problema:'modulo_id debe tener formato M1',clase:'Modulo',bloquea_modulos:false}),/izquierda a derecha/);
        """)

    def test_observations_drawings_and_photos_have_distinct_counts(self):
        self.js("""
        const assert=require('node:assert/strict');
        const issues=[{foto:'03',job_id:1,shape_id:10},{foto:'03',job_id:1,shape_id:10},
        {foto:'03',job_id:2,shape_id:10},{foto:'28',job_id:1,shape_id:null}];
        assert.deepEqual(Lab.issueCounts(issues),{observations:4,drawings:2,photos:2});
        assert.equal(Lab.groupIssues(issues)[0].drawings.length,2);
        assert.deepEqual(Lab.issueCounts([]),{observations:0,drawings:0,photos:0});
        """)

    def test_historical_and_unknown_issues_have_actionable_fallback(self):
        self.js("""
        const assert=require('node:assert/strict');
        assert.match(Lab.issueAdvice({problema:'Integridad pendiente',bloquea_modulos:true}),/encuadre/);
        assert.match(Lab.issueAdvice({problema:'modulo_id debe tener formato M01',bloquea_modulos:false}),/padre/);
        assert.match(Lab.issueAdvice({problema:'Polígono inválido: Self-intersection'}),/cruces/);
        assert.match(Lab.issueAdvice({problema:'Incidencia futura'}),/guía v2/);
        """)

    def test_defaults_distinguish_training_prediction_and_technical_runs(self):
        self.js("""
        const assert=require('node:assert/strict');
        const data={runs:[{id:'verificacion_panel_a',ready:true},{id:'piloto_01_a',ready:true}],
        models:[{id:'technical/best.pt',run:'verificacion_panel_a'},{id:'pilot/best.pt',run:'piloto_01_a'},
        {id:'general.pt',run:null}]};
        assert.equal(Lab.defaultModel(data,'predict'),'pilot/best.pt');
        assert.equal(Lab.defaultModel(data,'train'),'general.pt');
        data.models=data.models.slice(0,1);assert.equal(Lab.defaultModel(data,'predict'),'');
        assert.equal(Lab.defaultModel(data,'train'),'');
        """)

    def test_delta_requires_same_dataset_and_finished_distinct_runs(self):
        self.js("""
        const assert=require('node:assert/strict'),a={id:'a',ready:true,signature:'same',evaluation_protocol:{confidence:0.25,iou:0.5}},b={id:'b',ready:true,signature:'same',evaluation_protocol:{confidence:0.25,iou:0.5}};
        assert.equal(Lab.comparable(a,b),true);assert.equal(Lab.comparable(a,a),false);
        assert.equal(Lab.comparable(a,{...b,ready:false}),false);
        assert.equal(Lab.comparable(a,{...b,signature:'other'}),false);
        assert.equal(Lab.comparable(a,null),false);assert.equal(Lab.comparable(a,{...b,evaluation_protocol:null}),false);assert.equal(Lab.comparable(a,{...b,evaluation_protocol:{confidence:0.5,iou:0.5}}),false);
        assert.equal(Lab.comparable({...a,signature:undefined},{...b,signature:undefined}),false);
        """)

    def test_unfinished_evaluation_is_not_reported_as_completed(self):
        self.js("""
        const assert=require('node:assert/strict'),run={id:'pilot',ready:false,manifest:{imagenes:[{split:'val'}]}};
        assert.match(Lab.evaluationContext(run),/todavía no tiene una evaluación terminada/);
        run.ready=true;assert.match(Lab.evaluationContext(run),/Una sola escena/);
        run.id='verificacion_panel_a';assert.match(Lab.evaluationContext(run),/prueba técnica/);
        """)

    def test_all_javascript_parses(self):
        scripts='\n'.join(re.findall(r'<script[^>]*>(.*?)</script>',self.html,re.S))
        result=subprocess.run([self.node,'--check'],input=scripts,capture_output=True,
                              text=True,encoding='utf-8',timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_lot_groups_partial_history_without_hiding_the_complete_copy(self):
        self.js("""
        const assert=require('node:assert/strict');
        const source=(job,state='completed')=>({job_id:job,task_id:16,task_name:'Set imágenes 2.0',state});
        const groups=Lab.copiesByLot([
          {id:'partial',scope:'Nivel_estados',created_at:'2026-10-13',sources:[source(36)]},
          {id:'whole',scope:'Nivel_estados',created_at:'2026-10-14',state:'pendiente_revision',sources:[source(36),source(37),source(38)]}
        ]);
        assert.equal(groups.length,1);assert.equal(groups[0].person,'Set imágenes 2.0');
        assert.equal(groups[0].latest.id,'whole');assert.equal(groups[0].history[0].id,'partial');
        assert.equal(Lab.readyCopy(groups[0].latest),false);
        """)

    def test_model_choices_show_current_best_per_family_and_general_models(self):
        self.js("""
        const assert=require('node:assert/strict');
        const runs=[['old11_20261013_010000_a','yolo11'],['new11_20261015_010000_b','yolo11'],
          ['old26_20261013_020000_c','yolo26'],['new26_20261015_020000_d','yolo26'],
          ['running11_20261016_010000_e','yolo11']].map(([id,base])=>({id,ready:!id.startsWith('running'),
            scope:'Nivel_estados',config:{model:'Modelos/preentrenados/'+base+'.pt'}}));
        const models=runs.flatMap(run=>['best','last'].map(weight=>({id:'Laboratorio/Experimentos/'+run.id+'/entrenamiento/weights/'+weight+'.pt',run:run.id})));
        models.push({id:'Modelos/preentrenados/yolo11.pt',run:null},{id:'Modelos/preentrenados/yolo26.pt',run:null});
        const catalog={runs,models},visible=Lab.modelChoices(catalog);
        assert.equal(visible.length,4);
        assert.deepEqual(visible.filter(m=>m.run).map(m=>m.run).sort(),['new11_20261015_010000_b','new26_20261015_020000_d']);
        assert.ok(visible.filter(m=>m.run).every(m=>m.id.endsWith('/best.pt')));
        assert.equal(Lab.modelChoices(catalog,true).length,12);
        """)

    def test_warm_started_models_share_family_but_different_scopes_stay_separate(self):
        self.js("""
        const assert=require('node:assert/strict');
        const old={id:'old_20261013_010000_a',ready:true,scope:'Nivel_estados',config:{model:'Modelos/preentrenados/yolo11.pt'}};
        const recent={id:'new_20261015_010000_b',ready:true,scope:'Nivel_estados',config:{model:'Laboratorio/Experimentos/'+old.id+'/entrenamiento/weights/best.pt'}};
        const other={id:'modules_20261015_020000_c',ready:true,config:{model:'Modelos/preentrenados/yolo11.pt'}};
        const runs=[old,recent,other],models=runs.map(run=>({id:'Laboratorio/Experimentos/'+run.id+'/entrenamiento/weights/best.pt',run:run.id}));
        assert.deepEqual(Lab.modelChoices({runs,models}).map(m=>m.run).sort(),[other.id,recent.id].sort());
        """)

    def test_hidden_best_does_not_reappear_as_last_and_unknown_families_are_retained(self):
        self.js("""
        const assert=require('node:assert/strict');
        const runs=[{id:'a',ready:true},{id:'b',ready:true}];
        const models=[{id:'a/best.pt',run:'a'},{id:'b/last.pt',run:'b'}];
        assert.equal(Lab.modelChoices({runs,models}).length,2);
        const archived_models=[{id:'b/best.pt',run:'b'}];
        assert.deepEqual(Lab.modelChoices({runs,models,archived_models}).map(m=>m.run),['a']);
        assert.equal(Lab.modelChoices({runs,models,archived_models},true).length,2);
        """)


if __name__ == '__main__':
    unittest.main()
