"""Selección de proyecto y tarea: filtros, persistencia y recuperación de CVAT."""
from pathlib import Path
import re
import shutil
import subprocess
import unittest


class CvatProjectsUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        html = (Path(__file__).resolve().parents[1] / 'panel.html').read_text(encoding='utf-8')
        cls.node = shutil.which('node')
        if not cls.node:
            raise unittest.SkipTest('Se necesita Node.js.')
        preferences = re.search(r'<script id="ui-preferences">(.*?)</script>', html, re.S)[1]
        options = html[html.index('function options('):html.index('function renderCopyOptions(')]
        imports = html[html.index('function renderImportSources('):html.index('function selectedRun()')]
        cls.code = preferences + """
        const assert=require('node:assert/strict');
        const nodes=new Map(),$=id=>{if(!nodes.has(id))nodes.set(id,{
          value:'',textContent:'',hidden:false,classList:{toggle:()=>{}},
          setAttribute:()=>{},closest:()=>({open:false})});return nodes.get(id)};
        const esc=s=>String(s).replaceAll('<','&lt;'),localDate=String;
        const setHTML=(node,html)=>node.innerHTML=html;
        const uiPreferences={fields:{}},pendingChoices=new Set();
        const saveUiPreferences=()=>{},updateAvailability=()=>{},scopedSources=()=>importSources;
        let importing=false,sourcesLoading=false,sourcesUpdated='';
        const moduleTask={id:'task:14',task_id:14,project_id:4,project_name:'Módulos',
          name:'Lote',jobs:[30],image_ids:['28'],completed_jobs:1};
        const levelTask={id:'task:16',task_id:16,project_id:6,project_name:'Niveles',
          name:'Lote',jobs:[36],image_ids:['REAL_01'],fixed_validation:true,validation_ids:['REAL_01']};
        let importSources=[moduleTask,levelTask];
        let api=async()=>importSources;
        """ + options + imports

    def js(self, code):
        result = subprocess.run([self.node], input=self.code + code, capture_output=True,
                                text=True, encoding='utf-8', timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_project_filters_tasks_and_changes_task_and_validation_together(self):
        self.js("""
        renderImportSources('task:16');selectImportSource(true);
        assert.equal($('import-project').value,'6');
        assert.equal($('participant').value,'task:16');
        assert.ok(!$('participant').innerHTML.includes('task:14'));
        assert.equal($('import-task').value,16);
        assert.equal($('validation-ids').disabled,true);
        assert.equal($('validation-ids').value,'REAL_01');
        $('import-project').value='4';renderImportSources();selectImportSource(true);
        assert.equal($('participant').value,'task:14');
        assert.ok(!$('participant').innerHTML.includes('task:16'));
        assert.equal($('import-task').value,14);
        assert.equal($('validation-ids').disabled,false);
        assert.equal($('validation-ids').value,'28');
        $('participant').value='custom';selectImportSource(true);
        assert.equal($('custom-task').hidden,false);
        assert.equal($('import-task').value,'');
        """)

    def test_saved_project_and_task_survive_reload_and_refresh(self):
        self.js("""
        uiPreferences.fields={'import-project':'4',participant:'task:14'};
        pendingChoices.add('import-project');pendingChoices.add('participant');
        renderImportSources();selectImportSource();
        assert.equal($('import-project').value,'4');
        assert.equal($('participant').value,'task:14');
        refreshImportSources().then(()=>{
          assert.equal($('import-project').value,'4');
          assert.equal($('participant').value,'task:14');
          assert.equal($('import-task').value,14);
        }).catch(e=>{console.error(e);process.exitCode=1});
        """)

    def test_failed_refresh_keeps_cached_list_and_manual_task(self):
        self.js("""
        renderImportSources();$('participant').value='custom';$('import-task').value='19';
        api=async()=>{throw Error('Sin conexión')};
        refreshImportSources().then(()=>{
          assert.equal(importSources.length,2);
          assert.equal($('import-task').value,'19');
          assert.match($('import-sources-status').textContent,/Sin conexión/);
          assert.match($('import-sources-status').textContent,/reintentar/);
          assert.equal($('refresh-import-sources').disabled,false);
          assert.equal(sourcesLoading,false);
        }).catch(e=>{console.error(e);process.exitCode=1});
        """)

    def test_cache_keeps_project_names_and_migrates_older_sources(self):
        self.js("""
        const result=UiPreferences.sanitize({version:1,fields:{'import-project':'6'},
          sources:[levelTask,{...moduleTask,project_id:undefined,project_name:undefined}]});
        assert.equal(result.fields['import-project'],'6');
        assert.equal(result.sources[0].project_name,'Niveles');
        assert.equal(result.sources[1].project_id,4);
        """)

    def test_task_19_reports_pending_partition_without_inheriting_task_16_validation(self):
        self.js("""
        const source={...levelTask,id:'task:19',task_id:19,project_id:7,name:'Líder Express',
          project_name:'Estados por nivel',pending_partition:true,validation_ids:[],
          validation_note:'Tarea 19 · criterio v2: partición pendiente.',criterion_version:'disponibilidad_visual_nivel_v2_reponer'};
        importSources=[moduleTask,source];renderImportSources('task:19');selectImportSource(true);
        assert.equal($('import-project').value,'7');
        assert.equal($('import-task').value,19);
        assert.equal($('validation-ids').value,'');
        assert.equal($('validation-ids').disabled,true);
        assert.match($('import-source-help').textContent,/partición pendiente/);
        assert.match($('validation-help').textContent,/criterio v2/);
        assert.ok(!$('validation-help').textContent.includes('tarea 16'));
        const restored=UiPreferences.sanitize({version:1,sources:[source]});
        assert.equal(restored.sources[0].pending_partition,true);
        assert.equal(restored.sources[0].validation_note,source.validation_note);
        """)


if __name__ == '__main__':
    unittest.main()
