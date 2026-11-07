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
    card.appendChild(el('p','hint','Prices are in CAD before tax and shipping. Leave a price blank if it is not for sale yet. Untick "Sell this size" to hide a size, or "Show product" to stop selling a whole product. "In stock" is how many you have: it counts down when orders are paid and shows Out of stock at 0. Leave it blank to not track a size. Type a new number to restock.'));
    var rows={};
    Object.keys(S.catalog).forEach(function(slug){
      var p=S.catalog[slug], box=el('div','prod'), h=el('h3',null,p.name), en=chk('Show product',p.enabled); h.appendChild(en); box.appendChild(h);
      var sz=el('div','sizes'); rows[slug]={en:en,sizes:{}};
      Object.keys(p.sizes).forEach(function(k){
        var s=p.sizes[k], r=el('div','row'), pr=inp('number',s.price==null?'':s.price,{min:0,step:'0.01',inputmode:'decimal',placeholder:'no price'}), av=chk('Sell this size',s.available);
        var st=inp('number',s.stock==null?'':s.stock,{min:0,step:'1',inputmode:'numeric',placeholder:'not tracked'}), init=st.value;
        if(s.stock!=null&&s.stock<=0){st.style.borderColor='#b4503f';} else if(s.stock!=null&&s.stock<=5){st.style.borderColor='#d8c98b';}
        r.appendChild(el('div',null,s.label));
        if(s.derived){r.appendChild(el('div','hint','Price and stock follow the 5 lb bag ('+(s.price==null?'no price yet':'$'+s.price.toFixed(2))+'; '+(s.stock==null?'stock not tracked':s.stock+' available')+')'));r.appendChild(av);pr.disabled=true;st.disabled=true;}else{r.appendChild(field('Price ($)',pr)); r.appendChild(field('In stock',st)); r.appendChild(av);} sz.appendChild(r); rows[slug].sizes[k]={pr:pr,av:av,st:st,init:init};
      });
      box.appendChild(sz); card.appendChild(box);
    });
    var b=el('button','btn solid','Save products and prices'); b.type='button'; var m=msgBox(), bar=el('div','bar'); bar.appendChild(b); bar.appendChild(m); card.appendChild(bar);
    saver(b,m,function(){
      var out={};
      Object.keys(rows).forEach(function(slug){out[slug]={enabled:rows[slug].en.cb.checked,sizes:{}};Object.keys(rows[slug].sizes).forEach(function(k){var x=rows[slug].sizes[k];out[slug].sizes[k]={price:x.pr.value,available:x.av.cb.checked,stock:x.st.value,stock_changed:x.st.value!==x.init};});});
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

  function salesCard(){
    var card=el('div','ad-card'); card.appendChild(el('h2',null,'Sales'));
    card.appendChild(el('p','hint','Put products on sale. The store shows the old price crossed out, the sale price and a Sale tag, and checkout charges the sale price. Leave the dates empty to run it until you turn it off. If two sales match, the lower price is used.'));
    var list=el('div','codes'), sizeNames={};
    Object.keys(S.catalog).forEach(function(s){Object.keys(S.catalog[s].sizes).forEach(function(k){sizeNames[k]=S.catalog[s].sizes[k].label.split('(')[0].trim();});});
    function opt(sel,v,l){var o=el('option',null,l);o.value=v;sel.appendChild(o);}
    function addRow(d){
      d=d||{label:'',product:'all',size:'all',type:'percent',value:'',starts:'',ends:'',active:true};
      var r=el('div','row'), lab=inp('text',d.label,{maxlength:40,placeholder:'Black Friday'}), prod=el('select'), size=el('select'), type=el('select'), val=inp('number',d.value,{min:0,step:'0.01',inputmode:'decimal'});
      opt(prod,'all','All products'); Object.keys(S.catalog).forEach(function(s){opt(prod,s,S.catalog[s].name);}); prod.value=d.product;
      opt(size,'all','All sizes'); Object.keys(sizeNames).forEach(function(k){opt(size,k,sizeNames[k]);}); size.value=d.size;
      opt(type,'percent','Percent off (%)'); opt(type,'fixed','Dollars off ($)'); type.value=d.type;
      var st=inp('date',d.starts||''), en=inp('date',d.ends||''), act=chk('On',d.active), x=el('button','x','Delete'); x.type='button'; x.addEventListener('click',function(){r.remove();});
      r.appendChild(field('Name (optional)',lab)); r.appendChild(field('Product',prod)); r.appendChild(field('Size',size)); r.appendChild(field('Type',type)); r.appendChild(field('Amount',val)); r.appendChild(field('Starts',st)); r.appendChild(field('Ends',en)); r.appendChild(act); r.appendChild(x);
      r.f={lab:lab,prod:prod,size:size,type:type,val:val,st:st,en:en,act:act}; list.appendChild(r);
    }
    (S.sales||[]).forEach(addRow); card.appendChild(list);
    var add=el('button','btn','Add a sale'); add.type='button'; add.addEventListener('click',function(){addRow(null);});
    var b=el('button','btn solid','Save sales'); b.type='button'; var m=msgBox(), bar=el('div','bar'); bar.appendChild(add); bar.appendChild(b); bar.appendChild(m); card.appendChild(bar);
    saver(b,m,function(){return call('save_sales',{sales:Array.prototype.map.call(list.children,function(r){var f=r.f;return{label:f.lab.value,product:f.prod.value,size:f.size.value,type:f.type.value,value:f.val.value,starts:f.st.value,ends:f.en.value,active:f.act.cb.checked};})});});
    return card;
  }

  function settingsCard(){
    var card=el('div','ad-card'); card.appendChild(el('h2',null,'Free gift and reminders'));
    var g=S.settings.gift, r=S.settings.reminders;
    card.appendChild(el('p','hint','Free gift: orders at or above the amount (before tax, shipping and discount codes, after sales) get the gift added automatically at checkout. The customer picks one of the gift choices at checkout, and your order email and the Stripe order show which one to pack. Gift stock counts all gifts together and is not taken from product stock.'));
    var row=el('div','row'); row.style.gridTemplateColumns='repeat(auto-fill,minmax(180px,1fr))';
    var gon=chk('Free gift is on',g.enabled), thr=inp('number',g.threshold,{min:1,step:'0.01',inputmode:'decimal'}), ch0=inp('text',(g.choices[0]||{}).name||'',{maxlength:80}), ch1=inp('text',(g.choices[1]||{}).name||'',{maxlength:80}), wt=inp('number',g.weight_kg,{min:0,step:'0.01',inputmode:'decimal'}), stk=inp('number',g.stock==null?'':g.stock,{min:0,step:'1',inputmode:'numeric',placeholder:'not tracked'});
    row.appendChild(gon); row.appendChild(field('Order amount ($)',thr)); row.appendChild(field('Gift choice 1',ch0)); row.appendChild(field('Gift choice 2 (optional)',ch1)); row.appendChild(field('Gift weight (kg)',wt)); row.appendChild(field('Gift stock',stk)); card.appendChild(row);
    card.appendChild(el('p','hint','Restock reminders: customers get one email this many days after an order, with links to reorder what they bought and an unsubscribe link. It sends when the daily job runs (see setup steps).'));
    var row2=el('div','row'); row2.style.gridTemplateColumns='repeat(auto-fill,minmax(180px,1fr))';
    var ron=chk('Restock reminders are on',r.enabled), days=inp('number',r.days,{min:7,max:365,step:'1',inputmode:'numeric'});
    row2.appendChild(ron); row2.appendChild(field('Days after the order',days)); card.appendChild(row2);
    var b=el('button','btn solid','Save'); b.type='button'; var m=msgBox(), bar=el('div','bar'); bar.appendChild(b); bar.appendChild(m); card.appendChild(bar);
    saver(b,m,function(){return call('save_settings',{gift:{enabled:gon.cb.checked,threshold:thr.value,choices:[{id:(g.choices[0]||{}).id||'level-up',name:ch0.value},{id:(g.choices[1]||{}).id||'flower-power',name:ch1.value}],weight_kg:wt.value,stock:stk.value},reminders:{enabled:ron.cb.checked,days:days.value}});});
    return card;
  }

  function reviewsCard(){
    var card=el('div','ad-card'); card.appendChild(el('h2',null,'Customer reviews'));
    card.appendChild(el('p','hint','New reviews wait here until you approve them. Only approve real reviews from real customers. You can also add a review a customer sent you by email, text or social media.'));
    var names={}; Object.keys(S.catalog).forEach(function(s){names[s]=S.catalog[s].name;});
    var list=el('div'); var m=msgBox();
    function act(id,op){call('review_action',{id:id,op:op}).then(function(){return call('state');}).then(function(j){S.reviews=j.reviews;draw();}).catch(function(e){flash(m,false,e.message);});}
    function draw(){
      list.innerHTML='';
      if(!S.reviews.length) list.appendChild(el('p','hint','No reviews yet.'));
      S.reviews.forEach(function(r){
        var d=el('div','row'); d.style.gridTemplateColumns='1fr'; 
        d.appendChild(el('strong',null,(r.status==='pending'?'WAITING: ':r.status==='rejected'?'Hidden: ':'Live: ')+names[r.slug]+' - '+r.rating+' stars - '+r.name+' ('+r.date+')'+(r.source==='owner'?' - added by you':'')));
        d.appendChild(el('span',null,(r.title?r.title+' - ':'')+r.text)); if(r.contact) d.appendChild(el('span','used','Email: '+r.contact));
        var bar=el('div','bar'); bar.style.marginTop='4px';
        if(r.status!=='approved'){var a=el('button','btn','Approve'); a.type='button'; a.onclick=function(){act(r.id,'approve');}; bar.appendChild(a);}
        if(r.status==='approved'){var h=el('button','btn','Hide'); h.type='button'; h.onclick=function(){act(r.id,'reject');}; bar.appendChild(h);}
        var x=el('button','x','Delete'); x.type='button'; x.onclick=function(){if(confirm('Delete this review?'))act(r.id,'delete');}; bar.appendChild(x);
        d.appendChild(bar); list.appendChild(d);
      });
    }
    draw(); card.appendChild(list); card.appendChild(m);
    card.appendChild(el('h3',null,'Add a review you received'));
    var f=el('div','row'); f.style.gridTemplateColumns='repeat(auto-fill,minmax(200px,1fr))';
    var prod=el('select'); Object.keys(names).forEach(function(s){var o=el('option',null,names[s]);o.value=s;prod.appendChild(o);});
    var nm=inp('text','',{maxlength:40}), rt=el('select'); [5,4,3,2,1].forEach(function(n){var o=el('option',null,n+' stars');o.value=n;rt.appendChild(o);});
    var ti=inp('text','',{maxlength:80}), tx=el('textarea'); tx.maxLength=1000; tx.style.cssText='width:100%;min-height:90px;background:#0e0e0f;color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:10px;font:400 16px var(--text)';
    f.appendChild(field('Product',prod)); f.appendChild(field('Customer name (first name and initial)',nm)); f.appendChild(field('Rating',rt)); f.appendChild(field('Headline (optional)',ti)); card.appendChild(f); card.appendChild(field('What they said (their own words)',tx));
    var b=el('button','btn solid','Add review'); b.type='button'; var m2=msgBox(), bar2=el('div','bar'); bar2.appendChild(b); bar2.appendChild(m2); card.appendChild(bar2);
    saver(b,m2,function(){return call('add_review',{slug:prod.value,name:nm.value,rating:rt.value,title:ti.value,text:tx.value}).then(function(){nm.value='';ti.value='';tx.value='';return call('state');}).then(function(j){S.reviews=j.reviews;draw();});});
    return card;
  }

  function leadsCard(){
    var card=el('div','ad-card'); card.appendChild(el('h2',null,'Wholesale applications'));
    var list=el('div'), m=msgBox();
    function act(id,op){call('lead_action',{id:id,op:op}).then(function(){return call('state');}).then(function(j){S.leads=j.leads;draw();}).catch(function(e){flash(m,false,e.message);});}
    function draw(){
      list.innerHTML=''; if(!S.leads.length) list.appendChild(el('p','hint','No applications yet. New ones are also emailed to you.'));
      S.leads.forEach(function(l){
        var d=el('div','row'); d.style.gridTemplateColumns='1fr';
        d.appendChild(el('strong',null,(l.status==='new'?'NEW: ':'Contacted: ')+l.business+' - '+l.contact+' ('+l.date+')'));
        d.appendChild(el('span',null,l.email+' | '+l.phone+' | '+(l.city||'')+' | '+(l.type||'')+' | '+(l.volume||'')+(l.website_url?' | '+l.website_url:'')));
        if(l.message) d.appendChild(el('span','used',l.message));
        var bar=el('div','bar'); bar.style.marginTop='4px';
        var a=el('button','btn',l.status==='new'?'Mark contacted':'Mark new'); a.type='button'; a.onclick=function(){act(l.id,l.status==='new'?'contacted':'new');}; bar.appendChild(a);
        var x=el('button','x','Delete'); x.type='button'; x.onclick=function(){if(confirm('Delete this application?'))act(l.id,'delete');}; bar.appendChild(x);
        d.appendChild(bar); list.appendChild(d);
      });
    }
    draw(); card.appendChild(list); card.appendChild(m); return card;
  }

  function emailCard(){
    var card=el('div','ad-card'); card.appendChild(el('h2',null,'Email list, email test and backup'));
    card.appendChild(el('p','hint','Pop-up signups: '+S.subscribers+'. Customers with an email on a paid order: '+S.customers+'. The download has both, with unsubscribed people marked. Use it in an email tool such as Mailchimp to send newsletters.'));
    var bar=el('div','bar'); var dl=el('a','btn','Download email list (CSV)'); dl.href='/api/admin.php?action=export_subscribers'; bar.appendChild(dl);
    var t=el('button','btn','Send me a test email'); t.type='button'; var m=msgBox();
    t.addEventListener('click',function(){t.disabled=true;flash(m,true,'Sending...');call('test_mail',{}).then(function(j){flash(m,true,'Sent to '+j.to+'. Check your inbox and spam folder.');}).catch(function(e){flash(m,false,e.message);}).then(function(){t.disabled=false;});});
    var bk=el('button','btn','Back up now'); bk.type='button'; bk.addEventListener('click',function(){bk.disabled=true;flash(m,true,'Backing up...');call('backup_now',{}).then(function(j){flash(m,true,j.result);}).catch(function(e){flash(m,false,e.message);}).then(function(){bk.disabled=false;});});
    bar.appendChild(t); bar.appendChild(bk); card.appendChild(bar); card.appendChild(m);
    card.appendChild(el('p','hint','A backup of all your shop data (prices, stock, sales, codes, subscribers, reviews, leads) is saved and emailed to you every Sunday once the daily job is set up. Last backup week: '+(S.last_backup||'none yet')+'.'));
    return card;
  }

  function boot(){
    call('state').then(function(j){
      S=j; csrf=j.csrf; root.innerHTML='';
      var top=el('p'); var out=el('button','btn','Log out'); out.type='button'; out.addEventListener('click',function(){call('logout',{}).then(function(){location.reload();});}); top.appendChild(out); root.appendChild(top);
      root.appendChild(productsCard()); root.appendChild(salesCard()); root.appendChild(shippingCard()); root.appendChild(discountsCard()); root.appendChild(settingsCard()); root.appendChild(reviewsCard()); root.appendChild(leadsCard()); root.appendChild(emailCard());
    }).catch(function(e){ if(e.status===401) login(); else if(e.status===503){root.innerHTML='';root.appendChild(el('p','lede',e.message));} else login(e.message); });
  }
  function showFail(msg){root.innerHTML='';root.appendChild(el('p','lede','The admin page could not start: '+msg+' Please send this message to Claude.'));}
  window.addEventListener('error',function(e){showFail((e&&e.message)||'script error');});
  window.addEventListener('unhandledrejection',function(e){showFail((e&&e.reason&&e.reason.message)||'request failed');});
  try{boot();}catch(e){showFail(e.message);}
})();
