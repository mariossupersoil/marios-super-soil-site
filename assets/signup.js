(function(){
  'use strict';
  var f=document.getElementById('sigform'); if(!f) return;
  var em=document.getElementById('sig-email'), hp=document.getElementById('sig-hp'), msg=document.getElementById('sig-msg'), go=f.querySelector('button[type=submit]');
  function remember(){try{localStorage.setItem('mss_pop_v1',String(Date.now()+365*86400000));}catch(e){}}
  f.addEventListener('submit',function(e){
    e.preventDefault(); msg.className='pop-msg'; msg.textContent='';
    if(!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(em.value.trim())){msg.className='pop-msg err';msg.textContent='Please enter a valid email address.';em.focus();return;}
    go.disabled=true;
    fetch('/api/subscribe.php',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:em.value.trim(),website:hp.value})})
    .then(function(r){return r.json().then(function(j){if(!r.ok)throw new Error(j.error||'Something went wrong.');return j;});})
    .then(function(){remember();f.style.display='none';msg.textContent='Thanks! You are on the list.';})
    .catch(function(er){go.disabled=false;msg.className='pop-msg err';msg.textContent=er.message==='Failed to fetch'?'Could not connect. Please try again.':er.message;});
  });
})();
