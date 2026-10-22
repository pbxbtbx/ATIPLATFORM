(() => {
 const tray=document.getElementById('notification-tray');if(!tray)return;
 const position=()=>{if(tray.open){const bottom=tray.querySelector('summary').getBoundingClientRect().bottom;tray.style.setProperty('--tray-top',Math.min(bottom+10,window.innerHeight-120)+'px');}};
 tray.addEventListener('toggle',position);window.addEventListener('resize',position);
 document.addEventListener('click',event=>{if(tray.open&&!tray.contains(event.target))tray.open=false;});
 document.addEventListener('keydown',event=>{if(event.key==='Escape'&&tray.open){tray.open=false;tray.querySelector('summary').focus();}});
})();
