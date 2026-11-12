// Inferencia geométrica V3 en desarrollo y fotos nuevas. Sin estados de disponibilidad.
const V3Prediction=(()=>{
  const $=id=>document.getElementById(id),esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let catalog={models:[],runs:[]},ready=false,locked=false,upload=null,uploading=false,sending=false,jobId=null,shown=null;
  let original=null,prediction=null,view='original',modelKey='';
  const mode=()=>$('v3-predict-source').value;
  const model=()=>catalog.models.find(m=>m.id===$('v3-predict-model').value);
  function fail(message){$('v3-predict-error').hidden=false;$('v3-predict-error').textContent=message;}
  function availability(){
    $('v3-predict-fields').disabled=!ready||locked||uploading||sending||!catalog.models.length;
    $('v3-predict-submit').disabled=!ready||locked||uploading||sending||!model()||!original;
    $('v3-predict-upload').hidden=mode()!=='upload';$('v3-predict-validation').hidden=mode()!=='validation';
  }
  function renderView(){
    $('v3-predict-original-figure').hidden=!original||view==='contours';
    $('v3-predict-result-figure').hidden=view==='original'||!prediction;
    $('v3-predict-original').hidden=!original;
    if(original&&$('v3-predict-original').getAttribute('src')!==original)$('v3-predict-original').src=original;
    if(prediction&&$('v3-predict-result').getAttribute('src')!==prediction)$('v3-predict-result').src=prediction;
    $('v3-predict-images').classList.toggle('is-comparison',view==='compare');
    for(const name of ['original','contours','compare']){
      $('v3-predict-view-'+name).disabled=name!=='original'&&!prediction;
      $('v3-predict-view-'+name).setAttribute('aria-pressed',String(name===view));
    }
    $('v3-predict-empty').hidden=Boolean(original);
    ImageNavigation.mount($('v3-predict-images'));
  }
  function reset(){
    jobId=null;shown=null;prediction=null;view='original';$('v3-predict-error').hidden=true;
    $('v3-predict-status').textContent='';$('v3-predict-summary').textContent='El análisis mostrará niveles y contornos. La ocupación y la reposición todavía no se calculan en esta prueba V3.';
    $('v3-predict-detections').innerHTML='';$('v3-predict-download').hidden=true;
    $('v3-predict-log').textContent='';renderView();availability();
  }
  function selectPhoto(){
    const photo=(catalog.runs.find(r=>r.id===model()?.run)?.photos||[]).find(i=>i.name===$('v3-predict-photo').value);
    original=mode()==='upload'?upload?.url||null:photo?'/api/v3/development-image?model='+encodeURIComponent(model().id)+'&photo='+encodeURIComponent(photo.name):null;
    $('v3-predict-origin').textContent=mode()==='upload'?(upload?upload.name+' · Foto propia · sin anotaciones de referencia':'Sube una foto nueva; no se incorpora al entrenamiento.'):
      photo?`${photo.origin==='real'?'Validación real':'Diagnóstico sintético'} · ${photo.name} · ${photo.scene}`:'No hay fotos de validación disponibles.';
    reset();
  }
  function selectModel(){
    $('v3-predict-decision').dataset.objectId=model()?.run||'';$('v3-predict-decision').disabled=!model();
    const previous=$('v3-predict-photo').value,photos=catalog.runs.find(r=>r.id===model()?.run)?.photos||[];
    $('v3-predict-photo').innerHTML=photos.map(p=>`<option value="${esc(p.name)}">${p.origin==='real'?'Real':'Sintética'} · ${esc(p.name)}</option>`).join('');
    if(photos.some(p=>p.name===previous))$('v3-predict-photo').value=previous;
    $('v3-predict-size').value=String(model()?.imgsz||640);selectPhoto();
  }
  function show(job){
    const result=job.result,detections=result.detecciones||[],metrics=result.metricas;
    prediction=job.image_url;view='contours';shown=job.id;
    $('v3-predict-summary').textContent=`${detections.length} ${detections.length===1?'nivel localizado':'niveles localizados'}. `+(metrics?
      `${metrics.aciertos} de ${metrics.anotados} niveles anotados localizados · ${metrics.omitidos} omitidos · ${metrics.extras} detecciones extra (IoU de máscara ≥ 0,5).`:
      'Foto propia sin anotaciones: muestra predicciones, sin medir precisión.')+' Sin cálculo de ocupación ni estados de reposición.';
    $('v3-predict-detections').innerHTML=detections.length?`<div class="table-wrap"><table><thead><tr><th>Nivel</th><th>Confianza del detector</th><th>Contorno</th></tr></thead><tbody>${detections.map(d=>`<tr><th scope="row">${d.id}</th><td>${Math.round(d.confianza*100)} %</td><td>${d.contorno_valido===null?'Sin máscara':d.contorno_valido?'Válido':'Revisar'}</td></tr>`).join('')}</tbody></table></div><p class="field-help">La confianza del detector no es un porcentaje de ocupación.</p>`:'';
    $('v3-predict-download').href=job.image_url;$('v3-predict-download').download='niveles_v3_'+job.id+'.jpg';$('v3-predict-download').hidden=false;
    renderView();
  }
  function setActive(active,connected,value,allJobs,busy){
    $('v3-prediction').hidden=!active;$('v3-final-reserve').hidden=!active;
    if(!active)return;
    $('predict-intro').textContent='Prueba los contornos de V3 con validación o una foto nueva. La reserva final se consulta por separado.';
    ready=connected;locked=busy;catalog=value||{models:[],runs:[]};
    const key=JSON.stringify(catalog.models);
    if(key!==modelKey){
      modelKey=key;const previous=$('v3-predict-model').value;
      $('v3-predict-model').innerHTML=catalog.models.map(m=>`<option value="${esc(m.id)}">${esc(m.name||runName(m.run))}</option>`).join('');
      if(catalog.models.some(m=>m.id===previous))$('v3-predict-model').value=previous;
      selectModel();
    }
    $('v3-predict-no-model').hidden=Boolean(catalog.models.length);
    const job=allJobs.find(j=>j.id===jobId);
    if(job){
      $('v3-predict-status').textContent=job.state==='running'?'Analizando niveles…':job.state==='done'?'Análisis terminado.':'El análisis no terminó. Revisa el registro de diagnóstico.';
      $('v3-predict-log').textContent=job.log||job.error||'';
      if(job.state==='done'&&job.result&&shown!==job.id)show(job);
    }
    availability();
  }
  $('v3-predict-model').addEventListener('change',selectModel);
  for(const id of ['v3-predict-source','v3-predict-photo'])$(id).addEventListener('change',selectPhoto);
  for(const id of ['v3-predict-conf','v3-predict-nms','v3-predict-size'])$(id).addEventListener('change',reset);
  for(const name of ['original','contours','compare'])$('v3-predict-view-'+name).addEventListener('click',()=>{view=name;renderView();});
  $('v3-predict-file').addEventListener('change',async()=>{
    const file=$('v3-predict-file').files[0];if(!file)return;
    uploading=true;reset();availability();$('v3-predict-status').textContent='Preparando tu foto…';
    try{
      if(!file.size||file.size>15*1024*1024)throw Error('Elige una foto de hasta 15 MB.');
      const response=await fetch('/api/photos',{method:'POST',headers:{'Content-Type':file.type||'application/octet-stream','X-Filename':encodeURIComponent(file.name)},body:file});
      const photo=await response.json();if(!response.ok)throw Error(photo.error||'No se pudo preparar la foto.');
      upload=photo;selectPhoto();
    }catch(error){upload=null;original=null;fail(error.message);renderView();}
    finally{uploading=false;$('v3-predict-file').value='';availability();}
  });
  $('v3-predict-form').addEventListener('submit',async event=>{
    event.preventDefault();if(locked||sending||!original)return;sending=true;locked=true;availability();$('v3-predict-error').hidden=true;
    try{
      const config={action:'predict',pipeline:'geometria_nivel_v3',source_mode:mode(),model:model().id,
        conf:Number($('v3-predict-conf').value),nms:Number($('v3-predict-nms').value),imgsz:Number($('v3-predict-size').value)};
      if(mode()==='upload')config.image=upload.id;else config.photo=$('v3-predict-photo').value;
      const job=await api('/api/jobs',config);jobId=job.id;shown=null;
      jobs=[job,...jobs.filter(j=>j.id!==job.id)];busy=true;updateAvailability();await poll();
    }catch(error){locked=false;fail(error.message);availability();}
    finally{sending=false;updateAvailability();}
  });
  function chooseModel(id){if(catalog.models.some(m=>m.id===id)){$('v3-predict-model').value=id;selectModel()}}
  return {setActive,chooseModel};
})();
