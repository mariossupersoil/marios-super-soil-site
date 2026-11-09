/* Product wall: bags hang on a rail. Drag (or swipe) to slide along it with momentum, tap a bag to take it down.
   Drifts slowly on its own until you touch it. No drifting or swaying for reduced-motion users. */
(function () {
  var root = document.getElementById('room'); if (!root) return;
  var room = root.querySelector('.room'), track = root.querySelector('.roomtrack'), inner = root.querySelector('.rtrack'), wall = root.querySelector('.roomwall');
  var detail = document.getElementById('roomdetail'), store = root.querySelector('.dstore');
  var still = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var x = 0, vel = 0, sway = 0, dragging = false, moved = false, pid = null, last = 0, holdUntil = 0, dir = -1, playing = !still, visible = true, hover = false, suppress = 0, raf = 0, glide = null;
  var samples = [], x0 = 0, px0 = 0, selected = null;
  function min() { return Math.min(0, track.clientWidth - inner.scrollWidth - 24); }
  function clampSoft(v) { var lo = min(); if (v > 0) return v * 0.35; if (v < lo) return lo + (v - lo) * 0.35; return v; }
  function apply() {
    inner.style.transform = 'translate3d(' + x.toFixed(1) + 'px,0,0)';
    inner.style.setProperty('--sway', sway.toFixed(2));
    if (wall) wall.style.transform = 'translate3d(' + (x * 0.25).toFixed(1) + 'px,0,0)';
  }
  function tick(t) {
    raf = 0; var dt = Math.min(((t - (last || t)) / 1000), 0.05); last = t;
    var lo = min();
    if (glide !== null && !dragging) {                              // eased move to a target (arrows, selecting a bag)
      var d = glide - x; if (Math.abs(d) < 0.5) { x = glide; glide = null; vel = 0; } else { var nx = x + d * (1 - Math.exp(-dt * 7)); vel = (nx - x) / Math.max(dt, 0.001); x = nx; }
    } else if (!dragging) {
      if (x > 0 || x < lo) {                                        // spring back after pulling past the end
        var edge = x > 0 ? 0 : lo; x += (edge - x) * (1 - Math.exp(-dt * 10)); vel *= 0.8; if (Math.abs(edge - x) < 0.3) x = edge;
      } else if (Math.abs(vel) > 8) {                               // momentum after a flick
        x += vel * dt; vel *= Math.pow(0.04, dt);
      } else if (playing && !hover && visible && !document.hidden && Date.now() >= holdUntil && lo < -4) {   // slow idle drift, ping-pong
        vel = 0; x += dir * 20 * dt; if (x <= lo) { x = lo; dir = 1; } else if (x >= 0) { x = 0; dir = -1; }
      } else vel = 0;
    }
    var target = still ? 0 : Math.max(-9, Math.min(9, -vel * 0.012));   // bags swing a little with the motion
    sway += (target - sway) * (1 - Math.exp(-dt * 6));
    apply();
    raf = requestAnimationFrame(tick);
  }
  function kick() { if (!raf) { last = 0; raf = requestAnimationFrame(tick); } }
  function hold(ms) { holdUntil = Date.now() + (ms || 4000); }

  // press-and-drag / swipe
  room.addEventListener('pointerdown', function (e) {
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    pid = e.pointerId; x0 = e.clientX; px0 = x; moved = false; glide = null; samples = [[performance.now(), e.clientX]];
  });
  room.addEventListener('pointermove', function (e) {
    if (pid !== e.pointerId) return;
    var dx = e.clientX - x0;
    if (!moved && Math.abs(dx) > 8) { moved = true; dragging = true; try { room.setPointerCapture(pid); } catch (z) {} room.classList.add('drag'); }
    if (!dragging) return;
    hold(6000); x = clampSoft(px0 + dx);
    var n = performance.now(); samples.push([n, e.clientX]); while (samples.length > 2 && n - samples[0][0] > 90) samples.shift();
  });
  function up(e) {
    if (pid !== e.pointerId) return; pid = null;
    if (!dragging) return;
    dragging = false; room.classList.remove('drag'); suppress = Date.now() + 350;
    var a = samples[0], b = samples[samples.length - 1]; vel = b[0] > a[0] ? (b[1] - a[1]) / (b[0] - a[0]) * 1000 : 0;
    hold(6000);
  }
  room.addEventListener('pointerup', up); room.addEventListener('pointercancel', up);
  room.addEventListener('dragstart', function (e) { e.preventDefault(); });
  room.addEventListener('pointerenter', function (e) { if (e.pointerType === 'mouse') hover = true; });
  room.addEventListener('pointerleave', function () { hover = false; hold(1500); });
  room.addEventListener('wheel', function (e) {                       // sideways trackpad swipe or shift+wheel
    var dx = Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : (e.shiftKey ? e.deltaY : 0);
    if (!dx) return; e.preventDefault(); glide = null; hold(5000); x = Math.max(min(), Math.min(0, x - dx)); vel = 0;
  }, { passive: false });

  function slideTo(v) { glide = Math.max(min(), Math.min(0, v)); hold(5000); kick(); }
  root.querySelectorAll('.rbtn[data-dir]').forEach(function (b) { b.addEventListener('click', function () { slideTo(x - (+b.dataset.dir) * track.clientWidth * 0.7); }); });
  var pb = root.querySelector('.playbtn');
  function sync() { pb.innerHTML = playing ? '&#10074;&#10074;' : '&#9654;'; pb.setAttribute('aria-label', playing ? 'Pause sliding' : 'Start sliding'); }
  pb.addEventListener('click', function () { playing = !playing; holdUntil = 0; sync(); }); sync();
  track.addEventListener('keydown', function (e) { if (e.key === 'ArrowLeft') { e.preventDefault(); slideTo(x + 240); } else if (e.key === 'ArrowRight') { e.preventDefault(); slideTo(x - 240); } });

  // take a bag down
  function centerOn(li) { var c = li.offsetLeft + li.offsetParent.offsetLeft + li.offsetWidth / 2; slideTo(track.clientWidth / 2 - c); }
  function select(btn) {
    var li = btn.closest('.rbag'), slug = btn.dataset.slug;
    root.querySelectorAll('.rbag.sel').forEach(function (n) { n.classList.remove('sel'); });
    if (selected === slug) { selected = null; detail.hidden = true; detail.innerHTML = ''; return; }
    selected = slug; li.classList.add('sel'); centerOn(li);
    var t = store.querySelector('.dtpl[data-slug="' + slug + '"]'); if (!t) return;
    detail.innerHTML = ''; var box = document.createElement('div'); box.className = 'dcard'; box.style.cssText = t.getAttribute('style') || ''; box.innerHTML = t.innerHTML;
    var x2 = document.createElement('button'); x2.type = 'button'; x2.className = 'dclose'; x2.setAttribute('aria-label', 'Put it back'); x2.textContent = '×';
    x2.addEventListener('click', function () { var s = root.querySelector('.rbag.sel button'); if (s) select(s); });
    box.appendChild(x2); detail.appendChild(box); detail.hidden = false;
    try { detail.scrollIntoView({ block: 'nearest', behavior: still ? 'auto' : 'smooth' }); } catch (z) {}
  }
  root.querySelectorAll('.rbag button').forEach(function (b) {
    b.addEventListener('click', function (e) { if (Date.now() < suppress) { e.preventDefault(); return; } hold(8000); select(b); });
    b.addEventListener('focus', function () { if (pid === null) { var li = b.closest('.rbag'); var c = li.offsetLeft + li.offsetParent.offsetLeft + li.offsetWidth / 2 + x; if (c < 40 || c > track.clientWidth - 40) centerOn(li); } });
  });
  if ('IntersectionObserver' in window) new IntersectionObserver(function (e) { visible = e[0].isIntersecting; }).observe(room);
  window.addEventListener('resize', function () { x = Math.max(min(), Math.min(0, x)); });
  kick();
})();
