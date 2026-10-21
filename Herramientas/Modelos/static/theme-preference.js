(()=>{
  const key='walmart-modelos-tema',root=document.documentElement;
  const stored=()=>{try{const t=localStorage.getItem(key);return t==='dark'||t==='light'?t:null}catch{return null}};
  const system=window.matchMedia?window.matchMedia('(prefers-color-scheme: dark)'):null;
  root.dataset.theme=stored()||(system&&system.matches?'dark':'light');
  document.addEventListener('DOMContentLoaded',()=>{
    const button=document.getElementById('theme-toggle');if(!button)return;
    const sync=()=>{const dark=root.dataset.theme==='dark';button.setAttribute('aria-pressed',String(dark));button.title=dark?'Cambiar a modo claro':'Cambiar a modo oscuro'};
    button.addEventListener('click',()=>{root.dataset.theme=root.dataset.theme==='dark'?'light':'dark';try{localStorage.setItem(key,root.dataset.theme)}catch{}sync()});
    if(system&&system.addEventListener)system.addEventListener('change',e=>{if(!stored()){root.dataset.theme=e.matches?'dark':'light';sync()}});
    sync();
  });
})();
