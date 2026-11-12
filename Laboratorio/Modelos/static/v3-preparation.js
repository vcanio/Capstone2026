// Preparación V3 independiente de las copias históricas y del entrenamiento.
const V3Preparation = (() => {
  let active=false, ready=false, loading=false, loaded=false, copy=null, selection=[];
  const node=id=>document.getElementById(id);
  const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const names={train:'Entrenamiento',val:'Validación',test:'Prueba final'};
  const policy='niveles_visibles_revisados_v3_20261025';
  async function request(path,body){
    const response=await fetch(path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{signal:AbortSignal.timeout(20000)});
    const value=await response.json();if(!response.ok)throw Error(value.error||'No se pudo consultar la preparación V3.');return value;
  }
  function failure(error){const box=node('v3-error');box.hidden=false;box.textContent=error.message+' Conservamos la última copia. Revisa la conexión o lo indicado y reintenta.';box.focus()}
  function availability(){
    node('v3-prepare').disabled=!ready||loading;
    node('v3-prepare').textContent=loading?'Comprobando fotos y anotaciones…':'Traer y comprobar anotaciones V3';
    node('v3-reload').disabled=!ready||loading;
    node('v3-export-fields').disabled=!ready||loading||!copy||!copy.eligible_images||copy.policy_version!==policy;
    node('datasets-v3').setAttribute('aria-busy',String(loading));
  }
  function setActive(value,connected){
    active=value;ready=connected;node('datasets-v3').hidden=!active;node('datasets-legacy').hidden=active;
    availability();if(active&&ready&&!loaded&&!loading)load();
  }
  async function load(){
    loading=true;availability();node('v3-error').hidden=true;
    try{const value=await request('/api/v3/preparation');copy=value.report;loaded=true;render()}
    catch(err){loaded=true;node('v3-status').textContent='No pudimos consultar la última copia.';failure(err)}
    finally{loading=false;availability()}
  }
  async function prepare(){
    loading=true;availability();node('v3-error').hidden=true;
    node('v3-status').textContent='Verificando los archivos de la partición activa y leyendo sus tareas de CVAT. Puede tardar un par de minutos.';
    try{copy=await request('/api/v3/prepare',{});loaded=true;node('v3-reviewed').checked=false;node('v3-export-status').textContent='';render();document.dispatchEvent(new Event('v3-prepared'))}
    catch(err){node('v3-status').textContent='La consulta no terminó. Puedes reintentar.';failure(err)}
    finally{loading=false;availability()}
  }
  function render(){
    node('v3-report').hidden=!copy;
    node('v3-status').textContent=!copy?'Aún no hay una copia V3. Pulsa Traer y comprobar anotaciones V3 para comenzar.':copy.policy_version!==policy?'Esta copia usa el filtro anterior. Pulsa Traer y comprobar anotaciones V3 para aplicar la política de parciales revisados.':'Copia local disponible. Revisa las regiones visibles y sus avisos antes de exportar.';
    if(!copy)return;
    node('v3-summary').textContent=`${copy.image_count} fotos · ${copy.polygon_count} polígonos · ${copy.blocked_images} ${copy.blocked_images===1?'bloqueada':'bloqueadas'} · ${copy.eligible_images} sin bloqueos técnicos. ${copy.partial_polygons??copy.images.reduce((n,i)=>n+i.shapes.filter(s=>s.delimitacion==='parcial').length,0)} niveles parciales · ${copy.occluded_polygons} ocluidos. La revisión visual sigue siendo necesaria.`;
    node('v3-copy-date').textContent=`Consulta de CVAT: ${new Date(copy.created_at).toLocaleString('es-CL')} · Copia ${copy.id}. Los cambios posteriores de CVAT requieren una nueva consulta.`;
    filter();
  }
  function filter(){
    if(!copy)return;
    const split=node('v3-split').value,mode=node('v3-filter').value,previous=node('v3-photo').value;
    selection=copy.images.filter(i=>{
      if(split!=='all'&&i.split!==split)return false;
      if(mode==='partial')return i.shapes.some(s=>s.delimitacion==='parcial');
      if(mode==='occluded')return i.shapes.some(s=>s.occluded);
      if(mode==='warnings')return Boolean(i.warnings?.length);
      return mode==='all'||(mode==='eligible')===i.eligible;
    });
    node('v3-photo').innerHTML=selection.map(i=>`<option value="${escape(i.name)}">${escape(i.cvat_name ?? i.name)} · ${escape(names[i.split])}</option>`).join('');
    if(selection.some(i=>i.name===previous))node('v3-photo').value=previous;
    node('v3-empty').hidden=Boolean(selection.length);node('v3-inspector').hidden=!selection.length;node('v3-photo').disabled=!selection.length;
    photo();
  }
  function photo(){
    const index=selection.findIndex(i=>i.name===node('v3-photo').value),image=selection[index];
    node('v3-prev').disabled=index<=0;node('v3-next').disabled=index<0||index===selection.length-1;
    if(!image){node('v3-image').replaceChildren();return}
    node('v3-cvat').href=`http://localhost:8082/tasks/${image.cvat_task_id ?? image.task_id}/jobs/${image.job_id}?frame=${image.frame}`;
    const url='/api/v3/image?id='+encodeURIComponent(copy.id)+'&photo='+encodeURIComponent(image.name);
    const polygons=image.shapes.map(s=>{
      const points=s.points;if(!Array.isArray(points)||points.some(v=>typeof v!=='number'||!Number.isFinite(v)))return '';
      const pairs=[];for(let j=0;j+1<points.length;j+=2)pairs.push(points[j]+','+points[j+1]);
      return `<polygon class="${s.delimitacion==='completa'?'complete':'pending'}" points="${pairs.join(' ')}"><title>Nivel ${escape(s.id)} · ${escape(s.delimitacion)}${s.occluded?' · ocluido':''}</title></polygon>`;
    }).join('');
    node('v3-image').innerHTML=`<img src="${url}" alt="${escape(image.name)} con los contornos de la copia de CVAT"><svg viewBox="0 0 ${image.width} ${image.height}" aria-hidden="true">${polygons}</svg>`;
    node('v3-image').querySelector('img').addEventListener('error',()=>{node('v3-caption').textContent='No se pudo cargar la foto. Revisa que esté disponible en el equipo y vuelve a consultar.'});
    node('v3-caption').textContent=`${index+1} de ${selection.length} · ${names[image.split]} · ${image.origen==='real'?'Original real':'Variante sintética'} · ${image.grupo_escena}`;
    const describe=i=>`<li>${i.shape_id!=null?'Nivel '+escape(i.shape_id)+': ':''}${escape(i.detail)}</li>`;
    const partials=image.shapes.filter(s=>s.delimitacion==='parcial').length;
    const problems=image.issues.map(describe).join(''),warnings=(image.warnings||[]).map(describe).join('');
    node('v3-issues').innerHTML=`<p>${image.shapes.length} niveles · ${partials} ${partials===1?'parcial':'parciales'} · ${image.shapes.filter(s=>s.occluded).length} ocluidos.</p><p>${image.eligible?'Sin bloqueos técnicos. Confirma la revisión de las regiones visibles antes de exportar.':'Foto excluida de la exportación hasta resolver sus bloqueos.'}</p>${problems?'<h4>Bloqueos de exportación</h4><ul>'+problems+'</ul>':''}${warnings?'<div class="note"><strong>Avisos para la revisión visual</strong><ul>'+warnings+'</ul></div>':''}<details><summary>Delimitación de cada nivel</summary><ul>${image.shapes.map(s=>`<li>Nivel ${escape(s.id)}: ${escape(s.delimitacion)}${s.occluded?' · ocluido':''}</li>`).join('')}</ul></details>`;
  }
  node('v3-prepare').addEventListener('click',prepare);node('v3-reload').addEventListener('click',load);
  for(const id of ['v3-split','v3-filter'])node(id).addEventListener('change',filter);
  node('v3-photo').addEventListener('change',photo);
  for(const [id,offset] of [['v3-prev',-1],['v3-next',1]])node(id).addEventListener('click',()=>{const next=selection.findIndex(i=>i.name===node('v3-photo').value)+offset;if(selection[next]){node('v3-photo').value=selection[next].name;photo()}});
  node('v3-export-form').addEventListener('submit',async event=>{
    event.preventDefault();if(!copy||loading)return;loading=true;availability();node('v3-error').hidden=true;
    node('v3-export-status').textContent='Guardando imágenes, etiquetas y registro de exclusiones…';
    try{const result=await request('/api/v3/export',{id:copy.id,author:node('v3-author').value,reviewed:node('v3-reviewed').checked});node('v3-export-status').textContent=`Exportación guardada en ${result.path}. ${result.excluded} fotos excluidas. Puedes configurar el ensayo en Entrenar.`;document.dispatchEvent(new Event('v3-prepared'))}
    catch(err){node('v3-export-status').textContent='No se completó la exportación.';failure(err)}finally{loading=false;availability()}
  });
  return {setActive};
})();
