(function(){
  'use strict';
  var sec=document.getElementById('reviews'); if(!sec) return;
  var slug=sec.getAttribute('data-slug'), $=function(id){return document.getElementById(id);};
  function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e;}
  function stars(n){return '★★★★★'.slice(0,n)+'☆☆☆☆☆'.slice(0,5-n);}
  function fmt(d){var p=d.split('-');return new Date(+p[0],+p[1]-1,+p[2]).toLocaleDateString('en-CA',{year:'numeric',month:'long',day:'numeric'});}
  fetch('/api/reviews.php?slug='+encodeURIComponent(slug),{cache:'no-cache'}).then(function(r){return r.json();}).then(function(j){
    var list=$('rv-list'), sum=$('rv-summary'), rs=j.reviews||[];
    if(!rs.length){sum.textContent='No reviews yet. Be the first to share how it worked in your garden.';return;}
    var avg=rs.reduce(function(a,r){return a+r.rating;},0)/rs.length;
    sum.textContent=''; sum.appendChild(el('span','rv-stars',stars(Math.round(avg)))); sum.appendChild(document.createTextNode(' '+avg.toFixed(1)+' out of 5 from '+rs.length+' review'+(rs.length>1?'s':'')));
    rs.forEach(function(r){
      var d=el('article','rv'); var h=el('div','rv-h'); h.appendChild(el('span','rv-stars',stars(r.rating))); if(r.title) h.appendChild(el('strong',null,r.title)); d.appendChild(h);
      d.appendChild(el('p',null,r.text)); d.appendChild(el('p','rv-by',r.name+' · '+fmt(r.date))); list.appendChild(d);
    });
  }).catch(function(){});
  var open=$('rv-open'), form=$('rv-form'), msg=$('rv-msg');
  open.addEventListener('click',function(){form.hidden=!form.hidden;if(!form.hidden)$('rv-name').focus();});
  form.addEventListener('submit',function(e){
    e.preventDefault(); msg.className='rv-msg'; msg.textContent='';
    var rating=(form.querySelector('input[name=rating]:checked')||{}).value;
    var btn=form.querySelector('button[type=submit]'); btn.disabled=true;
    fetch('/api/reviews.php',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({slug:slug,name:$('rv-name').value,rating:rating,title:$('rv-title').value,text:$('rv-text').value,email:$('rv-email').value,website:$('rv-hp').value})})
    .then(function(r){return r.json().then(function(j){if(!r.ok)throw new Error(j.error||'Something went wrong.');return j;});})
    .then(function(){form.reset();form.hidden=true;open.hidden=true;msg.className='rv-msg ok';msg.textContent='Thank you! Your review will appear once we have checked it.';})
    .catch(function(er){msg.className='rv-msg err';msg.textContent=er.message==='Failed to fetch'?'Could not connect. Please try again.':er.message;btn.disabled=false;});
  });
})();
