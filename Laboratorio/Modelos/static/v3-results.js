// Resultados y decisión humana del detector geométrico; no aprueba ocupación ni publicación.
const V3Results=(()=>{
  const $=id=>document.getElementById(id),esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let runs=[],trainingSelections=[],current=null,released=null,ready=false,locked=false,saving=false,selection='';
  function render(){
    current=runs.find(r=>r.id===$('v3-result-run').value);
    $('v3-result-content').hidden=!current;$('v3-result-empty').hidden=Boolean(current);
    if(!current)return;
    const nextSelection=trainingSelections.find(s=>s.recommended)||trainingSelections.find(s=>s.source===current.source);
    $('v3-result-next-trial').hidden=current.decision?.status!=='seguir_ajustando'||!nextSelection;
    $('v3-result-next-trial').dataset.objectId=nextSelection?.id||'';
    $('v3-result-next-trial').textContent=nextSelection?`Configurar nuevo ensayo con ${nextSelection.development_counts.train} fotos`:'';
    $('v3-result-metrics').innerHTML=Object.entries(current.metrics?.sets||{}).map(([set,v])=>`<tr><th scope="row">${set==='val_real'?'Validación real':'Diagnóstico sintético'}</th>${['metrics/precision(M)','metrics/recall(M)','metrics/mAP50(M)','metrics/mAP50-95(M)'].map(k=>`<td>${Number.isFinite(v[k])?v[k].toFixed(3):'—'}</td>`).join('')}</tr>`).join('')||'<tr><td colspan="5">Este ensayo no tiene métricas disponibles. Revisa su registro antes de decidir.</td></tr>';
    const history=current.history||[];
    $('v3-result-curve').innerHTML=liveChart(history,[{key:'metrics/mAP50-95(M)',color:'var(--blue)'}],'Calidad de contornos V3 en validación real');
    $('v3-result-history').innerHTML=history.map(row=>`<tr><th scope="row">${esc(row.epoch)}</th><td>${Number.isFinite(row['metrics/mAP50-95(M)'])?row['metrics/mAP50-95(M)'].toFixed(3):'—'}</td></tr>`).join('')||'<tr><td colspan="2">No hay valores por época disponibles.</td></tr>';
    const d=current.decision,official=released?.run===current.id;
    $('v3-result-decision-title').textContent=official?'Modelo oficial':'Decidir el siguiente paso';
    $('v3-result-form').hidden=official;
    $('v3-result-decision').textContent=d?`${{candidato:'Candidato registrado',seguir_ajustando:'Necesita ajustes',descartado:'Descartado'}[d.status]} · ${d.author}. ${d.reason}`:'Falta tu revisión del ensayo. Consulta las métricas y registra la decisión.';
    $('v3-result-next').textContent=d?.status==='candidato'?'Siguiente paso: validar este candidato para la app de revisión antes de adoptarlo. Guardar esta decisión no reemplaza el modelo oficial ni publica el candidato.':d?.status==='seguir_ajustando'?'Siguiente paso: usa los errores observados para definir el cambio del próximo ensayo. Conserva este modelo como referencia.':d?.status==='descartado'?'Siguiente paso: configura otro ensayo desde Entrenar, con un propósito y nombre nuevos.':'Siguiente paso: revisa las métricas y las observaciones disponibles; después elige Candidato, Necesita ajustes o Descartar.';
    if(official)$('v3-result-decision').textContent=`Aceptado por ${released.accepted_by||'el equipo'}. Esta versión se conserva como base del próximo refuerzo.`;
    if(official)$('v3-result-next').textContent='Versión cerrada e integrada en Walmart Vision local. Se conserva su best.pt para el próximo refuerzo. La ocupación es experimental y la visibilidad se confirma manualmente. Los incidentes conocidos permanecen registrados.';
    if(selection!==current.id){selection=current.id;$('v3-result-status').value=d?.status||'seguir_ajustando';$('v3-result-reason').value=d?.reason||'';$('v3-result-author').value=d?.author||$('v3-result-author').value;}
    $('v3-result-fields').disabled=!ready||locked||saving||official;
  }
  function setActive(active,connected,catalog,busy){
    $('v3-results').hidden=!active;$('results-legacy').hidden=active;if(!active)return;
    ready=connected;locked=busy;runs=[...(catalog.v3_training?.runs||[])].filter(r=>r.ready).sort((a,b)=>b.id.localeCompare(a.id));
    trainingSelections=catalog.v3_training?.selections||[];
    released=catalog.v3_training?.vision_release||null;
    if(released)runs.sort((a,b)=>Number(b.id===released.run)-Number(a.id===released.run));
    const previous=$('v3-result-run').value,html=runs.map(r=>`<option value="${esc(r.id)}">${r.id===released?.run?'V3 estable · best.pt':esc(runName(r.id))}</option>`).join('');
    if($('v3-result-run').innerHTML!==html){$('v3-result-run').innerHTML=html;if(runs.some(r=>r.id===previous))$('v3-result-run').value=previous;}
    if(!$('v3-result-author').value)$('v3-result-author').value=catalog.v3_training?.exports?.[0]?.author||'';
    render();
  }
  $('v3-result-run').addEventListener('change',render);
  $('v3-result-form').addEventListener('submit',async event=>{
    event.preventDefault();if(saving||!current||released?.run===current.id)return;saving=true;render();$('v3-result-feedback').textContent='Guardando tu decisión…';
    try{await api('/api/runs/decision',{run:current.id,status:$('v3-result-status').value,reason:$('v3-result-reason').value,author:$('v3-result-author').value});await refresh();$('v3-result-feedback').textContent='Decisión guardada. El inicio del laboratorio ya muestra el siguiente paso.';}
    catch(error){$('v3-result-feedback').textContent=error.message;}
    finally{saving=false;render();}
  });
  function chooseRun(id){if(!runs.some(r=>r.id===id))return;$('v3-result-run').value=id;render();}
  return {setActive,chooseRun};
})();
