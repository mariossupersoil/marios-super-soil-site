/* Turning ring of bags, one product type at a time. Stops on hover, focus or touch; never turns for reduced-motion users. */
(function () {
  var root = document.getElementById('ring'); if (!root) return;
  var still = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var tabs = [].slice.call(root.querySelectorAll('[role=tab]'));
  var panels = [].slice.call(root.querySelectorAll('.ringpanel'));
  var suppress = 0, playing = !still, cur = null, active = 0, paused = false, visible = true, holdUntil = 0;
  function items() { return [].slice.call(cur.querySelectorAll('.rit')); }
  function layout() {
    var its = items(), n = its.length, w = cur.querySelector('.ringstage').clientWidth;
    var gap = Math.min(w * 0.22, 190);
    its.forEach(function (el, i) {
      var k = i - active; if (k > n / 2) k -= n; if (k < -n / 2) k += n;
      var ak = Math.abs(k), show = ak <= 2;
      el.classList.toggle('on', k === 0);
      el.style.opacity = show ? (ak === 0 ? 1 : ak === 1 ? 0.9 : 0.55) : 0;
      el.style.pointerEvents = show ? 'auto' : 'none';
      el.style.zIndex = 10 - ak;
      el.style.transform = 'translateX(calc(-50% + ' + (k * gap) + 'px)) translateZ(' + (-ak * 140) + 'px) rotateY(' + (-k * 26) + 'deg) scale(' + (ak === 0 ? 1 : 0.86) + ')';
      var a = el.querySelector('a'); if (a) a.tabIndex = (k === 0) ? 0 : -1;
    });
    var bar = cur.querySelector('.ringbar'); if (bar) bar.value = active;
  }
  function go(d, hold) { var n = items().length; active = (active + d + n) % n; if (hold) holdUntil = Date.now() + 6000; layout(); }
  function show(cat) {
    tabs.forEach(function (t) { t.setAttribute('aria-selected', t.dataset.cat === cat); });
    panels.forEach(function (p) { var on = p.id === 'ring-' + cat; p.hidden = !on; if (on) cur = p; });
    active = 0; holdUntil = Date.now() + 4000; setup();
  }
  function setup() {
    var n = items().length;
    var bar = cur.querySelector('.ringbar'); if (bar) bar.hidden = n < 3;
    if (n < 3) { cur.classList.remove('ring-on'); return; } // two bags: just show them
    cur.classList.add('ring-on'); layout();
  }
  tabs.forEach(function (t) { t.addEventListener('click', function () { show(t.dataset.cat); }); });
  panels.forEach(function (p) {
    var bar = p.querySelector('.ringbar');
    if (bar) bar.addEventListener('input', function () { cur = p; active = +bar.value; holdUntil = Date.now() + 6000; layout(); });
    p.querySelectorAll('.rbtn[data-dir]').forEach(function (b) { b.addEventListener('click', function () { cur = p; go(+b.dataset.dir, true); }); });
    p.querySelectorAll('.rit').forEach(function (el, i) {
      el.addEventListener('click', function (e) { if (Date.now() < suppress) { e.preventDefault(); return; } if (!p.classList.contains('ring-on')) return; if (i !== active) { e.preventDefault(); active = i; holdUntil = Date.now() + 6000; layout(); } });
    });
    p.addEventListener('pointerenter', function () { paused = true; });
    p.addEventListener('pointerleave', function () { paused = false; holdUntil = Date.now() + 1500; });
    p.addEventListener('focusin', function (e) { try { if (e.target.matches(':focus-visible')) paused = true; } catch (x) {} }); // keyboard users only
    p.addEventListener('focusout', function () { paused = false; });
    p.addEventListener('touchstart', function () { holdUntil = Date.now() + 6000; }, { passive: true });
    var sx = null;
    p.addEventListener('dragstart', function (e) { e.preventDefault(); });
    p.addEventListener('pointerdown', function (e) { sx = e.target.closest('.ringbar, .rbtn') ? null : e.clientX; });
    p.addEventListener('pointerup', function (e) {
      if (sx !== null && Math.abs(e.clientX - sx) > 40) { cur = p; var n = Math.max(1, Math.round(Math.abs(e.clientX - sx) / 140)); go(e.clientX < sx ? n : -n, true); suppress = Date.now() + 400; }
      sx = null;
    });
  });
  cur = panels[0]; setup();
  window.addEventListener('resize', function () { if (cur.classList.contains('ring-on')) layout(); });
  if ('IntersectionObserver' in window) new IntersectionObserver(function (e) { visible = e[0].isIntersecting; }).observe(root);
  function syncBtns() { root.querySelectorAll('.playbtn').forEach(function (b) { b.innerHTML = playing ? '&#10074;&#10074;' : '&#9654;'; b.setAttribute('aria-label', playing ? 'Pause turning' : 'Play turning'); }); }
  root.querySelectorAll('.playbtn').forEach(function (b) { b.addEventListener('click', function () { playing = !playing; holdUntil = 0; syncBtns(); }); });
  syncBtns();
  setInterval(function () { if (playing && !paused && visible && !document.hidden && Date.now() >= holdUntil && cur.classList.contains('ring-on')) go(1); }, 2000);
})();
