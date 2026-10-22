/* Filtra la revisión visual; el servidor valida siempre las selecciones. */
(() => {
 const form=document.querySelector('[data-ods-form]');if(!form)return;
 const sync=()=>{
  const selected=new Set(Array.from(form.querySelectorAll('[name="sheets"]:checked'),field=>field.value));
  form.querySelectorAll('[data-ods-sheet]').forEach(sheet=>{sheet.hidden=Number(sheet.dataset.odsRowCount)>0&&!selected.has(sheet.dataset.odsSheet);});
  form.querySelectorAll('[data-ods-row]').forEach(row=>{
   const destination=form.elements.namedItem('group_'+row.dataset.group);
   row.hidden=!selected.has(row.dataset.sheet)||!destination||!destination.value;
  });
 };
 form.addEventListener('change',event=>{if(event.target.name==='sheets'||event.target.name.startsWith('group_'))sync();});
 sync();
})();
