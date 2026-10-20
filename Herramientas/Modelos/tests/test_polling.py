"""Execute the browser's real polling code with controlled HTTP responses."""
from pathlib import Path
import shutil
import subprocess
import unittest


class PollingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = shutil.which('node')
        if not cls.node:
            raise unittest.SkipTest('Node.js is required for UI polling tests')
        html = (Path(__file__).resolve().parents[1] / 'panel.html').read_text(encoding='utf-8')
        start = html.index('function schedulePoll(){')
        cls.poll_code = html[start:html.index("document.addEventListener('visibilitychange'", start)]
        start = html.index('let catalogResponse=null;')
        cls.api_code = html[start:html.index('function options(', start)]

    def run_js(self, assertions):
        prelude = """
        const assert=require('node:assert/strict');
        let polling=false,pollTimer=null,busy=false,jobs=[],activityKey=null;
        let currentView='glossary',shownPredictionJob=null,predictJob=null;
        let lastCatalogRefresh=Date.now(),refreshes=0,predictions=0,renders=0,requests=0;
        const connection={phase:'ready',activityKnown:true,activityError:''},seen=new Set();
        const nodes=new Map(),scheduled=[];
        const $=id=>{if(!nodes.has(id))nodes.set(id,{style:{}});return nodes.get(id)};
        const document={hidden:false,querySelectorAll:()=>[],activeElement:{closest:()=>null}};
        const clearTimeout=()=>{},setTimeout=(fn,delay)=>{scheduled.push(delay);return scheduled.length};
        const esc=String,runName=String,setHTML=(node,html)=>{node.innerHTML=html};
        const updateAvailability=()=>{},renderHome=()=>renders++,renderTraining=()=>renders++;
        const renderVersionContext=()=>{},projectVersion='v1',jobInVersion=()=>true;
        const fullCatalog={runs:[],datasets:[]},Lab={versionOf:()=> 'v1'},versionNames={v1:'V1'};
        const error=message=>{throw Error(message)},showPrediction=()=>predictions++;
        const refresh=async()=>{refreshes++;lastCatalogRefresh=Date.now()};
        let response=[],pending=null;
        const api=async()=>{requests++;return pending?await pending:response};
        """
        script = prelude + self.poll_code + '\n(async()=>{' + assertions + '})().catch(e=>{console.error(e);process.exitCode=1});'
        result = subprocess.run([self.node], input=script, capture_output=True,
                                text=True, encoding='utf-8', timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_finished_prediction_is_not_reinserted_on_every_poll(self):
        self.run_js("""
        predictJob='prediction';
        response=[{id:'prediction',state:'done',config:{action:'predict',image:'01.jpg'}}];
        await poll();await poll();
        assert.equal(predictions,1);
        assert.equal(refreshes,0);assert.equal(renders,0);
        """)

    def test_poll_requests_do_not_overlap_and_schedule_after_completion(self):
        self.run_js("""
        let resolve;pending=new Promise(done=>resolve=done);
        const first=poll();await poll();
        assert.equal(requests,1);assert.equal(scheduled.length,0);
        resolve([]);await first;
        assert.equal(scheduled.length,1);assert.equal(polling,false);
        """)

    def test_training_catalog_refreshes_for_new_epochs_and_completion(self):
        self.run_js("""
        const job={id:'train',state:'running',config:{action:'train',run:'fixture'},
                   progress:{completed_epochs:2,stage:'training'}};
        jobs=[job];response=[job];seen.add('train');
        await poll();assert.equal(refreshes,0);
        response=[{...job,progress:{...job.progress,completed_epochs:3}}];
        await poll();assert.equal(refreshes,1);
        seen.delete('train');response=[{...response[0],state:'done'}];
        await poll();assert.equal(refreshes,2);
        await poll();assert.equal(refreshes,2);
        """)

    def test_catalog_304_reuses_value_without_parsing_and_recovers_after_failure(self):
        script = "const assert=require('node:assert/strict');\n" + self.api_code + """
        (async()=>{
          let result={status:200,ok:true,headers:{get:()=> 'W/"first"'},json:async()=>({runs:[]})};
          let options;
          global.fetch=async(path,value)=>{options=value;return result};
          const first=await api('/api/catalog');
          assert.equal(options.headers,undefined);
          result={status:304,json:()=>{throw Error('304 must not parse JSON')}};
          assert.equal(await api('/api/catalog'),first);
          assert.equal(options.headers['If-None-Match'],'W/"first"');
          result={status:503,ok:false,json:async()=>({error:'offline'})};
          await assert.rejects(api('/api/catalog'),/offline/);
          result={status:304};
          assert.equal(await api('/api/catalog'),first);
          result={status:200,ok:true,headers:{get:()=> 'W/"second"'},json:async()=>({runs:[{id:'new'}]})};
          const second=await api('/api/catalog');
          assert.notEqual(second,first);assert.equal(second.runs[0].id,'new');
          await api('/api/jobs');
          assert.equal(options.headers,undefined);
        })().catch(e=>{console.error(e);process.exitCode=1});
        """
        result = subprocess.run([self.node], input=script, capture_output=True,
                                text=True, encoding='utf-8', timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
