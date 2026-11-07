(function(){
  'use strict';
  var API='/api/admin.php', root=document.getElementById('ad-root'), csrf='', S=null;
  function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e;}
  function call(action,body){
    var o={method:body?'POST':'GET',headers:{'Content-Type':'application/json','X-CSRF':csrf},credentials:'same-origin'};
    if(body)o.body=JSON.stringify(body);
    return fetch(API+'?action='+action,o).then(function(r){return r.text().then(function(t){var j={};try{j=JSON.parse(t);}catch(e){}if(!r.ok){var e=new Error(j.error||'Something went wrong.');e.status=r.status;throw e;}return j;});});
  }
  function field(label,input){var d=el('div');var l=el('label',null,label);d.appendChild(l);d.appendChild(input);return d;}
  function inp(type,val,extra){var i=el('input');i.type=type;if(val!=null)i.value=val;if(extra)for(var k in extra)i.setAttribute(k,extra[k]);return i;}
  function chk(label,on){var l=el('label','chk');var c=inp('checkbox');c.checked=!!on;l.appendChild(c);l.appendChild(document.createTextNode(label));l.cb=c;return l;}
  function msgBox(){return el('p','msg');}
  function flash(m,ok,text){m.className='msg '+(ok?'ok':'err');m.textContent=text;}
  function saver(btn,m,fn){btn.addEventListener('click',function(){btn.disabled=true;flash(m,true,'Saving...');fn().then(function(){flash(m,true,'Saved. The shop uses it right away.');}).catch(function(e){if(e.status===401){location.reload();return;}flash(m,false,e.message);}).then(function(){btn.disabled=false;});});}

  function login(note){
    root.innerHTML='';
    var c=el('div','ad-card'); c.style.maxWidth='420px';
    c.appendChild(el('h2',null,'Owner login'));
    var p=inp('password','',{autocomplete:'current-password'}); c.appendChild(field('Password',p));
    var m=msgBox(); if(note)flash(m,false,note);
    var b=el('button','btn solid','Log in'); b.type='button'; var bar=el('div','bar'); bar.appendChild(b); c.appendChild(bar); c.appendChild(m); root.appendChild(c);
    function go(){b.disabled=true;call('login',{password:p.value}).then(boot).catch(function(e){flash(m,false,e.message);b.disabled=false;});}
    b.addEventListener('click',go); p.addEventListener('keydown',function(e){if(e.key==='Enter')go();}); p.focus();
  }

  function productsCard(){
    var card=el('div','ad-card'); card.appendChild(el('h2',null,'Products and prices'));
    card.appendChild(el('p','hint','Prices are in CAD before tax and shipping. Leave a price blank if it is not for sale yet. Untick "Sell this size" to hide a size, or "Show product" to stop selling a whole product.'));
    var rows={};
    Object.keys(S.catalog).forEach(function(slug){
      var p=S.catalog[slug], box=el('div','prod'), h=el('h3',null,p.name), en=chk('Show product',p.enabled); h.appendChild(en); box.appendChild(h);
      var sz=el('div','sizes'); rows[slug]={en:en,sizes:{}};
      Object.keys(p.sizes).forEach(function(k){
        var s=p.sizes[k], r=el('div','row'), pr=inp('number',s.price==null?'':s.price,{min:0,step:'0.01',inputmode:'decimal',placeholder:'no price'}), av=chk('Sell this size',s.available);
        r.appendChild(el('div',null,s.label)); r.appendChild(field('Price ($)',pr)); r.appendChild(av); sz.appendChild(r); rows[slug].sizes[k]={pr:pr,av:av};
      });
      box.appendChild(sz); card.appendChild(box);
    });
    var b=el('button','btn solid','Save products and prices'); b.type='button'; var m=msgBox(), bar=el('div','bar'); bar.appendChild(b); bar.appendChild(m); card.appendChild(bar);
    saver(b,m,function(){
      var out={};
      Object.keys(rows).forEach(function(slug){out[slug]={enabled:rows[slug].en.cb.checked,sizes:{}};Object.keys(rows[slug].sizes).forEach(function(k){var x=rows[slug].sizes[k];out[slug].sizes[k]={price:x.pr.value,available:x.av.cb.checked};});});
      return call('save_products',{products:out});
    });
    return card;
  }

  function shippingCard(){
    var card=el('div','ad-card'); card.appendChild(el('h2',null,'Shipping rates'));
    card.appendChild(el('p','hint','Flat rate by total order weight. The first row whose weight is at or above the order weight applies. Orders heavier than the last row cannot check out online.'));
    var list=el('div','tiers');
    function addRow(t){
      var r=el('div','row'), w=inp('number',t?t.max_kg:'',{min:0,step:'0.01',inputmode:'decimal'}), p=inp('number',t?t.price:'',{min:0,step:'0.01',inputmode:'decimal'}), x=el('button','x','Remove'); x.type='button';
      x.addEventListener('click',function(){r.remove();});
      r.appendChild(field('Up to (kg)',w)); r.appendChild(field('Price ($)',p)); r.appendChild(x); r.w=w; r.p=p; list.appendChild(r);
    }
    S.tiers.forEach(addRow); card.appendChild(list);
    var add=el('button','btn','Add row'); add.type='button'; add.addEventListener('click',function(){addRow(null);});
    var b=el('button','btn solid','Save shipping'); b.type='button'; var m=msgBox(), bar=el('div','bar'); bar.appendChild(add); bar.appendChild(b); bar.appendChild(m); card.appendChild(bar);
    saver(b,m,function(){return call('save_shipping',{tiers:Array.prototype.map.call(list.children,function(r){return{max_kg:r.w.value,price:r.p.value};})});});
    return card;
  }

  function discountsCard(){
    var card=el('div','ad-card'); card.appendChild(el('h2',null,'Discount codes'));
    card.appendChild(el('p','hint','Customers type the code in their cart. A percent code takes that % off the products. A dollar code takes that amount off the products. Neither changes shipping unless "Free shipping" is ticked. The "Used" count goes up when a paid order uses the code.'));
    var list=el('div','codes');
    function addRow(d){
      d=d||{type:'percent',active:true,value:'',min_subtotal:'',expires:'',max_uses:'',uses:0,free_shipping:false,code:''};
      var r=el('div','row'), code=inp('text',d.code,{maxlength:30,autocapitalize:'characters',placeholder:'SPRING10'}), type=el('select'), val=inp('number',d.value,{min:0,step:'0.01',inputmode:'decimal'});
      [['percent','Percent off (%)'],['fixed','Dollars off ($)']].forEach(function(o){var op=el('option',null,o[1]);op.value=o[0];type.appendChild(op);}); type.value=d.type;
      var min=inp('number',d.min_subtotal||'',{min:0,step:'0.01',inputmode:'decimal',placeholder:'none'}), exp=inp('date',d.expires||''), mx=inp('number',d.max_uses||'',{min:1,step:'1',inputmode:'numeric',placeholder:'unlimited'});
      var act=chk('Active',d.active), fs=chk('Free shipping',d.free_shipping), x=el('button','x','Delete'); x.type='button'; x.addEventListener('click',function(){r.remove();});
      r.appendChild(field('Code',code)); r.appendChild(field('Type',type)); r.appendChild(field('Amount',val)); r.appendChild(field('Minimum order ($)',min)); r.appendChild(field('Expires',exp)); r.appendChild(field('Max uses',mx));
      r.appendChild(act); r.appendChild(fs); r.appendChild(el('span','used','Used: '+(d.uses||0))); r.appendChild(x);
      r.f={code:code,type:type,val:val,min:min,exp:exp,mx:mx,act:act,fs:fs}; list.appendChild(r);
    }
    S.discounts.forEach(addRow); card.appendChild(list);
    var add=el('button','btn','Add a code'); add.type='button'; add.addEventListener('click',function(){addRow(null);});
    var b=el('button','btn solid','Save discount codes'); b.type='button'; var m=msgBox(), bar=el('div','bar'); bar.appendChild(add); bar.appendChild(b); bar.appendChild(m); card.appendChild(bar);
    saver(b,m,function(){return call('save_discounts',{discounts:Array.prototype.map.call(list.children,function(r){var f=r.f;return{code:f.code.value,type:f.type.value,value:f.val.value,min_subtotal:f.min.value,expires:f.exp.value,max_uses:f.mx.value,active:f.act.cb.checked,free_shipping:f.fs.cb.checked};})});});
    return card;
  }

  function boot(){
    call('state').then(function(j){
      S=j; csrf=j.csrf; root.innerHTML='';
      var top=el('p'); var out=el('button','btn','Log out'); out.type='button'; out.addEventListener('click',function(){call('logout',{}).then(function(){location.reload();});}); top.appendChild(out); root.appendChild(top);
      root.appendChild(productsCard()); root.appendChild(shippingCard()); root.appendChild(discountsCard());
    }).catch(function(e){ if(e.status===401) login(); else if(e.status===503){root.innerHTML='';root.appendChild(el('p','lede',e.message));} else login(e.message); });
  }
  boot();
})();
