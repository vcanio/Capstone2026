const UiPreferences=(()=>{
  const key='walmart-modelos-ui-v1';
  const choices=['project-version','import-project','participant','dataset-version','source','train-model','model','image','run','baseline','comparison-photo','monitor-job'];
  const selects=['train-size','predict-size','chart-metric','split','analysis-method'];
  const numbers=['epochs','batch','lr','seed','conf','nms','import-task'];
  const texts=['name','validation-ids','purpose'];
  const views=['version','datasets','train','results','predict','glossary'];
  function sanitize(value){
    if(!value||typeof value!=='object'||value.version!==1)return {version:1,fields:{},sources:[]};
    const fields={};
    for(const id of [...choices,...selects,...numbers,...texts])if(typeof value.fields?.[id]==='string'&&value.fields[id].length<=1000)fields[id]=value.fields[id];
    for(const id of ['show-copy-history','show-model-history-predict','show-model-history-train'])if(typeof value.fields?.[id]==='boolean')fields[id]=value.fields[id];
    const sources=Array.isArray(value.sources)?value.sources.slice(0,100).filter(s=>s&&typeof s.id==='string'&&/^task:[1-9][0-9]*$/.test(s.id)&&typeof s.name==='string'&&Array.isArray(s.jobs)&&s.jobs.length&&s.jobs.every(j=>Number.isInteger(j)&&j>0)&&Array.isArray(s.image_ids)&&s.image_ids.every(i=>typeof i==='string')).map(s=>({id:s.id,task_id:Number(s.id.slice(5)),project_id:Number.isInteger(s.project_id)?s.project_id:(s.scope==='Nivel_estados'?6:4),project_name:typeof s.project_name==='string'?s.project_name:'',name:s.name,completed_jobs:Number.isInteger(s.completed_jobs)?s.completed_jobs:0,excluded_image_ids:Array.isArray(s.excluded_image_ids)?s.excluded_image_ids.filter(i=>typeof i==='string'):[],group:typeof s.group==='string'?s.group:'',jobs:s.jobs,image_ids:s.image_ids,scope:s.scope,fixed_validation:s.fixed_validation===true,pending_partition:s.pending_partition===true,validation_note:typeof s.validation_note==='string'?s.validation_note:'',criterion_version:typeof s.criterion_version==='string'?s.criterion_version:'',validation_ids:Array.isArray(s.validation_ids)?s.validation_ids.filter(i=>typeof i==='string'):[]})):[];
    return {version:1,fields,sources,view:views.includes(value.view)?value.view:'version',sourcesUpdated:typeof value.sourcesUpdated==='string'?value.sourcesUpdated:''};
  }
  function read(storage){try{return sanitize(JSON.parse(storage.getItem(key)))}catch{return sanitize(null)}}
  function write(storage,value){try{storage.setItem(key,JSON.stringify(sanitize(value)));return true}catch{return false}}
  return {key,choices,selects,numbers,texts,views,sanitize,read,write};
})();
