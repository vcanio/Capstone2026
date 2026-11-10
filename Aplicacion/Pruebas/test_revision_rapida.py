"""Regresiones del flujo humano: concurrencia, trazabilidad y lotes recuperables."""
import unittest
import test_vision_ui as ui


class RapidReviewTests(unittest.TestCase):
    js = ui.VisionInterfaceTests.js

    def test_analysis_marks_session_dirty_before_replacement(self):
        self.js(r"""
        chooseBatch([{name:'a.jpg',type:'image/jpeg',size:1}]);
        global.fetch=async()=>({ok:true,json:async()=>prediction()});
        await analyzePhoto(); assert.equal(dirtySelection,true);
        let asked=0; global.confirm=()=>{asked++;return false};
        chooseBatch([{name:'b.jpg',type:'image/jpeg',size:1}]);
        assert.equal(asked,1); assert.equal(batch[0].file.name,'a.jpg');
        """)

    def test_evidence_scales_polygon_and_warns_for_unknown_reference(self):
        self.js(r"""
        let firstPoint=null; global.createImageBitmap=async()=>({width:6000,height:4000,close(){}});
        const ctx={drawImage(){},beginPath(){},moveTo(x,y){firstPoint=[x,y]},lineTo(){},closePath(){},stroke(){},fillRect(){},fillText(){}};
        document.createElement=()=>({getContext:()=>ctx,toBlob:cb=>cb(new Blob(['x']))});
        const item={file:{name:'a.jpg'},result:{width:4096,height:2731,analysis_context:{id:'old'}},issues:[{analysis_id:'old',polygon:[[1000,500],[2000,500],[2000,1000]]}]};
        let warnings=[]; await markedEvidence(item,warnings);
        assert.equal(firstPoint[0],1000*6000/4096); assert.equal(firstPoint[1],500*4000/2731); assert.equal(warnings.length,0);
        item.issues[0].analysis_id='missing'; firstPoint=null; await markedEvidence(item,warnings);
        assert.equal(firstPoint,null); assert.equal(warnings.length,1);
        item.issues[0].polygon_reference={width:4096,height:2731}; await markedEvidence(item,[]); assert.ok(firstPoint);
        """)

    def test_export_snapshot_keeps_later_changes_pending(self):
        self.js(r"""
        global.confirm=()=>true; global.setTimeout=()=>0;
        let release; const original={name:'a.jpg',type:'image/jpeg',size:1,arrayBuffer:()=>new Promise(resolve=>release=resolve)};
        chooseBatch([original]); document.createElement=()=>({click(){}});
        const exporting=exportReviewLot();
        chooseBatch([{name:'b.jpg',type:'image/jpeg',size:1}]);
        batch[0].result=prediction(); reviewCorrect(); assert.equal(dirtySelection,true);
        release(new Uint8Array([1]).buffer); await exporting;
        assert.equal(batch[0].file.name,'b.jpg'); assert.equal(dirtySelection,true);
        """)

    def test_review_during_background_analysis_keeps_each_result_with_its_photo(self):
        self.js(r"""
        chooseBatch([{name:'a.jpg',type:'image/jpeg',size:1},{name:'b.jpg',type:'image/jpeg',size:1},{name:'c.jpg',type:'image/jpeg',size:1}]);
        batch[0].result=prediction();batch[0].analyzedConfidence=.6;
        let finish;global.fetch=async(url,options)=>{await new Promise(resolve=>finish=resolve);return {ok:true,json:async()=>({...prediction(),tag:options.body.name})}};
        const queue=analyzeBatch();assert.equal(batchRunning,true);assert.equal(batchIndex,0);
        assert.equal($('batch-mark').disabled,false);assert.equal($('batch-next').disabled,false);
        reviewCorrect();assert.equal(batch[0].correct,true);
        await selectBatch(2);assert.equal(batchIndex,2);assert.equal(result,null);
        $('batch-pause').listeners.click();finish();await queue;
        assert.equal(batch[1].result.tag,'b.jpg');assert.equal(batch[2].result,null);assert.equal(batch[0].result.tag,undefined);
        assert.equal(result,null);assert.equal(batchIndex,2);
        """)

    def test_multiple_issues_preserve_level_expected_and_human_zone(self):
        self.js(r"""
        chooseBatch([{name:'a.jpg',type:'image/jpeg',size:1}]);batch[0].result=prediction();
        const item=batch[0];$('reviewer-name').value='QA';
        await openReview(1);$('review-level').value='1';$('batch-reason').value=ReviewDesk.reasons[4];suggestExpected();
        saveReviewIssue({preventDefault(){}});
        assert.equal(item.issues.length,1);assert.equal(item.issues[0].level_id,1);assert.equal(item.issues[0].expected,'reponer');
        await openReview();$('review-level').value='zone';reviewZone=ReviewDesk.zone({x:.8,y:.7},{x:.2,y:.3});$('batch-reason').value='Nivel omitido';
        saveReviewIssue({preventDefault(){}});
        assert.equal(item.issues.length,2);assert.equal(item.issues[1].zone.x,.2);assert.equal(item.issues[1].zone.coordinates,'normalized_oriented_image');
        assert.equal(ReviewDesk.status(item),'para_revision');assert.equal(item.issues[0].reviewer,'QA');
        undoReview();assert.equal(item.issues.length,1);
        """)

    def test_save_more_keeps_image_and_target_when_close_events_are_deferred(self):
        self.js(r"""
        chooseBatch([{name:'a.jpg',type:'image/jpeg',size:1},{name:'b.jpg',type:'image/jpeg',size:1}]);
        for(const item of batch)item.result={...prediction(),width:800,height:600};
        const item=batch[0],dialog=$('review-dialog'),pendingClose=[];
        $('review-save-more').id='review-save-more';$('review-save-next').id='review-save-next';
        // Los navegadores entregan el evento close en una tarea posterior.
        dialog.close=function(){this.open=false;pendingClose.push(()=>this.listeners.close())};
        let decoded=0,drawn=0,closed=0;
        global.createImageBitmap=async()=>{decoded++;return {width:800,height:600,close(){closed++}}};
        $('review-canvas').getContext=()=>({clearRect(){},drawImage(){drawn++},strokeRect(){}});
        await openReview(1);const bitmap=reviewBitmap;
        assert.equal(drawn,1);$('review-auto-next').checked=true;
        for(let i=0;i<3;i++){
          $('review-level').value=i===0?'1':'zone';
          reviewZone=i===0?null:ReviewDesk.zone({x:.1,y:.2},{x:.5,y:.6});
          $('batch-reason').value=i===0?'Contorno incorrecto':'Nivel omitido';
          $('batch-note').value='Detalle';$('review-expected').value='nivel';
          saveReviewIssue({preventDefault(){},submitter:$('review-save-more')});
          while(pendingClose.length)pendingClose.shift()();
          await Promise.resolve();
          assert.equal(dialog.open,true);assert.equal(reviewTarget,item);assert.equal(batchIndex,0);
          assert.equal(reviewBitmap,bitmap);assert.equal(closed,0);assert.equal(decoded,1);
          assert.equal(item.issues.length,i+1);assert.equal(reviewZone,null);assert.equal(reviewDrag,null);
          assert.equal($('batch-reason').value,'');assert.equal($('batch-note').value,'');
          assert.equal($('review-expected').value,'');assert.equal($('review-level').value,'photo');
          assert.equal($('review-zone-status').textContent,'');assert.equal(document.activeElement,$('batch-reason'));
        }
        assert.equal(item.issues[0].level_id,1);assert.equal(item.issues[1].zone.x,.1);
        assert.equal(drawn,4);
        $('batch-reason').value='Otro';
        saveReviewIssue({preventDefault(){},submitter:$('review-save-next')});
        assert.equal(dialog.open,false);assert.equal(batchIndex,1);assert.equal(item.issues.length,4);
        while(pendingClose.length)pendingClose.shift()();
        assert.equal(reviewTarget,null);assert.equal(reviewBitmap,null);assert.equal(closed,1);
        """)

    def test_reanalysis_requires_new_review_and_preserves_comparison(self):
        self.js(r"""
        const item={file:{name:'a.jpg'},result:{...prediction(),analysis_context:{id:'old'}},analyzedConfidence:.6};
        ReviewDesk.addIssue(item,{reason:'Contorno incorrecto',level_id:1,expected:'contorno',note:'Arriba'},'QA');
        const newer={...prediction(),analysis_context:{id:'new'}};ReviewDesk.accept(item,newer,.4);
        assert.equal(ReviewDesk.status(item),'sin_revisar');assert.equal(item.issues.length,1);
        assert.equal(item.previousAnalysis.analysis_id,'old');assert.equal(item.previousAnalysis.review.issues[0].analysis_id,'old');
        assert.equal(item.comparison.status,'pendiente');assert.equal(item.comparison.after,'new');
        ReviewDesk.correct(item,'QA');assert.equal(ReviewDesk.status(item),'correcta');assert.equal(item.issues.length,1);
        assert.equal(item.comparison.status,'pendiente');
        """)

    def test_pause_replay_resumes_remaining_photos_with_old_results(self):
        self.js(r"""
        chooseBatch([{name:'a.jpg',type:'image/jpeg',size:1},{name:'b.jpg',type:'image/jpeg',size:1}]);
        for(const item of batch)item.result=prediction();let finish,calls=[];
        global.fetch=async(url,options)=>{calls.push(options.body.name);await new Promise(resolve=>finish=resolve);return {ok:true,json:async()=>prediction()}};
        const replay=analyzeBatch(true);$('batch-pause').listeners.click();finish();await replay;
        assert.equal(batch[0].reanalysisPending,false);assert.equal(batch[1].reanalysisPending,true);
        global.fetch=async(url,options)=>{calls.push(options.body.name);return {ok:true,json:async()=>prediction()}};
        await analyzeBatch();assert.deepEqual(calls,['a.jpg','b.jpg']);assert.equal(batch[1].reanalysisPending,false);
        """)

    def test_fast_keys_advance_undo_and_do_not_mark_while_typing(self):
        self.js(r"""
        chooseBatch([{name:'a.jpg',type:'image/jpeg',size:1},{name:'b.jpg',type:'image/jpeg',size:1}]);
        for(const item of batch)item.result=prediction();$('review-auto-next').checked=true;$('camera-dialog').hidden=true;
        const key=(value,tag='BODY')=>reviewKeydown({key:value,target:{tagName:tag},preventDefault(){}});
        key('a','INPUT');assert.equal(batch[0].correct,undefined);
        key('a');assert.equal(batch[0].correct,true);assert.equal(batchIndex,1);
        key('z');assert.equal(batchIndex,0);assert.equal(ReviewDesk.status(batch[0]),'sin_revisar');
        key('f');key('5','SELECT');assert.equal($('review-expected').value,'reponer');
        key('Enter','TEXTAREA');assert.equal(batch[0].issues.length,0);
        key('Enter','SELECT');assert.equal(batch[0].issues.length,1);assert.equal(batchIndex,1);
        """)

    def test_zip_roundtrip_keeps_original_bytes_and_rejects_corruption(self):
        self.js(r"""
        global.File=class extends Blob{constructor(parts,name,options){super(parts,options);this.name=name}};
        const item={file:new File([new Uint8Array([1,2,3])],'foto.jpg',{type:'image/jpeg'}),result:{...prediction(false),width:100,height:80,image_url:'data:image/jpeg;base64,AA=='},analyzedConfidence:.6};
        ReviewDesk.addIssue(item,{reason:'Nivel omitido',zone:{x:.1,y:.2,width:.3,height:.4},expected:'nivel',note:'Arriba'},'QA');
        const record=ReviewDesk.exportRecord(item,{archivo:'originales/001_foto.jpg',resultado:'resultados/001.json'});
        const encode=value=>new TextEncoder().encode(JSON.stringify(value));
        const blob=zipSelected([{name:record.archivo,bytes:new Uint8Array([1,2,3])},{name:record.resultado,bytes:encode(item.result)},
          {name:'revision.json',bytes:encode({schema_version:2,fotos:[record]})}]);
        const bytes=await blob.arrayBuffer();const files=ReviewDesk.readZip(bytes);
        const restored=ReviewDesk.importRecords(files,{id:item.result.model});
        assert.deepEqual([...new Uint8Array(await restored[0].file.arrayBuffer())],[1,2,3]);
        assert.equal(restored[0].issues[0].expected,'nivel');assert.equal(ReviewDesk.status(restored[0]),'para_revision');
        const incompatible=ReviewDesk.importRecords(files,{id:'new-model'});assert.equal(incompatible[0].result,null);
        assert.equal(incompatible[0].previousAnalysis.result.model,item.result.model);assert.equal(ReviewDesk.status(incompatible[0]),'sin_revisar');
        new Uint8Array(bytes)[30+record.archivo.length]^=1;assert.throws(()=>ReviewDesk.readZip(bytes),/dañado/);
        """)

    def test_gallery_uses_decisions_instead_of_old_average_threshold(self):
        self.js(r"""
        chooseBatch([{name:'a.jpg',type:'image/jpeg',size:1}]);
        batch[0].result={...prediction(),detections:[{id:1,occupancy_estimate:{state:'reponer',pct:45}},{id:2,occupancy_estimate:{state:'suficiente',pct:99}},{id:3,occupancy_estimate:{state:'revisar',pct:null}}]};
        renderBatch();assert.match($('batch-grid').innerHTML,/1 reponer · 1 revisar/);assert.match($('batch-grid').innerHTML,/thumb-low/);
        assert.doesNotMatch($('batch-grid').innerHTML,/72%/);
        assert.match(ReviewDesk.csv([['=CMD()','Nombre']]),/\'=CMD/);
        """)


if __name__ == '__main__':
    unittest.main()
