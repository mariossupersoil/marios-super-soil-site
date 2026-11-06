(function(){
  var $=function(id){return document.getElementById(id)};
  // copy email
  var copy=$("copy");
  if(copy){
    copy.addEventListener("click",function(){
      var el=$("mail"), txt=el.textContent;
      var done=function(){copy.textContent="Copied";setTimeout(function(){copy.textContent="Copy email"},1800)};
      var fallback=function(){
        var r=document.createRange(); r.selectNodeContents(el);
        var s=window.getSelection(); s.removeAllRanges(); s.addRange(r);
      };
      try{ navigator.clipboard.writeText(txt).then(done,fallback); }catch(e){ fallback(); }
    });
  }
  // feeding calculator: 1 tbsp per gallon total, split 3:2 by stage (from the 5-gallon example)
  if($("gal")){
    var stage="veg";
    var frac=function(x){
      var q=Math.round(x*4)/4, w=Math.floor(q), f=Math.round((q-w)*4)/4;
      var g={0:"",0.25:"¼",0.5:"½",0.75:"¾"}[f];
      return (w?String(w):"")+g||"0";
    };
    var calc=function(){
      var n=parseFloat($("gal").value);
      if(!(n>0)){$("c-lu").textContent="–";$("c-fp").textContent="–";return}
      n=Math.min(n,100);
      var lu=stage==="veg"?0.6*n:0.4*n, fp=stage==="veg"?0.4*n:0.6*n;
      $("c-lu").textContent=frac(lu); $("c-fp").textContent=frac(fp);
      $("st-veg").setAttribute("aria-pressed",stage==="veg");
      $("st-flo").setAttribute("aria-pressed",stage==="flo");
    };
    $("gal").addEventListener("input",calc);
    $("st-veg").addEventListener("click",function(){stage="veg";calc()});
    $("st-flo").addEventListener("click",function(){stage="flo";calc()});
    calc();
  }
})();
