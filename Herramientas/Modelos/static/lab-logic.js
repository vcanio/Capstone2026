
// Funciones sin DOM: estados y selección probados con casos aislados.
const Lab = (() => {
  const readyCopy = copy => ['lista_modulos','lista_niveles'].includes(copy?.state);
  const blocked = report => report?.bloqueos_entrenamiento ?? report?.bloqueos_modulos ?? 0;
  const levelsCopy = copy => copy?.scope === 'Nivel_estados' || copy?.manifest?.scope === 'Nivel_estados';
  function profile(item){
    const report=item?.report||item?.manifest||item||{},criterion=report.criterion||item?.criterion||{},classes=report.clases||item?.classes||[];
    const known=classes.filter(name=>typeof name==='string'&&name.startsWith('Nivel_')).map(name=>name.slice(6));
    const legacy=['vacio','baja_disponibilidad','suficiente','no_evaluable'];
    if(known.includes('vacio')||known.includes('baja_disponibilidad')||criterion.version==='disponibilidad_visual_nivel_v1')return {id:'v1',label:'v1 · 4 estados',states:known.length?known:legacy};
    if(known.includes('reponer')||criterion.version==='disponibilidad_visual_nivel_v2_reponer'){
      const states=known.length?known:criterion.stage==='base'||report.stage==='base'?['reponer','suficiente']:['reponer','suficiente','no_evaluable'];
      return {id:states.includes('no_evaluable')?'v2_visibilidad':'v2_base',label:states.includes('no_evaluable')?'v2 · 3 estados':'v2 base · 2 estados',states};
    }
    return {id:levelsCopy(item)?'sin_registrar':'general',label:levelsCopy(item)?'Niveles · criterio sin registrar':report.scope==='Modulo'||classes.includes('Modulo')?'Piloto · módulos':'Modelo general',states:[]};
  }
  function versionOf(item,catalog={runs:[]}){
    if(item?.run){const run=catalog.runs.find(r=>r.id===item.run);if(run)return versionOf(run,catalog)}
    const id=profile(item).id,criterion=item?.criterion_version;
    if(id.startsWith('v2')||criterion==='disponibilidad_visual_nivel_v2_reponer'||[19,22].includes(item?.task_id))return 'v2';
    if(id==='v1'||criterion==='disponibilidad_visual_nivel_v1'||item?.task_id===16)return 'v1';
    return 'otros';
  }
  function versionCatalog(catalog,version){
    const belongs=item=>versionOf(item,catalog)===version;
    const runs=catalog.runs.filter(belongs),datasets=catalog.datasets.filter(belongs),names=new Set();
    for(const item of [...runs,...datasets])for(const photo of (item.report||item.manifest)?.imagenes||[])if(['train','val'].includes(photo.split))names.add(photo.imagen_id||photo.imagen?.replace(/\.[^.]+$/,''));
    return {...catalog,runs,datasets,images:(catalog.images||[]).filter(i=>i.project_version===version||names.has(i.name)||(version==='otros'&&!i.project_version)),
      archived_datasets:(catalog.archived_datasets||[]).filter(belongs),
      models:catalog.models.filter(m=>!m.run||belongs(m)),
      archived_models:(catalog.archived_models||[]).filter(belongs)};
  }
  function predictionImages(catalog,modelId){
    const model=catalog.models.find(m=>m.id===modelId);
    if(!model)return [];
    const trained=new Set(model.training_images||[]);
    return catalog.images.filter(image=>!trained.has(image.id));
  }
  function versionStatus(catalog,version,activeJobs=[]){
    const scoped=versionCatalog(catalog,version),running=activeJobs.some(j=>j.state==='running'&&j.config?.action==='train'&&versionOf(catalog.runs.find(r=>r.id===j.config.run||r.id===j.config.source)||catalog.datasets.find(v=>v.id===j.config.source),catalog)===version);
    if(running)return 'Entrenando · puedes seguir el avance en Entrenar';
    const count=new Set(scoped.models.filter(m=>m.run&&scoped.runs.some(r=>r.id===m.run&&r.ready)&&!technical(m.run)).map(m=>m.run)).size;
    if(count)return `Modelo disponible · ${count} ${count===1?'entrenamiento listo':'entrenamientos listos'} para probar`;
    if(scoped.datasets.some(readyCopy))return 'Datos preparados · listo para entrenar el primer modelo';
    if(scoped.datasets.length)return 'Anotaciones importadas · revisa su preparación';
    return 'Sin datos importados en esta versión';
  }
  const technical = run => Boolean(run?.startsWith('verificacion_panel'));
  function currentCopy(catalog, selectedId){
    return catalog.datasets.find(v=>v.id===selectedId) || [...catalog.datasets].sort((a,b)=>String(b.created_at).localeCompare(String(a.created_at)))[0] || null;
  }
  function homeState(catalog, selectedId, jobs, connection){
    const copy=currentCopy(catalog,selectedId),alternative=catalog.datasets.find(v=>readyCopy(v)&&v.id!==copy?.id)||null;
    const context={copy,alternative};
    if(connection.phase==='loading')return {...context,kind:'loading'};
    if(connection.phase==='error')return {...context,kind:'error',reason:connection.error};
    if(connection.activityError)return {...context,kind:'error',reason:connection.activityError};
    if(!connection.activityKnown)return {...context,kind:'loading'};
    const active=jobs.find(j=>j.state==='running');
    if(active)return {...context,kind:'active',active};
    if(!copy)return {...context,kind:'empty'};
    if(blocked(copy.report)>0)return {...context,kind:'blocked'};
    return {...context,kind:readyCopy(copy)?'ready':'review'};
  }
  function groupIssues(issues){
    const photos=new Map();
    for(const issue of issues){
      if(!photos.has(issue.foto))photos.set(issue.foto,new Map());
      const drawings=photos.get(issue.foto),key=JSON.stringify([issue.job_id??null,issue.shape_id??null]);
      if(!drawings.has(key))drawings.set(key,{jobId:issue.job_id,shapeId:issue.shape_id,issues:[]});
      drawings.get(key).issues.push(issue);
    }
    return [...photos].sort(([a],[b])=>String(a).localeCompare(String(b),undefined,{numeric:true})).map(([photo,drawings])=>({photo,drawings:[...drawings.values()]}));
  }
  function issueCounts(issues){
    const groups=groupIssues(issues);
    return {observations:issues.length,photos:groups.length,drawings:groups.reduce((n,p)=>n+p.drawings.filter(d=>d.shapeId!=null).length,0)};
  }
  function reportGroups(report){
    return {
      blocks:report.incidencias.filter(i=>(i.bloquea_entrenamiento??i.bloquea_modulos)),
      attributes:report.incidencias.filter(i=>!(i.bloquea_entrenamiento??i.bloquea_modulos)&&i.categoria==='atributos'),
      levels:report.incidencias.filter(i=>!(i.bloquea_entrenamiento??i.bloquea_modulos)&&i.categoria!=='atributos')
    };
  }
  function issueAdvice(issue,context){
    const m=String(issue.problema||'Observación sin detalle');
    const advice={
      'modulo_id debe tener formato M1':issue.clase==='Modulo'||issue.bloquea_modulos?'Cuando completes los IDs, usa M1, M2… de izquierda a derecha en esta foto.':'Cuando completes los IDs, escribe en modulo_id el identificador del módulo padre, como M1.',
      'modulo_id repetido':'Dos módulos de esta foto comparten identificador. Revisa el orden de izquierda a derecha y asigna un identificador diferente a cada módulo.',
      'Integridad pendiente':'Decide si el encuadre corta algún límite: parcial si está cortado, completo si sus límites se identifican dentro de la foto. Si hay duda, explica la incertidumbre y acuerda el caso con el equipo.',
      'Puntos fuera del encuadre':'Mueve los puntos que quedan fuera de la foto para que sigan los límites visibles dentro del encuadre.',
      'Polígono de módulo duplicado':'Comprueba si se dibujó dos veces el mismo módulo. Conserva una sola anotación correcta para ese módulo.',
      'nivel_id inválido o repetido dentro del módulo':'Usa N1, N2… desde abajo hacia arriba dentro de su módulo. Cada nivel debe tener un identificador diferente dentro de ese módulo.',
      'Límite superior pendiente':'Comprueba si hay una repisa física que cierra el nivel: cerrado cuando es identificable, abierto cuando puedes establecer que no existe. Un corte u ocultación no demuestra que esté abierto; explica la duda y revisa con el equipo.',
      'Nivel sin módulo padre existente':'Comprueba que existe el módulo padre en esta foto y copia su modulo_id en el nivel.',
      'Foto sin módulos: revisa que el trabajo esté completo':'Revisa la foto completa y anota los módulos visibles siguiendo la guía, incluidos los tramos parciales.'
    };
    if(m.startsWith('Tarea 16'))return m;if(m.startsWith('Foto sin niveles'))return 'Marca todos los niveles de los tramos elegidos con la guía del trabajo. Guarda en CVAT y pulsa el botón para traer las anotaciones.';if(m.startsWith('Estado pendiente')){const p=profile(context);return p.id==='v2_base'?'Revisa el estado en CVAT con la guía v2. Esta etapa aprende reponer y suficiente; los casos no evaluables corresponden a la etapa de visibilidad. Guarda y trae una copia nueva.':p.id==='v2_visibilidad'?'Elige reponer, suficiente o no evaluable en CVAT con la guía v2. Guarda y trae una copia nueva.':'Elige vacío, baja disponibilidad, suficiente o no evaluable en CVAT siguiendo el criterio v1. Guarda y vuelve a traer la copia.';}if(m.startsWith('Sin ejemplos'))return 'Cambia las fotos de validación para conservar ejemplos de este estado en entrenamiento, o agrega escenas anotadas.';if(m==='Polígono de nivel duplicado')return 'Conserva un solo polígono por nivel físico y revisa su estado.';if(m.startsWith('Polígono inválido:'))return 'Revisa los puntos y los cruces del contorno. El dibujo debe seguir la estructura visible y formar un polígono válido; acuerda los límites dudosos con el equipo.';
    return advice[m==='modulo_id debe tener formato M01'?'modulo_id debe tener formato M1':m]||'Comprueba esta observación en CVAT con la guía v2. Si no está claro cómo resolverla, revisa el dibujo con otro integrante antes de traer una copia nueva.';
  }
  function defaultRun(catalog,scope){
    const candidates=catalog.runs.filter(r=>r.ready&&!technical(r.id)&&(!scope||(levelsCopy(r)?'Nivel_estados':'Modulo')===scope));
    const stamp=r=>r.id.match(/_(\d{8}_\d{6})_/)?.[1]||r.created_at||r.id;
    return [...candidates].sort((a,b)=>stamp(b).localeCompare(stamp(a)))[0]?.id||'';
  }
  function modelChoices(catalog,all=false){
    if(all)return catalog.models;
    const runs=new Map(catalog.runs.map(run=>[run.id,run])),byRun=new Map();
    for(const model of catalog.models){if(!model.run)continue;if(!runs.get(model.run)?.ready||technical(model.run))continue;if(!byRun.has(model.run))byRun.set(model.run,[]);byRun.get(model.run).push(model)}
    function family(runId,visited=new Set()){
      if(visited.has(runId))return 'run:'+runId;visited.add(runId);
      const source=runs.get(runId)?.config?.model;
      if(typeof source!=='string')return 'run:'+runId;
      const parent=source.match(/^Experimentos\/([^/]+)\/entrenamiento\/weights\/[^/]+$/);
      return parent?family(parent[1],visited):source;
    }
    const latest=new Map(),stamp=run=>run.id.match(/_(\d{8}_\d{6})_/)?.[1]||run.created_at||run.id;
    for(const [id,weights] of byRun){
      const run=runs.get(id),best=weights.find(model=>model.id.endsWith('/best.pt'));
      if(!best&&(catalog.archived_models||[]).some(model=>model.run===id&&model.id.endsWith('/best.pt')))continue;
      const model=best||weights.find(model=>model.id.endsWith('/last.pt'))||weights[0];
      const key=JSON.stringify([family(id),levelsCopy(run)?'Nivel_estados':'Modulo',profile(run).id]);
      if(!latest.has(key)||stamp(run)>stamp(runs.get(latest.get(key).run)))latest.set(key,model);
    }
    return [...latest.values(),...catalog.models.filter(model=>!model.run)];
  }
  function defaultModel(catalog, mode, scope){
    const project=catalog.models.filter(m=>m.run&&!technical(m.run)&&catalog.runs.some(r=>r.id===m.run&&r.ready));
    const matching=scope?project.filter(m=>{const r=catalog.runs.find(r=>r.id===m.run);return (levelsCopy(r)?'Nivel_estados':'Modulo')===scope}):project;
    if(scope)matching.sort((a,b)=>(b.run.match(/_(\d{8}_\d{6})_/)?.[1]||b.run).localeCompare(a.run.match(/_(\d{8}_\d{6})_/)?.[1]||a.run));
    const general=catalog.models.find(m=>!m.run),best=(!scope?matching.find(m=>m.run.startsWith('piloto_01_')&&m.id.endsWith('best.pt')):null)||matching.find(m=>m.id.endsWith('best.pt'))||matching[0];
    return (mode==='train'?general||best:best||general)?.id||'';
  }
  function resultDecision(run,subject='El modelo seleccionado'){
    if(!run?.ready)return {kind:'limited',title:'La evaluación todavía no está terminada.',detail:'Puedes seguir el aprendizaje. Los resultados de validación aparecerán al terminar la evaluación.'};
    if(technical(run.id))return {kind:'limited',title:'Este ensayo comprueba el funcionamiento del panel.',detail:'Es una prueba técnica; no la uses para decidir si el modelo mejoró.'};
    const v=run.development_evaluation?.metrics||run.availability?.val;
    if(levelsCopy(run)){
      if(!v)return {kind:'limited',title:'Todavía no hay métricas de alertas para esta versión.',detail:'La localización por sí sola no permite saber si reconoce los estados y detecta la falta de producto.'};
      const a=v.alertas;
      if(!a.reales)return {kind:'limited',title:'Esta evaluación no tiene niveles anotados que requieran reposición.',detail:`Se registraron ${a.falsas} falsas alertas. Sin referencias de reposición no podemos medir qué proporción de esos niveles reconoce el modelo.`};
      const missed=Math.max(0,a.reales-a.acertadas);
      return {kind:missed?'attention':'observed',title:`${subject} reconoció ${a.acertadas} de ${a.reales} niveles que requerían reposición.`,detail:`La referencia son las anotaciones revisadas${Number.isFinite(v.fotos)?' de '+v.fotos+' fotos':''}. Omitió ${missed} ${missed===1?'nivel que necesitaba reposición':'niveles que necesitaban reposición'}. Emitió ${a.falsas} ${a.falsas===1?'falsa alerta':'falsas alertas'}: señaló reposición sin coincidir con un caso anotado como tal.`};
    }
    const rows=(run.comparisons||[]).filter(c=>c.split==='val');
    if(!rows.length)return {kind:'limited',title:'No hay fotos de validación comparadas.',detail:'Elige otro ensayo evaluado o revisa si falta generar sus comparaciones.'};
    const found=rows.reduce((n,c)=>n+c.aciertos,0),total=rows.reduce((n,c)=>n+c.anotados,0);
    return {kind:'neutral',title:`${subject} localizó ${found} de ${total} módulos en validación.`,detail:'Este ensayo aprende módulos. No evalúa estados ni alertas de disponibilidad. Revisa también omisiones, detecciones extra y la forma de los contornos.'};
  }
  function comparable(a,b){return Boolean(a&&b&&a.id!==b.id&&a.ready&&b.ready&&typeof a.signature==='string'&&a.signature.length&&a.signature===b.signature&&profile(a).id===profile(b).id);}
  function evaluationContext(run){
    const count=run.development_evaluation?.metrics?.fotos??run.manifest.imagenes.filter(i=>i.split==='val').length;
    if(!run.ready)return `Este ensayo todavía no tiene una evaluación terminada. Se separaron ${count} ${count===1?'foto':'fotos'} para validación de desarrollo. Puedes seguir la curva mientras aprende.`;
    if(technical(run.id))return 'Este ensayo comprueba que el panel funciona. Su entrenamiento corto es una prueba técnica, no un candidato de mejora.';
    return `Esta versión se evaluó en ${count} ${count===1?'foto':'fotos'} de validación. ${count===1?'Una sola escena da una primera señal; falta evaluar más escenas.':'Estos resultados orientan las decisiones del proyecto.'} Los puntajes no equivalen a porcentaje de exactitud en la tienda.`;
  }
  function copiesByPerson(copies){
    const groups=new Map(),people={27:'Vicente',28:'Vilches',29:'Paulo'},accounts={'vi.canio':'Vicente','vi.vilches':'Vilches','pau.guera':'Paulo'};
    for(const copy of copies){
      const person=[...new Set(copy.sources.map(source=>people[source.job_id]||accounts[source.assignee?.username]||source.assignee?.username||'Trabajo '+source.job_id))].sort().join(' + ');
      const key=JSON.stringify([copy.scope||'Modulo',person,copy.sources.map(s=>s.job_id).sort((a,b)=>a-b)]);if(!groups.has(key))groups.set(key,[]);groups.get(key).push(copy);
    }
    return [...groups].sort(([a],[b])=>a.localeCompare(b)).map(([person,values])=>{
      values.sort((a,b)=>String(b.created_at).localeCompare(String(a.created_at)));
      return {person:JSON.parse(person)[1],latest:values[0],history:values.slice(1)};
    });
  }
  function copiesByLot(copies){
    const groups=new Map(),legacy=[];
    for(const copy of copies){
      const tasks=[...new Set(copy.sources.map(source=>source.task_id).filter(Boolean))].sort((a,b)=>a-b);
      if(!tasks.length){legacy.push(copy);continue}
      const key=JSON.stringify([copy.scope||'Modulo',tasks]);if(!groups.has(key))groups.set(key,[]);groups.get(key).push(copy);
    }
    return [...groups.values()].map(values=>{values.sort((a,b)=>String(b.created_at).localeCompare(String(a.created_at)));const latest=values[0],names=[...new Set(latest.sources.map(source=>source.task_name||'Tarea '+source.task_id))];return {person:names.join(' + '),latest,history:values.slice(1)}}).concat(copiesByPerson(legacy));
  }
  function trainingState(job, run, now=Date.now()){
    const history=(run?.history||[]).filter(row=>Number.isFinite(row.epoch)&&row.epoch>0), p=job?.progress||{};
    const latest=history.at(-1)||{}, completed=Math.max(0, ...history.map(r=>r.epoch), Number(p.completed_epochs)||0);
    const total=Number(job?.config?.epochs)||Number(p.total_epochs)||null;
    const terminal=['done','error','interrupted'].includes(job?.state);
    const stage=job?.state==='done'?'done':p.stage|| (history.length?'training':'unknown');
    const points=history.filter(row=>Number.isFinite(row['metrics/mAP50-95(M)']));
    const best=points.reduce((chosen,row)=>!chosen||row['metrics/mAP50-95(M)']>chosen['metrics/mAP50-95(M)']?row:chosen,null);
    const started=Date.parse(p.started_at||job?.started_at), ended=Date.parse(job?.finished_at||p.updated_at);
    const elapsed=Number.isFinite(started)?Math.max(0, ((terminal&&Number.isFinite(ended)?ended:now)-started)/1000):null;
    return {history,latest,completed,total,stage,best,elapsed,terminal,percent:total?Math.min(100,Math.round(completed/total*100)):null};
  }
  return {readyCopy,blocked,levelsCopy,profile,versionOf,versionCatalog,predictionImages,versionStatus,technical,currentCopy,homeState,groupIssues,issueCounts,reportGroups,issueAdvice,defaultRun,modelChoices,defaultModel,resultDecision,comparable,evaluationContext,copiesByPerson,copiesByLot,trainingState};
})();
