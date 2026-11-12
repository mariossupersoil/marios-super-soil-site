/* Header product search. Loads /assets/search-index.json on first focus; plain DOM. */
(function () {
  'use strict';
  var form = document.querySelector('.hsearch'); if (!form) return;
  var input = form.querySelector('input'), list = form.querySelector('.hs-list');
  var data = null, alt = [], pop = [], byUrl = {}, loading = false, shown = [], active = -1;
  function el(t, c, x) { var n = document.createElement(t); if (c) n.className = c; if (x != null) n.textContent = x; return n; }
  function load(cb) {
    if (data) return cb();
    if (loading) return; loading = true;
    fetch('/assets/search-index.json').then(function (r) { return r.json(); }).then(function (d) { data = d.items; alt = d.alt || []; pop = d.pop || []; data.forEach(function (x) { byUrl[x.u] = x; }); cb(); }).catch(function () { loading = false; });
  }
  function score(it, toks) {
    var t = it.t.toLowerCase(), k = (it.k + ' ' + (it.d || '')).toLowerCase(), sc = 0;
    for (var i = 0; i < toks.length; i++) {
      var w = toks[i];
      if (t.indexOf(w) === 0) sc += 6; else if (t.indexOf(w) > -1) sc += 4; else if (k.indexOf(w) > -1) sc += 2; else return 0;
    }
    return sc + (it.g ? 0 : 1);
  }
  function search(q) {
    var toks = q.toLowerCase().split(/[^a-z0-9.\-]+/).filter(function (x) { return x.length > 1 || /^\d$/.test(x); });
    if (!toks.length) return [];
    return data.map(function (it) { return { it: it, s: score(it, toks) }; }).filter(function (x) { return x.s > 0; })
      .sort(function (a, b) { return b.s - a.s; }).slice(0, 7).map(function (x) { return x.it; });
  }
  function close() { list.hidden = true; input.setAttribute('aria-expanded', 'false'); active = -1; input.removeAttribute('aria-activedescendant'); }
  function mark(n) {
    var lis = list.querySelectorAll('li[role=option]');
    lis.forEach(function (li, i) { li.classList.toggle('on', i === n); li.setAttribute('aria-selected', i === n ? 'true' : 'false'); });
    active = n; if (n >= 0 && lis[n]) { input.setAttribute('aria-activedescendant', lis[n].id); lis[n].scrollIntoView({ block: 'nearest' }); }
  }
  function addRow(it, i) {
    var li = el('li'); li.setAttribute('role', 'option'); li.id = 'hs-o' + i;
    var a = el('a'); a.href = it.u;
    if (it.i) { var im = el('img'); im.src = it.i; im.alt = ''; im.width = 36; im.height = 47; a.appendChild(im); } else { a.appendChild(el('span', 'hs-ph', it.g === 'Guide' ? 'G' : '#')); }
    var tx = el('span', 'hs-tx'); tx.appendChild(el('strong', null, it.t)); if (it.d) tx.appendChild(el('small', null, it.d)); a.appendChild(tx);
    if (it.g) a.appendChild(el('em', null, it.g));
    li.appendChild(a); list.appendChild(li);
  }
  function note(t) { var n = el('li', 'hs-note', t); n.setAttribute('role', 'presentation'); list.appendChild(n); }
  function render() {
    var q = input.value.trim(), ql = q.toLowerCase();
    list.textContent = '';
    if (q.length < 2) { close(); return; }
    var found = search(q), sims = [], why = '';
    for (var i = 0; i < alt.length && !sims.length; i++) {
      for (var j = 0; j < alt[i].w.length; j++) {
        var w = alt[i].w[j];
        if (ql === w || ql.indexOf(w) > -1 && w.length > 3 || (w.length <= 3 && (' ' + ql + ' ').indexOf(' ' + w + ' ') > -1)) {
          sims = alt[i].u.map(function (u) { return byUrl[u]; }).filter(Boolean); why = alt[i].n; break;
        }
      }
    }
    shown = [];
    var exact = found.filter(function (x) { return !x.g && x.t.toLowerCase().indexOf(ql) > -1; });
    if (sims.length && !exact.length) {
      note('We do not sell "' + q + '", but these are similar: ' + why);
      sims.forEach(function (it) { shown.push(it); addRow(it, shown.length - 1); });
      found = found.filter(function (x) { return sims.indexOf(x) < 0; }).slice(0, 3);
      if (found.length) note('Also matching');
    } else { found = found.slice(0, 7); }
    found.forEach(function (it) { shown.push(it); addRow(it, shown.length - 1); });
    if (!shown.length) {
      note('No exact match for "' + q + '". Popular picks:');
      pop.map(function (u) { return byUrl[u]; }).filter(Boolean).forEach(function (it) { shown.push(it); addRow(it, shown.length - 1); });
      var n = el('li', 'hs-none'); n.appendChild(el('span', null, 'Need help choosing? '));
      var b = el('button', null, 'Ask Mario'); b.type = 'button';
      b.addEventListener('click', function () { close(); var c = document.querySelector('.chat-btn'); if (c) c.click(); });
      n.appendChild(b); list.appendChild(n);
    }
    list.hidden = false; input.setAttribute('aria-expanded', 'true'); active = -1;
  }
  input.addEventListener('focus', function () { load(function () { if (input.value.trim().length > 1) render(); }); });
  input.addEventListener('input', function () { load(render); });
  input.addEventListener('keydown', function (e) {
    var n = list.querySelectorAll('li[role=option]').length;
    if (e.key === 'ArrowDown' && n) { e.preventDefault(); mark((active + 1) % n); }
    else if (e.key === 'ArrowUp' && n) { e.preventDefault(); mark((active - 1 + n) % n); }
    else if (e.key === 'Escape') { close(); }
  });
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var go = function () {
      if (!shown.length) render();
      var t = active >= 0 ? shown[active] : shown[0];
      if (t) location.href = t.u; else render();
    };
    load(go);
  });
  document.addEventListener('click', function (e) { if (!form.contains(e.target)) close(); });
})();
