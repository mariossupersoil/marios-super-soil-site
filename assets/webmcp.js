/* WebMCP: lets in-browser AI agents use this site (read-only tools). Does nothing in browsers without navigator.modelContext. */
(function () {
  var mc = navigator.modelContext;
  if (!mc || typeof mc.registerTool !== 'function') return;
  function out(o) { return { content: [{ type: 'text', text: JSON.stringify(o) }] }; }
  function org() {
    var nodes = document.querySelectorAll('script[type="application/ld+json"]');
    for (var i = 0; i < nodes.length; i++) {
      try { var j = JSON.parse(nodes[i].textContent); var a = Array.isArray(j) ? j : [j];
        for (var k = 0; k < a.length; k++) if (a[k]['@type'] === 'Organization') return a[k]; } catch (e) {}
    }
    return {};
  }
  try {
    mc.registerTool({
      name: 'search_products',
      description: "Search Mario's Super Soil organic dry soil amendments (meals, rock dusts, worm castings, compost, blends). Returns product names, links and a starting price in CAD.",
      inputSchema: { type: 'object', properties: { query: { type: 'string', description: 'What the grower needs, e.g. "bloom", "nitrogen", "clay soil", "tomatoes"' } }, required: ['query'] },
      annotations: { readOnlyHint: true },
      execute: function (args) {
        var q = String((args && args.query) || '').toLowerCase().split(/\s+/).filter(Boolean);
        return fetch('/assets/search-index.json').then(function (r) { return r.json(); }).then(function (d) {
          var hits = (d.items || []).filter(function (i) {
            var hay = (i.t + ' ' + (i.k || '') + ' ' + (i.d || '')).toLowerCase();
            return q.every(function (w) { return hay.indexOf(w) > -1; });
          }).slice(0, 8).map(function (i) { return { name: i.t, url: location.origin + i.u, summary: i.d }; });
          return out({ results: hits });
        });
      }
    });
    mc.registerTool({
      name: 'get_store_info',
      description: "Contact details, shipping area and ordering info for Mario's Super Soil (Mississauga, Ontario, Canada).",
      inputSchema: { type: 'object', properties: {} },
      annotations: { readOnlyHint: true },
      execute: function () {
        var o = org();
        return out({ name: o.name, location: 'Mississauga, Ontario, Canada', ships_to: 'Canada', email: o.email, phone: o.telephone, contact_page: location.origin + '/contact/', shop: location.origin + '/#products', llms: location.origin + '/llms.txt' });
      }
    });
  } catch (e) { /* ignore: API is experimental */ }
})();
