(function(){
  'use strict';
  var path=location.pathname, KEY='mss_deal_v1', CODEKEY='mss_code_v1';
  function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e;}
  var m=location.search.match(/[?&]code=([A-Za-z0-9_-]{1,30})/);
  if(m){try{localStorage.setItem(CODEKEY,m[1].toUpperCase());}catch(e){}}
  if(/^\/admin\//.test(path)) return;
  function endText(d){if(!d) return ''; var p=d.split('-'); var mo=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][+p[1]-1]; return mo?('Ends '+mo+' '+(+p[2])):'';}
  function copy(btn,code){
    function ok(){var o=btn.textContent;btn.textContent='Copied';setTimeout(function(){btn.textContent=o;},1600);}
    try{navigator.clipboard.writeText(code).then(ok,function(){});}catch(e){}
  }
  fetch('/api/shop.php').then(function(r){return r.json();}).then(function(d){
    var P=d&&d.promo; if(!P) return;
    var link='/?code='+encodeURIComponent(P.code)+'#products', ends=endText(P.ends);
    // home page deal section
    var sec=document.getElementById('deal');
    if(sec){
      var w=el('div','wrap'), box=el('div','dealbox');
      box.appendChild(el('span','dealtag','Deal of the month'));
      box.appendChild(el('h2',null,P.title)); box.appendChild(el('p','dealtext',P.text+(ends?' \u00b7 '+ends:'')));
      var row=el('div','dealrow'), chip=el('span','dealcode',P.code), cp=el('button','btn','Copy code'); cp.type='button'; cp.addEventListener('click',function(){copy(cp,P.code);});
      var go=el('a','btn solid','Shop now'); go.href=link;
      row.appendChild(chip); row.appendChild(cp); row.appendChild(go); box.appendChild(row);
      box.appendChild(el('p','dealnote','The code is applied for you when you click Shop now. Or type it in your cart.'));
      w.appendChild(box); sec.appendChild(w); sec.hidden=false;
    }
    // corner tab: always there, can be minimised but never removed
    if(/^\/(cart|order-complete)\//.test(path)) return;
    var min=true; try{min=localStorage.getItem(KEY)!=='open';}catch(e){}
    var tab=el('div','dealtab'); tab.setAttribute('role','complementary'); tab.setAttribute('aria-label','Deal of the month');
    var pill=el('button','dealpill'); pill.type='button'; pill.appendChild(el('b',null,P.title)); pill.appendChild(document.createTextNode(' \u00b7 '+P.text));
    var panel=el('div','dealpanel');
    var x=el('button','dealx','\u2212'); x.type='button'; x.setAttribute('aria-label','Minimise deal');
    panel.appendChild(x); panel.appendChild(el('strong',null,P.title)); panel.appendChild(el('p',null,P.text+(ends?' \u00b7 '+ends:'')));
    var cr=el('div','dealrow'), cc=el('span','dealcode',P.code), cb=el('button','btn','Copy'); cb.type='button'; cb.addEventListener('click',function(){copy(cb,P.code);});
    var sn=el('a','btn solid','Shop now'); sn.href=link; cr.appendChild(cc); cr.appendChild(cb); cr.appendChild(sn); panel.appendChild(cr);
    tab.appendChild(panel); tab.appendChild(pill); document.body.appendChild(tab);
    function show(open){panel.hidden=!open;pill.hidden=open;pill.setAttribute('aria-expanded',String(open));try{localStorage.setItem(KEY,open?'open':'min');}catch(e){}}
    pill.addEventListener('click',function(){show(true);}); x.addEventListener('click',function(){show(false);});
    panel.hidden=!(!min); pill.hidden=!min;
  }).catch(function(){});
})();
