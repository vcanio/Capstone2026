(()=>{
  const $=id=>document.getElementById(id),data=JSON.parse($('gallery-data').textContent),size=24;
  let page=1;
  const real=data.photos.filter(p=>p.origin==='real').length;
  $('gallery-summary').textContent=`${data.photos.length} fotos seleccionadas: ${real} originales reales y ${data.photos.length-real} ${data.synthetic_label.toLowerCase()}.`;
  $('gallery-description').textContent=data.label+'. Pulsa una foto para abrirla en grande.';
  $('gallery-hard-only').parentElement.hidden=!data.photos.some(p=>p.hard_example);
  function render(){
    const query=$('gallery-search').value.trim().toLowerCase(),origin=$('gallery-origin').value;
    const rows=data.photos.filter(p=>(origin==='all'||p.origin===origin)&&(!$('gallery-hard-only').checked||p.hard_example)&&`${p.name} ${p.family} ${p.scene}`.toLowerCase().includes(query));
    const pages=Math.max(1,Math.ceil(rows.length/size));page=Math.min(page,pages);
    const start=(page-1)*size;
    $('gallery-count').textContent=rows.length?`${start+1}–${Math.min(start+size,rows.length)} de ${rows.length} ${rows.length===1?'foto':'fotos'}${rows.length!==data.photos.length?(rows.length===1?' filtrada':' filtradas'):''}`:'No hay fotos que coincidan. Cambia la búsqueda o limpia los filtros.';
    const items=rows.slice(start,start+size).map(p=>{
      const figure=document.createElement('figure'),link=document.createElement('a'),img=document.createElement('img'),caption=document.createElement('figcaption'),name=document.createElement('strong'),info=document.createElement('span');
      link.href=p.url;link.target='_blank';link.rel='noopener';link.setAttribute('aria-label','Abrir '+p.name+' en grande');
      img.src=p.thumbnail;img.alt=p.name;img.loading='lazy';img.decoding='async';
      img.addEventListener('error',()=>{img.alt='No se pudo cargar '+p.name;info.textContent='No se pudo cargar la miniatura. Pulsa para consultar el original.'},{once:true});
      name.textContent=p.name;info.textContent=`${p.origin==='real'?'Original real':'Variante sintética'} · ${p.scene}${p.hard_example?' · Caso de refuerzo':''}`;
      link.className='gallery-photo';link.append(img);
      if($('gallery-annotations').checked&&p.shapes?.length){
        const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');
        svg.setAttribute('viewBox',`0 0 ${p.width} ${p.height}`);svg.setAttribute('aria-hidden','true');
        for(const shape of p.shapes){const polygon=document.createElementNS(ns,'polygon'),points=[];for(let n=0;n<shape.points.length;n+=2)points.push(shape.points[n]+','+shape.points[n+1]);polygon.setAttribute('points',points.join(' '));polygon.setAttribute('vector-effect','non-scaling-stroke');if(shape.delimitacion==='parcial')polygon.setAttribute('stroke-dasharray','5 3');svg.append(polygon);}link.append(svg);
      }
      caption.append(name,info);
      if(p.cvat_url){const cvat=document.createElement('a');cvat.href=p.cvat_url;cvat.target='_blank';cvat.rel='noopener';cvat.textContent='Abrir en CVAT';caption.append(cvat);}
      figure.append(link,caption);return figure;
    });
    $('gallery-grid').replaceChildren(...items);$('gallery-prev').disabled=page===1;$('gallery-next').disabled=page===pages;
    $('gallery-page').textContent=`Página ${page} de ${pages}`;
  }
  $('gallery-filters').addEventListener('submit',event=>event.preventDefault());
  for(const id of ['gallery-search','gallery-origin'])$(id).addEventListener(id==='gallery-search'?'input':'change',()=>{page=1;render()});
  for(const id of ['gallery-hard-only','gallery-annotations'])$(id).addEventListener('change',()=>{page=1;render()});
  $('gallery-clear').addEventListener('click',()=>{$('gallery-search').value='';$('gallery-origin').value='all';$('gallery-hard-only').checked=false;page=1;render()});
  $('gallery-prev').addEventListener('click',()=>{page--;render();$('gallery-count').scrollIntoView({block:'start'})});
  $('gallery-next').addEventListener('click',()=>{page++;render();$('gallery-count').scrollIntoView({block:'start'})});
  render();
})();
