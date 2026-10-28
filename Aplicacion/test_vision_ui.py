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
  constructor(){this.hidden=false;this.disabled=false;this.value='';this.listeners={};this.attrs={};this.options=[];this.style={setProperty(key,value){this[key]=value}};this.classList={add(){},remove(){},toggle(){}}}
  set innerHTML(value){this.html=value;if(value.includes('<option')){this.options=[...value.matchAll(/<option value="([^"]+)">([^<]*)<\/option>/g)].map(m=>({value:m[1],textContent:m[2]}));this.value=this.options[0]?.value||''}}
  get innerHTML(){return this.html||''}
  get selectedOptions(){return this.options.filter(o=>o.value===this.value)}
  addEventListener(type,handler){this.listeners[type]=handler}
  setAttribute(key,value){this.attrs[key]=value}
  removeAttribute(key){delete this[key];delete this.attrs[key]}
  focus(){document.activeElement=this}
  scrollIntoView(){}
}
global.document={getElementById(id){if(!elements.has(id))elements.set(id,new Element());return elements.get(id)},querySelector(selector){return this.getElementById(selector)},addEventListener(){}};
global.window={addEventListener(){}};
global.matchMedia=()=>({matches:false});
global.URL.createObjectURL=()=> 'blob:original';global.URL.revokeObjectURL=()=>{};
document.getElementById('confidence').value='0.60';
document.getElementById('edge-view').innerHTML='<option value="occupancy_image_url">Mapa de señal</option><option value="filtered_edges_image_url">Bordes dentro de los niveles</option><option value="edges_image_url">Bordes de la foto</option>';
const fixtures=[{id:'V2-YOLO11',name:'V2-YOLO11',states:[{key:'reponer',label:'Reponer',color:'#f00'},{key:'suficiente',label:'Suficiente',color:'#080'}]},
 {id:'V2-YOLO26',name:'V2-YOLO26',states:[{key:'reponer',label:'Reponer',color:'#f00'},{key:'suficiente',label:'Suficiente',color:'#080'}]}];
global.fetch=async()=>({ok:true,json:async()=>({models:fixtures,default_model:'V2-YOLO26'})});
function prediction(edges=true){return {counts:{reponer:1,suficiente:0},detections:[{id:1,label:'Reponer',confidence:.9,...(edges?{occupancy_estimate:{pct:15,state:'reponer'}}:{})}],model:'V2-YOLO26',device:'cpu',seconds:1,image_url:'data:levels',...(edges?{occupancy:{},occupancy_image_url:'data:signal',edges_image_url:'data:edges',filtered_edges_image_url:'data:filtered'}:{})}}
"""


class VisionInterfaceTests(unittest.TestCase):
    def test_reanalyze_only_current_photo_with_selected_confidence(self):
        self.js("""
        chooseBatch([{name:'a.jpg',type:'image/jpeg',size:1},{name:'b.jpg',type:'image/jpeg',size:1}]);
        const old=prediction(),other=prediction();batch[0].result=old;batch[0].analyzedConfidence=.6;batch[1].result=other;
        selectBatch(0);$('confidence').value='0.4';let calls=[];
        global.fetch=async(url,options)=>{calls.push({url,body:options.body});return {ok:true,json:async()=>prediction()}};
        await $('reanalyze-current').listeners.click();
        assert.equal(calls.length,1);assert.equal(calls[0].body.name,'a.jpg');
        assert.equal(new URL(calls[0].url,'http://localhost').searchParams.get('confidence'),'0.4');
        assert.equal(batch[1].result,other);assert.equal(batch[0].analyzedConfidence,.4);
        assert.match($('photo-info').textContent,/40 %/);
        const latest=batch[0].result;global.fetch=async()=>{throw Error('Error de conexión')};
        await $('reanalyze-current').listeners.click();
        assert.equal(batch[0].result,latest);assert.equal(result,latest);assert.equal(batch[0].failure,'');
        """)

    def test_gallery_stops_at_ends_and_shows_position(self):
        self.js("""
        chooseBatch([{name:'a.jpg',type:'image/jpeg',size:1},{name:'b.jpg',type:'image/jpeg',size:1}]);
        assert.match($('batch-count').textContent,/Foto 1 de 2/);
        assert.equal($('batch-prev').disabled,true);
        moveBatch(-1);assert.equal(batchIndex,0);
        moveBatch(1);assert.match($('batch-count').textContent,/Foto 2 de 2/);
        assert.equal($('batch-next').disabled,true);
        moveBatch(1);assert.equal(batchIndex,1);
        """)

    def test_batch_retains_results_and_marks_originals(self):
        self.js("""
        currentModel={id:'V3',geometry_only:true};modelContext();
        const photos=[{name:'uno.jpg',type:'image/jpeg',size:10},{name:'dos.png',type:'image/png',size:20}];
        chooseBatch(photos);assert.equal(batch.length,2);
        assert.equal($('batch-analyze').disabled,false);
        $('batch-confirm').checked=true;$('batch-confirm').listeners.change();
        let calls=[];global.fetch=async(url,options)=>{calls.push(options.body.name);return {ok:true,json:async()=>prediction()}};
        assert.equal($('analyze').textContent,'Analizar 2 fotos');
        await $('form').listeners.submit({preventDefault(){}});
        assert.deepEqual(calls,['uno.jpg','dos.png']);assert.ok(batch.every(item=>item.result));
        selectBatch(0);assert.equal(file.name,'uno.jpg');assert.ok(result);
        $('batch-mark').listeners.click();assert.equal(batch[0].marked,true);
        selectBatch(1);assert.equal(batch[0].marked,true);assert.equal($('batch-download').disabled,false);
        """)

    def test_batch_pause_and_retry_failed_photo(self):
        self.js("""
        currentModel={id:'V3',geometry_only:true};modelContext();
        chooseBatch([{name:'a.jpg',type:'image/jpeg',size:1},{name:'b.jpg',type:'image/jpeg',size:1}]);
        $('batch-confirm').checked=true;let calls=[],finish;
        global.fetch=async(url,options)=>{calls.push(options.body.name);if(calls.length===1)await new Promise(resolve=>finish=resolve);return {ok:true,json:async()=>prediction()}};
        const run=analyzeBatch();$('batch-pause').listeners.click();finish();await run;
        assert.deepEqual(calls,['a.jpg']);assert.ok(batch[0].result);assert.equal(batch[1].result,null);
        global.fetch=async(url,options)=>{calls.push(options.body.name);return {ok:false,json:async()=>({error:'Fallo'})}};
        await analyzeBatch();assert.equal(batch[1].failure,'Fallo');assert.ok(batch[0].result);
        global.fetch=async()=>({ok:true,json:async()=>prediction()});
        await $('batch-retry').listeners.click();await new Promise(resolve=>setTimeout(resolve,0));
        assert.ok(batch[1].result);assert.equal(batch[1].failure,'');
        """)

    def test_review_metadata_and_filters(self):
        self.js("""
        chooseBatch([{name:'a.jpg',type:'image/jpeg',size:1},{name:'b.jpg',type:'image/jpeg',size:1}]);
        $('batch-mark').listeners.click();$('batch-reason').value='Nivel omitido';$('batch-reason').listeners.input();
        $('batch-note').value='Superior';$('batch-note').listeners.input();
        $('batch-filter').value='marked';$('batch-filter').listeners.change();
        assert.deepEqual(filteredBatchIndices(),[0]);
        assert.equal(batch[0].reason,'Nivel omitido');assert.equal(batch[0].note,'Superior');
        """)

    def test_gallery_can_collapse_without_hiding_review_actions(self):
        self.js("""
        chooseBatch([{name:'foto.jpg',type:'image/jpeg',size:1}]);
        $('batch-details').hidden=true;
        $('batch-toggle').listeners.click();assert.equal($('batch-details').hidden,false);
        assert.equal($('batch-toggle').attrs['aria-expanded'],'true');
        $('batch-toggle').listeners.click();assert.equal($('batch-details').hidden,true);
        assert.equal($('batch-mark').disabled,false);
        """)

    def test_batch_accepts_150_and_rejects_151_photos(self):
        self.js("""
        const photos=Array.from({length:151},(_,i)=>({name:`foto${i}.jpg`,type:'image/jpeg',size:1}));
        chooseBatch(photos.slice(0,150));assert.equal(batch.length,150);
        chooseBatch(photos);assert.equal(batch.length,150);
        assert.match($('error').textContent,/150 fotos/);
        """)

    def test_photo_wheel_zoom_and_reset_on_new_photo(self):
        self.js("""
        choose({name:'foto.jpg',type:'image/jpeg',size:1});let prevented=false;
        $('photo').listeners.wheel({deltaY:-1,preventDefault(){prevented=true}});
        assert.equal(prevented,true);assert.equal(photoZoom,1.25);assert.equal($('photo-zoom-label').textContent,'Zoom 125 %');
        $('photo-zoom-reset').listeners.click();assert.equal(photoZoom,1);
        $('photo').listeners.wheel({deltaY:-1,preventDefault(){}});
        choose({name:'otra.jpg',type:'image/jpeg',size:1});assert.equal(photoZoom,1);
        """)

    def test_zoom_out_gradually_recenters_dragged_photo(self):
        self.js("""
        choose({name:'foto.jpg',type:'image/jpeg',size:1});
        photoZoom=2;panX=100;panY=-60;
        $('photo').listeners.wheel({deltaY:1,preventDefault(){}});
        assert.equal(photoZoom,1.75);assert.equal(panX,75);assert.equal(panY,-45);
        for(let i=0;i<3;i++)$('photo').listeners.wheel({deltaY:1,preventDefault(){}});
        assert.equal(photoZoom,1);assert.equal(panX,0);assert.equal(panY,0);
        """)

    def test_gallery_is_below_upload_on_desktop_and_has_mobile_slot(self):
        self.assertLess(HTML.index('id="form"'), HTML.index('id="gallery-sidebar-slot"'))
        self.assertLess(HTML.index('id="gallery-sidebar-slot"'), HTML.index('<!-- Main Workspace Area -->'))
        self.assertNotIn('Consultar leyenda', HTML)
        self.assertIn('id="gallery-mobile-slot"', HTML)
        self.assertIn("galleryMedia.addEventListener?.('change',placeGallery)", SCRIPT)

    def test_camera_closes_tracks_and_ignores_late_permission(self):
        self.js("""
        let resolveCamera, stopped=0;
        Object.defineProperty(global,'navigator',{configurable:true,value:{mediaDevices:{getUserMedia:()=>new Promise(resolve=>{resolveCamera=resolve})}}});
        const opening=openCamera();
        assert.equal($('camera-dialog').hidden,false);
        closeCamera();
        resolveCamera({getTracks:()=>[{stop(){stopped++}}]});
        await opening;
        assert.equal(stopped,1);assert.equal(cameraStream,null);
        assert.equal($('camera-dialog').hidden,true);
        """)

    def test_camera_capture_selects_photo_and_stops_stream(self):
        self.js("""
        let stopped=0;
        Object.defineProperty(global,'navigator',{configurable:true,value:{mediaDevices:{getUserMedia:async()=>({getTracks:()=>[{stop(){stopped++}}]})}}});
        $('camera-video').play=async()=>{};
        $('camera-video').videoWidth=1920;$('camera-video').videoHeight=1080;
        document.createElement=()=>({getContext:()=>({drawImage(){}}),toBlob:callback=>callback(new Blob(['photo'],{type:'image/jpeg'}))});
        global.File=class extends Blob {constructor(parts,name,options){super(parts,options);this.name=name}};
        await openCamera();assert.equal($('camera-capture').disabled,false);
        captureCamera();
        assert.equal(stopped,1);assert.equal($('camera-dialog').hidden,true);
        assert.equal(file.name,'gondola.jpg');assert.equal($('analyze').disabled,false);
        """)

    def test_v3_allows_analysis_and_does_not_call_partial_sufficient(self):
        self.js("""
        currentModel={id:'V3',name:'V3',geometry_only:true,minimum_confidence:.4,guide:'V3'};modelContext();
        assert.equal($('confidence').value,'0.60');
        choose({name:'new.jpg',type:'image/jpeg',size:100});assert.equal($('analyze').disabled,false);
        const data=prediction(true);data.geometry_only=true;data.visibility='partial';
        data.detections[0].scope='Solo zona visible';data.detections[0].notice='Revisa el resto';
        data.detections[0].occupancy_estimate={pct:80,state:'revisar',label:'Revisar · zona visible'};
        show(data);assert.match($('occupancy-rows').innerHTML,/Solo zona visible/);
        assert.match($('occupancy-rows').innerHTML,/Revisar/);
        assert.doesNotMatch(resultDescription(data),/verde/);
        assert.doesNotMatch($('occupancy-rows').innerHTML,/occupancy-enough/);
        show({...data,photo_status:'gondola_tapada',detections:[],counts:{},message:'Góndola tapada'});
        assert.match($('summary').innerHTML,/Góndola tapada/);assert.equal($('result-tools').hidden,true);
        choose({name:'another.jpg',type:'image/jpeg',size:100});assert.equal($('analyze').disabled,false);
        """)
    def test_v2_selection_shows_weighted_measurement_and_clears_old_results(self):
        self.js("""
        choose({name:'foto.jpg',size:100,type:'image/jpeg'});

        const data=prediction();data.occupancy.method='paulo_mascara_v2_combinacion_ponderada';
        data.detections[0].occupancy={combined_signal_pct:44,area_signal_pct:20,width_signal_pct:100,status:'medido'};
        data.detections[0].occupancy_estimate={pct:44,state:'suficiente'};
        show(data);assert.match($('edge-summary').textContent,/Cómo se estima la ocupación/);
        assert.match($('edge-columns').innerHTML,/Combinado/);assert.match($('edge-rows').innerHTML,/44 %/);
        assert.match($('occupancy-rows').innerHTML,/44 %/);assert.match($('occupancy-rows').innerHTML,/occupancy-enough/);
        resetResult();
        assert.equal($('edge-results').hidden,true);assert.equal($('view-edges').disabled,true);
        assert.equal($('level-occupancy').hidden,true);assert.equal($('occupancy-rows').innerHTML,'');
        show(prediction(false));assert.equal($('edge-results').hidden,true);
        """)

    def js(self, body):
        code = HARNESS + SCRIPT + '\nsetImmediate(async()=>{try{' + body + "\n}catch(error){console.error(error);process.exitCode=1}});"
        result = subprocess.run([shutil.which('node') or 'node', '-'], input=code, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_current_models_and_default_load_directly(self):
        self.js("""
        assert.equal(currentModel.id,'V2-YOLO26');
        assert.deepEqual(states.map(s=>s[0]),['reponer','suficiente']);
        assert.equal($('fields').disabled,false);assert.equal($('analyze').disabled,true);
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

    def test_requests_keep_fixed_settings_without_visibility(self):
        self.js("""
        currentModel={id:'V3',geometry_only:true};modelContext();
        choose({name:'foto.jpg',size:100,type:'image/jpeg'});
        let requests=[];
        global.fetch=async(url,options)=>{requests.push({url,options});return {ok:true,json:async()=>prediction()}};
        await $('form').listeners.submit({preventDefault(){}});
        assert.equal(requests.length,1);
        const params=new URL(requests[0].url,'http://localhost').searchParams;
        assert.equal(params.get('model'),'V3');
        assert.equal(params.get('method'),'yolo_paulo_v2');
        assert.equal(Number(params.get('confidence')),0.6);
        assert.equal(params.has('visibility'),false);
        $('confidence').value='0.4';$('confidence').listeners.input();
        assert.equal($('confidence-value').textContent,'40 %');
        await $('form').listeners.submit({preventDefault(){}});
        assert.equal(new URL(requests[1].url,'http://localhost').searchParams.get('confidence'),'0.4');
        assert.equal(requests[0].options.body,file);
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
        choose({name:'foto.jpg',size:100,type:'image/jpeg'});show(prediction(false));
        assert.match($('summary').innerHTML,/Se detectaron 1 nivel/);
        assert.match($('summary').innerHTML,/Revisa sus contornos/);
        show({...prediction(false),detections:[],counts:{}});
        assert.match($('summary').innerHTML,/No se encontraron niveles/);
        """)

    def test_simple_occupancy_handles_threshold_missing_values_and_yolo_disagreement(self):
        self.js("""
        choose({name:'foto.jpg',size:100,type:'image/jpeg'});
        const data=prediction();data.counts={suficiente:5,reponer:0};
        data.detections=[0,29.99,30,100,null].map((pct,i)=>({id:i+1,label:'Suficiente',confidence:.99,occupancy_estimate:{pct}}));
        show(data);
        assert.equal($('level-occupancy').hidden,false);
        assert.match($('summary').innerHTML,/2 niveles necesitan reposición/);
        assert.match($('summary').innerHTML,/1 sin medición/);
        const rows=$('occupancy-rows').innerHTML.split('</tr>');
        for(const i of [0,1]){assert.match(rows[i],/occupancy-low/);assert.match(rows[i],/Reponer/)}
        for(const i of [2,3]){assert.match(rows[i],/occupancy-enough/);assert.match(rows[i],/Suficiente/)}
        assert.match(rows[4],/occupancy-unknown/);assert.match(rows[4],/Sin medición/);
        assert.match($('photo').alt,/Ocupación estimada/);
        view('compare');assert.equal($('compare-caption').textContent,'Ocupación estimada');
        data.detections=[{id:1,label:'Suficiente',confidence:.99}];show(data);
        assert.match($('summary').innerHTML,/No se pudo estimar/);
        assert.doesNotMatch($('occupancy-rows').innerHTML,/99 %/);
        show(prediction(false));assert.equal($('level-occupancy').hidden,true);
        assert.equal($('occupancy-rows').innerHTML,'');
        """)

    def test_workspace_has_no_version_controls_and_keeps_theme_toggle(self):
        for removed in ('version-step', 'version-cards', 'change-version', 'version-continue', 'version-group', 'id="model"', 'id="method"', 'Ajustes de detección', 'Detalle del modelo YOLO'):
            self.assertNotIn(removed, HTML)
        self.assertIn('<div id="workspace-step">', HTML)
        self.assertNotIn('value="yolo_paulo"', HTML)
        self.js("""
        assert.equal($('theme-toggle').attrs['aria-pressed'],'false');
        $('theme-toggle').listeners.click();
        assert.equal($('theme-toggle').attrs['aria-pressed'],'true');
        assert.equal($('theme-toggle').attrs['aria-label'],'Modo claro');
        $('theme-toggle').listeners.click();
        assert.equal($('theme-toggle').attrs['aria-pressed'],'false');
        assert.equal($('theme-toggle').attrs['aria-label'],'Modo oscuro');
        """)

    def test_thumbnails_are_bounded_and_do_not_replace_originals(self):
        self.js("""
        const original={name:'large.jpg',type:'image/jpeg',size:100};
        let closed=0,drawn,encoded;
        global.createImageBitmap=async file=>{assert.equal(file,original);return {width:4000,height:3000,close(){closed++}}};
        document.createElement=()=>({width:0,height:0,getContext(){return {drawImage(...args){drawn=args}}},toBlob(cb,type,quality){encoded={width:this.width,height:this.height,type,quality};cb({thumbnail:true})}});
        global.URL.createObjectURL=blob=>blob.thumbnail?'blob:thumbnail':'blob:original';
        batch=[{file:original,thumb:null}];
        await buildThumbnails(batch);
        assert.deepEqual(encoded,{width:240,height:180,type:'image/webp',quality:.8});
        assert.equal(drawn[3],240);assert.equal(drawn[4],180);
        assert.equal(batch[0].file,original);assert.equal(batch[0].thumb,'blob:thumbnail');assert.equal(closed,1);
        """)

    def test_analyzing_animation_elements_and_lifecycle(self):
        self.assertIn('spinner', HTML)
        for removed in ('scan-laser', 'scan-grid', 'scan-corner', 'scan-hud-badge', 'scan-line'):
            self.assertNotIn(removed, HTML)
        self.js("""
        choose({name:'test.jpg',size:100,type:'image/jpeg'});
        let submitted=false;
        global.fetch=async()=>{
            assert.equal($('scan-overlay').hidden,false);
            assert.equal($('progress').hidden,false);
            assert.equal($('stage').attrs['aria-busy'],'true');
            assert.match($('photo-info').innerHTML,/Analizando foto/);
            submitted=true;
            return {ok:true,json:async()=>prediction(false)};
        };
        await $('form').listeners.submit({preventDefault(){}});
        assert.equal(submitted,true);
        assert.equal($('scan-overlay').hidden,true);
        assert.equal($('progress').hidden,true);
        assert.equal($('stage').attrs['aria-busy'],'false');
        """)


if __name__ == '__main__':
    unittest.main()

