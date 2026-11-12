// Consulta visual de la reserva final; no ejecuta predicciones ni permite ajustes.
const V3FinalPreview=(()=>{
  let photos=[],visible=[],ready=false,key='';
  const $=id=>document.getElementById(id);
  function setActive(active,connected,catalog){
    $('v3-final-preview').hidden=!active;$('predict-legacy').hidden=active;
    $('predict-intro').textContent=active?'Fotos reservadas para la prueba final de V3.':'Evalúa el modelo con fotos de validación o fotos nuevas. Revisa sus errores para decidir qué ajustar.';
    if(!active)return;
    ready=connected;
    const nextKey=JSON.stringify([connected,catalog]);
    if(nextKey===key)return;key=nextKey;photos=catalog?.images||[];
    $('v3-final-summary').textContent=!ready?'Consultando las fotos reservadas…':photos.length?`${photos.length} fotos de prueba final · ${catalog.counts.real||0} originales reales · ${catalog.counts.sintetica||0} sintéticas.`:'No se pudo cargar la reserva V3. Revisa la conexión y los registros desde el inicio.';
    if($('v3-final-reserve').open)filter();
    else{$('v3-final-image').hidden=true;$('v3-final-image').removeAttribute('src')}
  }
  function filter(){
    const previous=$('v3-final-photo').value,origin=$('v3-final-origin').value;
    visible=photos.filter(i=>origin==='all'||i.origin===origin);
    $('v3-final-photo').replaceChildren(...visible.map(i=>{const option=document.createElement('option');option.value=i.name;option.textContent=i.name;return option}));
    if(visible.some(i=>i.name===previous))$('v3-final-photo').value=previous;
    $('v3-final-photo').disabled=!ready||!visible.length;$('v3-final-origin').disabled=!ready||!photos.length;
    render();
  }
  function render(){
    const index=visible.findIndex(i=>i.name===$('v3-final-photo').value),photo=visible[index],image=$('v3-final-image');
    $('v3-final-prev').disabled=!ready||index<=0;$('v3-final-next').disabled=!ready||index<0||index>=visible.length-1;
    $('v3-final-error').hidden=true;
    if(!photo){image.hidden=true;image.removeAttribute('src');$('v3-final-caption').textContent='No hay fotos disponibles con este filtro.';$('v3-final-details').textContent='';return}
    image.hidden=false;image.width=photo.width;image.height=photo.height;image.alt='Foto reservada para prueba final: '+photo.name;image.src=photo.url;
    $('v3-final-details').textContent=`${index+1} de ${visible.length} · ${photo.origin==='real'?'Original real':'Variante sintética'} · Escena ${photo.scene}`;
    $('v3-final-caption').textContent=photo.name+' · Prueba final V3';
  }
  $('v3-final-image').addEventListener('error',()=>{const error=$('v3-final-error');error.hidden=false;error.textContent='No se pudo cargar la foto. Revisa que el archivo reservado exista y conserve su contenido.'});
  $('v3-final-reserve').addEventListener('toggle',()=>{if($('v3-final-reserve').open&&ready)filter()});
  $('v3-final-origin').addEventListener('change',filter);$('v3-final-photo').addEventListener('change',render);
  for(const [id,offset] of [['v3-final-prev',-1],['v3-final-next',1]])$(id).addEventListener('click',()=>{const index=visible.findIndex(i=>i.name===$('v3-final-photo').value)+offset;if(visible[index]){$('v3-final-photo').value=visible[index].name;render()}});
  return {setActive};
})();
