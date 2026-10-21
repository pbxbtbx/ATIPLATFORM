/* No personal data or drafts are stored in the browser. */
(() => {
 document.querySelectorAll('label:not([for])').forEach((label,index)=>{let input=label.nextElementSibling;if(input&&input.matches('input,select,textarea')){if(!input.id)input.id='field-'+index;label.htmlFor=input.id;}});
 const rarityNode=document.getElementById('learning-rarity-map');
 const rarityMap=rarityNode?JSON.parse(rarityNode.textContent):{};
 const paintProgress=select=>{select.dataset.progress=select.value;select.dataset.rarity=rarityMap[select.value]||'common';};
 document.querySelectorAll('[data-progress-select]').forEach(select=>{paintProgress(select);select.addEventListener('change',()=>paintProgress(select));});
 let dirty=false, submitting=false;
 const retained=document.getElementById('retained-draft');
 if(retained){const values=JSON.parse(retained.textContent);document.querySelectorAll('form[data-dirty]').forEach(form=>{for(const [key,value] of Object.entries(values)){const field=form.elements.namedItem(key);if(!field||key==='csrfmiddlewaretoken')continue;if(field.type==='checkbox')field.checked=!!value;else {field.value=value;if(field.hasAttribute('data-progress-select'))paintProgress(field);}} });dirty=Object.keys(values).length>0;}
 document.querySelectorAll('form[data-dirty]').forEach(form => {
  form.addEventListener('input',()=>{dirty=true;document.querySelectorAll('[data-save-state]').forEach(n=>{n.textContent='● Cambios pendientes de guardar';n.classList.add('pink');});});
  form.addEventListener('submit',()=>{submitting=true;});
 });
 document.addEventListener('appearance-reset',()=>{dirty=false;document.querySelectorAll('[data-save-state]').forEach(n=>{n.textContent='Estilo guardado en tu cuenta';n.classList.remove('pink');});});
 window.addEventListener('beforeunload',event=>{if(dirty&&!submitting){event.preventDefault();event.returnValue='';}});
 function network(){document.querySelectorAll('[data-save-state]').forEach(n=>{if(!navigator.onLine)n.textContent='Sin conexión. Mantén esta página abierta y guarda al reconectar.';});}
 window.addEventListener('offline',network); window.addEventListener('online',()=>{document.querySelectorAll('[data-save-state]').forEach(n=>n.textContent=dirty?'Conexión recuperada. Guarda los cambios.':'Sin cambios pendientes');});
})();

/* Vista previa de apariencia: temporal hasta que el formulario se guarde en servidor. */
(() => {
 const form=document.getElementById('appearance-form');
 if(!form)return;
 const original=document.body.className;
 const originalValue=form.dataset.savedTheme||'rpg';
 const apply=value=>{document.body.classList.remove('theme-rpg','theme-classic','theme-night');document.body.classList.add('theme-'+value);};
 form.querySelectorAll('input[name="theme"]').forEach(input=>input.addEventListener('change',()=>apply(input.value)));
 document.getElementById('reset-theme').addEventListener('click',()=>{document.body.className=original;form.querySelectorAll('input[name="theme"]').forEach(input=>input.checked=input.value===originalValue);document.dispatchEvent(new Event('appearance-reset'));});
})();
