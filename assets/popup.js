(function(){
  'use strict';
  if(/^\/(cart|order-complete|admin|wholesale)\//.test(location.pathname)) return;
  var KEY='mss_pop_v1';
  var force=/[?&]popup=1\b/.test(location.search);
  try{if(!force&&parseInt(localStorage.getItem(KEY)||'0',10)>Date.now()) return;}catch(e){}
  var shown=false, prev=null;
  function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e;}
  function remember(days){try{localStorage.setItem(KEY,String(Date.now()+days*86400000));}catch(e){}}

  function open(){
    if(shown) return; shown=true; prev=document.activeElement;
    var back=el('div','pop-back'), box=el('div','pop'); box.setAttribute('role','dialog'); box.setAttribute('aria-modal','true'); box.setAttribute('aria-labelledby','pop-h');
    var x=el('button','pop-x','×'); x.type='button'; x.setAttribute('aria-label','Close');
    var h=el('h2',null,'Stay in the grow'); h.id='pop-h';
    var p=el('p',null,'Get restock reminders, planting tips and sale alerts from Mario’s Super Soil. No spam, and you can unsubscribe any time.');
    var f=el('form','pop-form'); f.noValidate=true;
    var lab=el('label','sr','Email address'); lab.htmlFor='pop-email';
    var em=el('input'); em.type='email'; em.id='pop-email'; em.placeholder='you@example.com'; em.autocomplete='email'; em.required=true; em.maxLength=120;
    var hp=el('input'); hp.type='text'; hp.name='website'; hp.tabIndex=-1; hp.autocomplete='off'; hp.setAttribute('aria-hidden','true'); hp.className='pop-hp';
    var go=el('button','btn solid','Sign me up'); go.type='submit';
    var msg=el('p','pop-msg'); msg.setAttribute('role','status');
    f.appendChild(lab); f.appendChild(em); f.appendChild(hp); f.appendChild(go);
    var no=el('button','pop-no','No thanks'); no.type='button';
    box.appendChild(x); box.appendChild(h); box.appendChild(p); box.appendChild(f); box.appendChild(msg); box.appendChild(no);
    back.appendChild(box); document.body.appendChild(back); em.focus();
    function close(days){remember(days);back.remove();document.removeEventListener('keydown',key);if(prev&&prev.focus)try{prev.focus();}catch(e){}}
    function key(e){
      if(e.key==='Escape'){close(7);return;}
      if(e.key==='Tab'){var els=box.querySelectorAll('button,input:not(.pop-hp)'),a=els[0],z=els[els.length-1];
        if(e.shiftKey&&document.activeElement===a){e.preventDefault();z.focus();}else if(!e.shiftKey&&document.activeElement===z){e.preventDefault();a.focus();}}
    }
    document.addEventListener('keydown',key);
    x.addEventListener('click',function(){close(7);}); no.addEventListener('click',function(){close(7);});
    back.addEventListener('click',function(e){if(e.target===back)close(7);});
    f.addEventListener('submit',function(e){
      e.preventDefault(); msg.className='pop-msg'; msg.textContent='';
      if(!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(em.value.trim())){msg.className='pop-msg err';msg.textContent='Please enter a valid email address.';em.focus();return;}
      go.disabled=true;
      fetch('/api/subscribe.php',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:em.value.trim(),website:hp.value})})
      .then(function(r){return r.json().then(function(j){if(!r.ok)throw new Error(j.error||'Something went wrong.');return j;});})
      .then(function(){remember(365);f.remove();no.remove();msg.textContent='Thanks! You are on the list.';setTimeout(function(){close(365);},2200);})
      .catch(function(er){go.disabled=false;msg.className='pop-msg err';msg.textContent=er.message==='Failed to fetch'?'Could not connect. Please try again.':er.message;});
    });
  }
  setTimeout(open,force?1500:12000);
  document.addEventListener('mouseout',function(e){if(!e.relatedTarget&&e.clientY<=0&&window.innerWidth>900&&document.visibilityState==='visible')setTimeout(open,0);});
})();
