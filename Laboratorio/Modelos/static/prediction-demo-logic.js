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
  function methodHelp(method){return method==='yolo_paulo_v2'?'V2 combina 70 % de superficie y 30 % de ancho, con umbral adaptativo por nivel. Señal experimental; YOLO determina el estado.':method==='yolo_paulo'?'Analiza bordes, color y textura en la foto original, dentro de cada nivel. El estado lo determina YOLO.':'YOLO localiza cada nivel y determina su estado.'}
  function methodConfig(method){return {occupancy:method==='yolo_paulo'||method==='yolo_paulo_v2',occupancy_version:method==='yolo_paulo_v2'?'v2':'v1'}}
  return {states,stateOf,summary,occupancyRows,occupancyRevision,methodHelp,methodConfig};
})();
