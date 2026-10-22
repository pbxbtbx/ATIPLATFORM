/* Un formulario pendiente pertenece a esta página: no persiste textos en cookies ni almacenamiento. */
(() => {
 const messagesNode=document.getElementById('browser-messages');
 const messages=messagesNode?JSON.parse(messagesNode.textContent):{};
 const dirtyForms=new Set();let submitting=false;
 const alert=document.getElementById('unsaved-alert');
 const update=()=>{
  const dirty=dirtyForms.size>0;
  if(alert)alert.hidden=!dirty;
  document.querySelectorAll('[data-unsaved-item]').forEach(node=>node.hidden=!dirty);
  document.querySelectorAll('[data-notification-count]').forEach(node=>{const count=Number(node.dataset.reminders||0)+(dirty?1:0);node.textContent=count;node.hidden=count===0;});
  document.querySelectorAll('[data-save-state]').forEach(node=>{node.textContent=!navigator.onLine?messages.offline:dirty?messages.unsaved:messages.saved;node.classList.toggle('has-unsaved',dirty);});
  const text=document.querySelector('[data-draft-message]');if(text)text.textContent=!navigator.onLine?messages.offline:messages.unsavedDetails;
 };
 const review=()=>{const form=dirtyForms.values().next().value;if(!form)return;form.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});const field=form.querySelector('input:not([type=hidden]):not([disabled]),textarea:not([disabled]),select:not([disabled])');if(field)field.focus({preventScroll:true});const tray=document.getElementById('notification-tray');if(tray)tray.open=false;};
 document.querySelectorAll('form[data-dirty]').forEach(form=>{
  const initial=new FormData(form);
  const changed=()=>{const current=new FormData(form);const names=new Set([...initial.keys(),...current.keys()]);return [...names].some(name=>{const a=initial.getAll(name),b=current.getAll(name);return a.length!==b.length||a.some((value,index)=>value instanceof File?!(b[index] instanceof File)||value.name!==b[index].name||value.size!==b[index].size:value!==b[index]);});};
  const check=()=>{if(changed()||form.dataset.restored==='true'||form.dataset.hasErrors==='true')dirtyForms.add(form);else dirtyForms.delete(form);update();};
  form.addEventListener('input',check);form.addEventListener('change',check);
  form.addEventListener('submit',()=>{submitting=true;});
  if(form.dataset.restored==='true'||form.dataset.hasErrors==='true')dirtyForms.add(form);
 });
 document.querySelectorAll('[data-review-draft]').forEach(button=>button.addEventListener('click',review));
 document.addEventListener('appearance-reset',()=>{const form=document.getElementById('appearance-form');if(form)dirtyForms.delete(form);update();});
 document.querySelectorAll('[data-language-form]').forEach(form=>form.addEventListener('submit',event=>{if(dirtyForms.size){event.preventDefault();update();review();}}));
 window.addEventListener('beforeunload',event=>{if(dirtyForms.size&&!submitting){event.preventDefault();event.returnValue='';}});
 window.addEventListener('offline',update);window.addEventListener('online',update);update();
})();
