(function(){
  'use strict';
  var MAX_PHOTOS=3, MAX_SIDE=1600, API='/api/diagnose.php';
  var $=function(id){return document.getElementById(id);};
  var root=$('dm'); if(!root) return;
  var photos=[]; // {url, data}
  var busy=false, heicLib=null;

  var drop=$('dm-drop'), fCam=$('dm-camera'), fPick=$('dm-files'), thumbs=$('dm-thumbs'),
      go=$('dm-go'), msg=$('dm-msg'), busyEl=$('dm-busy'), res=$('dm-res'), form=$('dm-form');

  function showMsg(t){msg.textContent=t;msg.classList.toggle('show',!!t);}
  function isHeic(f){return /hei[cf]/i.test(f.type)||/\.hei[cf]$/i.test(f.name||'');}

  function loadHeicLib(){
    if(heicLib) return heicLib;
    heicLib=new Promise(function(ok,bad){
      var s=document.createElement('script');
      s.src='https://cdn.jsdelivr.net/npm/heic2any@0.0.4/dist/heic2any.min.js';
      s.onload=function(){window.heic2any?ok(window.heic2any):bad(new Error('heic'));};
      s.onerror=function(){bad(new Error('heic'));};
      document.head.appendChild(s);
    });
    return heicLib;
  }

  function decodeBlob(blob){
    if(window.createImageBitmap){
      return createImageBitmap(blob,{imageOrientation:'from-image'}).catch(function(){return viaImg(blob);});
    }
    return viaImg(blob);
  }
  function viaImg(blob){
    return new Promise(function(ok,bad){
      var u=URL.createObjectURL(blob), im=new Image();
      im.onload=function(){URL.revokeObjectURL(u);ok(im);};
      im.onerror=function(){URL.revokeObjectURL(u);bad(new Error('decode'));};
      im.src=u;
    });
  }
  function toJpeg(src){
    var w=src.width||src.naturalWidth, h=src.height||src.naturalHeight;
    if(!w||!h) throw new Error('size');
    var sc=Math.min(1,MAX_SIDE/Math.max(w,h)), cw=Math.round(w*sc), ch=Math.round(h*sc);
    var c=document.createElement('canvas'); c.width=cw; c.height=ch;
    var x=c.getContext('2d'); x.fillStyle='#fff'; x.fillRect(0,0,cw,ch); x.drawImage(src,0,0,cw,ch);
    if(src.close) try{src.close();}catch(e){}
    return c.toDataURL('image/jpeg',0.85);
  }
  // Any picture the browser can open (JPG, PNG, WebP, GIF, AVIF, HEIC) becomes a resized JPEG.
  function prepare(file){
    return decodeBlob(file).then(toJpeg).catch(function(err){
      if(isHeic(file)||!file.type){
        return loadHeicLib().then(function(h){return h({blob:file,toType:'image/jpeg',quality:0.9});})
          .then(function(out){return decodeBlob(Array.isArray(out)?out[0]:out);}).then(toJpeg);
      }
      throw err;
    });
  }

  function addFiles(list){
    showMsg('');
    var files=Array.prototype.slice.call(list||[]);
    if(!files.length) return;
    var room=MAX_PHOTOS-photos.length;
    if(room<=0){showMsg('You can add up to '+MAX_PHOTOS+' photos. Remove one to add another.');return;}
    var take=files.slice(0,room), skipped=files.length-take.length, bad=0;
    var jobs=take.map(function(f){
      if(f.type&&!/^image\//.test(f.type)&&!isHeic(f)){bad++;return Promise.resolve();}
      return prepare(f).then(function(d){photos.push({data:d});}).catch(function(){bad++;});
    });
    setBusyLoad(true);
    Promise.all(jobs).then(function(){
      setBusyLoad(false); render();
      var m=[];
      if(bad) m.push(bad+' file'+(bad>1?'s':'')+' could not be opened. Try a normal photo (JPG, PNG, HEIC, WebP) or take a new picture.');
      if(skipped) m.push('Only '+MAX_PHOTOS+' photos are used.');
      showMsg(m.join(' '));
    });
  }
  function setBusyLoad(on){drop.style.opacity=on?'.6':'';}

  function render(){
    thumbs.innerHTML='';
    photos.forEach(function(p,i){
      var li=document.createElement('li'), im=document.createElement('img'), b=document.createElement('button');
      im.src=p.data; im.alt='Plant photo '+(i+1);
      b.type='button'; b.textContent='×'; b.setAttribute('aria-label','Remove photo '+(i+1));
      b.onclick=function(){photos.splice(i,1);render();};
      li.appendChild(im); li.appendChild(b); thumbs.appendChild(li);
    });
    go.disabled=!photos.length||busy;
  }

  ['dragenter','dragover'].forEach(function(e){drop.addEventListener(e,function(ev){ev.preventDefault();drop.classList.add('over');});});
  ['dragleave','drop'].forEach(function(e){drop.addEventListener(e,function(ev){ev.preventDefault();drop.classList.remove('over');});});
  drop.addEventListener('drop',function(ev){addFiles(ev.dataTransfer&&ev.dataTransfer.files);});
  [fCam,fPick].forEach(function(inp){inp.addEventListener('change',function(){addFiles(inp.files);inp.value='';});});
  $('dm-btn-cam').addEventListener('click',function(){fCam.click();});
  $('dm-btn-pick').addEventListener('click',function(){fPick.click();});

  function el(tag,cls,text){var e=document.createElement(tag);if(cls)e.className=cls;if(text!=null)e.textContent=text;return e;}
  var HEALTH={healthy:'Looks healthy',minor_issues:'Minor issues',needs_attention:'Needs attention',cannot_tell:'Hard to tell'};

  function show(r){
    res.innerHTML='';
    var head=el('div','dm-head');
    head.appendChild(el('span','dm-pill '+r.health,HEALTH[r.health]||HEALTH.cannot_tell));
    if(r.plant) head.appendChild(el('span','dm-pill',r.plant+(r.confidence?' · '+r.confidence+' confidence':'')));
    res.appendChild(head);
    var h=el('h2',null,r.is_plant===false?'That does not look like a plant':'Dr. Mario’s read'); res.appendChild(h);
    if(r.summary) res.appendChild(el('p',null,r.summary));
    if(r.photo_tips) res.appendChild(el('div','dm-note','Photo tip: '+r.photo_tips));
    if(r.problems&&r.problems.length){
      res.appendChild(el('h3',null,'What may be going on'));
      r.problems.forEach(function(p){
        var d=el('div','dm-prob'), s=el('strong',null,p.name); s.appendChild(el('span','tag',p.likelihood==='likely'?'Likely':'Possible')); d.appendChild(s);
        if(p.signs){var a=el('p'); a.appendChild(el('span','k','What I see: ')); a.appendChild(document.createTextNode(p.signs)); d.appendChild(a);}
        if(p.fix){var b=el('p'); b.appendChild(el('span','k','What to do: ')); b.appendChild(document.createTextNode(p.fix)); d.appendChild(b);}
        res.appendChild(d);
      });
    }
    if(r.products&&r.products.length){
      res.appendChild(el('h3',null,'Products that may help'));
      var g=el('div','dm-prods');
      r.products.forEach(function(p){
        var c=el('div','dm-prod'); c.appendChild(el('b',null,p.name)); c.appendChild(el('span','npk',p.npk)); c.appendChild(el('p',null,p.why));
        var a=el('a','btn',"View product"); a.href=p.url; a.target='_blank'; a.rel='noopener'; c.appendChild(a); g.appendChild(c);
      });
      res.appendChild(g);
      var f=el('p','dm-fine'); f.appendChild(document.createTextNode('Follow the directions on the bag, or work out amounts with the '));
      var ca=el('a',null,'soil amendment calculator'); ca.href='/soil-calculator/'; f.appendChild(ca); f.appendChild(document.createTextNode('.')); res.appendChild(f);
    }
    if(r.get_help) res.appendChild(el('div','dm-note',r.get_help));
    res.appendChild(el('p','dm-fine','Dr. Mario is an AI guess from a photo, not a lab test. Check the symptoms in person, and if a plant is declining fast, ask your local garden centre.'));
    var again=el('button','btn','Check another plant'); again.type='button';
    again.onclick=function(){photos=[];render();res.classList.remove('show');form.style.display='';showMsg('');window.scrollTo({top:root.offsetTop-20,behavior:'smooth'});};
    var w=el('p'); w.style.marginTop='22px'; w.appendChild(again); res.appendChild(w);
    res.classList.add('show');
  }

  go.addEventListener('click',function(){
    if(busy||!photos.length) return;
    busy=true; go.disabled=true; showMsg('');
    form.style.display='none'; busyEl.classList.add('show'); res.classList.remove('show');
    var ctl=window.AbortController?new AbortController():null, t=setTimeout(function(){ctl&&ctl.abort();},90000);
    fetch(API,{method:'POST',headers:{'Content-Type':'application/json'},signal:ctl?ctl.signal:undefined,
      body:JSON.stringify({images:photos.map(function(p){return p.data;}),plant:$('dm-plant').value,where:$('dm-where').value,note:$('dm-note').value})})
    .then(function(r){return r.text().then(function(t){var j=null;try{j=JSON.parse(t);}catch(e){}if(!r.ok||!j)throw new Error((j&&j.error)||'Something went wrong. Please try again.');return j;});})
    .then(function(j){busyEl.classList.remove('show');show(j);res.scrollIntoView({behavior:'smooth',block:'start'});})
    .catch(function(e){
      busyEl.classList.remove('show'); form.style.display='';
      showMsg(e.name==='AbortError'?'That took too long. Please try again.':(e.message==='Failed to fetch'?'Could not connect. Check your internet and try again.':e.message));
    })
    .then(function(){clearTimeout(t);busy=false;render();});
  });
  render();
})();
