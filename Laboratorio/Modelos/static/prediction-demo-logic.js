const PredictionDemo=(()=>{
  const states=[{key:'reponer',label:'Reponer',color:'var(--state-empty)'},{key:'vacio',label:'Vacío',color:'var(--state-empty)'},{key:'baja_disponibilidad',label:'Baja disponibilidad',color:'var(--state-low)'},{key:'suficiente',label:'Suficiente',color:'var(--state-enough)'},{key:'no_evaluable',label:'No evaluable',color:'var(--state-unknown)'}];
  function stateOf(d){return states.find(s=>d.clase==='Nivel_'+s.key)}
  function summary(detections,scope,modelStates){
    const levels=scope==='Nivel_estados'||detections.some(stateOf),counts=Object.fromEntries(states.map(s=>[s.key,detections.filter(d=>stateOf(d)?.key===s.key).length]));
    const alerts=counts.reponer+counts.vacio+counts.baja_disponibilidad,total=detections.length;
    const title=!total?'No se detectaron '+(levels?'niveles':'objetos'):!levels?`${total} detecciones del modelo`:alerts?`${alerts} ${alerts===1?'nivel con posible faltante':'niveles con posibles faltantes'}`:counts.no_evaluable===total?'Los niveles detectados no son evaluables':counts.no_evaluable?'Sin faltantes señalados; hay niveles no evaluables':'Los niveles detectados se ven suficientes';
    const detail=!total?'Prueba otra toma con la góndola completa o revisa la confianza mínima en los ajustes.':!levels?'Este modelo general detecta sus propias clases; elige un modelo del proyecto para ver disponibilidad.':`${total} ${total===1?'nivel detectado':'niveles detectados'}. `+(alerts?'El modelo señala posibles necesidades de reposición en los niveles marcados.':counts.no_evaluable?'En los no evaluables el modelo no pudo asignar un estado de disponibilidad.':'El resultado se refiere únicamente a los niveles que encontró el modelo.');
    const shownStates=Array.isArray(modelStates)?states.filter(s=>modelStates.includes(s.key)):states.filter(s=>s.key==='reponer'?counts.reponer>0:!counts.reponer||!['vacio','baja_disponibilidad'].includes(s.key));
    return {levels,counts,alerts,total,title,detail,states:shownStates};
  }
  function occupancyRows(detections){
    const value=x=>Number.isFinite(x)?x.toFixed(1)+' %':'Sin medición';
    return detections.map((d,i)=>({id:d.id||i+1,state:stateOf(d)?.label||d.clase,
      area:value(d.occupancy?.area_signal_pct),width:value(d.occupancy?.width_signal_pct),
      combined:value(d.occupancy?.combined_signal_pct),reason:d.occupancy?.reason||''}));
  }
  function occupancyRevision(method){return method==='paulo_mascara_v2_combinacion_ponderada'?'Bordes V2 · combinación ponderada':method==='paulo_mascara_v2_color_textura'?'Bordes V1 · Revisión 2 · color y textura':method==='paulo_mascara_v1'?'Revisión 1 · color y oscuridad':'Revisión sin registrar'}
  function occupancySummary(detections,method){
    const weighted=method==='paulo_mascara_v2_combinacion_ponderada';
    const rows=detections.map((d,i)=>{
      const o=d.occupancy,raw=d.occupancy_estimate?d.occupancy_estimate.pct:o?.status==='medido'?o[weighted?'combined_signal_pct':'area_signal_pct']:null;
      const pct=Number.isFinite(raw)&&raw>=0&&raw<=100?raw:null;
      return {id:d.id||i+1,pct,tone:pct===null?'unknown':pct<30?'low':'enough',label:pct===null?'Sin medición':pct<30?'Reponer':'Suficiente'};
    });
    const low=rows.filter(r=>r.tone==='low').length,unknown=rows.filter(r=>r.pct===null).length;
    const title=!rows.length?'No se detectaron niveles':low?`${low} ${low===1?'nivel necesita reposición':'niveles necesitan reposición'}`:unknown===rows.length?'No se pudo estimar la ocupación':unknown?'Sin reposición señalada; hay niveles sin medición':'Los niveles detectados se ven suficientes';
    const detail=`${rows.length} ${rows.length===1?'nivel detectado':'niveles detectados'}.${unknown?` ${unknown} sin medición.`:''}`;
    return {rows,title,detail};
  }
  function methodHelp(method){return method==='yolo'?'YOLO localiza cada nivel y determina su estado.':'Estima la ocupación de cada nivel. Rojo bajo el 30 %; verde desde el 30 %.'}
  function methodConfig(method){return {occupancy:method==='yolo_paulo'||method==='yolo_paulo_v2',occupancy_version:method==='yolo_paulo_v2'?'v2':'v1'}}
  return {states,stateOf,summary,occupancyRows,occupancyRevision,occupancySummary,methodHelp,methodConfig};
})();
