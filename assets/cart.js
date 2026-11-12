(function(){
  'use strict';
  var KEY='mss_cart_v1', CODEKEY='mss_code_v1', PRICES=null, SHIP=null, GIFT=null, PROMO=null, GCH='', $=function(id){return document.getElementById(id);};
  var mem=[], memCode='';

  function load(){try{var a=JSON.parse(localStorage.getItem(KEY)||'[]');return Array.isArray(a)?a:[];}catch(e){return mem;}}
  function save(a){mem=a;try{localStorage.setItem(KEY,JSON.stringify(a));}catch(e){}}
  function declined(){try{return sessionStorage.getItem('mss_nopromo')==='1';}catch(e){return false;}}
  function decline(on){try{if(on)sessionStorage.setItem('mss_nopromo','1');else sessionStorage.removeItem('mss_nopromo');}catch(e){}}
  function getCode(){try{return localStorage.getItem(CODEKEY)||'';}catch(e){return memCode;}}
  function setCode(c){memCode=c;try{if(c)localStorage.setItem(CODEKEY,c);else localStorage.removeItem(CODEKEY);}catch(e){}}
  function count(){return load().reduce(function(n,i){return n+(i.qty||0);},0);}
  function badge(){var n=$('cart-n');if(n){var c=count();n.textContent=c;n.classList.toggle('on',c>0);}}
  function money(v){return new Intl.NumberFormat('en-CA',{style:'currency',currency:'CAD'}).format(v);}
  function shop(){
    if(PRICES) return Promise.resolve(PRICES);
    return fetch('/api/shop.php',{cache:'no-cache'}).then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(j){PRICES=j.products||{};SHIP=j.tiers||[];GIFT=j.gift||null;PROMO=j.promo||null;return PRICES;});
  }
  function soldout(s){return !!s.soldout;}
  function find(slug,size){var P=PRICES&&PRICES[slug];return P&&P.enabled&&P.sizes&&P.sizes[size]?{p:P,s:P.sizes[size]}:null;}
  function valid(p){return typeof p==='number'&&p>0;}
  function unit(s){return valid(s.sale_price)?s.sale_price:s.price;}
  function onSale(s){return valid(s.sale_price)&&valid(s.price)&&s.sale_price<s.price;}
  function fmtEnd(d){if(!d)return '';var p=d.split('-');return new Date(+p[0],+p[1]-1,+p[2]).toLocaleDateString('en-CA',{month:'long',day:'numeric'});}
  function saleNote(s){return (s.sale_label||'Sale')+(s.sale_ends?' - ends '+fmtEnd(s.sale_ends):'');}
  function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e;}
  function post(url,body){
    return fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
      .then(function(r){return r.text().then(function(t){var j=null;try{j=JSON.parse(t);}catch(e){}if(!r.ok||!j)throw new Error((j&&j.error)||'Something went wrong. Please try again.');return j;});});
  }
  function neterr(e){return e.message==='Failed to fetch'?'Could not connect. Check your internet and try again.':e.message;}

  // ---- product page buy box
  var box=$('buy-box');
  if(box){
    var slug=box.getAttribute('data-slug'), sel=$('buy-size'), qty=$('buy-qty'), pr=$('buy-price'), add=$('buy-add'), msg=$('buy-msg');
    var update=function(){
      var P=PRICES&&PRICES[slug];
      if(P&&!P.enabled){pr.textContent='Currently unavailable';add.disabled=true;return;}
      var f=find(slug,sel.value), ok=f&&valid(f.s.price)&&!soldout(f.s);
      pr.textContent='';
      if(f&&f.s.coming_soon){pr.textContent='Coming soon';add.disabled=true;msg.textContent='';return;}
      qty.max=(f&&f.s.left)?f.s.left:20;
      if(f&&valid(f.s.price)&&soldout(f.s)){pr.textContent='Out of stock';add.disabled=true;msg.textContent='';return;}
      if(ok&&onSale(f.s)){
        var old=el('s','wasprice',money(f.s.price)); pr.appendChild(old); pr.appendChild(document.createTextNode(' '+money(f.s.sale_price)+' '));
        pr.appendChild(el('span','salebadge','Save '+Math.round((1-f.s.sale_price/f.s.price)*100)+'%'));
        var n=el('span','salenote',saleNote(f.s)); pr.appendChild(n);
      } else pr.textContent=ok?money(f.s.price):(f?'Price coming soon':'');
      add.disabled=!ok; msg.textContent=(ok&&f.s.left)?'Only '+f.s.left+' left in stock.':'';
    };
    add.disabled=true;
    shop().then(function(){
      var P=PRICES[slug];
      Array.prototype.slice.call(sel.options).forEach(function(o){
        var s=P&&P.sizes&&P.sizes[o.value];
        if(!s){o.remove();return;}
        if(s.coming_soon){o.textContent=s.label+' — Coming soon';return;}
        if(valid(s.price)&&s.soldout){o.textContent=s.label+' — Out of stock';return;}
        if(valid(s.price))o.textContent=s.label+' — '+(onSale(s)?money(s.sale_price)+' (was '+money(s.price)+')':money(s.price));
      });
      update();
    }).catch(function(){pr.textContent='Prices are unavailable right now.';add.disabled=true;});
    sel.addEventListener('change',update);
    shop().then(function(){if(GIFT){var g=el('p','giftnote','Free gift: orders of '+money(GIFT.threshold)+' or more include a free 2 lb bag of '+((GIFT.choices||[]).map(function(c){return c.name.replace(/ \(.*/,'').replace(/ [0-9-]+$/,'');}).join(' or ')||GIFT.name)+' (your choice).');box.appendChild(g);}}).catch(function(){});
    add.addEventListener('click',function(){
      var f0=find(slug,sel.value), cap=(f0&&f0.s.left)?f0.s.left:20, q=Math.max(1,Math.min(cap,parseInt(qty.value,10)||1)), c=load(), hit=null;
      c.forEach(function(i){if(i.slug===slug&&i.size===sel.value)hit=i;});
      if(hit)hit.qty=Math.min(cap,hit.qty+q);else c.push({slug:slug,size:sel.value,qty:q});
      save(c);badge();
      msg.textContent='';
      msg.appendChild(document.createTextNode('Added to your cart. '));
      var a=el('a',null,'View cart'); a.href='/cart/'; msg.appendChild(a);
    });
  }

  // ---- live "From $X" on tiles and the product page (static text is the fallback)
  function lowest(P){var m=null;Object.keys(P.sizes).forEach(function(k){var s=P.sizes[k];if(valid(s.price)&&!s.soldout){var v=(s.sale_price!=null&&s.sale_price<s.price)?s.sale_price:s.price;if(m===null||v<m)m=v;}});return m;}
  if(document.querySelector('.pick[data-slug] .from,#price-from')) shop().then(function(){
    Array.prototype.forEach.call(document.querySelectorAll('.pick[data-slug]'),function(a){
      var P=PRICES[a.getAttribute('data-slug')]; var f=a.querySelector('.from'); if(!P||!f) return;
      var m=lowest(P); if(m!==null) f.textContent='From '+money(m);
    });
    var pf=$('price-from'); if(pf){var P=PRICES[pf.getAttribute('data-slug')]; if(P){
      var m=lowest(P), parts=[], soon=[]; Object.keys(P.sizes).forEach(function(k){var s=P.sizes[k];if(valid(s.price)&&!s.soldout){var v=(s.sale_price!=null&&s.sale_price<s.price)?s.sale_price:s.price;parts.push(s.label.split(' (')[0]+' '+money(v));}else if(s.coming_soon){soon.push(s.label.split(' (')[0].replace(' kit',''));}});
      if(soon.length)parts.push(soon.join(' \u00b7 ')+': coming soon');
      if(m!==null){pf.textContent='';var st=el('strong',null,'From '+money(m)+' CAD');pf.appendChild(st);pf.appendChild(document.createTextNode(' '));pf.appendChild(el('span',null,parts.join(' \u00b7 ')));}
    }}
  }).catch(function(){});

  // ---- "Sale" tags on product tiles (home page and product pages)
  var tiles=document.querySelectorAll('.pick[data-slug]');
  if(tiles.length) shop().then(function(){
    Array.prototype.forEach.call(tiles,function(a){
      var P=PRICES[a.getAttribute('data-slug')]; if(!P||!P.enabled) return;
      var any=false; Object.keys(P.sizes).forEach(function(k){if(onSale(P.sizes[k]))any=true;});
      var allOut=true,anyP=false; Object.keys(P.sizes).forEach(function(k){var s=P.sizes[k];if(valid(s.price)){anyP=true;if(!s.soldout)allOut=false;}});
      if(anyP&&allOut){a.style.position='relative';var so=el('span','salebadge tile','Sold out');so.style.background='#555';a.appendChild(so);}
      else if(any){a.style.position='relative';a.appendChild(el('span','salebadge tile','Sale'));}
    });
  }).catch(function(){});

  // ---- cart page
  var root=$('cart-root');
  function tierFor(kg){var t=null;(SHIP||[]).forEach(function(x){if(t===null&&kg<=x.max_kg)t=x;});return t;}

  function renderCart(disc,codeMsg){
    var all=load(), c=all.filter(function(i){return find(i.slug,i.size);});
    if(c.length!==all.length) save(c);
    root.innerHTML='';
    if(!c.length){
      root.appendChild(el('p','lede','Your cart is empty.'));
      var a=el('a','btn solid','Shop products'); a.href='/#products'; var w=el('p'); w.style.marginTop='20px'; w.appendChild(a); root.appendChild(w); badge(); return;
    }
    var list=el('ul','cartlist'), total=0, missing=false, kg=0;
    c.forEach(function(i,idx){
      var f=find(i.slug,i.size), pr=unit(f.s), li=el('li','cartrow');
      var im=el('img'); im.src=f.p.img; im.alt=''; im.width=64; im.height=94; li.appendChild(im);
      var mid=el('div','cartinfo'); mid.appendChild(el('strong',null,f.p.name)); mid.appendChild(el('span',null,f.s.label));
      if(onSale(f.s)) mid.appendChild(el('span','cartsale','On sale: was '+money(f.s.price)+' each'));
      if(soldout(f.s)){missing=true;mid.appendChild(el('span','cartwarn','Out of stock. Remove this item to check out.'));}
      else if(f.s.left&&i.qty>f.s.left){missing=true;mid.appendChild(el('span','cartwarn','Only '+f.s.left+' left. Lower the quantity to check out.'));}
      if(!valid(pr)){missing=true;mid.appendChild(el('span','cartwarn',(f&&f.s.coming_soon)?'Coming soon. Remove this item to check out.':'No price yet. Remove this item to check out.'));}
      li.appendChild(mid);
      var q=el('div','cartqty'), lab=el('label',null,'Qty'); lab.className='sr'; lab.htmlFor='q'+idx;
      var inp=el('input'); inp.type='number'; inp.min=1; inp.max=20; inp.value=i.qty; inp.id='q'+idx; inp.setAttribute('inputmode','numeric');
      inp.addEventListener('change',function(){var a2=load();var n=Math.max(1,Math.min(20,parseInt(inp.value,10)||1));a2.forEach(function(x){if(x.slug===i.slug&&x.size===i.size)x.qty=n;});save(a2);start();});
      q.appendChild(lab); q.appendChild(inp); li.appendChild(q);
      li.appendChild(el('div','cartline',valid(pr)?money(pr*i.qty):'-'));
      var rm=el('button','cartrm','Remove'); rm.type='button'; rm.setAttribute('aria-label','Remove '+f.p.name+' '+f.s.label);
      rm.addEventListener('click',function(){save(load().filter(function(x){return !(x.slug===i.slug&&x.size===i.size);}));start();});
      li.appendChild(rm); list.appendChild(li);
      if(valid(pr)) total+=pr*i.qty;
      kg+=(f.s.weight_kg||0)*i.qty;
    });
    var gifted=GIFT&&total>=GIFT.threshold;
    if(gifted){
      var chs=GIFT.choices&&GIFT.choices.length?GIFT.choices:[{id:'',name:GIFT.name}];
      try{GCH=localStorage.getItem('mss_gift_v1')||'';}catch(e){}
      if(!chs.some(function(c){return c.id===GCH;}))GCH=chs[0].id;
      var cur=chs.filter(function(c){return c.id===GCH;})[0];
      var gl=el('li','cartrow'); gl.appendChild(el('span')); var gm=el('div','cartinfo'); gm.appendChild(el('strong',null,'Free gift: '+cur.name));
      if(chs.length>1){var gs=el('span',null,'Choose your free gift:'); gm.appendChild(gs); chs.forEach(function(c){var lb=el('label','giftopt'); var rd=el('input'); rd.type='radio'; rd.name='giftpick'; rd.value=c.id; rd.checked=(c.id===GCH); rd.addEventListener('change',function(){GCH=c.id;try{localStorage.setItem('mss_gift_v1',GCH);}catch(e){} renderCart(disc,codeMsg);}); lb.appendChild(rd); lb.appendChild(document.createTextNode(' '+c.name)); gm.appendChild(lb);});}
      else gm.appendChild(el('span',null,'Added automatically')); gl.appendChild(gm); gl.appendChild(el('span')); gl.appendChild(el('div','cartline','Free')); list.appendChild(gl);
      kg+=GIFT.weight_kg||0;
    }
    root.appendChild(list); kg=Math.round(kg*100)/100;
    if(GIFT){var gb=el('div','giftbar'+(gifted?' on':''));gb.textContent=gifted?'You earned a free 2 lb bag. Pick which one above.':'Add '+money(GIFT.threshold-total)+' more to get a free 2 lb bag of '+((GIFT.choices||[]).map(function(c){return c.name.replace(/ \(.*/,'');}).join(' or ')||GIFT.name)+'.';root.appendChild(gb);}
    var tier=tierFor(kg), tooHeavy=(SHIP&&SHIP.length&&tier===null);
    var ship=tier?tier.price:null, off=disc?disc.discount:0;
    if(disc&&disc.free_shipping&&tier) ship=0;

    // discount code box
    var cb=el('div','codebox'), ci=el('input'); ci.type='text'; ci.placeholder='Discount code'; ci.value=getCode(); ci.setAttribute('aria-label','Discount code'); ci.autocapitalize='characters'; ci.maxLength=30;
    var cbtn=el('button','btn',disc?'Update':'Apply'); cbtn.type='button';
    cb.appendChild(ci); cb.appendChild(cbtn);
    var cm=el('p','codemsg'); cm.setAttribute('role','status');
    if(disc) cm.textContent='Code '+disc.code+' applied'+(off>0?': -'+money(off):'')+(disc.free_shipping?' (free shipping)':'')+'.';
    if(codeMsg){cm.textContent=codeMsg;cm.className='codemsg err';}
    cbtn.addEventListener('click',function(){
      var v=ci.value.trim(); if(!v){setCode('');decline(true);start();return;}
      decline(false);
      cbtn.disabled=true;
      post('/api/discount.php',{items:load(),code:v}).then(function(d){setCode(d.code);d.code=d.code;renderCart(d);})
        .catch(function(e){setCode('');renderCart(null,neterr(e));});
    });
    ci.addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();cbtn.click();}});
    root.appendChild(cb); root.appendChild(cm);

    var sum=el('div','carttotal'); sum.appendChild(el('span',null,'Subtotal')); sum.appendChild(el('strong',null,money(total))); root.appendChild(sum);
    var lines=[];
    if(off>0) lines.push('Discount: -'+money(off)+'.');
    if(tier) lines.push('Shipping within Canada: '+(ship===0?'free':money(ship))+' ('+kg.toFixed(1)+' kg). Tax is added at checkout.');
    else if(tooHeavy) lines.push('This order is too heavy for online checkout. Please email us to arrange shipping.');
    else lines.push('Shipping and tax are added at checkout.');
    root.appendChild(el('p','lede',lines.join(' ')));
    var err=el('div','cartmsg'); err.setAttribute('role','alert');
    var go=el('button','btn solid','Checkout'); go.type='button'; go.disabled=missing||tooHeavy;
    go.addEventListener('click',function(){
      go.disabled=true; err.textContent=''; go.textContent='Opening secure checkout...';
      post('/api/checkout.php',{items:load().map(function(i){return{slug:i.slug,size:i.size,qty:i.qty};}),code:disc?disc.code:'',gift_choice:GCH})
        .then(function(j){if(!j.url)throw new Error('Could not start checkout. Please try again.');window.location.href=j.url;})
        .catch(function(e){go.disabled=missing||tooHeavy;go.textContent='Checkout';err.textContent=neterr(e);});
    });
    var w2=el('p'); w2.style.marginTop='18px'; w2.appendChild(go); root.appendChild(w2); root.appendChild(err);
    var more=el('p','lede'); more.style.marginTop='18px'; var ml=el('a',null,'Keep shopping'); ml.href='/#products'; more.appendChild(ml); root.appendChild(more);
    badge();
  }
  function start(){
    var code=getCode(), items=load();
    // the live deal-of-the-month code is applied for everyone who reaches the cart, unless they removed it themselves
    if(!code&&PROMO&&PROMO.code&&!declined()) code=PROMO.code;
    if(!code||!items.length){renderCart(null);return;}
    post('/api/discount.php',{items:items,code:code})
      .then(function(d){if(d&&d.code)setCode(d.code);renderCart(d);})
      .catch(function(e){setCode('');renderCart(null,neterr(e));});
  }
  if(root) shop().then(start).catch(function(){root.innerHTML='';root.appendChild(el('p','lede','Your cart could not be loaded. Please refresh the page.'));});

  // ---- order complete: clear the cart and let the server count a used discount code
  if($('order-done')){
    save([]);setCode('');
    var m=location.search.match(/session_id=(cs_[A-Za-z0-9_]+)/);
    if(m) fetch('/api/complete.php?session_id='+m[1]).catch(function(){});
  }
  badge();
})();
