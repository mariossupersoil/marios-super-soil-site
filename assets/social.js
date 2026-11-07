/* Loads the live Instagram feed (Behold widget) only when the feed is scrolled into view. */
(function(){
  var box=document.getElementById('igfeed'); if(!box) return;
  var id=box.getAttribute('data-feed'); if(!id) return;
  var done=false;
  function load(){
    if(done) return; done=true;
    var w=document.createElement('behold-widget'); w.setAttribute('feed-id',id); box.appendChild(w);
    var s=document.createElement('script'); s.type='module'; s.src='https://w.behold.so/widget.js'; document.head.appendChild(s);
  }
  if('IntersectionObserver' in window){
    var io=new IntersectionObserver(function(e){if(e[0].isIntersecting){io.disconnect();load();}},{rootMargin:'300px'});
    io.observe(box);
  } else load();
})();
