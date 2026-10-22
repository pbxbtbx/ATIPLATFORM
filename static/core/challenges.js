/* Vista previa local de casillas; solo Guardar envía datos al servidor. */
(() => {
 document.querySelectorAll('[data-challenge-total]').forEach(list => {
  const row=list.closest('.student-record'),total=Number(list.dataset.challengeTotal);
  const sync=()=>{
   const count=list.querySelectorAll('input[type="checkbox"]:checked').length;
   const tier=count===total?'legendary':count>=Math.ceil(total*.75)?'epic':count>=Math.ceil(total*.5)?'rare':count>=Math.ceil(total*.25)?'uncommon':'common';
   row.querySelectorAll('[data-challenge-count]').forEach(node=>node.textContent=count);
   const badge=row.querySelector('[data-challenge-badge]');
   if(badge){badge.classList.remove('rarity-common','rarity-uncommon','rarity-rare','rarity-epic','rarity-legendary');badge.classList.add('rarity-'+tier);}
   const label=row.querySelector('[data-challenge-legendary]');if(label)label.hidden=tier!=='legendary';
  };
  list.addEventListener('change',sync);sync();
 });
})();
