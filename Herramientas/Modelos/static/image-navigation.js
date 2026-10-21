const ImageNavigation=(()=>{
  const clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
  function constrain(state){
    const {width,height,fitWidth,fitHeight,scale}=state;
    return {...state,x:fitWidth*scale<=width?(width-fitWidth*scale)/2:clamp(state.x,width-fitWidth*scale,0),y:fitHeight*scale<=height?(height-fitHeight*scale)/2:clamp(state.y,height-fitHeight*scale,0)};
  }
  function zoom(state,scale,x=state.width/2,y=state.height/2){
    scale=clamp(scale,1,8);const ratio=scale/state.scale;
    return constrain({...state,scale,x:x-(x-state.x)*ratio,y:y-(y-state.y)*ratio});
  }
  function mount(root){
    for(const image of root.querySelectorAll('img.photo,.drawing-photo>img,#monitor-preview-image')){
      if(image.hidden||!image.getAttribute('src')||image.closest('.image-viewer'))continue;
      const target=image.closest('.drawing-photo')||image,viewer=document.createElement('div');viewer.className='image-viewer';
      const icon=plus=>`<svg viewBox="0 0 20 20" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M4 10h12${plus?'M10 4v12':''}"/></svg>`;
      viewer.innerHTML=`<div class="image-tools" title="Haz clic en la imagen para activar el zoom con la rueda. Arrastra para desplazarte."><button type="button" data-zoom="out" aria-label="Alejar imagen">${icon(false)}</button><output aria-label="Nivel de zoom">100%</output><button type="button" data-zoom="in" aria-label="Acercar imagen">${icon(true)}</button><button type="button" data-zoom="fit">Ajustar</button></div><div class="image-viewport" tabindex="0" role="region"><div class="image-stage"></div><p class="image-failure" hidden>No se pudo cargar la imagen. Vuelve a seleccionar la foto para reintentar.</p></div>`;
      target.before(viewer);
      const viewport=viewer.querySelector('.image-viewport'),stage=viewer.querySelector('.image-stage'),tools=viewer.querySelector('.image-tools'),output=viewer.querySelector('output'),failure=viewer.querySelector('.image-failure');
      viewport.setAttribute('aria-label',(image.alt||'Imagen')+'. Zoom con las teclas más y menos; flechas para desplazarte; cero para ajustar.');
      image.draggable=false;stage.append(target);
      let state={width:0,height:0,fitWidth:0,fitHeight:0,scale:1,x:0,y:0},drag=null;
      function paint(){stage.style.transform=`translate(${state.x}px,${state.y}px) scale(${state.scale})`;output.value=Math.round(state.scale*100)+'%';viewport.dataset.zoomed=String(state.scale>1);tools.querySelector('[data-zoom="out"]').disabled=state.scale===1;tools.querySelector('[data-zoom="in"]').disabled=state.scale===8}
      function measure(){
        const {width,height}=viewport.getBoundingClientRect();if(!width||!height||!image.naturalWidth||!image.naturalHeight)return;
        const fit=Math.min(width/image.naturalWidth,height/image.naturalHeight);
        state=constrain({width,height,fitWidth:image.naturalWidth*fit,fitHeight:image.naturalHeight*fit,scale:1,x:0,y:0});
        stage.style.width=state.fitWidth+'px';stage.style.height=state.fitHeight+'px';paint();
      }
      function change(scale,x,y){if(!state.width)return;state=zoom(state,scale,x,y);paint()}
      tools.addEventListener('click',event=>{const action=event.target.closest('[data-zoom]')?.dataset.zoom;if(!action)return;change(action==='fit'?1:state.scale*(action==='in'?1.25:1/1.25));viewport.focus({preventScroll:true})});
      viewport.addEventListener('wheel',event=>{if(!viewer.contains(document.activeElement)&&!event.ctrlKey)return;if(!state.width)return;event.preventDefault();const rect=viewport.getBoundingClientRect();change(state.scale*Math.exp(-clamp(event.deltaY,-100,100)*.003),event.clientX-rect.left,event.clientY-rect.top)},{passive:false});
      viewport.addEventListener('pointerdown',event=>{if(event.button!==0||event.target.closest('button'))return;viewport.focus({preventScroll:true});if(state.scale===1)return;drag={id:event.pointerId,x:event.clientX,y:event.clientY,originX:state.x,originY:state.y};viewport.setPointerCapture(event.pointerId);viewport.dataset.dragging='true';event.preventDefault()});
      viewport.addEventListener('pointermove',event=>{if(!drag||drag.id!==event.pointerId)return;state=constrain({...state,x:drag.originX+event.clientX-drag.x,y:drag.originY+event.clientY-drag.y});paint()});
      function endDrag(){drag=null;viewport.dataset.dragging='false'}
      viewport.addEventListener('pointerup',endDrag);viewport.addEventListener('pointercancel',endDrag);viewport.addEventListener('lostpointercapture',endDrag);
      viewport.addEventListener('keydown',event=>{if(event.ctrlKey||event.altKey||event.metaKey)return;const key=event.key;if(['+','=','-','0','Home','ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(key)){event.preventDefault();if(['+','=','-'].includes(key))change(state.scale*(key==='-'?1/1.25:1.25));else if(['0','Home'].includes(key))change(1);else{state=constrain({...state,x:state.x+(key==='ArrowLeft'?40:key==='ArrowRight'?-40:0),y:state.y+(key==='ArrowUp'?40:key==='ArrowDown'?-40:0)});paint()}}else if(key==='Escape')viewport.blur()});
      image.addEventListener('load',()=>{failure.hidden=true;stage.hidden=false;tools.hidden=false;measure()});
      image.addEventListener('error',()=>{failure.hidden=false;stage.hidden=true;tools.hidden=true});
      const observer=new ResizeObserver(measure);observer.observe(viewport);
      // Release resize observers when a selection replaces its images.
      viewer.releaseViewer=()=>observer.disconnect();
      measure();
    }
  }
  function release(root){for(const viewer of root.querySelectorAll('.image-viewer'))viewer.releaseViewer?.()}
  return {constrain,zoom,mount,release};
})();
