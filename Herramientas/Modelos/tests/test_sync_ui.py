"""CVAT solo se consulta cuando el usuario pulsa sus botones."""
from pathlib import Path
import re
import shutil
import subprocess
import unittest


class ManualCvatUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (Path(__file__).resolve().parents[1] / 'panel.html').read_text(encoding='utf-8')
        cls.node = shutil.which('node')
        if not cls.node:
            raise unittest.SkipTest('Se necesita Node.js.')

    def run_js(self, code):
        result = subprocess.run([self.node], input=code, capture_output=True,
                                text=True, encoding='utf-8', timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_loading_panel_does_not_query_cvat_or_start_cvat_timer(self):
        start = self.html.rindex('(async()=>{')
        startup = self.html[start:self.html.index('</script>', start)]
        prelude = """
        const assert=require('node:assert/strict');
        const calls=[],timers=[],seen=new Set(),connection={phase:'ready'};
        const api=async path=>{calls.push(path);return []};
        let jobs=[];
        const renderConnectionStatus=()=>{},updateImportLabel=()=>{},updateAvailability=()=>{},refresh=async()=>{},
          renderOriginal=()=>{},modelHelp=()=>{},renderGlossary=()=>{},poll=async()=>{},schedulePoll=()=>{};
        const setInterval=(fn,delay)=>timers.push(delay);
        """
        self.run_js(prelude + startup + """
        setImmediate(()=>{assert.deepEqual(calls,['/api/jobs']);assert.deepEqual(timers,[])});
        """)
        self.assertNotIn('/api/datasets/sync', self.html)
        # Solo la declaración y la asociación al botón pueden consultar tareas.
        self.assertEqual(len(re.findall(r'\brefreshImportSources\b', self.html)), 2)

    def test_button_reads_tasks_once_without_scheduling_followup(self):
        start = self.html.index('async function refreshImportSources(){')
        code = self.html[start:self.html.index('function selectedRun()', start)]
        prelude = """
        const assert=require('node:assert/strict');
        let sourcesLoading=false,importing=false,importSources=[];
        const calls=[],nodes=new Map();let sourcesUpdated='';const uiPreferences={fields:{}},saveUiPreferences=()=>{};
        const $=id=>{if(!nodes.has(id))nodes.set(id,{value:'',textContent:''});return nodes.get(id)};
        const api=async path=>{calls.push(path);return [{id:'task:16',jobs:[36,37,38],image_ids:['REAL_01']}]};
        const renderImportSources=preferred=>{$('participant').value=preferred},selectImportSource=()=>{},setLoadingButton=()=>{},updateAvailability=()=>{};
        """
        self.run_js(prelude + code + """
        assert.deepEqual(calls,[]);
        refreshImportSources().then(()=>{
          assert.deepEqual(calls,['/api/datasets/sources']);
          assert.equal(sourcesLoading,false);
          assert.equal($('participant').value,'task:16');
        }).catch(e=>{console.error(e);process.exitCode=1});
        """)

    def test_catalog_failure_keeps_retry_available_without_home_page(self):
        start = self.html.index('function renderConnectionStatus(){')
        code = self.html[start:self.html.index('function updateAvailability(){', start)]
        prelude = """
        const assert=require('node:assert/strict');
        const node={hidden:true},$=id=>node,esc=String;
        const setHTML=(target,html)=>{target.innerHTML=html};
        const connection={phase:'error',error:'Servidor desconectado'};
        """
        self.run_js(prelude + code + """
        renderConnectionStatus();
        assert.equal(node.hidden,false);assert.match(node.innerHTML,/data-retry/);
        assert.match(node.innerHTML,/Servidor desconectado/);
        connection.phase='ready';renderConnectionStatus();assert.equal(node.hidden,true);
        """)


if __name__ == '__main__':
    unittest.main()
