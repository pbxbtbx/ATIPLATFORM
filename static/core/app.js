/* Ayudas de interfaz: no guarda datos del alumnado en el navegador. */
(() => {
 document.querySelectorAll('label:not([for])').forEach((label,index)=>{const input=label.nextElementSibling;if(input&&input.matches('input,select,textarea')){if(!input.id)input.id='field-'+index;label.htmlFor=input.id;}});
 const rarityNode=document.getElementById('learning-rarity-map');
 const rarityMap=rarityNode?JSON.parse(rarityNode.textContent):{};
 const paintProgress=select=>{select.dataset.rarity=rarityMap[select.value]||'common';};
 document.querySelectorAll('[data-progress-select]').forEach(select=>{paintProgress(select);select.addEventListener('change',()=>paintProgress(select));});
 const retained=document.getElementById('retained-draft');
 if(retained){const values=JSON.parse(retained.textContent);document.querySelectorAll('form[data-dirty]').forEach(form=>{for(const [key,value] of Object.entries(values)){if(Array.isArray(value)){Array.from(form.elements).filter(f=>f.name===key).forEach(f=>f.checked=value.includes(f.value));continue;}const field=form.elements.namedItem(key);if(!field||key==='csrfmiddlewaretoken')continue;if(field.type==='checkbox')field.checked=!!value;else{field.value=value;if(field.hasAttribute('data-progress-select'))paintProgress(field);}}if(Object.keys(values).length)form.dataset.restored='true';});}
 const form=document.getElementById('appearance-form');
 if(!form)return;
 const original=document.body.className,originalValue=form.dataset.savedTheme||'rpg';
 const apply=value=>{document.body.classList.remove('theme-rpg','theme-classic','theme-night');document.body.classList.add('theme-'+value);};
 const palette=form.elements.learning_palette, savedPalette=palette.value;
 palette.addEventListener('change',()=>{document.body.classList.remove('learning-palette-rpg','learning-palette-basic');document.body.classList.add('learning-palette-'+palette.value);});
 form.querySelectorAll('input[name="theme"]').forEach(input=>input.addEventListener('change',()=>apply(input.value)));
 document.getElementById('reset-theme').addEventListener('click',()=>{document.body.className=original;palette.value=savedPalette;form.querySelectorAll('input[name="theme"]').forEach(input=>input.checked=input.value===originalValue);document.dispatchEvent(new Event('appearance-reset'));});
})();
