(function(){
  'use strict';
  var f=document.getElementById('ws-form'); if(!f) return;
  var msg=document.getElementById('ws-msg'), $=function(n){return f.elements[n].value;};
  f.addEventListener('submit',function(e){
    e.preventDefault(); msg.className='ws-msg'; msg.textContent='';
    var btn=f.querySelector('button[type=submit]'); btn.disabled=true;
    fetch('/api/wholesale.php',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({business:$('business'),contact:$('contact'),email:$('email'),phone:$('phone'),city:$('city'),type:$('type'),volume:$('volume'),site:$('site'),message:$('message'),website:$('website')})})
    .then(function(r){return r.json().then(function(j){if(!r.ok)throw new Error(j.error||'Something went wrong.');return j;});})
    .then(function(){f.hidden=true;msg.className='ws-msg ok';msg.textContent='Thank you! We have your application and will be in touch by email or phone.';})
    .catch(function(er){msg.className='ws-msg err';msg.textContent=er.message==='Failed to fetch'?'Could not connect. Please try again.':er.message;btn.disabled=false;});
  });
})();
