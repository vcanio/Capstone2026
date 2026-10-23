"""Persistencia local y navegación real de imágenes, sin modelos ni CVAT."""
from pathlib import Path
from panel_source import read_panel
import re
import shutil
import subprocess
import unittest


class QolUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = read_panel()
        cls.node = shutil.which('node')
        if not cls.node:
            raise unittest.SkipTest('Se necesita Node.js.')
        cls.preferences = re.search(r'<script id="ui-preferences">(.*?)</script>', cls.html, re.S)[1]
        cls.navigation = re.search(r'<script id="image-navigation">(.*?)</script>', cls.html, re.S)[1]
        start = cls.html.index('let uiPreferences;')
        cls.adapter = cls.html[start:cls.html.index('const glossary=[', start)]
        start = cls.html.index('function options(')
        cls.options = cls.html[start:cls.html.index('function renderCopyOptions(', start)]

    def js(self, code):
        result = subprocess.run([self.node], input="const assert=require('node:assert/strict');\n" + code,
                                text=True, encoding='utf-8', capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_edges_view_uses_current_analysis_and_resets_when_unavailable(self):
        start = self.html.index('let edgeLayers=[];')
        views = self.html[start:self.html.index('function resetPrediction(){', start)]
        self.js("""
        const nodes=new Map(),$=id=>{
          if(!nodes.has(id))nodes.set(id,{value:'',dataset:{},attributes:{},
            setAttribute(name,value){this.attributes[name]=value},
            removeAttribute(name){delete this.attributes[name]}});
          return nodes.get(id);
        };
        const tabs=['original','result','edges','compare'].map(mode=>
          Object.assign($('photo-view-'+mode),{id:'photo-view-'+mode,dataset:{demoView:mode},disabled:false}));
        const document={querySelectorAll:()=>tabs},ImageNavigation={mount:()=>{},release:()=>{}};
        const esc=String,setHTML=(node,html)=>node.innerHTML=html;
        const options=(id,items)=>$(id).value=items[0]?.id||'';
        """ + views + """
        renderEdgeViews({result:{occupancy:{}},occupancy_image_url:'signal.jpg',
          occupancy_edges_url:'edges.png',occupancy_filtered_edges_url:'levels.png'});
        assert.equal($('photo-view-edges').disabled,false);
        assert.match($('edge-output').innerHTML,/signal.jpg/);
        demoView('edges');
        assert.equal($('demo-visual').dataset.mode,'edges');
        assert.equal($('photo-view-edges').attributes['aria-selected'],'true');
        assert.equal($('photo-view-original').tabIndex,-1);
        $('edge-layer').value='photo';renderEdgeLayer();
        assert.match($('edge-output').innerHTML,/edges.png/);
        renderEdgeViews({result:{}});demoView('result');demoView('edges');
        assert.equal($('photo-view-edges').disabled,true);
        assert.equal($('demo-visual').dataset.mode,'result');
        assert.match($('edge-output').textContent,/Analiza con YOLO/);
        assert.equal($('edge-open').attributes.href,undefined);
        """)

    def test_corrupt_or_unavailable_storage_keeps_panel_usable(self):
        self.js(self.preferences + """
        assert.deepEqual(UiPreferences.read({getItem:()=>'{invalid'}).fields,{});
        const denied={getItem:()=>{throw Error('denied')},setItem:()=>{throw Error('full')}};
        assert.deepEqual(UiPreferences.read(denied).fields,{});
        assert.equal(UiPreferences.write(denied,{version:1,fields:{epochs:'75'}}),false);
        assert.deepEqual(UiPreferences.sanitize({version:99,fields:{epochs:'75'}}).fields,{});
        """)

    def test_preferences_never_restore_review_consent_or_secrets(self):
        self.js(self.preferences + """
        const source={id:'task:16',name:'Tarea 16',jobs:[36,37,38],image_ids:['REAL_01'],
          fixed_validation:true,validation_ids:['REAL_01'],token:'secret'};
        let stored;const storage={setItem:(key,value)=>stored=value,getItem:()=>stored};
        assert.equal(UiPreferences.write(storage,{version:1,view:'train',fields:{
          name:'ensayo',epochs:'75',reviewed:'true',reviewer:'Persona',password:'secret'},
          sources:[source,{id:'broken',name:'Invalid',jobs:['36'],image_ids:[]}]}),true);
        const result=UiPreferences.read(storage);
        assert.deepEqual(result.fields,{name:'ensayo',epochs:'75'});
        assert.equal(result.sources.length,1);assert.equal(result.sources[0].fixed_validation,true);
        assert.deepEqual(result.sources[0].validation_ids,['REAL_01']);
        assert.equal(result.sources[0].token,undefined);
        """)

    def test_zoom_keeps_pointer_anchor_and_pan_inside_image(self):
        self.js(self.navigation + """
        const fit={width:400,height:300,fitWidth:400,fitHeight:300,scale:1,x:0,y:0};
        const state=ImageNavigation.zoom(fit,2,100,100);
        assert.equal(state.x,-100);assert.equal(state.y,-100);
        assert.equal((100-state.x)/state.scale,100);
        assert.equal((100-state.y)/state.scale,100);
        const pan=ImageNavigation.constrain({...state,x:-999,y:999});
        assert.equal(pan.x,-400);assert.equal(pan.y,0);
        assert.deepEqual(ImageNavigation.zoom(state,0),fit);
        assert.equal(ImageNavigation.zoom(state,99).scale,8);
        const portrait=ImageNavigation.constrain({...fit,fitWidth:150});
        assert.equal(portrait.x,125);
        """)

    def test_dynamic_selection_restores_once_and_deleted_option_falls_back(self):
        self.js(self.preferences + """
        let projectVersion='v2';
        const nodes=new Map(),$=id=>{if(!nodes.has(id))nodes.set(id,{value:''});return nodes.get(id)};
        const localStorage={getItem:()=>JSON.stringify({version:1,fields:{model:'saved',source:'deleted',baseline:'saved'}})};
        const esc=String,setHTML=(node,html)=>node.innerHTML=html,localDate=String;
        """ + self.adapter + self.options + """
        const items=[{id:'default',name:'Default'},{id:'saved',name:'Saved'}];
        options('model',items,false,'default');assert.equal($('model').value,'saved');
        $('model').value='default';options('model',items,false,'saved');
        assert.equal($('model').value,'default');
        options('source',items,false,'default');assert.equal($('source').value,'default');
        options('baseline',items,true);assert.equal($('baseline').value,'saved');
        """)

    def test_restore_cached_task_is_local_and_invalid_settings_keep_defaults(self):
        self.js(self.preferences + """
        let projectVersion='v2';
        const source={id:'task:16',name:'Tarea 16',jobs:[36],image_ids:['REAL_01']};
        const localStorage={getItem:()=>JSON.stringify({version:1,view:'predict',
          fields:{epochs:'999',batch:'3',conf:'NaN','train-size':'9999',reviewed:'true',participant:'task:16'},sources:[source]})};
        const nodes=new Map();
        const $=id=>{if(!nodes.has(id))nodes.set(id,{value:'default',min:'1',max:'500',maxLength:-1,tagName:'INPUT'});return nodes.get(id)};
        Object.assign($('epochs'),{value:'100'});Object.assign($('batch'),{value:'2',min:'1',max:'4'});
        Object.assign($('conf'),{value:'.25',min:'.01',max:'.99'});Object.assign($('nms'),{value:'.70'});
        Object.assign($('train-size'),{tagName:'SELECT',value:'640',options:[{value:'640'}]});
        let importSources=[],monitorJob=null,currentView='version';
        const renderImportSources=()=>{},selectImportSource=()=>{},switchTab=()=>{throw Error('unexpected view')},localDate=String;
        """ + self.adapter + """
        restoreUiPreferences();
        assert.equal(currentView,'version');
        assert.equal(UiPreferences.views.includes('version'),true);
        assert.equal($('epochs').value,'100');assert.equal($('batch').value,'3');
        assert.equal($('conf').value,'.25');assert.equal($('train-size').value,'640');
        assert.equal($('reviewed').checked,undefined);
        assert.equal(importSources[0].id,'task:16');
        assert.match($('import-sources-status').textContent,/Tareas guardadas/);
        """)

    def test_started_training_is_available_before_opening_its_monitor(self):
        start = self.html.index('async function submit(config){')
        submit = self.html[start:self.html.index('function showPrediction(', start)]
        self.js("""
        const nodes=new Map(),$=id=>{if(!nodes.has(id))nodes.set(id,{style:{},scrollIntoView:()=>{}});return nodes.get(id)};
        const job={id:'new',state:'running',config:{action:'train',run:'new_run'}};
        let jobs=[{id:'old',state:'done',config:{action:'train',run:'old_run'}}],busy=false,monitorJob=null,pendingRun=null;
        const api=async()=>job,document={querySelectorAll:()=>[]},saveUiPreferences=()=>{},poll=async()=>{};
        const refresh=async()=>{assert.equal(jobs.find(j=>j.id===monitorJob)?.state,'running')};
        const switchTab=view=>{assert.equal(view,'train');assert.equal(monitorJob,'new')};
        """ + submit + """
        submit({action:'train'}).catch(e=>{console.error(e);process.exitCode=1});
        """)


    def test_home_preserves_navigation_and_syncs_shell_view(self):
        self.assertIn('<div class="shell" data-view="version">', self.html)
        self.assertIn('<div id="version-cards" class="version-cards"', self.html)
        self.assertIn('class="version-card" data-version="v2"', self.html)
        self.assertIn('class="version-card" data-version="v1"', self.html)
        nav = re.search(r'<nav id="sections-nav"[^>]*>(.*?)</nav>', self.html, re.S)[1]
        self.assertNotIn('data-tab="version"', nav)
        self.assertIn('id="work-summary"', self.html)
        start = self.html.index('function switchTab(id){')
        switch_tab = self.html[start:self.html.index('async function retryQueries(', start)]
        self.js("""
        let currentView='version',glossaryReturn='version';const fullCatalog=null;
        const shell={dataset:{view:'version'}},heading={tabIndex:0,focus:()=>{}};
        const views=['version','datasets','train','results','predict','glossary'].map(id=>({
          id,classList:{contains:c=>c==='view',toggle(c,on){this.active=on}},querySelector:()=>heading}));
        const navButtons=['datasets','train','results','predict','glossary'].map(tab=>({
          dataset:{tab},attributes:{},classList:{toggle(c,on){this.active=on}},
          setAttribute(k,v){this.attributes[k]=v},removeAttribute(k){delete this.attributes[k]}}));
        const nodes=new Map(views.map(v=>[v.id,v]));
        nodes.set('workspace-version',{hidden:true});
        nodes.set('mobile-section',{textContent:''});
        nodes.set('sections-nav',{classList:{remove:()=>{}}});
        nodes.set('sections-toggle',{setAttribute:()=>{}});
        const $=id=>nodes.get(id);
        const document={querySelector:s=>s==='.shell'?shell:null,
          querySelectorAll:s=>s==='.view'?views:navButtons};
        const window={scrollTo:()=>{}},closeHelp=()=>{},renderGlossary=()=>{},renderTraining=()=>{},renderResults=()=>{},renderWorkspace=()=>{};
        """ + switch_tab + """
        switchTab('datasets');
        assert.equal(shell.dataset.view,'datasets');
        assert.equal($('workspace-version').hidden,false);
        assert.equal(navButtons.find(b=>b.dataset.tab==='datasets').attributes['aria-current'],'page');
        switchTab('version');
        assert.equal(shell.dataset.view,'version');
        assert.equal($('workspace-version').hidden,false);
        assert.equal(navButtons.every(b=>!b.attributes['aria-current']),true);
        """)


if __name__ == '__main__':
    unittest.main()
