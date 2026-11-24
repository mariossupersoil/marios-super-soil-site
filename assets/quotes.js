/* Slow drifting reviews row, same behaviour as the product rail. Stops on hover, focus or touch, and never moves for people who prefer reduced motion. */
(function () {
  var rail = document.getElementById('rvrail'); if (!rail) return;
  var track = rail.querySelector('.rvtrack');
  var still = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var pos = 0, dir = 1, paused = false, visible = true, resumeAt = 0, last = 0, SPEED = 22; // pixels per second
  function max() { return track.scrollWidth - track.clientWidth; }
  function hold(ms) { resumeAt = Date.now() + (ms || 3500); pos = track.scrollLeft; }
  function tick(t) {
    if (!last) last = t;
    var dt = Math.min(t - last, 100); last = t;
    if (!still && !paused && visible && !document.hidden && Date.now() >= resumeAt && max() > 4) {
      pos += dir * SPEED * dt / 1000;
      if (pos >= max()) { pos = max(); dir = -1; } else if (pos <= 0) { pos = 0; dir = 1; }
      track.scrollLeft = pos;
    }
    requestAnimationFrame(tick);
  }
  ['pointerenter', 'focusin'].forEach(function (e) { rail.addEventListener(e, function () { paused = true; }); });
  ['pointerleave', 'focusout'].forEach(function (e) { rail.addEventListener(e, function () { paused = false; hold(1500); }); });
  ['touchstart', 'wheel', 'pointerdown', 'keydown'].forEach(function (e) { track.addEventListener(e, function () { hold(5000); }, { passive: true }); });
  track.addEventListener('scroll', function () { if (Date.now() < resumeAt || paused) pos = track.scrollLeft; }, { passive: true });
  rail.querySelectorAll('.rbtn').forEach(function (b) {
    b.addEventListener('click', function () { hold(5000); track.scrollBy({ left: +b.dataset.dir * track.clientWidth * 0.8, behavior: 'smooth' }); });
  });
  if ('IntersectionObserver' in window) new IntersectionObserver(function (e) { visible = e[0].isIntersecting; }).observe(rail);
  requestAnimationFrame(tick);
})();
