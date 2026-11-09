/* Each goal group slides up and fades in as it scrolls into view. No effect for reduced-motion users or if JS is off. */
(function () {
  var g = document.querySelector('.guide'); if (!g) return;
  if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if (!('IntersectionObserver' in window)) return;
  var blocks = [].slice.call(g.querySelectorAll('.gblock'));
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
  }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });
  blocks.forEach(function (b) { b.classList.add('pre'); io.observe(b); });
})();
