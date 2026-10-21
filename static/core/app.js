/* No personal data or drafts are stored in the browser. */
(() => {
 document.querySelectorAll('label:not([for])').forEach((label,index)=>{let input=label.nextElementSibling;if(input&&input.matches('input,select,textarea')){if(!input.id)input.id='field-'+index;label.htmlFor=input.id;}});
 document.querySelectorAll('[data-progress-select]').forEach(select=>{const paint=()=>{select.dataset.progress=select.value;};paint();select.addEventListener('change',paint);});
 let dirty=false, submitting=false;
 const retained=document.getElementById('retained-draft');
 if(retained){const values=JSON.parse(retained.textContent);document.querySelectorAll('form[data-dirty]').forEach(form=>{for(const [key,value] of Object.entries(values)){const field=form.elements.namedItem(key);if(!field||key==='csrfmiddlewaretoken')continue;if(field.type==='checkbox')field.checked=!!value;else {field.value=value;if(field.hasAttribute('data-progress-select'))field.dataset.progress=value;}} });dirty=Object.keys(values).length>0;}
 document.querySelectorAll('form[data-dirty]').forEach(form => {
  form.addEventListener('input',()=>{dirty=true;document.querySelectorAll('[data-save-state]').forEach(n=>{n.textContent='● Cambios pendientes de guardar';n.classList.add('pink');});});
  form.addEventListener('submit',()=>{submitting=true;});
 });
 window.addEventListener('beforeunload',event=>{if(dirty&&!submitting){event.preventDefault();event.returnValue='';}});
 function network(){document.querySelectorAll('[data-save-state]').forEach(n=>{if(!navigator.onLine)n.textContent='Sin conexión. Mantén esta página abierta y guarda al reconectar.';});}
 window.addEventListener('offline',network); window.addEventListener('online',()=>{document.querySelectorAll('[data-save-state]').forEach(n=>n.textContent=dirty?'Conexión recuperada. Guarda los cambios.':'Sin cambios pendientes');});
})();
