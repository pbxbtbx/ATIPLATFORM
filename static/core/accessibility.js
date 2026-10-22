/* Ayudas estáticas y bajo demanda: nunca lee valores, nombres ni notas del DOM. */
(() => {
 const settingsNode=document.getElementById('accessibility-settings'),messagesNode=document.getElementById('audio-messages');
 if(!settingsNode||!messagesNode)return;
 const settings=JSON.parse(settingsNode.textContent),messages=JSON.parse(messagesNode.textContent);
 const triggers=document.querySelectorAll('[data-speech-page],[data-speech-sample],[data-speak]');
 const controls=document.querySelectorAll('[data-audio-toolbar] button');
 const output=document.querySelector('[data-speech-status]');
 const status=text=>{if(output)output.textContent=text;};
 if(!settings.audio){triggers.forEach(button=>button.hidden=true);return;}
 const synth=window.speechSynthesis;
 if(!synth||!window.SpeechSynthesisUtterance){status(messages.unsupported);[...triggers,...controls].forEach(button=>button.disabled=true);return;}
 const language=document.documentElement.lang.split('-')[0];
 let voice=null;
 const refresh=()=>{
  voice=synth.getVoices().find(v=>v.localService===true&&v.lang.toLowerCase().split(/[-_]/)[0]===language)||null;
  [...triggers,...controls].forEach(button=>button.disabled=!voice);
  status(voice?messages.ready:messages.unavailable);
 };
 refresh();synth.addEventListener('voiceschanged',refresh);
 const speak=text=>{
  if(!voice){status(messages.unavailable);return;}
  synth.cancel();const utterance=new SpeechSynthesisUtterance(text);
  utterance.voice=voice;utterance.lang=voice.lang;utterance.rate=Number(settings.speech_rate);
  utterance.onstart=()=>status(messages.speaking);utterance.onend=()=>status(messages.finished);
  utterance.onerror=()=>status(messages.stopped);synth.speak(utterance);
 };
 document.querySelectorAll('[data-speech-page]').forEach(button=>button.addEventListener('click',()=>speak(messages.pageHelp)));
 document.querySelectorAll('[data-speech-sample]').forEach(button=>button.addEventListener('click',()=>speak(messages.sample)));
 document.querySelectorAll('[data-speak]').forEach(button=>button.addEventListener('click',()=>speak(button.dataset.speak)));
 document.querySelectorAll('[data-speech-pause]').forEach(button=>button.addEventListener('click',()=>{synth.pause();status(messages.paused);}));
 document.querySelectorAll('[data-speech-resume]').forEach(button=>button.addEventListener('click',()=>{synth.resume();status(messages.speaking);}));
 document.querySelectorAll('[data-speech-stop]').forEach(button=>button.addEventListener('click',()=>{synth.cancel();status(messages.stopped);}));
 document.addEventListener('keydown',event=>{if(event.key==='Escape'){synth.cancel();status(messages.stopped);}});
 window.addEventListener('pagehide',()=>synth.cancel());
})();
