// Flujo de entrenamiento geométrico. Los estados de disponibilidad pertenecen a V1/V2.
const V3Training=(()=>{
  const $=id=>document.getElementById(id),esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let exports=[],selections=[],trainingDefaults={},selectionKey='',sending=false,currentJob=null,chartKey=null;
  const basePurpose=$('v3-train-purpose').value;
  function selection(){return selections.find(s=>s.id===$('v3-train-selection').value&&s.source===$('v3-train-source').value)}
  function describeModel(){
    const value=$('v3-train-model').value,required=selection()?.required_initial_model;
    const mismatch=Boolean(required&&value&&value!==required);
    $('v3-model-explanation').textContent=mismatch?'Esta selección requiere otro modelo de partida. Elige el modelo preparado para ella o cambia la selección de fotografías.':!value?'Elige un modelo de partida.':value.startsWith('Modelos/preentrenados/')?'Entrenamiento nuevo desde un modelo general preentrenado. No utiliza los pesos del modelo V3 actual.':'Afinado de un modelo de segmentación ya entrenado. Continúa desde sus pesos.';
    $('v3-train-submit').disabled=mismatch||!value;
  }
  function selectChoice(){
    const row=selection(),defaults={...trainingDefaults,...row?.training_defaults};
    $('v3-train-name').value=row?.trial_name||defaults.name||'v3_refuerzo_actual';
    $('v3-train-purpose').value=row?.purpose||defaults.purpose||basePurpose;summary();
    for(const [key,value] of Object.entries(defaults))if(['epochs','batch','lr','seed','patience','imgsz','model'].includes(key))$('v3-train-'+key).value=String(value);
    describeModel();
  }
  function renderSelections(){
    const rows=selections.filter(s=>s.source===$('v3-train-source').value),key=JSON.stringify(rows)+$('v3-train-source').value;
    if(key===selectionKey)return;selectionKey=key;
    const previous=$('v3-train-selection').value;
    $('v3-train-selection').innerHTML='<option value="">Todos los datos de esta exportación revisada</option>'+rows.map(s=>`<option value="${esc(s.id)}">${esc(s.label)} · ${s.development_counts.train} fotos</option>`).join('');
    $('v3-train-selection').value=rows.some(s=>s.id===previous)?previous:rows[0]?.id||'';selectChoice();
  }
  function summary(){
    const row=exports.find(e=>e.id===$('v3-train-source').value),c={...row?.counts,...selection()?.development_counts};
    const gallery=$('v3-train-gallery');gallery.hidden=!selection();if(selection()){gallery.href='/v3/selection?selection='+encodeURIComponent(selection().id);gallery.textContent=`Ver las ${c.train} fotos seleccionadas`;}
    const testCount=Number(c.test_real||0)+Number(c.test_sintetica||0);
    $('v3-train-data').textContent=row?`${c.train||0} fotos para aprender · ${c.val_real||0} reales para validar · ${c.val_sintetica||0} sintéticas para diagnóstico. ${testCount?`${testCount} fotos de prueba interna reservadas.`:'Prueba final externa aún no incorporada.'} ${row.excluded} ${row.excluded===1?'foto excluida':'fotos excluidas'} de la exportación.${selection()?` Esta selección aparta ${selection().excluded_train_count} de entrenamiento y ${selection().excluded_val_count||0} de validación.`:''}${row.partition_note?' Compara métricas solo entre ensayos con la misma validación.':''}`:'Guarda una exportación revisada en Preparar datos para configurar el entrenamiento.';
  }
  function setActive(active,ready,catalog,jobs,busy){
    $('v3-training').hidden=!active;$('train-layout').hidden=active;if(!active)return;
    const value=catalog?.v3_training||{},previous=$('v3-train-source').value;
    if(value.initial_models){const previousModel=$('v3-train-model').value,markup=value.initial_models.map(m=>`<option value="${esc(m.id)}">${esc(m.label)}</option>`).join('');if($('v3-train-model').innerHTML!==markup){$('v3-train-model').innerHTML=markup;if(value.initial_models.some(m=>m.id===previousModel))$('v3-train-model').value=previousModel;}}
    const pilot=value.module_pilot;$('v3-module-pilot').hidden=!pilot;
    if(pilot)$('v3-module-pilot').innerHTML=(pilot.partition_note?esc(pilot.partition_note)+' ':`Piloto de módulos: ${pilot.train_images} fotos de entrenamiento y ${pilot.val_images} de validación. Propuestas pendientes de revisión; sin entrenamiento de módulos. `)+Object.entries(pilot.tasks).map(([split,t])=>`<a href="http://localhost:8082/tasks/${Number(t.task_id)}/jobs/${Number(t.job_id)}" target="_blank" rel="noopener">Revisar tarea ${Number(t.task_id)} en CVAT</a>`).join(' · ');
    exports=value.exports||[];selections=value.selections||[];trainingDefaults=value.defaults||{};
    const markup=exports.map(e=>`<option value="${esc(e.id)}">${e.created_at?esc(new Date(e.created_at).toLocaleDateString('es-CL',{timeZone:'America/Santiago',day:'2-digit',month:'short',year:'numeric'})):'Exportación revisada'} · ${e.counts.train} fotos</option>`).join('');
    if($('v3-train-source').innerHTML!==markup){$('v3-train-source').innerHTML=markup;if(exports.some(e=>e.id===previous))$('v3-train-source').value=previous;}
    renderSelections();summary();describeModel();$('v3-train-fields').disabled=!ready||!value.supported||busy||sending||!exports.length;
    if(value.error)$('v3-train-data').textContent=value.error;
    const relevant=jobs.filter(j=>j.config?.action==='train'&&j.config?.pipeline==='geometria_nivel_v3');
    const job=relevant.find(j=>j.state==='running')||relevant.find(j=>j.id===currentJob)||relevant[0];
    const runs=value.runs||[],run=runs.find(r=>r.id===job?.config.run);
    // Un ensayo cerrado se consulta en Resultados; el seguimiento muestra trabajo activo o fallido.
    $('v3-training-monitor').hidden=!job||job.state==='done';
    if(!job)return;
    const monitor=$('v3-training-monitor'),container=$('v3-training');
    if(container.firstElementChild!==monitor)container.prepend(monitor);
    currentJob=job.id;
    const p=job.progress||{},history=run?.history||[],last=history.at(-1)||{};
    const completed=Math.max(p.completed_epochs||0,...history.map(r=>r.epoch||0));
    const stage={preparing:`Preparando fotos y etiquetas${p.total_images?' · '+(p.prepared_images||0)+' de '+p.total_images:''}`,training:'Aprendiendo contornos',evaluating:'Evaluando reales y sintéticas por separado',done:'Entrenamiento terminado'}[p.stage]||'Preparando';
    $('v3-training-state').textContent=job.state==='error'||job.state==='interrupted'?'El ensayo se detuvo. Revisa el registro antes de reintentar.':stage;
    $('v3-training-run').textContent=job.config.run;
    $('v3-training-progress').max=job.config.epochs;$('v3-training-progress').value=completed;
    const epoch=p.stage==='training'&&job.state==='running'&&p.current_epoch?`Época ${p.current_epoch} de ${job.config.epochs} en curso · ${completed} completadas`:`${completed} / ${job.config.epochs} épocas completadas`;
    $('v3-training-count').textContent=`${epoch} · ${p.device||'Dispositivo por confirmar'} · mAP50–95 de máscaras: ${Number.isFinite(last['metrics/mAP50-95(M)'])?last['metrics/mAP50-95(M)'].toFixed(3):'—'}`;
    const state=Lab.trainingState(job,run),number=v=>Number.isFinite(v)?v.toFixed(3):'—';
    $('v3-training-duration').textContent=`Tiempo ${state.terminal?'registrado':'transcurrido'}: ${duration(state.elapsed)}${job.state==='done'&&completed<job.config.epochs?' · Terminó antes del máximo configurado':''}`;
    $('v3-training-map').textContent=number(last['metrics/mAP50-95(M)']);
    $('v3-training-best').textContent=number(state.best?.['metrics/mAP50-95(M)']);
    $('v3-training-best-epoch').textContent=state.best?'Observado en época '+state.best.epoch:'Esperando validación real';
    $('v3-training-loss').textContent=number(last['train/seg_loss']);
    const key=JSON.stringify([job.id,history]);
    if(key!==chartKey){
      chartKey=key;
      $('v3-live-quality').innerHTML=liveChart(history,[{key:'metrics/mAP50-95(M)',color:'var(--blue)'}],'Evolución V3 de la calidad de contornos en validación real');
      $('v3-live-loss').innerHTML=liveChart(history,[{key:'train/seg_loss',color:'var(--blue)'},{key:'val/seg_loss',color:'var(--green)',dashed:true}],'Evolución V3 del error de aprendizaje y validación real');
      $('v3-training-history').innerHTML=history.map(r=>`<tr><th scope="row">${r.epoch}</th><td>${number(r['metrics/mAP50-95(M)'])}</td><td>${number(r['train/seg_loss'])}</td><td>${number(r['val/seg_loss'])}</td></tr>`).join('')||'<tr><td colspan="4">Esperando la primera época completada.</td></tr>';
    }
    const preview=p.preview_url;$('v3-training-preview').hidden=!preview;
    if(preview){
      if($('v3-training-preview-image').getAttribute('src')!==preview)$('v3-training-preview-image').src=preview;
      const validation=p.preview_kind==='validation';
      $('v3-training-preview-title').textContent=validation?'Lo que encuentra en validación real':'Ejemplos que está usando';
      $('v3-training-preview-caption').textContent=validation?'Predicciones del ensayo en validación real. La prueba final permanece reservada.':'Imágenes y anotaciones del entrenamiento.';
      $('v3-training-preview-image').alt=validation?'Predicciones V3 en fotos de validación real':'Fotos y anotaciones del entrenamiento V3';
      ImageNavigation.mount($('v3-training-preview'));
    }
    $('v3-training-log').textContent=job.log||'Esperando el primer avance.';
    const metrics=run?.metrics?.sets||job.result?.metrics;
    $('v3-training-metrics').hidden=!metrics;
    if(metrics){
      const keys=['metrics/precision(M)','metrics/recall(M)','metrics/mAP50(M)','metrics/mAP50-95(M)'];
      $('v3-training-metric-rows').innerHTML=Object.entries(metrics).map(([split,values])=>`<tr><th scope="row">${split==='val_real'?'Validación real':'Diagnóstico sintético'}</th>${keys.map(k=>`<td>${Number.isFinite(values[k])?values[k].toFixed(3):'—'}</td>`).join('')}</tr>`).join('');
    }
  }
  $('v3-train-source').addEventListener('change',()=>{renderSelections();summary()});
  $('v3-train-selection').addEventListener('change',selectChoice);
  $('v3-train-model').addEventListener('change',describeModel);
  $('v3-train-form').addEventListener('submit',async event=>{
    event.preventDefault();if(sending)return;sending=true;$('v3-train-error').hidden=true;$('v3-train-fields').disabled=true;
    try{
      const config={action:'train',pipeline:'geometria_nivel_v3',source:$('v3-train-source').value,
        name:$('v3-train-name').value,model:$('v3-train-model').value,purpose:$('v3-train-purpose').value};
      if(selection())config.selection=selection().id;
      for(const key of ['epochs','batch','lr','seed','patience','imgsz'])config[key]=Number($('v3-train-'+key).value);
      await submit(config);
    }catch(error){$('v3-train-error').textContent=error.message;$('v3-train-error').hidden=false;$('v3-train-error').focus();}
    finally{sending=false;updateAvailability();}
  });
  function chooseSelection(id){const row=selections.find(s=>s.id===id);if(!row)return;$('v3-train-source').value=row.source;selectionKey='';renderSelections();$('v3-train-selection').value=id;selectChoice();const defaults={...trainingDefaults,...row.training_defaults};for(const key of ['epochs','batch','lr','seed','patience','imgsz','model'])if(defaults[key]!==undefined)$('v3-train-'+key).value=String(defaults[key]);describeModel();}
  return {setActive,chooseSelection};
})();
