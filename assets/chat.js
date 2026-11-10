/* Ask Mario: small chat assistant. Talks to /api/chat.php. Plain DOM, no libraries. */
(function () {
  'use strict';
  var KEY = 'mss_chat_v1', MAX = 600, busy = false, msgs = [], open = false;
  var root, panel, log, form, input, sendBtn, launcher;

  function load() { try { var s = JSON.parse(sessionStorage.getItem(KEY) || '[]'); if (Array.isArray(s)) msgs = s.slice(-20); } catch (e) { msgs = []; } }
  function save() { try { sessionStorage.setItem(KEY, JSON.stringify(msgs.slice(-20))); } catch (e) {} }
  function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }

  function bubble(role, text, products) {
    var b = el('div', 'cm cm-' + role);
    String(text).split('\n').forEach(function (line, i) { if (i) b.appendChild(document.createElement('br')); b.appendChild(document.createTextNode(line)); });
    if (products && products.length) {
      var w = el('div', 'cm-prods');
      products.forEach(function (p) {
        var a = el('a', 'cm-prod'); a.href = p.url;
        a.appendChild(el('strong', null, p.name));
        if (p.price) a.appendChild(el('span', null, p.price));
        w.appendChild(a);
      });
      b.appendChild(w);
    }
    log.appendChild(b);
    log.scrollTop = log.scrollHeight;
    return b;
  }

  function greet() {
    bubble('bot', "Hi, I'm Mario's assistant. Ask me about growing, soil, or which of our organic dry amendments fits your plants.");
    var chips = el('div', 'cm-chips');
    ['Which product do I need?', 'How much should I use?', 'Do you ship to my province?'].forEach(function (q) {
      var c = el('button', 'cm-chip', q); c.type = 'button';
      c.addEventListener('click', function () { chips.remove(); send(q); });
      chips.appendChild(c);
    });
    log.appendChild(chips);
  }

  function render() {
    log.textContent = '';
    if (!msgs.length) { greet(); return; }
    msgs.forEach(function (m) { bubble(m.role === 'assistant' ? 'bot' : 'me', m.content, m.products); });
  }

  function send(text) {
    text = String(text || '').trim().slice(0, MAX);
    if (!text || busy) return;
    var chips = log.querySelector('.cm-chips'); if (chips) chips.remove();
    msgs.push({ role: 'user', content: text });
    bubble('me', text);
    input.value = ''; setBusy(true);
    var wait = bubble('bot', 'Thinking...'); wait.classList.add('cm-wait');
    var ctrl = window.AbortController ? new AbortController() : null;
    var timer = setTimeout(function () { if (ctrl) ctrl.abort(); }, 50000);
    fetch('/api/chat.php', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: msgs.slice(-8).map(function (m) { return { role: m.role, content: m.content }; }) }),
      signal: ctrl ? ctrl.signal : undefined
    }).then(function (r) { return r.json().catch(function () { return {}; }).then(function (d) { return { ok: r.ok, d: d }; }); })
      .then(function (x) {
        wait.remove();
        if (!x.ok || !x.d.reply) { bubble('bot', (x.d && x.d.error) || 'Sorry, something went wrong. Please try again, or email us.'); msgs.pop(); save(); return; }
        msgs.push({ role: 'assistant', content: x.d.reply, products: x.d.products || [] });
        bubble('bot', x.d.reply, x.d.products); save();
      })
      .catch(function () { wait.remove(); msgs.pop(); bubble('bot', 'I could not reach the server. Please try again in a moment.'); })
      .then(function () { clearTimeout(timer); setBusy(false); input.focus(); });
  }

  function setBusy(v) { busy = v; sendBtn.disabled = v; panel.setAttribute('aria-busy', v ? 'true' : 'false'); }

  function toggle(v) {
    open = typeof v === 'boolean' ? v : !open;
    root.classList.toggle('is-open', open);
    launcher.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) { if (!log.childNodes.length) render(); setTimeout(function () { input.focus(); }, 50); } else { launcher.focus(); }
  }

  function build() {
    root = el('div', 'chat'); root.id = 'askmario';
    launcher = el('button', 'chat-btn'); launcher.type = 'button'; launcher.setAttribute('aria-expanded', 'false'); launcher.setAttribute('aria-controls', 'askmario-panel');
    launcher.appendChild(el('span', 'chat-btn-ico', '?')); launcher.appendChild(el('span', 'chat-btn-txt', 'Ask Mario'));
    panel = el('div', 'chat-panel'); panel.id = 'askmario-panel'; panel.setAttribute('role', 'dialog'); panel.setAttribute('aria-label', 'Ask Mario chat');
    var head = el('div', 'chat-head'); head.appendChild(el('strong', null, 'Ask Mario'));
    var x = el('button', 'chat-x', '×'); x.type = 'button'; x.setAttribute('aria-label', 'Close chat'); head.appendChild(x);
    log = el('div', 'chat-log'); log.setAttribute('role', 'log'); log.setAttribute('aria-live', 'polite');
    form = el('form', 'chat-form');
    input = el('input'); input.type = 'text'; input.maxLength = MAX; input.placeholder = 'Ask about growing or our products'; input.setAttribute('aria-label', 'Your question'); input.autocomplete = 'off';
    sendBtn = el('button', 'chat-send', 'Send'); sendBtn.type = 'submit';
    form.appendChild(input); form.appendChild(sendBtn);
    var note = el('p', 'chat-note', 'AI assistant. It can make mistakes. For orders, email us.');
    panel.appendChild(head); panel.appendChild(log); panel.appendChild(form); panel.appendChild(note);
    root.appendChild(panel); root.appendChild(launcher);
    document.body.appendChild(root);
    launcher.addEventListener('click', function () { toggle(); });
    x.addEventListener('click', function () { toggle(false); });
    form.addEventListener('submit', function (e) { e.preventDefault(); send(input.value); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && open) toggle(false); });
  }

  function init() { load(); build(); if (msgs.length) { /* restore lazily on first open */ } }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
