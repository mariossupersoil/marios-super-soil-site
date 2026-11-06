(function(){
  'use strict';
  var KEY='mss_cart_v1', PRICES=null, $=function(id){return document.getElementById(id);};

  function load(){try{var a=JSON.parse(localStorage.getItem(KEY)||'[]');return Array.isArray(a)?a:[];}catch(e){return mem;}}
  var mem=[];
  function save(a){mem=a;try{localStorage.setItem(KEY,JSON.stringify(a));}catch(e){}}
  function count(){return load().reduce(function(n,i){return n+(i.qty||0);},0);}
  function badge(){var n=$('cart-n');if(n){var c=count();n.textContent=c;n.classList.toggle('on',c>0);}}
  function money(v){return new Intl.NumberFormat('en-CA',{style:'currency',currency:'CAD'}).format(v);}
  function prices(){
    if(PRICES) return Promise.resolve(PRICES);
    return fetch('/api/prices.json',{cache:'no-cache'}).then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(j){PRICES=j.products||{};return PRICES;});
  }
  function find(slug,size){var P=PRICES&&PRICES[slug];return P&&P.sizes&&P.sizes[size]?{p:P,s:P.sizes[size]}:null;}
  function valid(p){return typeof p==='number'&&p>0;}
  function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e;}

  // ---- product page buy box
  var box=$('buy-box');
  if(box){
    var slug=box.getAttribute('data-slug'), sel=$('buy-size'), qty=$('buy-qty'), pr=$('buy-price'), add=$('buy-add'), msg=$('buy-msg');
    var update=function(){
      var f=find(slug,sel.value), ok=f&&valid(f.s.price);
      pr.textContent=ok?money(f.s.price):(f?'Price coming soon':'');
      add.disabled=!ok; msg.textContent='';
    };
    prices().then(function(){
      Array.prototype.forEach.call(sel.options,function(o){var f=find(slug,o.value);if(f&&valid(f.s.price))o.textContent=f.s.label+' — '+money(f.s.price);});
      update();
    }).catch(function(){pr.textContent='Prices are unavailable right now.';add.disabled=true;});
    add.disabled=true;
    sel.addEventListener('change',update);
    add.addEventListener('click',function(){
      var q=Math.max(1,Math.min(20,parseInt(qty.value,10)||1)), c=load(), hit=null;
      c.forEach(function(i){if(i.slug===slug&&i.size===sel.value)hit=i;});
      if(hit)hit.qty=Math.min(20,hit.qty+q);else c.push({slug:slug,size:sel.value,qty:q});
      save(c);badge();
      msg.textContent='';
      msg.appendChild(document.createTextNode('Added to your cart. '));
      var a=el('a',null,'View cart'); a.href='/cart/'; msg.appendChild(a);
    });
  }

  // ---- cart page
  var root=$('cart-root');
  function renderCart(){
    var c=load().filter(function(i){return find(i.slug,i.size);});
    if(c.length!==load().length) save(c);
    root.innerHTML='';
    if(!c.length){
      root.appendChild(el('p','lede','Your cart is empty.'));
      var a=el('a','btn solid','Shop products'); a.href='/#products'; var w=el('p'); w.style.marginTop='20px'; w.appendChild(a); root.appendChild(w); badge(); return;
    }
    var list=el('ul','cartlist'), total=0, missing=false;
    c.forEach(function(i,idx){
      var f=find(i.slug,i.size), pr=f.s.price, li=el('li','cartrow');
      var im=el('img'); im.src=f.p.img; im.alt=''; im.width=64; im.height=94; li.appendChild(im);
      var mid=el('div','cartinfo'); mid.appendChild(el('strong',null,f.p.name)); mid.appendChild(el('span',null,f.s.label));
      if(!valid(pr)){missing=true;mid.appendChild(el('span','cartwarn','No price yet. Remove this item to check out.'));}
      li.appendChild(mid);
      var q=el('div','cartqty'), lab=el('label',null,'Qty'); lab.className='sr'; lab.htmlFor='q'+idx;
      var inp=el('input'); inp.type='number'; inp.min=1; inp.max=20; inp.value=i.qty; inp.id='q'+idx; inp.setAttribute('inputmode','numeric');
      inp.addEventListener('change',function(){var all=load();var n=Math.max(1,Math.min(20,parseInt(inp.value,10)||1));all.forEach(function(x){if(x.slug===i.slug&&x.size===i.size)x.qty=n;});save(all);renderCart();});
      q.appendChild(lab); q.appendChild(inp); li.appendChild(q);
      var lt=el('div','cartline',valid(pr)?money(pr*i.qty):'-'); li.appendChild(lt);
      var rm=el('button','cartrm','Remove'); rm.type='button'; rm.setAttribute('aria-label','Remove '+f.p.name+' '+f.s.label);
      rm.addEventListener('click',function(){save(load().filter(function(x){return !(x.slug===i.slug&&x.size===i.size);}));renderCart();});
      li.appendChild(rm); list.appendChild(li);
      if(valid(pr)) total+=pr*i.qty;
    });
    root.appendChild(list);
    var sum=el('div','carttotal'); sum.appendChild(el('span',null,'Subtotal')); sum.appendChild(el('strong',null,money(total))); root.appendChild(sum);
    root.appendChild(el('p','lede','Shipping and tax are added at checkout.'));
    var err=el('div','cartmsg'); err.setAttribute('role','alert');
    var go=el('button','btn solid','Checkout'); go.type='button'; go.disabled=missing;
    go.addEventListener('click',function(){
      go.disabled=true; err.textContent=''; go.textContent='Opening secure checkout...';
      fetch('/api/checkout.php',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({items:load().map(function(i){return{slug:i.slug,size:i.size,qty:i.qty};})})})
      .then(function(r){return r.text().then(function(t){var j=null;try{j=JSON.parse(t);}catch(e){}if(!r.ok||!j||!j.url)throw new Error((j&&j.error)||'Could not start checkout. Please try again.');return j;});})
      .then(function(j){window.location.href=j.url;})
      .catch(function(e){go.disabled=missing;go.textContent='Checkout';err.textContent=e.message==='Failed to fetch'?'Could not connect. Check your internet and try again.':e.message;});
    });
    var w2=el('p'); w2.style.marginTop='18px'; w2.appendChild(go); root.appendChild(w2); root.appendChild(err);
    var more=el('p','lede'); more.style.marginTop='18px'; var ml=el('a',null,'Keep shopping'); ml.href='/#products'; more.appendChild(ml); root.appendChild(more);
    badge();
  }
  if(root) prices().then(renderCart).catch(function(){root.innerHTML='';root.appendChild(el('p','lede','Your cart could not be loaded. Please refresh the page.'));});

  // ---- order complete: clear the cart
  if($('order-done')){save([]);}
  badge();
})();
