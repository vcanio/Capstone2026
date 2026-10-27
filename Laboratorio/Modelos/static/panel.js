const $=id=>document.getElementById(id);let data={runs:[],models:[],archived_models:[],images:[],datasets:[]},jobs=[],predictJob=null,seen=new Set(),busy=false,polling=false,pendingRun=null,currentView='version',glossaryReturn='version',glossaryFocus=null,helpPanel=null,helpButton=null,thumbnailKey='',activityKey='',monitorJob=null,reportVersion=null,importing=false,importSources=[],sourcesLoading=false;
let modelListBusy=false;
let fullCatalog=null,projectVersion='v2',versionContextKey='';
const connection={phase:'loading',error:'',activityKnown:false,activityError:''};
const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const fmt=value=>Number.isFinite(value)?value.toFixed(3):'—';

let uiPreferences;try{uiPreferences=UiPreferences.read(localStorage)}catch{uiPreferences=UiPreferences.sanitize(null)}
if(['v1','v2','v3','otros'].includes(uiPreferences.fields['project-version']))projectVersion=uiPreferences.fields['project-version'];
$('project-version').value=projectVersion;
const pendingChoices=new Set(UiPreferences.choices);
pendingChoices.delete('project-version');
const versionNames={v1:'V1',v2:'V2',v3:'V3',otros:'Piloto y otros ensayos'};
function scopedSources(){return importSources.filter(s=>Lab.versionOf(s)===projectVersion)}
function jobInVersion(job){
  if(!fullCatalog)return false;
  const c=job.config||{},item=fullCatalog.runs.find(r=>r.id===c.run||r.id===c.source)||fullCatalog.datasets.find(v=>v.id===c.source)||fullCatalog.models.find(m=>m.id===c.model);
  return Lab.versionOf(item,fullCatalog)===projectVersion;
}
function renderVersionContext(){
  if(!fullCatalog)return;
  const other=[...fullCatalog.runs,...fullCatalog.datasets].some(item=>Lab.versionOf(item,fullCatalog)==='otros');
  const versions=other||projectVersion==='otros'?['v2','v1','v3','otros']:['v2','v1','v3'];
  const key=JSON.stringify([projectVersion,connection.phase==='ready'&&!importing,connection.activityKnown,connection.activityError,versions,versions.map(id=>Lab.versionStatus(fullCatalog,id,jobs)),fullCatalog.datasets.map(v=>[v.id,v.created_at])]);
  renderWorkspace();if(key===versionContextKey)return;versionContextKey=key;
  $('project-version').value=projectVersion;$('workspace-version-name').textContent=versionNames[projectVersion];
  $('workspace-version').hidden=false;


  const cards=$('version-cards'),hadFocus=cards?.contains?.(document.activeElement);
  setHTML(cards,versions.map(id=>{const active=projectVersion===id,scoped=Lab.versionCatalog(fullCatalog,id),dates=[...scoped.datasets,...scoped.runs].map(i=>i.created_at).filter(Boolean).sort(),desc=id==='v3'?'Una clase Nivel. Exportación y entrenamiento desde el panel pendientes; ocupación y alertas requieren validaciones separadas.':id==='v1'?'Criterio original: vacío, baja disponibilidad, suficiente y no evaluable.':id==='v2'?'Etapa base: suficiente y reponer, además agrega la detección de bordes. La siguiente etapa incorpora no evaluable con el lote de visibilidad limitada.':'Laboratorio/Experimentos previos de módulos y ensayos con criterio sin registrar.';return `<button type="button" class="version-card" data-version="${id}" aria-pressed="${active}"${connection.phase!=='ready'||importing?' disabled':''}><div class="version-card-head"><strong class="version-card-title">${esc(versionNames[id])}</strong><span class="version-card-badge">${active?'Seleccionada':'Elegir'}</span></div><p class="version-card-desc">${esc(desc)}</p><div class="version-card-foot"><strong>${esc(connection.phase==='ready'&&connection.activityKnown&&!connection.activityError?Lab.versionStatus(fullCatalog,id,jobs):'Estado sin verificar · reintenta la consulta')}</strong>${dates.length?`<span>Primer registro: ${esc(localDate(dates[0]))}</span>`:''}</div></button>`}).join(''));
  if(hadFocus)cards.querySelector(`[data-version="${projectVersion}"]`)?.focus({preventScroll:true});
}
function selectProjectVersion(version){
  if(!fullCatalog||importing||!['v1','v2','v3','otros'].includes(version)||version===projectVersion)return;
  saveUiPreferences();projectVersion=version;$('project-version').value=version;
  for(const id of ['dataset-version','source','train-model','model','run','baseline','participant','import-project','monitor-job','archived-version']){pendingChoices.delete(id);$(id).value=''}
  $('reviewed').checked=false;$('import-task').value='';$('validation-ids').value='';
  monitorJob=null;pendingRun=null;activityKey='';reportVersion=null;
  data=Lab.versionCatalog(fullCatalog,version);resetPrediction();
  $('activity').textContent='Actualizando la actividad de esta versión…';
  $('message').style.display='none';for(const action of ['train','predict','import','review'])clearOperationError(action);
  renderScopedCatalog();renderOriginal();renderImportSources();selectImportSource(true);renderTraining();renderVersionContext();saveUiPreferences();poll();
}
let sourcesUpdated=uiPreferences.sourcesUpdated||'',preferenceTimer=null;
function restoreUiPreferences(){
  for(const id of [...UiPreferences.texts,...UiPreferences.numbers,...UiPreferences.selects]){
    const node=$(id),value=uiPreferences.fields[id];if(value===undefined)continue;
    if(node.tagName==='SELECT'){if([...node.options].some(o=>o.value===value))node.value=value}
    else if(UiPreferences.numbers.includes(id)){const n=Number(value);if(value.trim()&&Number.isFinite(n)&&n>=Number(node.min)&&n<=Number(node.max))node.value=value}
    else node.value=value.slice(0,node.maxLength>0?node.maxLength:1000);
  }
  for(const id of ['show-copy-history','show-model-history-predict','show-model-history-train'])$(id).checked=uiPreferences.fields[id]===true;
  for(const id of ['conf','nms'])$(id+'-value').textContent=Number($(id).value).toFixed(2);
  importSources=uiPreferences.sources;
  if(uiPreferences.fields.participant?.startsWith('job:')){const job=Number(uiPreferences.fields.participant.slice(4)),lot=importSources.find(source=>source.jobs.includes(job));uiPreferences.fields.participant=lot?.id||'custom'}
  if(importSources.length){renderImportSources();selectImportSource();$('import-sources-status').textContent='Tareas guardadas'+(sourcesUpdated?' · consultadas '+localDate(sourcesUpdated):'')+'. Pulsa Cargar proyectos y tareas de CVAT para consultar cambios.'}
  monitorJob=uiPreferences.fields['monitor-job']||null;
  // Open on step 0; keep the saved version and form choices as starting values.
}
function saveUiPreferences(){
  const fields={};for(const id of [...UiPreferences.choices,...UiPreferences.selects,...UiPreferences.numbers,...UiPreferences.texts])fields[id]=pendingChoices.has(id)&&uiPreferences.fields[id]!==undefined?uiPreferences.fields[id]:$(id).value;
  for(const id of ['show-copy-history','show-model-history-predict','show-model-history-train'])fields[id]=$(id).checked;
  uiPreferences={version:1,fields,sources:importSources,sourcesUpdated,view:currentView};
  try{UiPreferences.write(localStorage,uiPreferences)}catch{}
}
function schedulePreferences(){clearTimeout(preferenceTimer);preferenceTimer=setTimeout(saveUiPreferences,200)}

const glossary=[
['modulo','Anotaciones','Módulo','Un tramo de góndola entre sus soportes delimitadores. Los ensayos históricos localizan módulos; el trabajo actual se centra en niveles y estados.','Un cambio de marca dentro del mismo tramo no crea otro módulo.'],
['nivel','Anotaciones','Nivel','La apertura de exhibición sobre una repisa dentro de un módulo. Se anota también cuando está vacía.','N1 es el nivel inferior del módulo M1; los IDs son locales a cada foto.'],
['cvat','Anotaciones','CVAT','La herramienta donde dibujamos y revisamos módulos y niveles sobre las fotos. El laboratorio trae una copia de los cambios que guardaste allí.','Guardar en CVAT y luego traer las anotaciones permite preparar una versión nueva.'],
['job','Anotaciones','Trabajo de CVAT · job','Una porción de una tarea de anotación asignada a una persona. Su número permite identificarla.','En el piloto, el trabajo 27 es de Vicente, el 28 de Vilches y el 29 de Paulo.'],
['anotacion','Anotaciones','Anotación y etiqueta','Una anotación es el dibujo que marca un objeto en la foto. La etiqueta indica qué es: Modulo o Nivel. En niveles, el atributo estado indica vacío, baja disponibilidad, suficiente o no evaluable. Los IDs y observaciones ayudan a revisar.','Un polígono con etiqueta Modulo y modulo_id M1 describe el primer módulo de una foto.'],
['poligono','Anotaciones','Polígono y contorno','Un polígono es una figura delimitada por puntos unidos. El contorno es el borde de la región. Nuestros dibujos deben seguir los límites estructurales visibles.','Un contorno que se cruza a sí mismo requiere corrección antes de usarlo para aprender.'],
['mascara','Resultados','Máscara y segmentación','Una máscara marca los píxeles que pertenecen a un objeto. La segmentación predice una máscara por objeto; el panel muestra su contorno.','Un módulo puede estar encontrado, pero su máscara puede incluir parte de un módulo vecino.'],
['dataset','Datos','Conjunto de datos · dataset','Las fotos, sus anotaciones y la separación entre aprendizaje y validación que utilizamos en un ensayo.','En el piloto, cuatro fotos enseñan al modelo y una foto sirve para validación.'],
['version','Datos','Versión de datos y snapshot','Una copia guardada en un momento concreto, con fotos, dibujos, atributos y procedencia. Snapshot significa esa fotografía del estado de las anotaciones.','Si corriges un borde en CVAT, trae una copia nueva: una versión antigua conserva el borde anterior.'],
['escena','Datos','Escena','Un grupo de vistas relacionadas de una misma góndola. Las fotos del grupo deben permanecer juntas al separar entrenamiento y validación.','Dos fotos casi iguales de la misma góndola no son dos evaluaciones independientes.'],
['entrenamiento','Aprendizaje','Entrenamiento','El proceso en el que el modelo ajusta lo que sabe usando fotos y anotaciones de ejemplo. Al terminar obtenemos nuevos pesos.','Agregar escenas nuevas y revisadas cambia los ejemplos con los que aprende.'],
['validacion','Aprendizaje','Validación de desarrollo','Fotos separadas del aprendizaje directo que usamos para evaluar avances y elegir configuraciones o pesos. Es parte del desarrollo del modelo.','La foto 28 ya sirve para elegir y comparar versiones del piloto. No es nuestra prueba final independiente.'],
['reserva','Datos','Reserva de evaluación final','Escenas apartadas para medir el candidato elegido cuando terminemos de tomar decisiones. No se usan para ajustar el modelo ni sus filtros.','El laboratorio deja esas fotos fuera del selector de pruebas.'],
['modelo','Aprendizaje','Modelo','Un sistema que recibe una foto y produce detecciones. Su arquitectura define cómo funciona y sus pesos guardan lo aprendido.','Un modelo de niveles aprende a localizar cada nivel y clasificar su estado. El piloto histórico aprende módulos.'],
['preentrenado','Aprendizaje','Modelo preentrenado','Un modelo que ya aprendió a partir de otros datos. Podemos usarlo como punto de partida y entrenarlo con nuestras fotos y anotaciones, sean módulos o niveles con estado.','El YOLO general local reconoce sus clases originales. Primero hay que entrenarlo con las clases de la copia elegida; aún no reconoce nuestros niveles ni sus estados.'],
['pesos','Aprendizaje','Pesos y checkpoint','Los pesos son los valores que el modelo aprendió. Un checkpoint es un archivo que guarda una versión de esos valores, como best.pt o last.pt.','Elegir otro archivo de pesos cambia la versión del modelo que pruebas.'],
['best','Aprendizaje','Mejor versión · best / última · last','Best guarda los pesos elegidos por el criterio de validación del entrenamiento. Last guarda los del último paso completado.','Best y last pertenecen al mismo ensayo; no son dos arquitecturas distintas ni garantizan el mejor resultado en todas las fotos.'],
['epoca','Aprendizaje','Época','Una vuelta de aprendizaje por el conjunto de entrenamiento. Configuramos un máximo; el entrenamiento puede parar antes si no mejora.','El piloto tenía un máximo de 100 épocas y terminó después de 92.'],
['batch','Aprendizaje','Batch','Cuántas fotos se procesan juntas en cada paso de aprendizaje. Un lote mayor suele necesitar más memoria.','El piloto usa batch 2: procesa grupos de dos fotos.'],
['tasa','Aprendizaje','Tasa de aprendizaje','Controla el tamaño de los ajustes de los pesos durante el entrenamiento. Un valor mayor no significa automáticamente que aprenderá mejor.','El piloto parte de 0.001. Al comparar ese valor, conserva los otros ajustes.'],
['semilla','Aprendizaje','Semilla','Un número que configura parte del azar del entrenamiento. Ayuda a repetir un experimento bajo las mismas condiciones.','Usamos 42 como punto de partida. Misma semilla no garantiza resultados idénticos en cualquier equipo.'],
['resolucion','Pruebas','Resolución de entrada','El tamaño objetivo con el que se prepara la imagen para el modelo, conservando su proporción. Aumentarlo puede mostrar más detalle y requerir más recursos.','640 es la configuración del piloto. La foto original se conserva; no se reemplaza por una copia pequeña.'],
['prediccion','Pruebas','Predicción o inferencia','Usar un modelo ya entrenado para ver qué encuentra en una foto. Este paso no modifica sus pesos.','Ver qué encuentra ejecuta una predicción. Entrenar inicia un aprendizaje nuevo.'],
['confianza','Pruebas','Confianza y umbral','La confianza es el puntaje que el modelo asigna a una detección. El umbral es el mínimo que exigimos para mostrarla. No es un porcentaje de exactitud.','Con filtro 0.25 se descartan las detecciones con puntaje menor. Bajarlo puede recuperar detecciones y también dejar pasar más errores. No cambia lo que el modelo aprendió.'],
['nms','Pruebas','NMS · filtro de superposición','Un filtro que elimina detecciones redundantes muy superpuestas, conservando las de mayor confianza. El umbral regula qué superposición se permite.','Un umbral menor suele suprimir más detecciones superpuestas. Cambiarlo no vuelve a entrenar el modelo.'],
['iou','Resultados','IoU · coincidencia de áreas','El área compartida entre la anotación y la predicción, dividida por toda el área que ocupan entre ambas. Va de 0 a 1. Aquí se calcula sobre máscaras.','IoU 1 significa que las áreas coinciden. El laboratorio exige al menos 0.5 para contar una pareja; no es un criterio aprobado para medir ocupación.'],
['map','Resultados','mAP50 y mAP50–95','Medidas de detección que resumen precisión y cobertura. mAP50 exige IoU de al menos 0.50; mAP50–95 promedia exigencias de 0.50 a 0.95. Aquí usamos máscaras.','El 0.807 del piloto es una medida en su validación. No significa que el modelo tenga 80.7% de exactitud en toda la tienda.'],
['errores','Resultados','Encontrados, omitidos y extras','Encontrados son los objetos emparejados con una anotación: niveles o módulos según el ensayo. Omitidos son anotaciones sin pareja. Extras son detecciones sin pareja.','Si hay tres niveles anotados, dos encontrados y una detección extra, todavía faltó encontrar uno. Localizarlo tampoco garantiza acertar su estado.'],
['perdida','Resultados','Pérdida · loss','La medida de error que utiliza el aprendizaje para ajustar los pesos. Una pérdida menor suele ser mejor dentro de un ensayo comparable.','La curva de error ayuda a ver el aprendizaje; no reemplaza revisar objetos omitidos, estados equivocados y límites incorrectos.'],
['sobreajuste','Resultados','Sobreajuste','Cuando el modelo se adapta a los ejemplos de aprendizaje pero funciona peor en escenas diferentes.','Si mejora mucho al aprender y no mejora en validación, hay que investigar un posible sobreajuste.'],
['gpu','Aprendizaje','GPU · tarjeta gráfica','La parte del computador que acelera estos cálculos. El laboratorio ejecuta un trabajo de modelo a la vez.','Durante un entrenamiento puedes explorar el historial y leer el glosario mientras esperas.']
];
const localDate=value=>value&&!Number.isNaN(new Date(value).getTime())?new Date(value).toLocaleString('es-CL',{timeZone:'America/Santiago',day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit',second:'2-digit'}):'fecha no registrada';
const renderedHTML=new WeakMap();
const setHTML=(node,html)=>{if(renderedHTML.get(node)!==html){ImageNavigation.release(node);node.innerHTML=html;renderedHTML.set(node,html)}};
function copyOrigin(v){const tasks=[...new Set(v.sources.map(s=>s.task_id).filter(Boolean))];return `${[...new Set(v.sources.map(source=>source.task_name).filter(Boolean))].join(' / ')}; ${tasks.length?'tarea '+tasks.join(', ')+'; ':''}${v.sources.map(s=>({'vi.canio':'Vicente','vi.vilches':'Vilches','pau.guera':'Paulo'}[s.assignee?.username]||({27:'Vicente',28:'Vilches',29:'Paulo'}[s.job_id])||'Trabajo '+s.job_id)).join(' + ')}; trabajos ${v.sources.map(s=>s.job_id).join(', ')}; guardada ${localDate(v.created_at)}`;}
function copyStatus(v){return Lab.blocked(v.report)>0?`${Lab.blocked(v.report)} observaciones de ${Lab.levelsCopy(v)?'niveles y estados':'módulos'} por corregir`:Lab.readyCopy(v)?'Anotaciones revisadas; copia lista para entrenar':'Sin bloqueos técnicos; falta revisión visual'}
function runName(id){if(id.startsWith('piloto_01_'))return 'Piloto · módulos de Vicente';if(id.startsWith('verificacion_panel'))return 'Prueba técnica del panel';const stamp=id.match(/_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})_[a-f0-9]{4}$/),name=id.replace(/_\d{8}_\d{6}_[a-f0-9]{4}$/,'').replaceAll('_',' ');return stamp?name+' · '+localDate(`${stamp[1]}-${stamp[2]}-${stamp[3]}T${stamp[4]}:${stamp[5]}:${stamp[6]}Z`):name}
function shortRunName(id){return id.startsWith('piloto_01_')?'Piloto histórico · módulos':id.startsWith('verificacion_panel')?'Prueba técnica':id.replace(/_\d{8}_\d{6}_[a-f0-9]{4}$/,'').replaceAll('_',' ')}
function datasetName(v){const lot=Lab.copiesByLot([v])[0].person.split(' - ')[0],date=v.created_at?new Date(v.created_at).toLocaleDateString('es-CL',{timeZone:'America/Santiago',day:'2-digit',month:'short'}):'sin fecha',photos=v.report?.imagenes?.length;return `${lot} · ${date} · ${Lab.readyCopy(v)?'revisada':'por revisar'}`}
function lotCopyStatus(v){const completed=v.cvat_status?.completed_jobs??v.sources.filter(source=>source.state==='completed').length,excluded=v.sources.reduce((total,source)=>total+(source.excluded_frames?.length||0),0);return `<p class="field-help">Última consulta de CVAT: ${esc(localDate(v.cvat_status?.checked_at))} · ${completed}/${v.sources.length} trabajos completados · ${v.report.imagenes.length} fotos${excluded?' · '+excluded+' excluidas en CVAT':''}.</p>`}

function modelProfile(m){return Lab.profile(data.runs.find(run=>run.id===m?.run)||m)}
function profileDescription(item){const p=Lab.profile(item);return p.label+(p.states.length?' · '+p.states.map(key=>PredictionDemo.states.find(s=>s.key===key)?.label||key).join(' / '):'')}
function modelName(m,detail=false){return m.run?`${detail?(m.id.endsWith('best.pt')?'Mejor (best) · ':'Última (last) · '):''}${shortRunName(m.run)} · ${modelProfile(m).label}`:`${m.name.split(' · ')[0]} · modelo general`}
function predictionScope(){const copy=Lab.currentCopy(data,$('dataset-version').value);return copy?(Lab.levelsCopy(copy)?'Nivel_estados':'Modulo'):undefined}
function normalizeTerm(value){return value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'')}
function renderGlossary(){const q=normalizeTerm($('glossary-search').value.trim()),category=$('glossary-category').value;const matches=glossary.filter(t=>(!category||t[1]===category)&&normalizeTerm(t.join(' ')).includes(q));$('glossary-count').textContent=matches.length?`${matches.length} ${matches.length===1?'término':'términos'} ${q?(matches.length===1?'encontrado':'encontrados'):'para explorar'}`:'No encontramos coincidencias. Prueba otra palabra o pulsa Limpiar filtros.';$('glossary-list').innerHTML=matches.map(([id,group,title,meaning,example])=>`<details class="glossary-entry" id="term-${id}" ${q&&matches.length<=3?'open':''}><summary>${esc(title)}</summary><p>${esc(meaning)}</p><p class="example">${esc(example)}</p></details>`).join('')}
function openTerm(id,button){
  const term=glossary.find(t=>t[0]===id);if(!term)return;
  if(helpButton===button){closeHelp();return}closeHelp(false);
  helpButton=button;helpPanel=document.createElement('div');helpPanel.className='context-help';helpPanel.id='context-help';helpPanel.setAttribute('role','region');helpPanel.setAttribute('aria-labelledby','context-help-title');
  helpPanel.innerHTML=`<h3 id="context-help-title">${esc(term[2])}</h3><p>${esc(term[3])}</p><details class="secondary-section"><summary>Ejemplo</summary><p>${esc(term[4])}</p></details><div class="help-actions"><button type="button" class="text-button" data-full-term="${esc(id)}">Ver en el glosario</button><button type="button" class="secondary" data-close-help>Cerrar</button></div>`;
  (button.closest('.field')||button.closest('h2')||button).after(helpPanel);
  button.setAttribute('aria-expanded','true');button.setAttribute('aria-controls','context-help');helpPanel.querySelector('[data-close-help]').focus({preventScroll:true});
}
function closeHelp(restore=true){const opener=helpButton;helpPanel?.remove();if(opener){opener.setAttribute('aria-expanded','false');opener.removeAttribute('aria-controls')}helpPanel=null;helpButton=null;if(restore&&opener?.isConnected)opener.focus({preventScroll:true})}
function showGlossaryTerm(id){const term=glossary.find(t=>t[0]===id);if(!term)return;glossaryFocus=helpButton;glossaryReturn=currentView;$('glossary-category').value='';$('glossary-search').value=term[2];switchTab('glossary');$('glossary-search').focus()}

function renderConnectionStatus(){
  const node=$('catalog-error');
  node.hidden=connection.phase!=='error';
  if(node.hidden)return;
  setHTML(node,`<p>No pudimos consultar el panel. ${esc(connection.error)}</p><button type="button" class="text-button" data-retry>Reintentar</button>`);
}
function updateAvailability(){
  renderWorkspace();const ready=connection.phase==='ready';
  $('analysis-method').disabled=!ready||busy;
  $('project-version').disabled=!ready||importing;document.querySelectorAll('.version-card').forEach(b=>b.disabled=!ready||importing);
  $('version-continue').disabled=!ready||importing||projectVersion==='v3';
  $('analyze-photo').textContent=uploadingPhoto?'Preparando foto…':predictJob&&jobs.some(j=>j.id===predictJob&&j.state==='running')?'Analizando…':'Analizar foto';
  for(const id of ['predict-form','import-form','review-form','train-form'])$(id+'-fields').disabled=!ready||projectVersion==='v3';
  for(const id of ['run','baseline','model','image','source','dataset-version','train-model'])$(id).disabled=!ready||!$(id).options.length||[...$(id).options].every(o=>!o.value);
  document.querySelector('#predict-form button.primary').disabled=!ready||!connection.activityKnown||busy||uploadingPhoto||!$('model').value||!currentPredictionImage();
  document.querySelector('#train-form button.primary').disabled=!ready||!connection.activityKnown||busy||!$('source').value||!$('train-model').value;
  $('import-form-fields').disabled=!ready||importing||projectVersion==='v3';
  for(const id of ['import-project','participant','import-task'])$(id).disabled=sourcesLoading;
  $('import-button').disabled=!ready||importing||sourcesLoading||projectVersion==='v3';
  const v=data.datasets.find(v=>v.id===$('dataset-version').value);
  $('archive-copy').disabled=!ready||importing||archiving||!v||Boolean(v.archive_uses?.length);
  $('restore-copy').disabled=!ready||archiving||!$('archived-version').value;
  $('review-button').disabled=!ready||!v||v.state!=='pendiente_revision'||Lab.blocked(v.report)>0;
  for(const mode of ['predict','train']){
    const model=data.models.find(m=>m.id===$(mode==='predict'?'model':'train-model').value);
    const inUse=model&&jobs.some(j=>j.state==='running'&&(j.config?.model===model.id||j.config?.run===model.run));
    $('archive-model-'+mode).disabled=!ready||!connection.activityKnown||modelListBusy||!model?.run||Boolean(inUse);
    $('restore-model-'+mode).disabled=!ready||modelListBusy||!$('archived-model-'+mode).value;
    $('archived-model-'+mode).disabled=!ready||modelListBusy;
    $('model-list-hint-'+mode).textContent=!model?'Elige un modelo para organizar la lista.':!model.run?'Los modelos generales se conservan como punto de partida.':inUse?'Disponible cuando termine el trabajo en curso.':'Conserva los pesos y resultados.';
  }
}

function workspaceStatus(){return Lab.workspaceState(data,$('dataset-version').value,$('run').value,jobs.filter(jobInVersion),connection,projectVersion)}
function renderWorkspace(){
  const state=workspaceStatus(),copy=state.copy,run=state.run;
  $('next-title').textContent=state.title;
  const reasons={blocked:`Copia ${copy?.id}: resuelve las incidencias antes de aprobarla.`,review:`Copia ${copy?.id}: comprueba las fotos y registra quién las revisó.`,ready:`Copia ${copy?.id}: está aprobada y permite configurar un nuevo ensayo.`,results:`Ensayo ${run?.id}: la evaluación permite revisar sus errores.`,active:`Ensayo ${state.job?.config.run}: ${state.trialState}.`};
  $('next-reason').textContent=reasons[state.kind]||state.reason||'';
  const label=copy?datasetName(copy):'Sin copia seleccionada';
  $('work-context').textContent=`${versionNames[projectVersion]} / ${label}${run?' / ensayo '+shortRunName(run.id):''}`;
  setHTML($('work-states'),[['Datos',state.dataState],['Ensayo',state.trialState],['Evaluación',state.evaluation],['Ocupación y alertas',state.occupancy]].map(([k,v])=>`<div><dt>${esc(k)}</dt><dd>${esc(['loading','error'].includes(state.kind)?'sin verificar':v)}</dd></div>`).join(''));
  const button=$('next-action');button.textContent=state.action;button.disabled=state.kind==='loading'||importing;
  button.dataset.contextAction=state.target==='train'?(state.kind==='active'||state.kind==='failed'?'monitor':'trainCopy'):state.target;
  button.dataset.objectId=state.target==='train'?(state.job&&['active','failed'].includes(state.kind)?state.job.id:copy?.id||''):state.target==='results'?run?.id||'':copy?.id||'';
  setHTML($('work-alternatives'),state.model?`<button type="button" class="text-button" data-context-action="predict" data-object-id="${esc(state.model.id)}">Probar ${esc(shortRunName(state.model.run))}</button>${state.target!=='results'?` <button type="button" class="text-button" data-context-action="results" data-object-id="${esc(state.model.run)}">Ver sus resultados</button>`:''}`:'');
  $('state-checked').textContent=state.kind==='error'?'La información anterior requiere una nueva consulta.':state.kind==='loading'?'Esperando catálogo y actividad del servidor.':`Estado consultado: ${connection.checkedAt?localDate(connection.checkedAt):'ahora'}. CVAT se consulta manualmente.`;
  $('v3-dependencies').hidden=projectVersion!=='v3';
  $('version-continue').hidden=projectVersion==='v3';
  const screenRun=currentView==='results'?selectedRun():currentView==='predict'?data.runs.find(r=>r.id===data.models.find(m=>m.id===$('model').value)?.run):null;
  const trainingSource=currentView==='train'?(data.datasets.find(v=>v.id===$('source').value)||data.runs.find(r=>r.id===$('source').value)):null;
  const context=$('active-context');context.hidden=currentView==='version'||currentView==='glossary';
  context.textContent=`${versionNames[projectVersion]} / ${screenRun?shortRunName(screenRun.id)+' / '+(currentView==='predict'?$('model').value:'ensayo '+screenRun.id):label}`;
  if(trainingSource)context.textContent=`${versionNames[projectVersion]} / ${trainingSource.report?datasetName(trainingSource):shortRunName(trainingSource.id)} / datos ${trainingSource.id}`;
  if(projectVersion==='v3'&&!context.hidden)context.textContent+=' · Flujo pendiente de integración. Consulta las dependencias en el inicio.';
  const statuses={datasets:state.dataState,train:state.trialState,results:state.evaluation,predict:state.model?'modelo disponible':'sin modelo entrenado'};
  for(const [id,text] of Object.entries(statuses)){
    const nav=document.querySelector(`nav [data-tab="${id}"] .nav-label`);if(!nav)continue;
    let status=nav.querySelector('.nav-status');if(!status){status=document.createElement('small');status.className='nav-status';nav.append(status)}
    const label=['loading','error'].includes(state.kind)?'Sin verificar':projectVersion==='v3'?'Integración pendiente':text;
    const path=['aprobados','terminado','disponible','modelo disponible'].includes(label)?'m7 12 3 3 7-7':label==='requieren corrección'||label==='Sin verificar'?'M12 7v6m0 3v1':label==='entrenando'||label==='evaluando'||label==='preparando'?'m10 8 6 4-6 4Z':'M12 7v5l3 2';
    setHTML(status,`<svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="${path}"/></svg><span>${esc(label)}</span>`);
  }
}
function contextAction(action,id){
  if(action==='retry'){retryQueries();return}
  if(action==='v3'){switchTab('version');$('v3-dependencies').scrollIntoView({block:'center'});const heading=$('v3-dependencies').querySelector('h3');heading.tabIndex=-1;heading.focus({preventScroll:true});return}
  if(action==='datasets'){if(id&&!data.datasets.some(v=>v.id===id)){error('La copia ya no está disponible. Reintenta la consulta.');return}if(id)selectCopy(id);switchTab('datasets');$('module-issues')?.setAttribute('open','');}
  if(action==='trainCopy'){
    const copy=data.datasets.find(v=>v.id===id);if(!copy||!Lab.readyCopy(copy)||Lab.blocked(copy.report)){error('Esta copia no está disponible o requiere revisión antes de entrenar.','train');return}
    pendingChoices.delete('source');$('source').value=id;if($('source').value!==id){error('La copia no está disponible en los datos de entrenamiento.');return}sourceSummary();switchTab('train');
  }
  if(action==='results'){
    if(!data.runs.some(r=>r.id===id)){error('Este ensayo ya no está disponible en la versión activa.');return}
    pendingChoices.delete('run');$('run').value=id;switchTab('results');
  }
  if(action==='predict'){
    const model=data.models.find(m=>m.id===id);if(!model?.run){error('Estos pesos ya no están disponibles. Revisa los modelos quitados de la lista.');return}
    $('show-model-history-predict').checked=true;pendingChoices.delete('model');renderModelOptions('predict');$('model').value=id;
    if($('model').value!==id){error('No se pudieron seleccionar estos pesos. Reintenta la consulta.');return}
    $('predict-size').value=String(model.imgsz||640);resetPrediction();renderOriginal();modelHelp();switchTab('predict');
  }
  if(action==='monitor'){const job=jobs.find(j=>j.id===id&&jobInVersion(j));if(!job){error('El trabajo ya no está disponible. Reintenta la consulta.');return}monitorJob=id;switchTab('train');$('training-monitor').open=true;}
  renderWorkspace();saveUiPreferences();
}
function renderReviewReceipt(copy){
  const approved=Boolean(copy&&Lab.readyCopy(copy)&&!Lab.blocked(copy.report));$('review-form').hidden=approved;$('review-receipt').hidden=!approved;
  if(!approved)return;
  setHTML($('review-receipt'),`<h2>Revisión terminada</h2><p><strong>${esc(datasetName(copy))}</strong></p><dl><dt>Copia</dt><dd>${esc(copy.id)}</dd><dt>Persona</dt><dd>${esc(copy.review?.reviewer||'Sin registrar')}</dd><dt>Fecha</dt><dd>${esc(localDate(copy.review?.date))}</dd><dt>Alcance</dt><dd>${esc(copy.review?.scope||copy.scope||'Módulos')}. Esta revisión corresponde únicamente a esta copia.</dd></dl><button type="button" class="primary" data-context-action="trainCopy" data-object-id="${esc(copy.id)}">Configurar entrenamiento con esta copia</button><p class="field-help">El historial y la procedencia están en el detalle de la copia.</p>`);
}
function renderTrainingPreview(){
  const copy=data.datasets.find(v=>v.id===$('source').value),source=copy||data.runs.find(r=>r.id===$('source').value),reference=selectedBaseline()||selectedRun();
  const photos=(source?.report||source?.manifest)?.imagenes||[],model=data.models.find(m=>m.id===$('train-model').value);
  const changes=reference?['source','model','epochs','batch','imgsz','lr','seed'].filter(key=>String(reference.config?.[key]??'')!==String(({source:source?.id,model:model?.id,epochs:$('epochs').value,batch:$('batch').value,imgsz:$('train-size').value,lr:$('lr').value,seed:$('seed').value})[key])).map(k=>({source:'datos',model:'modelo de partida',epochs:'épocas',batch:'batch',imgsz:'resolución',lr:'tasa',seed:'semilla'})[k]):[];
  $('training-preview').textContent=source?`${profileDescription(source)} / ${source.id}. ${copy?'Copia aprobada':'Snapshot del ensayo'}. Partición: ${photos.filter(i=>i.split==='train').length} entrenamiento y ${photos.filter(i=>i.split==='val').length} validación. Partida: ${model?.id||'pendiente'}. ${reference?'Referencia: '+reference.id+'. Cambios de configuración: '+(changes.join(', ')||'ninguno')+'. Los valores ausentes en la referencia requieren revisión.':'Sin ensayo de referencia seleccionado.'}`:'Falta una copia revisada para configurar el ensayo.';
}
let renderedDecisionRun=null;
function renderResultActions(run){
  const model=data.models.find(m=>m.run===run?.id&&m.id.endsWith('/best.pt'))||data.models.find(m=>m.run===run?.id);
  setHTML($('result-model-action'),(run?.config?.purpose?`<p class="field-help">Propósito registrado: ${esc(run.config.purpose)}</p>`:'')+(model?`<button type="button" class="secondary" data-context-action="predict" data-object-id="${esc(model.id)}">Probar este modelo</button><span class="field-help">Pesos: ${esc(model.id)}</span>`:run?'<p class="field-help">No hay pesos visibles para este ensayo. Revisa los modelos quitados de la lista.</p>':''));
  if(renderedDecisionRun!==run?.id){renderedDecisionRun=run?.id;const d=run?.decision;$('decision-status').value=d?.status||'seguir_ajustando';$('decision-reason').value=d?.reason||'';$('decision-author').value=d?.author||'';$('decision-feedback').textContent='';}
  const decision=run?.decision;$('saved-decision').textContent=decision?`${({candidato:'Candidato',seguir_ajustando:'Seguir ajustando',descartado:'Descartado'})[decision.status]} · ${decision.author} · ${localDate(decision.date)}. ${decision.reason}`:'Sin decisión registrada. Este registro no certifica validación ni modifica umbrales.';
}
function modelHelp(){
  for(const [id,help,mode] of [['model','model-help','predict'],['train-model','train-model-help','train']]){
    const m=data.models.find(m=>m.id===$(id).value);
    $(help).textContent=!m?(mode==='predict'?'Esta versión todavía no tiene un modelo entrenado disponible. Entrena con sus datos preparados y vuelve aquí para probar una foto.':'Selecciona un modelo.'):Lab.technical(m.run)?'Prueba técnica del panel; no es un candidato de mejora.':!m.run?(mode==='train'?'Modelo general: aprenderá las clases de tus anotaciones.':'Modelo general: todavía no reconoce las clases del proyecto.'):mode==='train'?'Continúa desde los pesos de '+shortRunName(m.run)+'.':shortRunName(m.run)+' · '+(m.id.endsWith('best.pt')?'pesos elegidos por validación.':'pesos de la última época.');
    const target=data.datasets.find(v=>v.id===$('source').value)||data.runs.find(r=>r.id===$('source').value);
    const context=mode==='train'?target:data.runs.find(r=>r.id===m?.run)||m;
    if(m&&context&&Lab.profile(context).states.length)$(help).textContent+=' '+(mode==='train'?'Este ensayo aprenderá: ':'Salidas del modelo: ')+profileDescription(context)+'.';
  }
  const selected=data.models.find(m=>m.id===$('model').value),profile=modelProfile(selected),legend=document.querySelector('.demo-legend');
  const combined=profile.id.startsWith('v2');$('analysis-method-field').hidden=!combined;
  if(!combined)$('analysis-method').value='yolo';
  $('analysis-method-help').textContent=PredictionDemo.methodHelp($('analysis-method').value);
  legend.innerHTML=profile.states.map(key=>{const state=PredictionDemo.states.find(s=>s.key===key);return state?`<span><i style="--state-color:${state.color}"></i>${esc(state.label)}</span>`:''}).join('');
  legend.hidden=!profile.states.length||Boolean(predictJob);
  updateAvailability();
}
function renderModelOptions(mode){
  const all=$('show-model-history-'+mode).checked,models=Lab.modelChoices(data,all).filter(m=>mode==='train'||m.run),id=mode==='predict'?'model':'train-model';
  const preferred=Lab.defaultModel({...data,models},mode,mode==='predict'?predictionScope():undefined);
  const choices=models.map(model=>({...model,name:modelName(model,all),group:Lab.technical(model.run)?'Pruebas técnicas':model.run?modelProfile(model).label:'Modelos generales'})).sort((a,b)=>Number(Lab.technical(a.run))-Number(Lab.technical(b.run))||(mode==='train'?Number(Boolean(a.run))-Number(Boolean(b.run)):Number(!a.run)-Number(!b.run)));
  const previous=pendingChoices.has(id)?uiPreferences.fields[id]:$(id).value,previousRun=data.models.find(model=>model.id===previous)?.run;
  const sameRun=!all&&previousRun?models.find(model=>model.run===previousRun):null;
  options(id,choices,false,sameRun?.id||preferred);
}
function renderModelLists(){
  const archived=data.archived_models||[];
  for(const mode of ['predict','train']){
    options('archived-model-'+mode,archived.map(m=>({...m,name:modelName(m,true),group:shortRunName(m.run)})),false);
    $('archived-models-'+mode).hidden=!archived.length;
    $('archived-models-title-'+mode).textContent=`Modelos quitados (${archived.length}) · recuperar`;
  }
}
async function manageModel(action,mode,id){
  if(modelListBusy)return;
  id=id||(action==='archive'?$(mode==='predict'?'model':'train-model').value:$('archived-model-'+mode).value);
  if(!id)return;
  const status=$('model-list-status-'+mode),previousPrediction=$('model').value;
  modelListBusy=true;updateAvailability();status.textContent=action==='archive'?'Quitando el modelo de la lista…':'Recuperando el modelo…';
  try{
    await api('/api/models/'+action,{id});await refresh();
    if(connection.phase!=='ready')throw Error('La acción se guardó, pero falta actualizar la lista. Reintenta la consulta.');
    if(action==='restore'){$('show-model-history-'+mode).checked=true;renderModelOptions(mode);$(mode==='predict'?'model':'train-model').value=id;saveUiPreferences()}
    if(previousPrediction!==$('model').value)renderOriginal();
    modelHelp();
    if(action==='archive')status.innerHTML=`Modelo quitado de la lista. <button type="button" class="text-button" data-undo-model="${esc(id)}" data-model-mode="${mode}">Deshacer</button>`;
    else status.textContent='Modelo recuperado. Ya está disponible en Probar una foto y Entrenar.';
    if(action==='archive')$(mode==='predict'?'model':'train-model').focus({preventScroll:true});
    else $('archived-models-'+mode).open=false;
  }catch(err){status.textContent='No se pudo actualizar la lista. '+err.message;error(err.message,mode)}
  finally{modelListBusy=false;updateAvailability()}
}
for(const mode of ['predict','train']){
  $('show-model-history-'+mode).addEventListener('change',()=>{const previous=$('model').value;renderModelOptions(mode);if(mode==='predict'&&previous!==$('model').value)renderOriginal();modelHelp();saveUiPreferences()});
  $('archive-model-'+mode).addEventListener('click',()=>manageModel('archive',mode));
  $('restore-model-'+mode).addEventListener('click',()=>manageModel('restore',mode));
  $('archived-model-'+mode).addEventListener('change',updateAvailability);
}
let catalogResponse=null;
async function api(path,config){
  const conditional=!config&&path==='/api/catalog';
  const options=config?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(config)}:{signal:AbortSignal.timeout(path==='/api/datasets/sources'?30000:15000)};
  if(conditional){options.cache='no-store';if(catalogResponse?.etag)options.headers={'If-None-Match':catalogResponse.etag}}
  const response=await fetch(path,options);
  if(conditional&&response.status===304&&catalogResponse)return catalogResponse.value;
  const value=await response.json();
  if(!response.ok)throw Error(value.error||'No se pudo completar la solicitud.');
  if(conditional)catalogResponse={etag:response.headers.get('ETag'),value};
  return value;
}
function clearOperationError(operation){const node=$(operation+'-error');if(node){node.hidden=true;node.textContent=''}}
function error(message,operation){$('message').textContent=message;$('message').style.display='block';const node=operation&&$(operation+'-error');if(node){node.hidden=false;node.innerHTML=`<p><strong>No se pudo completar la acción.</strong> ${esc(message)}</p><p>Tus selecciones se conservan. Corrige lo indicado y vuelve a intentar.</p>`;node.focus();node.scrollIntoView({block:'center',behavior:'instant'})}}

function options(id,items,blank=false,preferred){
  const node=$(id),old=pendingChoices.has(id)&&uiPreferences.fields[id]!==undefined?uiPreferences.fields[id]:node.value,groups=new Map();pendingChoices.delete(id);
  for(const item of items){const key=item.group||'';if(!groups.has(key))groups.set(key,[]);groups.get(key).push(item)}
  const placeholder=blank?'Sin comparación':items.length?'Selecciona una opción':'Sin opciones disponibles';
  const names=new Map();for(const item of items)names.set(item.name,(names.get(item.name)||0)+1);
  const label=item=>{if(names.get(item.name)<2)return item.name||item.id;const stamp=(item.run||item.id).match(/_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})_/);const date=item.created_at||(stamp?`${stamp[1]}-${stamp[2]}-${stamp[3]}T${stamp[4]}:${stamp[5]}:${stamp[6]}Z`:null);return `${item.name} · ${date?localDate(date):item.id}`};
  setHTML(node,`<option value=""${!blank&&items.length?' disabled':''}>${placeholder}</option>`+[...groups].map(([group,values])=>{const html=values.map(item=>`<option value="${esc(item.id)}">${esc(label(item))}</option>`).join('');return group?`<optgroup label="${esc(group)}">${html}</optgroup>`:html}).join(''));
  node.value=items.some(i=>i.id===old)?old:blank?'':preferred!==undefined?(items.some(i=>i.id===preferred)?preferred:''):(items[0]?.id||'');
}
function renderCopyOptions(preferred){
  const groups=Lab.copiesByLot(data.datasets),show=$('show-copy-history').checked;
  const selected=preferred||$('dataset-version').value||(pendingChoices.has('dataset-version')?uiPreferences.fields['dataset-version']:'');
  const items=groups.flatMap(group=>[group.latest,...(show?group.history:group.history.filter(v=>v.id===selected))].map(copy=>({...copy,group:group.person,name:`${copy.id===group.latest.id?'Más reciente':'Anterior'} · ${datasetName(copy)}`})));
  options('dataset-version',items,false,preferred||Lab.currentCopy(data,null)?.id||'');
  $('copy-list-help').textContent=show?'Copias agrupadas por lote, de la más reciente a la más antigua.':'Por defecto se muestra la copia más reciente de cada lote.';
}
function renderImportSources(preferred){
  const projects=new Map();
  for(const source of scopedSources()){
    const id=String(source.project_id),project=projects.get(id)||{id,name:source.project_name||'Proyecto '+id,count:0};
    project.count++;projects.set(id,project);
  }
  const selected=scopedSources().find(s=>s.id===(pendingChoices.has('participant')?uiPreferences.fields.participant:$('participant').value))||scopedSources().find(s=>s.id===preferred);
  options('import-project',[{id:'all',name:'Todos los proyectos compatibles'},...[...projects.values()].map(p=>({id:p.id,name:`${p.name} · ${p.count} ${p.count===1?'tarea':'tareas'}`}))],false,selected?String(selected.project_id):'all');
  const project=$('import-project').value;
  const items=scopedSources().filter(s=>project==='all'||String(s.project_id)===project);
  options('participant',[...items.map(s=>({...s,name:`Tarea ${s.task_id} · ${s.name}`,group:project==='all'?(s.project_name||'Proyecto '+s.project_id):''})),{id:'custom',name:'Otra tarea · introducir número'}],false,preferred);
}
function updateImportLabel(){
  const source=importSources.find(item=>item.id===$('participant').value);
  if(!importing)$('import-button').textContent='Traer anotaciones del lote';
  const excluded=source?.excluded_image_ids?.length||0;
  $('import-source-help').textContent=source?`${source.jobs.length} trabajos reunidos · ${source.image_ids.length} fotos${excluded?' · '+excluded+' excluidas en CVAT':''}${source.completed_jobs!=null?' · '+source.completed_jobs+'/'+source.jobs.length+' trabajos completados':''}.${source.pending_partition?' '+source.validation_note:''}`:'Elige un lote de CVAT o indica su número de tarea.';
}
function selectImportSource(changed=false){
  const source=importSources.find(item=>item.id===$('participant').value);
  $('custom-task').hidden=Boolean(source);
  if(changed&&!source)$('import-task').value='';
  if(source){
    $('import-task').value=source.task_id||Number(source.id.slice(5));
    const validation=$('validation-ids').value.split(',').map(v=>v.trim()).filter(Boolean);
    if(source.fixed_validation){
      $('validation-ids').value=source.validation_ids.join(', ');
    }else if(changed&&(!validation.length||validation.some(id=>!source.image_ids.includes(id)))){
      $('validation-ids').value=source.scope==='Nivel_estados'&&['04','22','29'].every(i=>source.image_ids.includes(i))?'04, 22, 29':source.image_ids.includes('28')?'28':'';
      if(!$('validation-ids').value)$('validation-ids').closest('details').open=true;
    }
  }
  $('validation-ids').disabled=Boolean(source?.fixed_validation);
  $('validation-ids').required=!source?.fixed_validation;
  $('validation-help').textContent=source?.validation_note|| (source?.fixed_validation?'La tarea 16 conserva la partición del paquete. Sus cinco fotos de validación son reales; las sintéticas quedan en entrenamiento.':'Conserven la misma validación al comparar modelos. Todas las vistas de una escena quedan juntas.');
  updateImportLabel();
}
function setLoadingButton(button,active,label){button.classList.toggle('is-loading',active);button.setAttribute('aria-busy',String(active));button.textContent=label}
function importFeedback(phase,message){
  const active=phase==='reading'||phase==='report';
  $('import-feedback').hidden=false;$('import-feedback').dataset.state=active?'loading':phase;
  $('import-progress').hidden=!active;
  $('import-progress').setAttribute('aria-label',phase==='report'?'Actualizando el informe del lote':'Importando el lote de anotaciones');
  $('import-status-text').textContent=message;$('import-status-icon').hidden=active;
  $('import-status-mark').setAttribute('d',phase==='success'?'m7 12 3 3 7-7':'m9 9 6 6m0-6-6 6');
  setLoadingButton($('import-button'),active,active?(phase==='report'?'Actualizando informe…':'Importando lote…'):'Traer anotaciones del lote');
}
async function refreshImportSources(){
  if(sourcesLoading||importing)return;
  sourcesLoading=true;$('refresh-import-sources').disabled=true;setLoadingButton($('refresh-import-sources'),true,'Consultando CVAT…');updateAvailability();
  try{
    const items=await api('/api/datasets/sources');if(importing)return;
    // Conservar la selección y los IDs manuales al actualizar en segundo plano.
    const previous=$('participant').value,firstSelection=!importSources.length&&!$('import-task').value.trim()&&!uiPreferences.fields.participant;importSources=items;sourcesUpdated=new Date().toISOString();
    renderImportSources(firstSelection?'task:16':undefined);
    selectImportSource(previous!==$('participant').value);saveUiPreferences();
    const projectCount=new Set(items.map(s=>s.project_id)).size;
    $('import-sources-status').textContent=items.length?`${projectCount} ${projectCount===1?'proyecto':'proyectos'} · ${items.length} ${items.length===1?'tarea compatible':'tareas compatibles'}. Lista actualizada desde CVAT. Cargar la lista no importa anotaciones.`:'No hay tareas compatibles con el inventario interno en los proyectos de Walmart. Puedes indicar un número de tarea para comprobarla.';
  }catch(err){$('import-sources-status').textContent='No pudimos consultar CVAT. '+err.message+' Puedes reintentar; se conserva la última lista guardada.'}
  finally{sourcesLoading=false;$('refresh-import-sources').disabled=false;setLoadingButton($('refresh-import-sources'),false,'Cargar proyectos y tareas de CVAT');updateAvailability()}
}
function selectedRun(){return data.runs.find(run=>run.id===$('run').value)}
function selectedBaseline(){return data.runs.find(run=>run.id===$('baseline').value)}
function renderResults(){const run=selectedRun(),base=selectedBaseline();renderResultActions(run);renderDecision(run);renderAvailability(run);$('results-empty').hidden=Boolean(run);$('results-content').hidden=!run;if(!run){$('baseline-status').hidden=true;setHTML($('metric-cards'),'');$('results-context').textContent='Los resultados aparecerán cuando un ensayo tenga una evaluación disponible.';$('run-table').innerHTML='';$('comparison').innerHTML='';$('comparison-note').innerHTML='';$('chart').innerHTML='';$('legend').innerHTML='';return}const comparable=Lab.comparable(run,base);$('baseline-status').hidden=!base||comparable;$('baseline-status').textContent=Lab.comparisonReason(run,base);const comparisons=run.comparisons.filter(i=>i.split==='val'),truth=comparisons.reduce((sum,i)=>sum+i.anotados,0),found=comparisons.reduce((sum,i)=>sum+i.aciertos,0);const cards=[['Calidad de contornos · validación original',fmt(run.metrics['metrics/mAP50-95(M)']),'metrics/mAP50-95(M)','mAP50–95 · escala de 0 a 1','map'],[Lab.levelsCopy(run)?'Detección de niveles y estados':'Detección de módulos',fmt(run.metrics['metrics/mAP50(M)']),'metrics/mAP50(M)','mAP50 · escala de 0 a 1','map'],[Lab.levelsCopy(run)?'Niveles localizados':'Módulos encontrados',comparisons.length?`${found} / ${truth}`:'—',null,'Validación original · revisa también sus límites','errores'],['Vueltas de aprendizaje',run.history.length,null,'Épocas completadas','epoca']];setHTML($('metric-cards'),cards.map(([label,value,key,note,term])=>{const delta=comparable&&key&&Number.isFinite(base.metrics[key])?run.metrics[key]-base.metrics[key]:null;return `<div class="metric"><span>${label}</span><strong>${value}</strong><small>${note}</small>${delta===null?'':`<small class="${delta>=0?'positive':'negative'}">${delta>=0?'+':''}${fmt(delta)} respecto a la referencia</small>`}<button type="button" class="help" data-term="${term}" aria-label="Explicar ${label}">?</button></div>`}).join(''));$('metrics-guide').textContent=Lab.levelsCopy(run)?'Encontrar un nivel, clasificar su estado y generar la alerta correcta son comprobaciones distintas. Las medidas de localización no sustituyen la evaluación de alertas.':'Estas medidas resumen la localización y la forma de los módulos. No evalúan estados ni alertas de disponibilidad.';$('results-context').textContent=runName(run.id)+'. '+profileDescription(run)+'. '+Lab.evaluationContext(run);$('comparison-help').textContent='Conjunto: validación original del entrenamiento. Verde: anotaciones · azul: predicción.'+(run.development_evaluation?' Estas comparaciones se guardaron durante el entrenamiento. Puedes analizar cualquiera de las '+run.development_evaluation.metrics.fotos+' fotos disponibles en Probar una foto.':'');drawChart(run,base);const items=run.comparisons.filter(i=>$('split').value==='all'||i.split===$('split').value);options('comparison-photo',items.map(i=>({id:i.imagen,name:`Foto ${i.imagen} · ${i.split==='val'?'validación':'aprendizaje'}`})));renderComparison();$('run-table').innerHTML=data.runs.map(i=>`<tr><td>${esc(runName(i.id))}</td><td><span class="pill">${i.ready?'Evaluado':i.history.length?'En curso / incompleto':'Preparado'}</span></td><td>${i.history.length}</td><td>${fmt(i.metrics['metrics/mAP50-95(M)'])}</td><td>${fmt(i.metrics['metrics/mAP50(M)'])}</td><td>${i.manifest.imagenes.filter(j=>j.split==='train').length} para aprender / ${i.manifest.imagenes.filter(j=>j.split==='val').length} para validar</td></tr>`).join('');$('chart-caption').textContent=base?(base.id===run.id?'Selecciona otro ensayo para comparar.':!comparable?Lab.comparisonReason(run,base)+' Puedes explorar las curvas.':'Estos ensayos comparten criterio, fotos, referencias, partición y parámetros. Las diferencias corresponden a la validación original.'):'Cada punto corresponde a una vuelta de aprendizaje. En medidas de calidad, más alto suele ser mejor. En curvas de error, más bajo suele ser mejor.'}
function renderDecision(run){const node=$('result-decision');node.hidden=!run;if(!run){setHTML(node,'');return}const d=Lab.resultDecision(run,`El modelo «${shortRunName(run.id)}»`);node.dataset.kind=d.kind;setHTML(node,`<h2>${esc(d.title)}</h2><p>${esc(d.detail)}</p>`)}
function drawChart(run,base){
  const key=$('chart-metric').value,label=$('chart-metric').selectedOptions[0].textContent;
  const series=[{run,color:'var(--blue)'},...(base&&base.id!==run.id?[{run:base,color:'var(--chart-reference)',dashed:true}]:[])];
  $('legend').innerHTML=series.map(s=>`<span><svg aria-hidden="true" viewBox="0 0 24 12" style="width:24px;height:12px;vertical-align:middle"><path d="M1 6h22" stroke="${s.color}" stroke-width="3" ${s.dashed?'stroke-dasharray="5 3"':''}/></svg> ${esc(shortRunName(s.run.id))}${s.dashed?' · referencia':''}</span>`).join('');
  $('chart-value-label').textContent=label;
  setHTML($('chart-value-rows'),series.flatMap(s=>s.run.history.map(r=>`<tr><td>${esc(runName(s.run.id))}</td><td>${r.epoch}</td><td>${fmt(r[key])}</td></tr>`)).join('')||'<tr><td colspan="3">Todavía no hay épocas completadas.</td></tr>');
  const values=series.flatMap(s=>s.run.history.map(r=>r[key])).filter(Number.isFinite);
  if(!values.length){$('chart').innerHTML='<div class="empty">La curva aparecerá cuando se registre la primera época con esta medida.</div>';return}
  const width=Math.max(300,Math.floor($('chart').clientWidth||900)),height=290,left=58,right=width-24,bottom=248;
  const maxX=Math.max(1,...series.flatMap(s=>s.run.history.map(r=>r.epoch))),maxY=key.includes('loss')?Math.max(.01,...values)*1.08:1;
  const x=v=>left+(v-1)/Math.max(1,maxX-1)*(right-left),y=v=>bottom-v/maxY*218;
  let svg=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(label)} por época. Consulta los valores en la tabla debajo de la curva.">`;
  for(let i=0;i<=4;i++){const v=maxY*i/4;svg+=`<line x1="${left}" y1="${y(v)}" x2="${right}" y2="${y(v)}" stroke="var(--line)"/><text x="${left-10}" y="${y(v)+5}" text-anchor="end" font-size="14" fill="var(--muted)">${v.toFixed(2)}</text>`}
  for(const v of [...new Set([1,Math.max(1,Math.round(maxX/4)),Math.max(1,Math.round(maxX/2)),Math.max(1,Math.round(3*maxX/4)),maxX])])svg+=`<text x="${x(v)}" y="271" text-anchor="middle" font-size="14" fill="var(--muted)">${v}</text>`;
  svg+=`<text x="${(left+right)/2}" y="288" text-anchor="middle" font-size="14" fill="var(--muted)">Épocas completadas</text>`;
  for(const s of series){const points=s.run.history.filter(r=>Number.isFinite(r[key]));svg+=`<polyline points="${points.map(r=>`${x(r.epoch)},${y(r[key])}`).join(' ')}" fill="none" stroke="${s.color}" stroke-width="2.5" ${s.dashed?'stroke-dasharray="7 5"':''}/>`;if(points.length){const last=points.at(-1);svg+=`<circle cx="${x(last.epoch)}" cy="${y(last[key])}" r="4" fill="${s.color}"><title>Época ${last.epoch}: ${fmt(last[key])}</title></circle>`}}
  $('chart').innerHTML=svg+'</svg>';
}
$('learning-curves').addEventListener('toggle',()=>{if($('learning-curves').open)drawChart(selectedRun(),selectedBaseline())});
function renderComparison(){
  const run=selectedRun(),item=run?.comparisons.find(item=>item.imagen===$('comparison-photo').value),base=selectedBaseline(),other=base?.comparisons.find(value=>value.imagen===item?.imagen);
  ImageNavigation.release($('comparison'));
  if(!item){$('comparison').innerHTML='<div class="empty">No hay fotos evaluadas para esta selección. Prueba otro ensayo o cambia el grupo de fotos.</div>';$('comparison-note').innerHTML='Las comparaciones se generan al terminar el entrenamiento y la evaluación.';return}
  $('comparison').innerHTML=`${other?.url&&base.id!==run.id?`<p class="muted">${esc(runName(run.id))}</p>`:''}${item.url?`<img class="photo" src="${esc(item.url)}" alt="Anotación y predicción del ensayo seleccionado">`:'<div class="empty">La imagen de comparación no está disponible en este ensayo.</div>'}`+(other?.url&&base.id!==run.id?`<p class="muted">Referencia: ${esc(runName(base.id))}</p><img class="photo" src="${esc(other.url)}" alt="Anotación y predicción del ensayo de referencia">`:'');
  ImageNavigation.mount($('comparison'));
  const iou=item.parejas.length?item.parejas.reduce((sum,value)=>sum+value.iou_mascara,0)/item.parejas.length:null;
  $('comparison-note').className='comparison-details';$('comparison-note').innerHTML=`<div class="result-summary"><div><strong>${item.aciertos} / ${item.anotados}</strong><span>${Lab.levelsCopy(run)?'Niveles localizados':'Módulos emparejados'}</span></div><div><strong>${item.omitidos}</strong><span>${Lab.levelsCopy(run)?'Niveles omitidos':'Módulos omitidos'}</span></div><div><strong>${item.falsos_positivos}</strong><span>Detecciones extra</span></div></div>${item.contornos_xy_invalidos?`<p class="contour-warning"><strong>${item.contornos_xy_invalidos} ${item.contornos_xy_invalidos===1?'contorno requiere':'contornos requieren'} revisión.</strong> El polígono puede cruzarse o unir zonas separadas.</p>`:''}<details class="secondary-section"><summary>Detalle de la comparación</summary><p>IoU medio de las máscaras emparejadas: ${fmt(iou)} (escala de 0 a 1). Confianza mínima: ${esc(item.conf)}.</p><p>${item.split==='train'?'Esta foto se usó para enseñar al modelo. Su resultado no mide cómo funciona en escenas nuevas.':'Esta foto se usa para validación de desarrollo; no es la reserva de evaluación final.'}</p></details>`;
}
let photoMode='upload',uploadedPhoto=null,uploadingPhoto=false,uploadSequence=0;
function availablePredictionImages(){return Lab.predictionImages(data,$('model').value)}
function currentPredictionImage(){return photoMode==='upload'?uploadedPhoto:availablePredictionImages().find(item=>item.id===$('image').value)}
function renderProjectPhotos(){
  const previous=$('image').value,images=availablePredictionImages();
  options('image',images.map(i=>({...i,name:`Foto ${i.name}`})),false,images.find(i=>i.name==='28')?.id||images[0]?.id||'');
  const model=data.models.find(m=>m.id===$('model').value);
  $('project-photo-help').textContent=!model?'Elige un modelo para ver las fotos disponibles.':!images.length?'No hay fotos de desarrollo disponibles fuera del entrenamiento de este modelo. Usa Subir mi foto para evaluar una imagen nueva.':model.run?`${images.length} ${images.length===1?'foto disponible':'fotos disponibles'} para evaluar y ajustar. Se excluyen las usadas para entrenar este modelo.`:'Fotos de desarrollo disponibles. Este modelo general no tiene entrenamiento local registrado.';
  $('photo-picker').hidden=!images.length;
  return previous!==$('image').value;
}
let edgeLayers=[];
function demoView(mode){
  const tabs=[...document.querySelectorAll('[data-demo-view]')],selected=tabs.find(b=>b.dataset.demoView===mode&&!b.disabled);
  if(!selected)return;
  $('demo-visual').dataset.mode=mode;$('demo-visual').setAttribute('aria-labelledby',selected.id);
  for(const button of tabs){const active=button===selected;button.setAttribute('aria-selected',String(active));button.tabIndex=active?0:-1}
  if(mode==='edges')ImageNavigation.mount($('edge-output'));
}
function renderEdgeLayer(){
  const layer=edgeLayers.find(item=>item.id===$('edge-layer').value);
  ImageNavigation.release($('edge-output'));
  if(!layer){$('edge-output').className='empty';$('edge-output').textContent='Analiza con YOLO + detección de bordes para ver el mapa de señal.';$('edge-help').textContent='';$('edge-open').removeAttribute('href');return}
  $('edge-output').className='';setHTML($('edge-output'),`<img class="photo" src="${esc(layer.url)}" alt="${esc(layer.name)} de la foto seleccionada">`);
  $('edge-help').textContent=layer.help;$('edge-open').href=layer.url;
  ImageNavigation.mount($('edge-output'));
}
function renderEdgeViews(job){
  edgeLayers=job.result.occupancy?[
    {id:'signal',name:'Mapa de señal',url:job.occupancy_image_url,help:'Fucsia: señal dentro de cada nivel. Los números corresponden a los niveles detectados.'},
    {id:'levels',name:'Bordes de los niveles',url:job.occupancy_filtered_edges_url,help:'Bordes filtrados dentro de los niveles analizados. Los niveles sin medición quedan negros.'},
    {id:'photo',name:'Bordes de toda la foto',url:job.occupancy_edges_url,help:'Bordes obtenidos de la foto original, sin colores ni etiquetas de YOLO.'}
  ].filter(layer=>layer.url):[];
  options('edge-layer',edgeLayers);
  $('photo-view-edges').disabled=!edgeLayers.length;
  $('photo-view-edges').title=edgeLayers.length?'Mapa de señal y bordes del análisis':'Disponible al analizar con YOLO + detección de bordes';
  renderEdgeLayer();
}
function resetPrediction(){
  edgeLayers=[];$('edge-layer').value='';renderEdgeLayer();
  $('prediction-occupancy').hidden=true;setHTML($('prediction-occupancy'),'');
  ImageNavigation.release($('prediction-output'));$('prediction-output').className='empty';$('prediction-output').textContent='Analiza la foto para ver los niveles.';
  $('prediction-stats').innerHTML='';$('prediction-detections').innerHTML='';$('prediction-summary').innerHTML='<p>El resultado aparecerá aquí después del análisis.</p>';
  $('prediction-caption').textContent='Niveles detectados';predictJob=null;$('demo-progress').hidden=true;document.querySelector('.demo-stage').setAttribute('aria-busy','false');document.querySelector('.demo-legend').hidden=false;
  for(const button of document.querySelectorAll('[data-demo-view]'))button.disabled=button.dataset.demoView!=='original';demoView('original');
}
function renderOriginal(){
  renderProjectPhotos();
  const item=currentPredictionImage();if(item){$('original').src=item.url;$('original').hidden=false}else{$('original').removeAttribute('src');$('original').hidden=true}
  $('original').onload=()=>{$('demo-visual').style.setProperty('--photo-ratio',String($('original').naturalWidth/Math.max(1,$('original').naturalHeight)))};
  if(item?.width&&item?.height)$('demo-visual').style.setProperty('--photo-ratio',String(item.width/item.height));
  $('demo-empty').hidden=Boolean(item);$('demo-photo-name').textContent=item?(photoMode==='upload'?item.name:'Foto '+item.name):'Tu foto de la góndola';
  $('demo-photo-info').textContent=item?(photoMode==='upload'?`${item.width} × ${item.height} px · Foto subida por ti · Revisión visual sin anotaciones`:'Foto del proyecto · Evaluación de desarrollo'):'Sube una imagen o elige una del proyecto para empezar.';
  resetPrediction();ImageNavigation.mount($('predict'));if($('original').closest('.image-viewer'))$('original').closest('.image-viewer').hidden=!item;
  renderThumbnails();updateAvailability();
}
function selectPhotoMode(mode){photoMode=mode;$('upload-source').hidden=mode!=='upload';$('project-source').hidden=mode!=='project';document.querySelectorAll('[data-photo-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.photoMode===mode)));clearOperationError('predict');renderOriginal()}
async function uploadPhoto(file){
  if(!file)return;$('photo-upload').value='';clearOperationError('predict');
  if(!/\.(jpe?g|png|webp)$/i.test(file.name)&&!['image/jpeg','image/png','image/webp'].includes(file.type)){error('Elige una foto JPG, PNG o WebP.','predict');return}
  if(!file.size||file.size>15*1024*1024){error('La foto debe pesar como máximo 15 MB.','predict');return}
  const ticket=++uploadSequence;uploadingPhoto=true;selectPhotoMode('upload');$('upload-status').textContent='Subiendo y preparando la foto…';updateAvailability();
  try{
    const response=await fetch('/api/photos',{method:'POST',headers:{'Content-Type':file.type||'application/octet-stream','X-Filename':encodeURIComponent(file.name)},body:file,signal:AbortSignal.timeout(60000)});
    const photo=await response.json();if(!response.ok)throw Error(photo.error||'No se pudo cargar la foto.');if(ticket!==uploadSequence)return;
    uploadedPhoto=photo;$('upload-label').textContent='Cambiar foto';$('upload-zone').classList.add('has-photo');$('upload-status').textContent='Foto lista para analizar.';renderOriginal();
  }catch(err){if(ticket===uploadSequence){$('upload-status').textContent='La foto no se pudo cargar. Puedes volver a intentarlo.';error(err.name==='TimeoutError'?'La carga tardó demasiado. Vuelve a subir la foto.':err.message,'predict')}}
  finally{if(ticket===uploadSequence){uploadingPhoto=false;$('photo-upload').value='';updateAvailability()}}
}
function renderThumbnails(){
  const images=availablePredictionImages(),key=JSON.stringify(images.map(i=>[i.id,i.url]));
  if(key!==thumbnailKey){thumbnailKey=key;$('photo-thumbnails').innerHTML=images.map(i=>`<button type="button" class="photo-choice" data-photo="${esc(i.id)}" aria-label="Elegir foto ${esc(i.name)}" aria-pressed="false"><img src="${esc(i.url)}&amp;preview=thumb" width="280" height="210" alt="" loading="lazy" decoding="async"><span>Foto ${esc(i.name)}</span></button>`).join('')}
  document.querySelectorAll('[data-photo]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.photo===$('image').value)));
  const item=images.find(i=>i.id===$('image').value);$('photo-picker-title').textContent=item?`Elegir por imagen; seleccionada foto ${item.name}`:'No hay fotos disponibles fuera del entrenamiento';
}
function sourceSummary(){
  const source=data.runs.find(i=>i.id===$('source').value)||data.datasets.find(i=>i.id===$('source').value);
  if(!source){$('train-data-help').textContent='Prepara una copia revisada para entrenar.';setHTML($('source-summary'),'<p>No hay datos seleccionados.</p>');modelHelp();renderTrainingPreview();return}
  const images=source.report?.imagenes||source.manifest.imagenes,isCopy=Boolean(source.report);
  setHTML($('train-data-help'),`<p><strong>${esc(profileDescription(source))}</strong><br><strong>${images.filter(i=>i.split==='train').length}</strong> fotos para entrenar · <strong>${images.filter(i=>i.split==='val').length}</strong> para validar.</p>`);
  setHTML($('source-summary'),`<p><strong>Origen:</strong> ${esc(isCopy?copyOrigin(source):runName(source.id))}</p><p>${source.review?'Revisado por '+esc(source.review.reviewer):'Copia conservada del ensayo anterior.'}</p>${isCopy?'':'<p>Usa las anotaciones guardadas en ese ensayo, aunque CVAT haya cambiado.</p>'}<p>Fotos: ${images.filter(i=>['train','val'].includes(i.split)).map(i=>esc(i.imagen)).join(', ')}.</p>`);
  modelHelp();renderTrainingPreview();
}
function duration(seconds){if(seconds==null)return '—';const mins=Math.floor(seconds/60),secs=Math.floor(seconds%60);return mins>=60?`${Math.floor(mins/60)} h ${mins%60} min`:mins?`${mins} min ${secs} s`:`${secs} s`}
function liveChart(history, series, label){
  const rows=history.filter(row=>Number.isFinite(row.epoch)),values=rows.flatMap(row=>series.map(item=>row[item.key])).filter(Number.isFinite);
  if(!values.length)return '<div class="empty">La curva aparecerá con las primeras métricas de una época completada.</div>';
  const maxX=Math.max(1,...rows.map(r=>r.epoch)),maxY=series[0].key.includes('loss')?Math.max(.01,...values)*1.12:1;
  const x=v=>42+(v-1)/Math.max(1,maxX-1)*326,y=v=>164-v/maxY*136;
  let svg=`<svg viewBox="0 0 390 202" role="img" aria-label="${esc(label)}. Valores disponibles en la tabla por época.">`;
  for(let i=0;i<=4;i++){const v=maxY*i/4;svg+=`<line x1="42" x2="368" y1="${y(v)}" y2="${y(v)}" stroke="var(--line)"/><text x="34" y="${y(v)+4}" text-anchor="end" font-size="14" fill="var(--muted)">${v.toFixed(2)}</text>`}
  const ticks=[...new Set([1,Math.max(1,Math.round(maxX/2)),maxX])];for(const v of ticks)svg+=`<text x="${x(v)}" y="183" text-anchor="middle" font-size="14" fill="var(--muted)">${v}</text>`;
  svg+='<text x="205" y="199" text-anchor="middle" font-size="14" fill="var(--muted)">Épocas</text>';
  for(const item of series){const points=rows.filter(r=>Number.isFinite(r[item.key]));svg+=`<polyline fill="none" stroke="${item.color}" stroke-width="2.5" ${item.dashed?'stroke-dasharray="5 4"':''} points="${points.map(r=>`${x(r.epoch)},${y(r[item.key])}`).join(' ')}"/>`;if(points.length){const last=points.at(-1);svg+=`<circle cx="${x(last.epoch)}" cy="${y(last[item.key])}" r="3.5" fill="${item.color}"><title>Época ${last.epoch}: ${last[item.key].toFixed(3)}</title></circle>`}}
  return svg+'</svg>';
}
let monitorDisplayState=null;
function renderTraining(){
  const trainingJobs=jobs.filter(j=>j.config?.action==='train'&&jobInVersion(j));
  if(!monitorJob)monitorJob=trainingJobs.find(j=>j.state==='running')?.id||trainingJobs[0]?.id||null;
  if(connection.activityKnown&&monitorJob&&!trainingJobs.some(j=>j.id===monitorJob))monitorJob=trainingJobs[0]?.id||null;
  if(connection.activityKnown)options('monitor-job',trainingJobs.map(j=>({id:j.id,name:runName(j.config.run)})),false,monitorJob);
  if(monitorJob)$('monitor-job').value=monitorJob;
  const job=trainingJobs.find(j=>j.id===monitorJob),run=data.runs.find(r=>r.id===job?.config.run),state=Lab.trainingState(job,run);
  const known=connection.phase==='ready'&&connection.activityKnown,failed=connection.phase==='error'||Boolean(connection.activityError);
  $('train-layout').classList.toggle('has-training',job?.state==='running');
  arrangeTraining(job?.state==='running');
  const displayState=[job?.id,job?.state,known,failed].join(':');
  if(displayState!==monitorDisplayState){const wasRunning=monitorDisplayState?.startsWith(job?.id+':running:');$('training-monitor').open=job?.state==='running'||['error','interrupted'].includes(job?.state)||failed||(wasRunning&&$('training-monitor').open);monitorDisplayState=displayState;}
  $('monitor-select-wrap').hidden=trainingJobs.length<2;$('monitor-values').hidden=!job;
  $('monitor-badge').dataset.state=job?.state||'';
  $('monitor-title').textContent=job?.state==='running'?'Entrenamiento en curso':'Seguimiento';
  $('monitor-badge').textContent=!known?(failed?'Sin actualizar':'Consultando'):({running:'En curso',done:'Completado',error:'Con error',interrupted:'Interrumpido'}[job?.state]||'Sin iniciar');
  $('monitor-run').textContent=job?runName(job.config.run):'';
  const messages={preparing:'Preparando fotos y etiquetas.',training:`El modelo está aprendiendo${job?.progress?.current_epoch?' · época actual '+job.progress.current_epoch:''}. Las métricas se publican al completar cada época.`,evaluating:'Evaluando los mejores pesos en validación.',comparing:'Generando las comparaciones por foto.',done:'Entrenamiento terminado. Revisa sus resultados.',unknown:'El trabajo está en ejecución. Esperando el primer avance registrado.'};
  $('monitor-message').textContent=!known?(failed?'No pudimos actualizar el seguimiento. Los últimos datos se conservan; reintenta la consulta desde el aviso superior.':'Consultando la actividad del laboratorio. El seguimiento aparecerá al terminar la consulta.'):!job?'El avance aparecerá al iniciar un entrenamiento.':['error','interrupted'].includes(job.state)?'El ensayo se detuvo. Revisa el registro técnico antes de volver a intentarlo; los avances guardados siguen disponibles.':messages[state.stage]||messages.unknown;
  $('monitor-alert').hidden=known||!failed;$('monitor-alert').textContent=failed?'Seguimiento sin actualizar. '+(connection.activityError||connection.error):'';
  const stages=['preparing','training','evaluating','comparing'],index=stages.indexOf(state.stage);
  document.querySelectorAll('.training-steps li').forEach((li,i)=>{const status=!job?'waiting':job.state==='done'||i<index?'complete':i===index?(['error','interrupted'].includes(job.state)?'failed':'current'):'waiting';li.dataset.state=status;if(status==='current')li.setAttribute('aria-current','step');else li.removeAttribute('aria-current');li.querySelector('span').textContent=({complete:'Completado',current:'En curso',failed:'Detenido',waiting:['Fotos y etiquetas','Épocas y curvas','Validación','Resultados por foto'][i]})[status]});
  if(!job)return;
  $('monitor-epochs').textContent=job.state==='done'?`${state.completed} épocas ejecutadas · ensayo terminado`:`${state.completed} / ${state.total||'—'}${state.percent!==null?' · '+state.percent+'%':''}`;
  $('monitor-progress').hidden=state.terminal;
  $('monitor-progress').max=state.total||Math.max(1,state.completed);$('monitor-progress').value=state.completed;
  $('monitor-progress').setAttribute('aria-valuetext',`${state.completed} épocas completadas de un máximo de ${state.total||'no registrado'}${job.state==='done'&&state.total&&state.completed<state.total?'; terminó antes del máximo':''}`);
  $('monitor-duration').textContent=`Tiempo ${state.terminal?'registrado':'transcurrido'}: ${duration(state.elapsed)}${job.state==='done'&&state.total&&state.completed<state.total?' · Terminó antes del máximo':''}`;
  $('monitor-device').textContent='Dispositivo: '+(job.progress?.device||'por confirmar');
  $('monitor-map').textContent=fmt(state.latest['metrics/mAP50-95(M)']);$('monitor-best').textContent=fmt(state.best?.['metrics/mAP50-95(M)']);$('monitor-best-epoch').textContent=state.best?'Observado en época '+state.best.epoch:'Esperando validación';$('monitor-loss').textContent=fmt(state.latest['train/seg_loss']);
  setHTML($('live-quality'),liveChart(state.history,[{key:'metrics/mAP50-95(M)',color:'var(--blue)'}],'Evolución de calidad de contornos'));
  setHTML($('live-loss'),liveChart(state.history,[{key:'train/seg_loss',color:'var(--blue)'},{key:'val/seg_loss',color:'var(--green)',dashed:true}],'Evolución del error de aprendizaje y validación'));
  setHTML($('monitor-table'),state.history.map(r=>`<tr><td>${r.epoch}</td><td>${fmt(r['metrics/mAP50-95(M)'])}</td><td>${fmt(r['train/seg_loss'])}</td><td>${fmt(r['val/seg_loss'])}</td></tr>`).join('')||'<tr><td colspan="4">Esperando la primera época completada.</td></tr>');
  const preview=job.progress?.preview_url;$('monitor-preview').hidden=!preview;
  if(preview){if($('monitor-preview-image').getAttribute('src')!==preview)$('monitor-preview-image').src=preview;const validation=job.progress.preview_kind==='validation';$('monitor-preview-title').textContent=validation?'Lo que encuentra en validación':'Ejemplos que está usando';$('monitor-preview-caption').textContent=validation?'Predicciones del ensayo en validación.':'Fotos y anotaciones del lote de entrenamiento.';$('monitor-preview-image').alt=validation?'Predicciones del ensayo en fotos de validación':'Fotos y anotaciones del lote de entrenamiento'}
  ImageNavigation.mount($('monitor-preview'));
  $('monitor-results').disabled=!run;
}
const trainingNarrow=matchMedia('(max-width:1000px)');
function arrangeTraining(hasJob){
  const layout=$('train-layout'),form=$('train-form'),stack=layout.querySelector('.train-stack');
  const first=trainingNarrow.matches&&hasJob?stack:form;
  if(layout.firstElementChild!==first){const focused=document.activeElement;layout.prepend(first);if(focused?.isConnected)focused.focus({preventScroll:true})}
}
trainingNarrow.addEventListener('change',()=>arrangeTraining(jobs.find(j=>j.id===monitorJob)?.state==='running'));
$('monitor-job').addEventListener('change',()=>{monitorJob=$('monitor-job').value;renderTraining();$('training-monitor').open=true;saveUiPreferences()});
$('monitor-results').addEventListener('click',()=>{const job=jobs.find(j=>j.id===monitorJob);if(!job)return;$('run').value=job.config.run;renderResults();switchTab('results')});
$('monitor-log').addEventListener('click',()=>{$('activity-panel').open=true;const item=[...document.querySelectorAll('#activity details')].find(d=>d.dataset.job===monitorJob);if(item){item.open=true;item.querySelector('summary').focus();item.scrollIntoView({block:'center',behavior:'instant'})}});
let catalogKey=null,lastCatalogRefresh=0,shownPredictionJob=null,pollTimer=null;
async function refresh(){
  try{
    const catalog=await api('/api/catalog');connection.checkedAt=new Date().toISOString();lastCatalogRefresh=Date.now();connection.phase='ready';connection.error='';if(catalog===catalogKey&&!pendingRun){renderVersionContext();renderConnectionStatus();updateAvailability();return}catalogKey=catalog;fullCatalog={...catalog,datasets:catalog.datasets||[],archived_datasets:catalog.archived_datasets||[],archived_models:catalog.archived_models||[]};data=Lab.versionCatalog(fullCatalog,projectVersion);connection.phase='ready';connection.error='';
    renderScopedCatalog();renderImportSources();selectImportSource();renderVersionContext();
  }catch(err){connection.phase='error';connection.error='Comprueba que el servidor local esté abierto. '+err.message;renderConnectionStatus();updateAvailability();throw err}
}
function renderScopedCatalog(){
    const runs=data.runs.map(r=>({...r,name:shortRunName(r.id)+' · '+Lab.profile(r).label,group:Lab.technical(r.id)?'Pruebas técnicas':Lab.profile(r).label})).sort((a,b)=>Number(Lab.technical(a.id))-Number(Lab.technical(b.id)));
    options('run',runs,false,Lab.defaultRun(data,predictionScope()));if(pendingRun&&runs.some(r=>r.id===pendingRun)){$('run').value=pendingRun;pendingRun=null}options('baseline',runs,true);
    const sources=[...data.datasets.filter(v=>Lab.readyCopy(v)).map(v=>({...v,name:datasetName(v),group:'Copias revisadas de anotaciones'})),...data.runs.filter(r=>r.ready).map(r=>({...r,name:shortRunName(r.id)+' · '+Lab.profile(r).label,group:Lab.technical(r.id)?'Copias de pruebas técnicas':'Copias guardadas en ensayos'}))].sort((a,b)=>Number(Lab.technical(a.id))-Number(Lab.technical(b.id)));
    options('source',sources,false,sources.find(v=>!Lab.technical(v.id))?.id||'');
    const previousCopy=$('dataset-version').value;renderCopyOptions();if(previousCopy!==$('dataset-version').value)$('reviewed').checked=false;
    options('archived-version',data.archived_datasets.map(v=>({...v,name:datasetName(v)})),false);
    $('archived-copies').hidden=!data.archived_datasets.length;$('archived-title').textContent=`Copias archivadas (${data.archived_datasets.length})`;renderDataset();
    const previousPrediction=$('model').value;for(const mode of ['predict','train'])renderModelOptions(mode);
    const photoChanged=renderProjectPhotos();
    if(photoChanged||previousPrediction!==$('model').value)renderOriginal();
    renderModelLists();renderResults();sourceSummary();renderConnectionStatus();modelHelp();renderThumbnails();renderTraining();
}
async function submit(config){$('message').style.display='none';const job=await api('/api/jobs',config);jobs=[job,...jobs.filter(item=>item.id!==job.id)];busy=true;document.querySelectorAll('#train-form button.primary,#predict-form button.primary').forEach(button=>button.disabled=true);if(config.action==='predict'){resetPrediction();predictJob=job.id;$('prediction-output').className='empty';$('prediction-output').textContent='';$('prediction-stats').innerHTML='';$('prediction-detections').innerHTML='';$('prediction-summary').innerHTML='';$('demo-progress').hidden=false;document.querySelector('.demo-stage').setAttribute('aria-busy','true');$('analyze-photo').textContent='Analizando…'}else{monitorJob=job.id;pendingRun=job.config.run;await refresh();switchTab('train');saveUiPreferences();$('training-monitor').scrollIntoView({block:'start',behavior:'instant'})}await poll()}
function showPrediction(job){
  const result=job.result;if(!result)return;const detections=result.detecciones||[],summary=PredictionDemo.summary(detections,result.config.scope,result.level_states);
  ImageNavigation.release($('prediction-output'));$('prediction-output').className='';$('prediction-output').innerHTML=`<img class="photo" src="${esc(job.image_url)}" alt="Resultado: ${esc(summary.title)}. Niveles numerados y coloreados según su estado.">`;ImageNavigation.mount($('prediction-output'));
  $('demo-progress').hidden=true;document.querySelector('.demo-stage').setAttribute('aria-busy','false');for(const b of document.querySelectorAll('[data-demo-view]'))b.disabled=false;renderEdgeViews(job);demoView('result');
  const model=data.models.find(m=>m.id===result.config.model);$('demo-photo-info').textContent=(model?modelName(model,false):'Modelo seleccionado')+(result.config.image_source==='upload'?' · Revisión visual de foto subida':' · Evaluación de desarrollo');
  $('prediction-summary').innerHTML=`<h3>${esc(summary.title)}</h3><p>${esc(summary.detail)}</p>${summary.levels&&summary.total?`<div class="demo-state-counts">${summary.states.map(s=>`<span><i style="--state-color:${s.color}"></i><b>${summary.counts[s.key]}</b> ${s.label}</span>`).join('')}</div>`:''}`;
  document.querySelector('.demo-legend').hidden=summary.levels&&summary.total>0;
  $('prediction-caption').textContent='Niveles detectados';
  $('prediction-stats').innerHTML=result.metricas?`<details class="secondary-section"><summary>Comparación con las anotaciones de esta foto</summary><p class="demo-result-meta">${result.metricas.aciertos} de ${result.metricas.anotados} niveles localizados · ${result.metricas.omitidos} omitidos · ${result.metricas.extras} detecciones extra. ${result.config.split==='train'?'Foto de entrenamiento.':'Validación de desarrollo.'} Localizar un nivel no confirma su estado.</p>${result.metricas.scope==='Nivel_estados'?`<p class="demo-result-meta">Reposición: ${result.metricas.alertas_acertadas} de ${result.metricas.alertas_reales} casos detectados · ${result.metricas.alertas_omitidas??result.metricas.alertas_reales-result.metricas.alertas_acertadas} omitidos · ${result.metricas.falsas_alertas} falsas alertas.</p>`:''}</details>`:'';
  $('prediction-detections').innerHTML=`<details class="secondary-section"><summary>Ver ${summary.total} detecciones y datos del análisis</summary><p class="demo-result-meta">Confianza mínima ${result.config.conf} · entrada ${result.config.imgsz} px. ${result.config.image_source==='upload'?'Foto propia sin anotaciones de referencia: esta prueba muestra predicciones, no una medición de precisión.':''}</p>${summary.total?`<div class="table-wrap"><table><thead><tr><th>Nivel</th><th>Estado detectado</th><th>Confianza</th><th>Contorno</th></tr></thead><tbody>${detections.map((d,i)=>`<tr><td>${d.id||i+1}</td><td>${esc(PredictionDemo.stateOf(d)?.label||d.clase)}</td><td>${Math.round(d.confianza*100)} %</td><td>${d.contorno_valido===null?'Caja':d.contorno_valido?'Válido':'Revisar'}</td></tr>`).join('')}</tbody></table></div>`:''}</details>`;
  const occupancy=$('prediction-occupancy');occupancy.hidden=!result.occupancy;
  const occupancyRevision=PredictionDemo.occupancyRevision(result.occupancy?.method);
  const weighted=result.occupancy?.method==='paulo_mascara_v2_combinacion_ponderada';
  setHTML(occupancy,result.occupancy?`<details class="secondary-section"><summary>Mediciones por nivel · ${esc(occupancyRevision)}</summary><p>${weighted?'Combinado = 70 % de superficie + 30 % de ancho. ':''}Cálculo sobre la foto original. Área y ancho con señal son experimentales; todavía no equivalen a porcentaje real de producto. El estado de YOLO se conserva.</p><div class="table-wrap"><table><thead><tr><th>Nivel</th><th>Estado YOLO</th>${weighted?'<th>Combinado</th>':''}<th>Área con señal</th><th>Ancho con señal</th></tr></thead><tbody>${PredictionDemo.occupancyRows(detections).map(r=>`<tr><td>${r.id}</td><td>${esc(r.state)}</td>${weighted?`<td>${esc(r.combined)}</td>`:''}<td>${esc(r.area)}</td><td>${esc(r.width)}${r.reason?`<br><small>${esc(r.reason)}</small>`:''}</td></tr>`).join('')}</tbody></table></div></details>`:'');
  updateAvailability();
  if(currentView==='predict'&&matchMedia('(max-width:760px)').matches)document.querySelector('.demo-stage').scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'instant':'smooth'});
}
function schedulePoll(){
  clearTimeout(pollTimer);
  const delay=document.hidden?30000:busy?2500:connection.activityError?8000:10000;
  pollTimer=setTimeout(poll,delay);
}
async function poll(){
  if(polling)return;
  clearTimeout(pollTimer);polling=true;
  try{
    const previousJobs=jobs; jobs=await api('/api/jobs');
    connection.activityKnown=true;connection.activityError='';connection.checkedAt=new Date().toISOString();
    let finishedTraining=false;
    const active=jobs.find(job=>job.state==='running');busy=Boolean(active);updateAvailability();

    if(currentView==='train')renderTraining();renderVersionContext();
    $('jobbar').style.display=active?.config.action==='train'?'block':'none';
    if(active?.config.action==='train'){const version=Lab.versionOf(fullCatalog?.runs.find(r=>r.id===active.config.run||r.id===active.config.source)||fullCatalog?.datasets.find(v=>v.id===active.config.source),fullCatalog||{runs:[]});setHTML($('jobbar'),`Entrenamiento en curso · ${esc(versionNames[version])} · ${esc(runName(active.config.run))} <button class="text-button" data-version="${version}" data-tab="train">Ver seguimiento</button>`)}
    const versionJobs=jobs.filter(jobInVersion),nextActivityKey=JSON.stringify([projectVersion,versionJobs.map(j=>[j.id,j.state,j.config,j.log,j.error])]);
    if(activityKey!==nextActivityKey){
      const expanded=new Set([...document.querySelectorAll('#activity details[open]')].map(node=>node.dataset.job));
      const focused=document.activeElement.closest?.('#activity details')?.dataset.job;
      activityKey=nextActivityKey;
      $('activity').innerHTML=versionJobs.length?versionJobs.map(job=>`<details data-job="${job.id}" ${expanded.has(job.id)?'open':''}><summary>${job.config.action==='train'?'Entrenamiento':'Predicción'} · ${esc(job.config.run?runName(job.config.run):job.config.image.split('/').pop())} · ${esc(({running:'En curso',done:'Terminado',error:'Error',interrupted:'Interrumpido'})[job.state]||job.state)}</summary><pre>${esc(job.log||job.error||'Preparando…')}</pre></details>`).join(''):'Todavía no hay trabajos en esta versión.';
      if(focused){const target=[...document.querySelectorAll('#activity details')].find(d=>d.dataset.job===focused);target?.querySelector('summary').focus({preventScroll:true})}
    }
    for(const job of jobs){
      if(job.state!=='running'&&!seen.has(job.id)){
        seen.add(job.id);if(job.config.action==='train')finishedTraining=true;
        if(job.state==='error'||job.state==='interrupted'){
          if(jobInVersion(job))error(`${job.config.action==='train'?'Entrenamiento':'Predicción'}: ${job.error||'falló; revisa la salida en Actividad reciente.'}`);
          if(job.id===predictJob){$('demo-progress').hidden=true;document.querySelector('.demo-stage').setAttribute('aria-busy','false');$('prediction-summary').innerHTML='<p>No se pudo completar el análisis. Tu foto se conserva; vuelve a intentarlo.</p>';$('prediction-output').className='empty';$('prediction-output').textContent='La prueba no pudo completarse. Tus selecciones se conservan; revisa el aviso y vuelve a intentar.';error(job.error||'No se pudo generar la predicción. Vuelve a intentarlo cuando el laboratorio esté disponible.','predict')}
        }
      }
      if(job.id===predictJob&&job.state==='done'&&shownPredictionJob!==job.id){showPrediction(job);shownPredictionJob=job.id}
    }
    const previous=previousJobs.find(job=>job.id===active?.id);
    const progressChanged=active?.config.action==='train'&&(previous?.progress?.completed_epochs!==active.progress?.completed_epochs||previous?.progress?.stage!==active.progress?.stage);
    if(finishedTraining||(active?.config.action==='train'&&(progressChanged||Date.now()-lastCatalogRefresh>=10000)))await refresh();
  }catch(err){
    connection.activityKnown=false;connection.activityError='No pudimos consultar la actividad. '+err.message;
    updateAvailability();if(currentView==='train')renderTraining();
    $('jobbar').style.display='block';setHTML($('jobbar'),(connection.phase==='error'?'No pudimos actualizar el catálogo del laboratorio.':'No pudimos consultar la actividad. Las acciones de modelo esperan a recuperar la consulta.')+' <button class="text-button" data-retry>Reintentar</button>');
  }finally{polling=false;schedulePoll()}
}
document.addEventListener('visibilitychange',()=>{if(!document.hidden)poll();else schedulePoll()});
function switchTab(id){
  if(!$(id)?.classList.contains('view'))return;if(id==='glossary'&&currentView!=='glossary')glossaryReturn=currentView;closeHelp(false);currentView=id;const shell=document.querySelector('.shell');if(shell)shell.dataset.view=id;
  document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id===id));document.querySelectorAll('nav [data-tab]').forEach(b=>{b.classList.toggle('active',b.dataset.tab===id);if(b.dataset.tab===id)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')});
  $('workspace-version').hidden=false;renderWorkspace();
  $('mobile-section').textContent={version:'Inicio',datasets:'Preparar datos',train:'Entrenar',predict:'Probar una foto',results:'Comparar resultados',glossary:'Glosario'}[id];$('sections-nav').classList.remove('is-open');$('sections-toggle').setAttribute('aria-expanded','false');
  if(id==='version'&&fullCatalog&&Date.now()-lastCatalogRefresh>15000)retryQueries();if(id==='glossary')renderGlossary();if(id==='train')renderTraining();if(id==='results')renderResults();const heading=$(id).querySelector('h2');if(heading){heading.tabIndex=-1;heading.focus({preventScroll:true})}window.scrollTo({top:0,behavior:'instant'});
}
async function retryQueries(){connection.phase='loading';connection.activityKnown=false;connection.error='';connection.activityError='';renderConnectionStatus();updateAvailability();try{await refresh();await poll();if(connection.activityKnown)$('message').style.display='none';if(!$('original').getAttribute('src'))renderOriginal()}catch(err){error(err.message)}}
function selectCopy(id){if(!data.datasets.some(v=>v.id===id))return;if(!Lab.copiesByLot(data.datasets).some(g=>g.latest.id===id))$('show-copy-history').checked=true;renderCopyOptions(id);$('dataset-version').value=id;$('reviewed').checked=false;renderDataset();renderConnectionStatus();saveUiPreferences()}
document.addEventListener('click',event=>{
  const button=event.target.closest('button');if(!button)return;
  if(button.dataset.evalPhoto){contextAction('predict',button.dataset.evalModel);if($('model').value!==button.dataset.evalModel)return;const photo=availablePredictionImages().find(i=>i.id===button.dataset.evalPhoto);if(!photo){error('Esta foto ya no está disponible para estos pesos.');return}$('image').value=photo.id;selectPhotoMode('project');saveUiPreferences();return}
  if(button.dataset.contextAction){contextAction(button.dataset.contextAction,button.dataset.objectId);return}
  if(button.dataset.version){selectProjectVersion(button.dataset.version);if(button.dataset.tab)switchTab(button.dataset.tab);return}
  if(button.dataset.undoModel){manageModel('restore',button.dataset.modelMode,button.dataset.undoModel);return}
  if(button.hasAttribute('data-close-help')){closeHelp();return}
  if(button.dataset.fullTerm){showGlossaryTerm(button.dataset.fullTerm);return}
  if(button.dataset.term){openTerm(button.dataset.term,button);return}
  if(button.hasAttribute('data-retry')){retryQueries();return}
  if(button.dataset.photo&&availablePredictionImages().some(i=>i.id===button.dataset.photo)){$('image').value=button.dataset.photo;selectPhotoMode('project');saveUiPreferences();return}
  if(button.dataset.resultsAnchor){const target=$(button.dataset.resultsAnchor);target.scrollIntoView({block:'start',behavior:'instant'});const heading=target.querySelector('h2');if(heading){heading.tabIndex=-1;heading.focus({preventScroll:true})}return}
  if(button.dataset.tab){if(button.dataset.tab==='glossary'){$('glossary-search').value='';$('glossary-category').value='';glossaryFocus=button}switchTab(button.dataset.tab);saveUiPreferences()}
});
$('sections-toggle').addEventListener('click',()=>{const open=$('sections-nav').classList.toggle('is-open');$('sections-toggle').setAttribute('aria-expanded',String(open))});
$('project-version').addEventListener('change',()=>selectProjectVersion($('project-version').value));
document.addEventListener('keydown',event=>{if(event.key!=='Escape')return;if(helpPanel){event.preventDefault();closeHelp()}else if($('sections-nav').classList.contains('is-open')){$('sections-nav').classList.remove('is-open');$('sections-toggle').setAttribute('aria-expanded','false');$('sections-toggle').focus()}});
$('glossary-search').addEventListener('input',renderGlossary);
$('glossary-category').addEventListener('change',renderGlossary);
$('glossary-reset').addEventListener('click',()=>{$('glossary-search').value='';$('glossary-category').value='';renderGlossary();$('glossary-search').focus()});
document.addEventListener('invalid',event=>{const details=event.target.closest('details');if(details)details.open=true},true);$('glossary-back').addEventListener('click',()=>{switchTab(glossaryReturn);if(glossaryFocus?.isConnected)glossaryFocus.focus({preventScroll:true})});$('import-project').addEventListener('change',()=>{const previous=$('participant').value;renderImportSources();selectImportSource(previous!==$('participant').value);saveUiPreferences()});$('participant').addEventListener('change',()=>selectImportSource(true));$('refresh-import-sources').addEventListener('click',refreshImportSources);$('train-model').addEventListener('change',modelHelp);
for(const id of ['run','baseline','chart-metric','split'])$(id).addEventListener('change',renderResults);$('comparison-photo').addEventListener('change',renderComparison);$('image').addEventListener('change',renderOriginal);$('source').addEventListener('change',sourceSummary);$('dataset-version').addEventListener('change',()=>{$('reviewed').checked=false;renderDataset();renderConnectionStatus()});
for(const id of ['conf','nms'])$(id).addEventListener('input',()=>$(id+'-value').textContent=Number($(id).value).toFixed(2));
$('model').addEventListener('change',()=>{const model=data.models.find(item=>item.id===$('model').value);$('predict-size').value=String(model?.imgsz||640);renderOriginal();modelHelp()});
$('analysis-method').addEventListener('change',()=>{resetPrediction();modelHelp()});

document.querySelectorAll('[data-photo-mode]').forEach(button=>button.addEventListener('click',()=>selectPhotoMode(button.dataset.photoMode)));
document.querySelectorAll('[data-demo-view]').forEach(button=>{
  button.addEventListener('click',()=>demoView(button.dataset.demoView));
  button.addEventListener('keydown',event=>{
    if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
    const tabs=[...document.querySelectorAll('[data-demo-view]')].filter(tab=>!tab.disabled),index=tabs.indexOf(button);
    const next=event.key==='Home'?tabs[0]:event.key==='End'?tabs.at(-1):tabs[(index+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length];
    event.preventDefault();demoView(next.dataset.demoView);next.focus();
  });
});
$('edge-layer').addEventListener('change',renderEdgeLayer);
$('photo-upload').addEventListener('change',()=>uploadPhoto($('photo-upload').files[0]));
$('empty-upload').addEventListener('click',()=>{$('photo-upload').click()});
for(const eventName of ['dragenter','dragover'])$('upload-zone').addEventListener(eventName,event=>{event.preventDefault();$('upload-zone').classList.add('is-dragging')});
for(const eventName of ['dragleave','drop'])$('upload-zone').addEventListener(eventName,event=>{event.preventDefault();$('upload-zone').classList.remove('is-dragging')});
$('upload-zone').addEventListener('drop',event=>{if(event.dataTransfer.files.length!==1){error('Arrastra una sola foto para analizarla.','predict');return}uploadPhoto(event.dataTransfer.files[0])});

$('predict-form').addEventListener('submit',async event=>{event.preventDefault();clearOperationError('predict');$('prediction-occupancy').hidden=true;try{await submit({action:'predict',model:$('model').value,image:currentPredictionImage()?.id,conf:Number($('conf').value),nms:Number($('nms').value),imgsz:Number($('predict-size').value),...PredictionDemo.methodConfig($('analysis-method').value)})}catch(err){error(err.message,'predict')}});
$('train-form').addEventListener('submit',async event=>{event.preventDefault();clearOperationError('train');try{await submit({action:'train',name:$('name').value,source:$('source').value,model:$('train-model').value,purpose:$('purpose').value,reference_run:$('baseline').value||$('run').value,epochs:Number($('epochs').value),batch:Number($('batch').value),lr:Number($('lr').value),seed:Number($('seed').value),imgsz:Number($('train-size').value)})}catch(err){error(err.message,'train')}});

let archiving=false;
function updateReviewLabels(v){
  renderReviewReceipt(v);
  const levels=Lab.levelsCopy(v),packaged=Boolean(v?.report?.package),v2=v?.report?.criterion?.version==='disponibilidad_visual_nivel_v2_reponer';
  $('review-title').textContent=levels?'3. Revisar niveles y estados':'3. Dejar los módulos listos';
  $('review-description').textContent=v2?'Criterio v2: reponer bajo el 30% de ocupación, suficiente desde el 30% y no evaluable cuando no se puede decidir. La etapa base aprende reponer y suficiente. La partición se aplica al traer una copia nueva.':packaged?'Seguimiento de la tarea 16 con la guía v1.3 y fotos completas. La aprobación para entrenar requiere revisión del paquete.':levels?'Comprueba los contornos y los estados con el criterio v1: presencia por ancho útil, umbral inicial del 30%. No evaluable no significa vacío.':'Una persona debe comprobar que los límites siguen la estructura y están todos los módulos visibles.';
  $('reviewer-label').textContent=levels?'¿Quién revisó niveles y estados?':'¿Quién revisó los módulos?';
  $('review-checkbox-label').textContent=levels?`Revisé los niveles y estados de esta copia con el criterio ${v2?'v2':'v1'}.`:'Revisé los módulos de esta copia siguiendo la guía de anotación v2.';
  $('review-scope-help').textContent=levels?'IDs, integridad y observación son opcionales. Los estados pendientes y los contornos inválidos deben corregirse antes de entrenar.':'La revisión de módulos no aprueba los niveles.';
}
function renderLevelsDataset(v,blocks,previous,expanded){
  const r=v.report,counts=r.estados||{},split=r.estados_por_split||{},v2=r.criterion?.version==='disponibilidad_visual_nivel_v2_reponer',states=r.trained_states||(v2?['reponer','suficiente','no_evaluable']:['vacio','baja_disponibilidad','suficiente','no_evaluable']);
  $('review-guidance').textContent=r.partition_pending?'Tarea 19: puedes revisar las anotaciones. Falta definir y congelar familias, escenas y particiones antes de aprobar para entrenar.':Lab.readyCopy(v)?'Copia revisada. Puedes usarla para entrenar.':blocks.length?'Corrige en CVAT y trae una copia nueva antes de aprobarla.':'Comprueba contornos y estados en las fotos antes de registrar la revisión.';
  const issues=Lab.groupIssues(blocks).map(g=>`<section class="issue-photo"><h3>${g.photo?'Foto '+esc(g.photo):'Separación de entrenamiento y validación'}</h3>${g.drawings.map(d=>{const source=v.sources.find(s=>s.job_id===d.jobId);return `<div class="issue-drawing"><h4>${d.shapeId!=null?'Dibujo '+esc(d.shapeId):'Revisión del conjunto'}</h4><ol>${d.issues.map(i=>`<li>${esc(Lab.issueAdvice(i,v))}${Lab.issueAdvice(i,v)===i.problema?'':`<details class="issue-technical"><summary>Detalle técnico</summary>${esc(i.problema)}</details>`}</li>`).join('')}</ol>${source&&d.shapeId!=null?`<button type="button" class="secondary" data-drawing-photo="${esc(g.photo)}" data-drawing-id="${esc(d.shapeId)}" data-drawing-job="${source.job_id}" aria-expanded="false">Ver dibujo en la foto</button><div class="drawing-preview" hidden></div><a href="http://localhost:8082/tasks/${source.task_id}/jobs/${source.job_id}" target="_blank" rel="noopener">Abrir trabajo en CVAT</a>`:''}</div>`}).join('')}</section>`).join('');
  setHTML($('dataset-report'),`<p><span class="pill">${esc(Lab.profile(v).label)}</span> <span class="pill">${Lab.readyCopy(v)?'Lista para entrenar niveles y estados':'Pendiente de revisión'}</span></p>${lotCopyStatus(v)}${r.fixed_partition?`<p class="reading-guide"><strong>Etapa base · partición fijada</strong><br>${r.partition_counts.train} imágenes para aprender · ${r.partition_counts.val} reales para validar.<br>${r.partition_counts.diagnostico} variantes para diagnóstico y ${r.partition_counts.reserva} imágenes finales quedan fuera de esta exportación.</p>`:''}<details class="report-group"><summary>Criterio de estados</summary><p><strong>${v2?'Criterio v2 · tarea 19':r.package?'Guía v1.3 · tarea 16':'Criterio v1'}:</strong> ${v2?'Reponer: vacío o menos del 30% de ocupación; suficiente desde el 30%.':'Vacío sin producto visible; baja disponibilidad bajo el 30% del ancho útil; suficiente desde el 30%.'} ${r.stage==='base'?'No evaluable se incorporará en la etapa con obstáculos.':'No evaluable se aprende como salida separada y no genera alerta de stock.'} El porcentaje es una referencia inicial pendiente de calibración.</p></details><div class="table-wrap"><table><thead><tr><th>Estado</th><th>Total</th><th>Aprender</th><th>Validar</th></tr></thead><tbody>${states.map(state=>`<tr><td>${esc(({reponer:'Reponer',vacio:'Vacío',baja_disponibilidad:'Baja disponibilidad',suficiente:'Suficiente',no_evaluable:'No evaluable'})[state]||state.replaceAll('_',' '))}</td><td>${counts[state]||0}</td><td>${r.partition_pending?'—':split.train?.[state]||0}</td><td>${r.partition_pending?'—':split.val?.[state]||0}</td></tr>`).join('')}</tbody></table></div>${r.advertencias?.length?`<details class="report-group"><summary>Balance y observaciones</summary><ul>${r.advertencias.map(w=>`<li>${esc(w)}</li>`).join('')}</ul></details>`:''}${blocks.length?`<p class="issue-summary">${blocks.length} ${blocks.length===1?'observación':'observaciones'} por corregir antes de entrenar.</p>`:''}${blocks.length?`<details id="module-issues" class="report-group"><summary>Observaciones por corregir (${blocks.length})</summary>${issues}</details>`:''}<details class="report-group"><summary>Fotos y partición</summary><div class="table-wrap"><table><thead><tr><th>Foto</th><th>Escena</th><th>Uso</th><th>Niveles</th></tr></thead><tbody>${r.imagenes.map(i=>`<tr><td>${esc(i.imagen)}</td><td>${esc(i.grupo_escena)}</td><td>${({pending:'Pendiente de partición',val:'Validar · real',train:'Aprender',diagnostico:'Diagnóstico IA · excluida',reserva:'Evaluación final · reservada'})[i.split]||i.split}</td><td>${i.niveles}</td></tr>`).join('')}</tbody></table></div></details><details id="copy-provenance" class="report-group"><summary>Procedencia y revisión</summary><p>${esc(copyOrigin(v))}</p><p>${v.review?'Revisado por '+esc(v.review.reviewer):'Pendiente de revisión humana.'}</p></details>`);
  if(previous===v.id)for(const id of expanded){const d=$(id);if(d)d.open=true;}updateAvailability();
}
function renderAvailability(run){
  const element=$('availability-results'),evaluation=run?.development_evaluation,v=evaluation?.metrics||run?.availability?.val;element.hidden=!v;
  if(!v){setHTML(element,'');return;}
  const percent=n=>Number.isFinite(n)?(100*n).toFixed(1)+'%':'No calculable';
  setHTML(element,`<h2>${evaluation?'Evaluación de desarrollo · '+v.fotos+' fotos':'Alertas de validación'}</h2>${evaluation?'<p class="reading-guide"><strong>Conjunto mixto de desarrollo: originales reales y variantes sintéticas.</strong> Este agregado no es evidencia exclusivamente real. Las curvas y mAP conservan la validación original del entrenamiento.</p>':'<p class="field-help">Conjunto: validación original del entrenamiento.</p>'}<p>${v.alertas.acertadas} de ${v.alertas.reales} casos de reposición detectados · ${v.alertas.omitidas} omitidos. Recall ${percent(v.alertas.recall)} · precisión ${percent(v.alertas.precision)} · ${v.alertas.falsas} falsas alertas (${fmt(v.alertas.falsas_por_foto)} por foto).</p><details class="secondary-section"><summary>Detalle por estado y criterios</summary><p class="reading-guide"><strong>Recall:</strong> qué proporción de casos críticos detecta. <strong>Precisión:</strong> qué proporción de sus alertas era correcta. Los estados de reposición son los casos críticos; se interpretan según las clases de cada modelo.</p><div class="table-wrap"><table><thead><tr><th>Estado</th><th>Referencias</th><th>Aciertos</th><th>Precisión</th><th>Recall</th></tr></thead><tbody>${Object.entries(v.por_estado).map(([state,m])=>`<tr><td>${esc(({reponer:'Reponer',vacio:'Vacío',baja_disponibilidad:'Baja disponibilidad',suficiente:'Suficiente',no_evaluable:'No evaluable'})[state]||state.replaceAll('_',' '))}</td><td>${m.referencias}</td><td>${m.aciertos}</td><td>${percent(m.precision)}</td><td>${percent(m.recall)}</td></tr>`).join('')}</tbody></table></div><p class="field-help">${v.alertas.precision==null?'La precisión no se calcula cuando el modelo no predice ninguna alerta. ':''}${v.no_evaluables_predichos} salidas no evaluables. Los niveles críticos no detectados o predichos no evaluables cuentan como alertas omitidas. Localización por IoU ≥ 0.5 y confianza ≥ 0.25. La confianza no es porcentaje de stock.</p></details>${evaluationCases(run)}`);
}
function evaluationCases(run){
  const evaluation=run.development_evaluation,rows=evaluation?.images||run.comparisons?.filter(r=>r.split==='val')||[];
  const model=data.models.find(m=>m.id===evaluation?.model)||(!evaluation?data.models.find(m=>m.run===run.id&&m.id.endsWith('/best.pt')):null);
  if(!rows.length)return '<p class="field-help">No hay detalle por foto para relacionar omisiones y falsas alertas con sus casos.</p>';
  return `<details class="evaluation-cases"><summary>Revisar casos por foto · ${evaluation?'conjunto mixto de desarrollo':'validación original'}</summary><p>Las cifras de alertas y las omisiones de localización se muestran por separado. La reserva final queda fuera de este conjunto.</p><ol>${[...rows].sort((a,b)=>(b.alertas_omitidas||0)+(b.falsas_alertas||0)-(a.alertas_omitidas||0)-(a.falsas_alertas||0)).map(row=>{
    const image=row.sha256?data.images.find(i=>i.sha256===row.sha256&&i.id.split('/').at(-1)===row.imagen):null;
    const origin=row.origen||image?.origin,group=origin==='real'?'original real de desarrollo':origin==='sintetica'||origin==='sintetico'?'variante sintética':'procedencia no desglosada';
    const available=image&&model&&!model.training_images?.includes(image.id);
    return `<li><strong>${esc(row.imagen)}</strong> · ${evaluation?esc(group):'validación original'}<br>${Number.isFinite(row.alertas_omitidas)?`${row.alertas_omitidas} ${row.alertas_omitidas===1?'alerta omitida':'alertas omitidas'} · ${row.falsas_alertas} ${row.falsas_alertas===1?'falsa alerta':'falsas alertas'}`:'Sin detalle de alertas por foto'} · ${row.omitidos??'—'} ${row.omitidos===1?'omisión':'omisiones'} de localización.${available?` <button type="button" class="text-button" data-eval-photo="${esc(image.id)}" data-eval-model="${esc(model.id)}">Abrir esta foto con estos pesos</button>`:' <span class="field-help">Sin correspondencia verificada con una foto disponible para probar.</span>'}</li>`;
  }).join('')}</ol></details>`;
}
function renderDataset(){
  const v=data.datasets.find(i=>i.id===$('dataset-version').value),previous=reportVersion,expanded=new Set([...document.querySelectorAll('#dataset-report details[open]')].map(d=>d.id));reportVersion=v?.id;
  $('copy-review-title').textContent=v?'2. Revisar anotaciones de '+Lab.copiesByLot([v])[0].person:'2. Revisar qué falta';
  $('archive-help').textContent=v?.archive_uses?.length?`Se conserva porque la usan estos ensayos: ${v.archive_uses.map(runName).join(', ')}.`:'Archivar oculta la copia; conserva sus archivos y los dibujos de CVAT.';
  if(!v){updateReviewLabels(null);setHTML($('dataset-report'),'<p class="muted">Trae un trabajo para ver las fotos y las observaciones.</p>');$('review-guidance').textContent='Primero trae las anotaciones del paso 1.';$('preparation-summary').textContent=projectVersion==='v3'?'V3: consulta las dependencias en el inicio. El importador actual no admite este criterio.':'Sin copia importada para revisar.';updateAvailability();return}
  const r=v.report,{blocks,attributes,levels}=Lab.reportGroups(r),count=Lab.issueCounts(blocks);updateReviewLabels(v);$('preparation-summary').textContent=`${r.imagenes.length} fotos · ${copyStatus(v)} · ${blocks.length} bloqueos · ${attributes.length+levels.length} advertencias. La copia conserva las anotaciones de su consulta de CVAT; no se comprueban cambios en vivo.`;if(Lab.levelsCopy(v)){renderLevelsDataset(v,blocks,previous,expanded);return;}
  $('review-guidance').textContent=Lab.readyCopy(v)?'Copia revisada. Puedes usarla para entrenar.':blocks.length?'Corrige en CVAT y trae una copia nueva antes de aprobarla.':'Comprueba que los contornos y todos los módulos visibles estén anotados.';
  function issues(items){return Lab.groupIssues(items).map(group=>`<section class="issue-photo"><h3>Foto ${esc(group.photo)}</h3>${group.drawings.map(d=>{const source=v.sources.find(s=>s.job_id===d.jobId)||(d.jobId==null&&v.sources.length===1?v.sources[0]:null);return `<div class="issue-drawing"><h4>${d.shapeId!=null?'Dibujo '+esc(d.shapeId):'Revisión de la foto'}${d.jobId!=null?' / trabajo '+esc(d.jobId):''}</h4><ol>${d.issues.map(i=>`<li>${esc(Lab.issueAdvice(i,v))}${Lab.issueAdvice(i,v)===i.problema?'':`<details class="issue-technical"><summary>Detalle técnico</summary>${esc(i.problema)}</details>`}</li>`).join('')}</ol>${d.shapeId!=null&&source?`<button type="button" class="secondary" data-drawing-photo="${esc(group.photo)}" data-drawing-id="${esc(d.shapeId)}" data-drawing-job="${esc(source.job_id)}" aria-expanded="false">Ver dibujo en la foto</button><div class="drawing-preview" hidden></div>`:''}${source?.task_id?`<a href="http://localhost:8082/tasks/${encodeURIComponent(source.task_id)}/jobs/${encodeURIComponent(source.job_id)}" target="_blank" rel="noopener">Abrir trabajo ${esc(source.job_id)} en CVAT</a><p class="locate">Busca la foto ${esc(group.photo)}${d.shapeId!=null?' y el dibujo '+esc(d.shapeId):''}.</p>`:'<p class="locate">Abre el trabajo correspondiente en CVAT y busca esta foto y su dibujo.</p>'}</div>`}).join('')}</section>`).join('')}
  const html=`<p><span class="pill">${Lab.readyCopy(v)?'Lista para entrenar módulos':'Pendiente de revisión'}</span></p>${lotCopyStatus(v)}${blocks.length?`<p class="issue-summary">${count.observations} observaciones · ${count.drawings} dibujos · ${count.photos} fotos.</p>`:''}<details class="report-group"><summary>Fotos y partición</summary><div class="table-wrap"><table><thead><tr><th>Foto</th><th>Uso</th><th>Módulos</th><th>Niveles</th></tr></thead><tbody>${r.imagenes.map(i=>`<tr><td>${esc(i.imagen)}</td><td>${i.split==='val'?'Validar el modelo':'Enseñar al modelo'}</td><td>${i.modulos}</td><td>${i.niveles_solo_revision}</td></tr>`).join('')}</tbody></table></div></details>${blocks.length?`<details id="module-issues" class="report-group"><summary>Observaciones por corregir (${count.observations})</summary>${issues(blocks)}</details>`:''}${attributes.length?`<details id="attribute-advice" class="report-group"><summary>Atributos opcionales (${attributes.length})</summary><p class="field-help">No bloquean el entrenamiento. Los contornos requieren revisión humana.</p>${issues(attributes)}</details>`:''}${levels.length?`<details id="level-issues" class="report-group"><summary>Observaciones de niveles (${levels.length})</summary><p class="field-help">La revisión de módulos no aprueba los niveles.</p>${issues(levels)}</details>`:''}<details id="copy-provenance" class="report-group"><summary>Procedencia y revisión</summary><p class="field-help">${esc(copyOrigin(v))}${v.review?'; módulos revisados por '+esc(v.review.reviewer):''}.</p><p class="field-help" style="overflow-wrap:anywhere">Referencia: ${esc(v.id)}</p></details>`;
  setHTML($('dataset-report'),html);if(previous===v.id)for(const id of expanded){const d=$(id);if(d)d.open=true}updateAvailability();
}
$('show-copy-history').addEventListener('change',()=>{renderCopyOptions();$('reviewed').checked=false;renderDataset();renderConnectionStatus()});
$('dataset-report').addEventListener('click',async event=>{
  const button=event.target.closest('[data-drawing-photo]');if(!button)return;
  const holder=button.nextElementSibling,id=$('dataset-version').value;
  if(button.getAttribute('aria-expanded')==='true'){holder.hidden=true;button.setAttribute('aria-expanded','false');return}
  button.disabled=true;button.textContent='Cargando dibujo…';
  try{
    const query=new URLSearchParams({id,photo:button.dataset.drawingPhoto,shape_id:button.dataset.drawingId,job_id:button.dataset.drawingJob});
    const drawing=await api('/api/datasets/drawing?'+query);
    if(!button.isConnected||$('dataset-version').value!==id)return;
    const points=drawing.points,valid=drawing.type==='polygon'&&Array.isArray(points)&&points.length>=6&&points.length%2===0&&points.every(Number.isFinite);
    const outline=valid?Array.from({length:points.length/2},(_,i)=>points[2*i]+','+points[2*i+1]).join(' '):'';
    const cvat=drawing.task_id?`http://localhost:8082/tasks/${encodeURIComponent(drawing.task_id)}/jobs/${encodeURIComponent(drawing.job_id)}${drawing.cvat_frame!=null?'?frame='+encodeURIComponent(drawing.cvat_frame):''}`:null;
    ImageNavigation.release(holder);holder.innerHTML=`<figure><div class="drawing-photo"><img src="${esc(drawing.image_url)}" alt="Foto ${esc(drawing.photo)} de la copia seleccionada">${valid?`<svg viewBox="0 0 ${Number(drawing.width)} ${Number(drawing.height)}" role="img" aria-label="Contorno del dibujo ${esc(drawing.shape_id)} resaltado"><polygon points="${outline}" fill="var(--outline-highlight)" fill-opacity="0.2" stroke="var(--outline-edge)" stroke-width="5" vector-effect="non-scaling-stroke"/><polygon points="${outline}" fill="none" stroke="var(--outline-highlight)" stroke-width="2" vector-effect="non-scaling-stroke"/></svg>`:''}</div><figcaption><strong>${esc(drawing.label)} · dibujo ${esc(drawing.shape_id)}</strong>. ${valid?'Contorno amarillo: dibujo de esta copia.':'Este dibujo no contiene un polígono que se pueda resaltar; revisa su tipo y puntos en CVAT.'}<br>Copia guardada ${esc(localDate(drawing.created_at))}; puede diferir de los últimos cambios en CVAT.</figcaption></figure>${cvat?`<a href="${esc(cvat)}" target="_blank" rel="noopener">${drawing.cvat_frame!=null?'Abrir esta foto en CVAT':'Abrir trabajo en CVAT'}</a>`:''}`;
    holder.hidden=false;ImageNavigation.mount(holder);button.setAttribute('aria-expanded','true');
  }catch(err){error(err.message)}finally{button.disabled=false;button.textContent='Ver dibujo en la foto'}
});
async function manageCopy(action){
  const id=action==='archive'?$('dataset-version').value:$('archived-version').value;
  if(!id||archiving)return;
  const copy=(action==='archive'?data.datasets:data.archived_datasets).find(v=>v.id===id);
  archiving=true;updateAvailability();$('copy-management-status').textContent=action==='archive'?'Archivando copia…':'Recuperando copia…';
  try{
    const result=await api('/api/datasets/'+action,{id});await refresh();
    if(action==='restore'){selectCopy(result.id);$('dataset-version').focus()}
    else{$('archived-version').value=id;$('archived-copies').open=true;$('dataset-version').focus()}
    $('copy-management-status').textContent=(action==='archive'?'Copia archivada: ':'Copia recuperada: ')+(copy?datasetName(copy):id)+'.';
  }catch(err){error(err.message);$('copy-management-status').textContent='No se pudo cambiar esta copia.'}
  finally{archiving=false;updateAvailability()}
}
$('archive-copy').addEventListener('click',()=>manageCopy('archive'));
$('restore-copy').addEventListener('click',()=>manageCopy('restore'));
$('archived-version').addEventListener('change',updateAvailability);
$('import-form').addEventListener('submit',async event=>{
  event.preventDefault();if(importing||sourcesLoading)return;clearOperationError('import');$('message').style.display='none';
  const taskId=Number($('import-task').value),validation=$('validation-ids').value.split(',').map(v=>v.trim()).filter(Boolean);
  if(!Number.isInteger(taskId)||taskId<1){error('Indica el número de la tarea en CVAT.','import');return}
  importing=true;updateAvailability();importFeedback('reading','Leyendo CVAT y comprobando las fotos del lote…');
  let importedCopy=null;
  try{
    const result=await api('/api/datasets/import',{task_id:taskId,validation});importedCopy=result;
    importFeedback('report','Anotaciones recibidas. Actualizando el informe…');
    await refresh();const version=Lab.versionOf(result,fullCatalog);if(version!==projectVersion)selectProjectVersion(version);selectCopy(result.id);
    importFeedback('success',result.import_reused?`Sin cambios: la copia ya está actualizada. Guardada ${localDate(result.created_at)}.`:'Copia guardada. El informe está listo para revisar.');
  }catch(err){error(err.message,'import');importFeedback('error',importedCopy?'Copia guardada. No se pudo actualizar el informe; reintenta la consulta del panel.':'No se pudo completar la consulta. Tus selecciones se conservan.')}
  finally{importing=false;updateAvailability()}
});
$('review-form').addEventListener('submit',async event=>{event.preventDefault();clearOperationError('review');$('review-button').disabled=true;try{const result=await api('/api/datasets/approve',{id:$('dataset-version').value,reviewer:$('reviewer').value,reviewed:$('reviewed').checked});await refresh();$('source').value=result.id;sourceSummary();switchTab('train');saveUiPreferences()}catch(err){error(err.message,'review')}finally{renderDataset()}});

$('decision-form').addEventListener('submit',async event=>{
  event.preventDefault();const runId=$('run').value,button=event.submitter;button.disabled=true;
  try{await api('/api/runs/decision',{run:runId,status:$('decision-status').value,reason:$('decision-reason').value,author:$('decision-author').value});await refresh();$('decision-feedback').textContent=`Decisión guardada para ${shortRunName(runId)}.`}catch(err){$('decision-feedback').textContent=err.message}finally{button.disabled=false}
});
for(const id of ['source','train-model','epochs','batch','train-size','lr','seed','baseline','run'])$(id).addEventListener('change',()=>{renderTrainingPreview();renderWorkspace()});
for(const id of ['dataset-version','model'])$(id).addEventListener('change',renderWorkspace);

for(const [control,description] of [['name','name-help'],['source','train-data-help'],['model','model-help'],['train-model','train-model-help'],['reviewer','review-guidance'],['import-task','import-source-help'],['participant','import-source-help']])$(control).setAttribute('aria-describedby',description);
document.addEventListener('change',event=>{if([...UiPreferences.choices,...UiPreferences.selects,...UiPreferences.numbers,...UiPreferences.texts,'show-copy-history'].includes(event.target.id))saveUiPreferences()});
document.addEventListener('input',event=>{if([...UiPreferences.numbers,...UiPreferences.texts].includes(event.target.id))schedulePreferences()});
window.addEventListener('pagehide',saveUiPreferences);
restoreUiPreferences();
(async()=>{updateImportLabel();renderConnectionStatus();updateAvailability();try{await refresh();renderOriginal();modelHelp();renderGlossary();jobs=await api('/api/jobs');connection.activityKnown=true;jobs.filter(job=>job.state!=='running').forEach(job=>seen.add(job.id));await poll()}catch(err){if(connection.phase==='ready'){connection.activityKnown=false;connection.activityError='No pudimos consultar la actividad. '+err.message}renderConnectionStatus();updateAvailability()}finally{schedulePoll()}})();
