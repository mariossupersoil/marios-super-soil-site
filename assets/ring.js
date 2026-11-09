/* Turning ring of bags, one product type at a time.
   The ring follows your finger or mouse continuously (no lifting, no steps), glides on after you let go, then settles on a bag.
   It turns by itself, stops on hover, touch or keyboard focus, and never turns on its own for reduced-motion users. */
(function () {
  var root = document.getElementById('ring'); if (!root) return;
  var still = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var tabs = [].slice.call(root.querySelectorAll('[role=tab]'));
  var panels = [].slice.call(root.querySelectorAll('.ringpanel'));
  var playing = !still, paused = false, visible = true, holdUntil = 0, suppress = 0;
  var P = null;                                   // current panel state

  function make(el) {
    var its = [].slice.call(el.querySelectorAll('.rit'));
    return { el: el, its: its, n: its.length, pos: 0, target: null, bar: el.querySelector('.ringbar'), on: false, raf: 0, last: 0 };
  }
  var states = panels.map(make);

  function wrapK(i, pos, n) { var k = (i - pos) % n; if (k > n / 2) k -= n; if (k < -n / 2) k += n; return k; }
  function render(S) {
    var w = S.el.querySelector('.ringstage').clientWidth, gap = Math.min(w * 0.22, 190), best = 0, bk = 9;
    S.its.forEach(function (el, i) {
      var k = wrapK(i, S.pos, S.n), ak = Math.abs(k), kc = Math.max(-2, Math.min(2, k));
      var op = ak <= 1 ? 1 - 0.1 * ak : ak <= 2 ? 0.9 - 0.35 * (ak - 1) : Math.max(0, 0.55 * (1 - (ak - 2) / 0.6));
      el.style.opacity = op;
      el.style.pointerEvents = ak < 2.2 ? 'auto' : 'none';
      el.style.zIndex = Math.round(100 - ak * 10);
      var cap = Math.max(0, 1 - ak * 1.6); el.style.setProperty('--cap', cap); el.style.filter = 'brightness(' + (0.55 + 0.45 * cap).toFixed(2) + ')';
      el.style.transform = 'translateX(calc(-50% + ' + (k * gap).toFixed(1) + 'px)) translateZ(' + (-Math.min(ak, 2.6) * 140).toFixed(0) + 'px) rotateY(' + (-kc * 26).toFixed(1) + 'deg) scale(' + (1 - 0.14 * Math.min(ak, 1)).toFixed(3) + ')';
      var a = el.querySelector('a'); if (a) a.tabIndex = ak < 0.5 ? 0 : -1;
      if (ak < bk) { bk = ak; best = i; }
    });
    S.front = best;
    if (S.bar && !S.barDrag) S.bar.value = Math.min(S.n - 1, ((S.pos % S.n) + S.n) % S.n);
  }
  function loop(t) {
    var S = P; if (!S) return;
    S.raf = 0;
    var dt = Math.min(((t - (S.last || t)) / 1000), 0.05); S.last = t;
    if (S.target !== null && !S.drag) {
      var d = S.target - S.pos;
      if (Math.abs(d) < 0.002) { S.pos = S.target; S.target = null; }
      else S.pos += d * (1 - Math.exp(-dt * 8));
    }
    render(S);
    if (S.target !== null || S.drag) S.raf = requestAnimationFrame(loop); else S.last = 0;
  }
  function kick() { if (P && !P.raf) { P.last = 0; P.raf = requestAnimationFrame(loop); } }
  function glideTo(target) { P.target = target; kick(); }
  function step(d, hold) { if (hold) holdUntil = Date.now() + 5000; glideTo(Math.round(P.pos) + d); }

  function setup(S) {
    if (S.bar) S.bar.hidden = S.n < 3;
    if (S.n < 3) { S.el.classList.remove('ring-on'); return; }
    S.el.classList.add('ring-on'); S.pos = 0; S.target = null; render(S);
  }
  function show(cat) {
    tabs.forEach(function (t) { t.setAttribute('aria-selected', t.dataset.cat === cat); });
    panels.forEach(function (p, i) { var on = p.id === 'ring-' + cat; p.hidden = !on; if (on) P = states[i]; });
    holdUntil = Date.now() + 4000; setup(P);
  }
  tabs.forEach(function (t) { t.addEventListener('click', function () { show(t.dataset.cat); }); });

  states.forEach(function (S) {
    var p = S.el, stage = p.querySelector('.ringstage');
    p.addEventListener('dragstart', function (e) { e.preventDefault(); });
    p.addEventListener('pointerenter', function () { paused = true; });
    p.addEventListener('pointerleave', function () { paused = false; holdUntil = Date.now() + 1500; });
    p.addEventListener('focusin', function (e) { try { if (e.target.matches(':focus-visible')) paused = true; } catch (x) {} });
    p.addEventListener('focusout', function () { paused = false; });
    p.querySelectorAll('.rbtn[data-dir]').forEach(function (b) { b.addEventListener('click', function () { P = S; step(+b.dataset.dir, true); }); });

    // slider bar: follows the handle continuously, settles on release
    if (S.bar) {
      S.bar.step = 'any';
      S.bar.addEventListener('input', function () { P = S; S.barDrag = true; S.target = null; S.pos = +S.bar.value; holdUntil = Date.now() + 6000; render(S); });
      var endBar = function () { if (!S.barDrag) return; S.barDrag = false; P = S; glideTo(Math.round(S.pos)); };
      S.bar.addEventListener('change', endBar); S.bar.addEventListener('pointerup', endBar); S.bar.addEventListener('keyup', endBar);
    }

    // press-and-drag / swipe on the bags: the ring follows the pointer, then glides on with a little momentum
    var gap = function () { return Math.min(stage.clientWidth * 0.22, 190); };
    var x0 = 0, pos0 = 0, id = null, samples = [];
    stage.addEventListener('pointerdown', function (e) {
      if (!S.el.classList.contains('ring-on') || (e.pointerType === 'mouse' && e.button !== 0)) return;
      P = S; id = e.pointerId; x0 = e.clientX; pos0 = S.pos; S.drag = false; samples = [[performance.now(), e.clientX]];
    });
    stage.addEventListener('pointermove', function (e) {
      if (id !== e.pointerId) return;
      var dx = e.clientX - x0;
      if (!S.drag && Math.abs(dx) > 8) { S.drag = true; S.target = null; try { stage.setPointerCapture(id); } catch (x) {} kick(); }
      if (!S.drag) return;
      holdUntil = Date.now() + 6000;
      S.pos = pos0 - dx / (gap() * 0.85);
      var now = performance.now(); samples.push([now, e.clientX]); while (samples.length > 2 && now - samples[0][0] > 90) samples.shift();
    });
    var up = function (e) {
      if (id !== e.pointerId) return;
      id = null;
      if (!S.drag) return;
      S.drag = false; suppress = Date.now() + 350;
      var a = samples[0], b = samples[samples.length - 1], v = (b[0] > a[0]) ? (b[1] - a[1]) / (b[0] - a[0]) : 0;   // px per ms
      var proj = S.pos - (v / (gap() * 0.85)) * 260;                                                              // momentum
      holdUntil = Date.now() + 5000; glideTo(Math.round(proj));
    };
    stage.addEventListener('pointerup', up); stage.addEventListener('pointercancel', up);
    S.its.forEach(function (el, i) {
      el.addEventListener('click', function (e) {
        if (Date.now() < suppress) { e.preventDefault(); return; }
        if (!S.el.classList.contains('ring-on')) return;
        if (i !== S.front) { e.preventDefault(); P = S; holdUntil = Date.now() + 5000; glideTo(S.pos + wrapK(i, S.pos, S.n)); }
      });
    });
  });

  P = states[0]; setup(P);
  window.addEventListener('resize', function () { if (P.el.classList.contains('ring-on')) render(P); });
  if ('IntersectionObserver' in window) new IntersectionObserver(function (e) { visible = e[0].isIntersecting; }).observe(root);
  function syncBtns() { root.querySelectorAll('.playbtn').forEach(function (b) { b.innerHTML = playing ? '&#10074;&#10074;' : '&#9654;'; b.setAttribute('aria-label', playing ? 'Pause turning' : 'Play turning'); }); }
  root.querySelectorAll('.playbtn').forEach(function (b) { b.addEventListener('click', function () { playing = !playing; holdUntil = 0; syncBtns(); }); });
  syncBtns();
  setInterval(function () { if (playing && !paused && visible && !document.hidden && Date.now() >= holdUntil && P.el.classList.contains('ring-on') && !P.drag && !P.barDrag) glideTo(Math.round(P.pos) + 1); }, 2200);
})();
