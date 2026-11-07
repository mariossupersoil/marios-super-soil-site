#!/usr/bin/env python3
"""Generate the static site from data/site.json and data/products.json.

Run from the repo root:  python3 tools/build.py
Hostinger serves the repo files as-is (no build step), so the generated HTML is committed.
Edit the data files (or this template), rebuild, then commit everything.
"""
import hashlib, html, json, pathlib, datetime, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "data/site.json").read_text())
PRODUCTS = json.loads((ROOT / "data/products.json").read_text())
HASH_FILE = ROOT / "data/.page-hashes.json"
TODAY = datetime.date.today().isoformat()
BASE = SITE["base_url"].rstrip("/")


def esc(s):
    return html.escape(str(s), quote=True)


def npk_text(p):
    return " - ".join(str(x) for x in p["npk"])


def npk_dash(p):
    return "-".join(str(x) for x in p["npk"])


def name_html(p):
    return f'<b>{esc(p["a"])}</b> <i>{esc(p["b"])}</i>'


def plain_name(p):
    return f'{p["a"]} {p["b"]}'


def abs_url(path):
    return BASE + path


# ---------------------------------------------------------------- shared pieces
def head(title, description, path, og_image="/img/og-image.jpg?v=3", jsonld=None, noindex=False):
    robots = '<meta name="robots" content="noindex, nofollow">\n' if (SITE["staging"] or noindex) else ""
    ld = ""
    for obj in (jsonld or []):
        ld += '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>\n"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
{robots}<link rel="canonical" href="{esc(abs_url(path))}">
<meta name="theme-color" content="#0e0e0f">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(SITE['name'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(abs_url(path))}">
<meta property="og:image" content="{esc(abs_url(og_image))}">
<meta property="og:locale" content="en_CA">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" sizes="32x32" href="/img/favicon-32.png?v=3">
<link rel="apple-touch-icon" href="/img/apple-touch-icon.png?v=3">
<link rel="preload" href="/assets/fonts/anton-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/oswald-latin-300-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/style.css?v=10">
{ld}</head>
<body id="top">
"""


def header():
    gu = (SITE.get("google_review_url") or "").strip()
    gl = f'<a class="tb-g" href="{esc(gu)}" target="_blank" rel="noopener">&#9733; Review us on Google</a>' if gu else ""
    return f"""<div class="topbar"><div class="wrap"><span>Free 2 lb Level Up or Flower Power on orders over $120</span><a href="/wholesale/">Wholesale</a>{gl}</div></div>
<header>
  <div class="wrap">
    <a class="brand" href="/"><img src="/img/logo.png?v=3" width="54" height="54" alt="Mario's Super Soil logo"><span>Mario's Super Soil</span></a>
    <nav aria-label="Main">
      <a href="/#products">Products</a>
      <a href="/#blends">Blends</a>
      <a href="/#buy">Where to buy</a>
      <a href="/plant-drmario/">Plant Dr. Mario</a>
      <a href="/soil-calculator/">Calculator</a>
      <a href="/wholesale/">Wholesale</a>
      <a href="/#faq">FAQ</a>
      <a href="/#mission">About</a>
      <a href="/#contact">Contact</a>
    </nav>
    <a class="cartlink" href="/cart/" aria-label="Shopping cart">Cart <span id="cart-n" class="cartn">0</span></a>
    <a class="btn solid" href="/#products">Shop online</a>
  </div>
</header>
<main>
"""


def google_review(cls="gr"):
    u = (SITE.get("google_review_url") or "").strip()
    if not u:
        return ""
    return (f'<div class="{cls}"><p><strong>Happy with your soil?</strong> A quick Google review helps other Canadian gardeners find us.</p>'
            f'<p><a class="btn" href="{esc(u)}" target="_blank" rel="noopener">Review us on Google</a></p></div>')


def footer():
    L = SITE["links"]
    GR_FOOT = ('      <a href="' + esc(SITE["google_review_url"]) + '" target="_blank" rel="noopener">Review us on Google</a>\n') if (SITE.get("google_review_url") or "").strip() else ""
    return f"""</main>
<footer>
  <div class="wrap">
    <strong>A Canadian company, Mississauga, Ontario</strong>
    <p>Store in a cool, dry place, away from moisture. <span lang="fr">Conserver dans un endroit frais et sec, à l'abri de l'humidité.</span></p>
    <p>Dust hazard. Wear an appropriate dust mask when handling.</p>
    <nav class="flinks" aria-label="More from Mario's Super Soil">
      <a href="/wholesale/">Wholesale</a>
      <a href="/shipping-returns/">Shipping &amp; returns</a>
{GR_FOOT}      <a href="{esc(L['blog'])}" target="_blank" rel="noopener">Blog</a>
      <a href="/shipping-returns/">Refund policy</a>
      <a href="{esc(L['privacy'])}" target="_blank" rel="noopener">Privacy policy</a>
    </nav>
  </div>
</footer>
<script src="/assets/app.js" defer></script>
<script src="/assets/cart.js?v=6" defer></script>
<script src="/assets/social.js?v=1" defer></script>
<script src="/assets/popup.js?v=1" defer></script>
</body>
</html>
"""


def size_key(label):
    return re.sub(r"\s+", "", label.split("(")[0].strip().lower())


def default_kg(label):
    """Shipping weight guess: lb sizes by weight; gallon/litre sizes use the heavy end (5 lb per gallon). Editable in api/prices.json."""
    m = re.match(r"([\d.]+)\s*(lb|gallons?|l)\b", label.strip().lower())
    n, u = float(m.group(1)), m.group(2)
    if u == "lb": return round(n * 0.4536, 2)
    if u == "l": return round(n * 0.6, 2)
    return round(n * 2.27, 2)


def sync_prices():
    """api/prices.json holds the real prices (edit by hand). This keeps its structure in step with products.json
    and never invents or overwrites a price. null = no price yet, so the item can't be bought."""
    f = ROOT / "api/prices.json"
    old = json.loads(f.read_text()) if f.exists() else {}
    oldp = old.get("products", {})
    prods = {}
    for p in PRODUCTS:
        sizes = {}
        for lab in p["sizes"]:
            k = size_key(lab)
            o = oldp.get(p["slug"], {}).get("sizes", {}).get(k, {})
            sizes[k] = {"label": lab, "price": o.get("price"), "weight_kg": o.get("weight_kg", default_kg(lab))}
            m = re.match(r"(\d+) lb \(.*= (\d+) x 5 lb", lab)
            if m:  # packed as several 5 lb bags: price and stock come from the 5lb size
                sizes[k]["pack_of"] = int(m.group(2)); sizes[k]["pack_from"] = "5lb"; sizes[k]["price"] = None
        prods[p["slug"]] = {"name": f"{plain_name(p)} {npk_dash(p)}", "img": f"/img/{p['f']}-front.webp", "sizes": sizes}
    out = {"currency": "CAD", "note": "Prices in Canadian dollars before tax and shipping, for example 24.99. null means no price yet.", "products": prods}
    f.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")


_PRICES = None


def price_rows(slug):
    """Effective list prices from api/prices.json: [(short label, price)]. 10 and 20 lb are packs of the 5 lb bag."""
    global _PRICES
    if _PRICES is None:
        _PRICES = json.loads((ROOT / "api/prices.json").read_text())["products"]
    sizes = _PRICES.get(slug, {}).get("sizes", {})
    out = []
    for k, z in sizes.items():
        pr = z.get("price")
        if z.get("pack_of") and z.get("pack_from"):
            base = sizes.get(z["pack_from"], {}).get("price")
            pr = round(base * z["pack_of"], 2) if base else None
        if pr:
            out.append((z["label"].split(" (")[0], pr))
    return out


def price_line(p):
    rows = price_rows(p["slug"])
    if not rows:
        return f'<p class="pricefrom" id="price-from" data-slug="{p["slug"]}"><span>Price coming soon</span></p>'
    low = min(x[1] for x in rows)
    each = " · ".join(f"{esc(l)} ${v:,.2f}" for l, v in rows)
    return (f'<p class="pricefrom" id="price-from" data-slug="{p["slug"]}"><strong>From ${low:,.2f} CAD</strong> '
            f'<span>{each}</span></p>')


def sizes_text(p):
    return " · ".join(p["sizes"])


def picker_item(p, eager=False):
    load = "" if eager else ' loading="lazy"'
    return (f'<li><a class="pick" data-slug="{p["slug"]}" href="/products/{p["slug"]}/" style="--accent:{p["accent"]}">'
            f'<img src="/img/{p["f"]}-front.webp" width="170" height="250"{load} alt="{esc(plain_name(p))} {esc(npk_dash(p))} organic fertilizer stand-up pouch">'
            f'<span class="nm">{name_html(p)}</span><span class="npk">{esc(npk_text(p))}</span>'
            + (f'<span class="from">From ${min(x[1] for x in price_rows(p["slug"])):,.2f}</span>' if price_rows(p["slug"]) else '')
            + '</a></li>')


def org_ld():
    a = SITE["address"]
    return {
        "@context": "https://schema.org", "@type": "Organization",
        "name": SITE["name"], "url": BASE + "/", "logo": abs_url("/img/logo.png?v=3"),
        "email": SITE["email"], "telephone": "+1-" + SITE["phone"],
        "foundingDate": "2019",
        "address": {"@type": "PostalAddress", "streetAddress": a["street"], "addressLocality": a["city"],
                    "addressRegion": a["region"], "addressCountry": a["country"]},
        "sameAs": [u for _, u in SITE["social"]],
    }


# ---------------------------------------------------------------- home
def build_home():
    H = SITE["home"]
    ld = [org_ld(),
          {"@context": "https://schema.org", "@type": "WebSite", "name": SITE["name"], "url": BASE + "/"},
          {"@context": "https://schema.org", "@type": "FAQPage",
           "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in SITE["faq"]]}]
    out = head(H["title"], H["description"], "/", jsonld=ld)
    out += header()
    # hero
    out += f"""  <section class="hero">
    <div class="wrap">
      <div class="hero-top">
        <div>
          <h1>{H['h1']}</h1>
          <span class="tag">Premium quality, made in Canada</span>
        </div>
        <div>
          <p class="lede">{esc(H['lede'])}</p>
          <div class="ctas">
            <a class="btn solid" href="/#products">Shop online</a>
            <a class="btn" href="/#buy">Find a store</a>
          </div>
        </div>
      </div>
      <ul class="picker" aria-label="Our organic fertilizers and amendments">
        {''.join(picker_item(p, eager=True) for p in PRODUCTS)}
      </ul>
    </div>
  </section>
"""
    # compare
    rows = ""
    maxv = 11.0
    for p in PRODUCTS:
        def bar(v):
            return f'<div class="bar"><em>{v}</em><span style="width:{max(0, v / maxv * 70):.0f}%"></span></div>'
        rows += (f'<tr style="--accent:{p["accent"]}"><td class="p"><a href="/products/{p["slug"]}/">{name_html(p)}</a></td>'
                 f'<td>{bar(p["npk"][0])}</td><td>{bar(p["npk"][1])}</td><td>{bar(p["npk"][2])}</td>'
                 f'<td class="a">{esc(p["when"])}</td><td class="a">{"<br>".join(esc(x) for x in p["sizes"])}</td></tr>')
    out += f"""  <section id="products" class="sec">
    <div class="wrap">
      <h2>Organic fertilizers and soil amendments</h2>
      <p class="lede">Six single-ingredient bags, each with a clear job. Guaranteed analysis in percent; bars share one scale so you can see which product leads in nitrogen, phosphorus or potassium.</p>
      <div class="tablewrap">
        <table>
          <caption class="sr">Nutrient comparison of Mario's Super Soil organic amendments</caption>
          <thead><tr><th scope="col">Product</th><th scope="col">Nitrogen (N)</th><th scope="col">Phosphorus (P)</th><th scope="col">Potassium (K)</th><th scope="col">How much and when</th><th scope="col">Sizes</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </div>
  </section>
"""
    # blends + calculator
    blends = ""
    for b in SITE["blends"]:
        dl = "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in b["rows"])
        blends += f"""        <article class="blend" style="--accent:{b['accent']}">
          <div><h3 class="nm"><b>{esc(b['a'])}</b> <i>{esc(b['b'])}</i></h3><p class="bsub">{esc(b['tagline'])}</p></div>
          <div><p>{esc(b['text'])}</p><dl>{dl}</dl></div>
        </article>
"""
    out += f"""  <section id="blends" class="sec">
    <div class="wrap">
      <h2>Blends and kits</h2>
      <p class="lede">Two all-in-one dry blends that combine several of the amendments above, and a kit that puts the range in one box.</p>
      <div class="blends">
{blends}      </div>
      <div class="calc" id="calc">
        <h3>Feeding calculator</h3>
        <p class="lede">Works out how much of each blend to mix in for your pot. It scales the 1 tablespoon per gallon rate and the 5 gallon example from our product pages.</p>
        <div class="crow">
          <label for="gal">Pot size in gallons</label>
          <input id="gal" type="number" min="1" max="100" step="1" value="5" inputmode="numeric">
          <div class="langs" role="group" aria-label="Growth stage">
            <button type="button" id="st-veg" aria-pressed="true">Vegetative</button>
            <button type="button" id="st-flo" aria-pressed="false">Flowering</button>
          </div>
        </div>
        <div class="cout" aria-live="polite">
          <div><span class="big" id="c-lu">3</span><span>tbsp Level Up 3-3-3</span></div>
          <div><span class="big" id="c-fp">2</span><span>tbsp Flower Power 2-6-4</span></div>
        </div>
        <p class="store">Mix into the soil and water in. <a href="/soil-calculator/">Open the full product calculator</a></p>
      </div>
    </div>
  </section>
"""
    # buy
    stores = ""
    for s in SITE["stores"]:
        link = f'<a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(re.sub(r"^https?://(www\.)?|/.*$", "", s["url"]))}</a>' if s["url"] else ""
        extra = (f'<span>Hours: {esc(s["hours"])}</span>' if s.get("hours") else "") + (f'<span>Carries: {esc(s["carries"])}</span>' if s.get("carries") else "")
        stores += f'<li><strong>{esc(s["name"])}</strong><span>{esc(s["address"])}</span><span>{esc(s["phone"])}</span>{extra}{link}</li>'
    out += f"""  <section id="buy" class="sec">
    <div class="wrap buy">
      <div>
        <h2>Where to buy</h2>
        <p class="lede">Order online and we ship within Canada. You can also pick up from a local shop.</p>
        <p class="ctas"><a class="btn solid" href="/#products">Shop online</a></p>
      </div>
      <div>
        <h3 class="subh">Local shops</h3>
        <ul class="stores">{stores}</ul>
        <p class="store">Want to stock Mario's Super Soil? Email {esc(SITE['email'])}.</p>
      </div>
    </div>
  </section>
"""
    # about
    quotes = "".join(f'<blockquote><p>{esc(q)}</p><cite>{esc(c)}</cite></blockquote>' for q, c in SITE["quotes"])
    out += f"""  <section id="mission" class="sec">
    <div class="wrap">
      <div class="mission">
        <h2>Good for your plants, better for the planet</h2>
        <div>
          <p>Mario's Super Soil started in 2019 as a basement operation in Mississauga, Ontario. We began by experimenting with synthetic nutrients for growing cannabis, then moved to organic gardening because it fit our values better.</p>
          <p>We found that high costs and limited availability kept organic dry amendments out of reach for many growers, so we set out to make them accessible, affordable and effective. We also want to encourage younger people to take up gardening as a life skill.</p>
          <p>We believe nature provides the best path to plant health, helping gardeners of all levels cultivate a vibrant, sustainable future, one garden at a time.</p>
          <ul class="pledges">
            <li>100% natural, no synthetic chemicals</li>
            <li>Low usage rates: 1 tablespoon per gallon for Level Up and Flower Power</li>
            <li>Fully recyclable, reusable bags</li>
            <li>Used by home gardeners and commercial farmers</li>
          </ul>
        </div>
      </div>
      <div class="quotes">{quotes}</div>
    </div>
  </section>
"""
    # social: follow links, plus a live Instagram feed once a feed id is set in data/site.json
    fid = (SITE.get("instagram_feed_id") or "").strip()
    follow = "".join(f'<a class="btn" href="{esc(u)}" target="_blank" rel="noopener">{esc(n)}</a>' for n, u in SITE["social"])
    feed = (f'<div class="igfeed" id="igfeed" data-feed="{esc(fid)}"><noscript><p><a href="{esc(SITE["social"][0][1])}">See our posts on Instagram</a></p></noscript></div>' if fid else "")
    out += f"""  <section id="social" class="sec">
    <div class="wrap">
      <h2>Follow along</h2>
      <p class="lede">Grow tips, new products and what is happening at Mario's Super Soil.</p>
      {feed}
      <p class="ctas" style="margin-top:20px">{follow}</p>
    </div>
  </section>
"""
    # faq
    faq = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in SITE["faq"])
    out += f"""  <section id="faq" class="sec">
    <div class="wrap">
      <h2>Questions</h2>
      <div class="faq">{faq}</div>
    </div>
  </section>
"""
    # contact
    hours = "".join(f"<dt>{esc(d)}</dt><dd>{esc(t)}</dd>" for d, t in SITE["hours"])
    social = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(n)}</a></li>' for n, u in SITE["social"])
    a = SITE["address"]
    out += f"""  <section id="contact" class="sec contact">
    <div class="wrap cgrid">
      <div>
        <h2>Contact</h2>
        <p class="lede">Questions about which product to use, or how much? Get in touch.</p>
        <div class="row">
          <span class="mail" id="mail">{esc(SITE['email'])}</span>
          <button class="btn" type="button" id="copy">Copy email</button>
        </div>
        <p class="site">{esc(SITE['phone'])}<br>{esc(a['street'])}, {esc(a['city'])}, Ontario</p>
      </div>
      <div>
        <h3 class="subh">Hours</h3>
        <dl class="hours">{hours}</dl>
        <h3 class="subh">Follow along</h3>
        <ul class="social">{social}</ul>
        <p class="store"><a href="{esc(SITE['links']['newsletter'])}" target="_blank" rel="noopener">Sign up for deals and gardening tips</a></p>
      </div>
    </div>
  </section>
"""
    out += footer()
    return out


# ---------------------------------------------------------------- product page
def build_product(p):
    path = f"/products/{p['slug']}/"
    others = [q for q in PRODUCTS if q["slug"] != p["slug"]]
    rows = price_rows(p["slug"])
    offers = ({"@type": "AggregateOffer", "priceCurrency": "CAD", "lowPrice": f"{min(x[1] for x in rows):.2f}",
               "highPrice": f"{max(x[1] for x in rows):.2f}", "offerCount": len(rows), "url": abs_url(path)} if rows else None)
    ld = [org_ld(),
          {"@context": "https://schema.org", "@type": "Product", **({"offers": offers} if offers else {}),
           "name": f"{plain_name(p)} {npk_dash(p)}", "description": p["meta"], "url": abs_url(path),
           "image": [abs_url(f"/img/{p['f']}-front.webp"), abs_url(f"/img/{p['f']}-back.webp")],
           "brand": {"@type": "Brand", "name": SITE["name"]}, "category": "Organic fertilizer",
           "size": ", ".join(p["sizes"]),
           "countryOfOrigin": {"@type": "Country", "name": "Canada"}},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
              {"@type": "ListItem", "position": 2, "name": "Products", "item": BASE + "/#products"},
              {"@type": "ListItem", "position": 3, "name": plain_name(p), "item": abs_url(path)}]}]
    size_opts = ''.join(f'<option value="{esc(size_key(x))}">{esc(x)}</option>' for x in p['sizes'])
    out = head(p["title"], p["meta"], path, og_image=f"/img/{p['f']}-front.webp", jsonld=ld)
    out += header()
    ben = "".join(f'<li><img src="/img/ic-{p["f"]}-{i + 1}.webp" alt="" width="60" height="60" loading="lazy"><span>{esc(t)}</span></li>'
                  for i, t in enumerate(p["ben"]))
    desc = "".join(f"<p>{esc(d)}</p>" for d in p["desc"])
    n, ph, k = p["npk"]
    ing = (f'<dt>Nitrogen (N) <small lang="fr">Azote (N)</small></dt><dd>{n}%</dd>'
           f'<dt>Phosphorus (P) <small lang="fr">Phosphore (P)</small></dt><dd>{ph}%</dd>'
           f'<dt>Potassium (K) <small lang="fr">Potassium (K)</small></dt><dd>{k}%</dd>'
           f'<dt class="sub">Micronutrients <small lang="fr">Micronutriments</small></dt><dd class="sub"></dd>')
    for en, fr, val in p["micro"]:
        ing += f'<dt>{esc(en)}{"" if en == fr else f" <small lang=fr>{esc(fr)}</small>"}</dt><dd>{esc(val)}</dd>'
    more = "".join(picker_item(q) for q in others)
    out += f"""  <section class="pdp" style="--accent:{p['accent']}">
    <div class="wrap">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/#products">Products</a> / <span aria-current="page">{esc(plain_name(p))}</span></nav>
      <div class="viewer">
        <div class="stage">
          <div class="glow"><div class="pair">
            <img src="/img/{p['f']}-front.webp" width="380" height="560" alt="{esc(plain_name(p))} {esc(npk_dash(p))} organic fertilizer stand-up pouch, front">
            <img src="/img/{p['f']}-back.webp" width="380" height="560" loading="lazy" alt="Back of the {esc(plain_name(p))} pouch with ingredients and directions">
          </div></div>
        </div>
        <div class="info">
          <h1 class="nm">{name_html(p)}</h1>
          <span class="pq">Premium quality</span>
          <div class="npkline"><span class="big">{esc(npk_text(p))}</span><span class="net">Sizes: {esc(sizes_text(p))}</span></div>
          {price_line(p)}
          {('<p class="store">' + esc(p['size_note']) + '</p>') if p.get('size_note') else ''}
          <div class="desc">{desc}</div>
          <ul class="benefits">{ben}</ul>
          <div class="facts">
            <div><h2>Ingredients <small lang="fr">Ingrédients</small></h2><dl>{ing}</dl></div>
            <div><h2>How to use <small lang="fr">Comment utiliser</small></h2><p>{esc(p['how_en'])}</p><p lang="fr">{esc(p['how_fr'])}</p></div>
          </div>
          <p class="store">Store in a cool, dry place, away from moisture.</p>
          <div class="shopbox" id="buy-box" data-slug="{esc(p['slug'])}">
            <div class="buyrow">
              <div><label for="buy-size">Size</label><select id="buy-size">{size_opts}</select></div>
              <div><label for="buy-qty">Quantity</label><input id="buy-qty" type="number" min="1" max="20" value="1" inputmode="numeric"></div>
            </div>
            <p class="buyprice" id="buy-price" aria-live="polite">Choose a size</p>
            <button class="btn solid" type="button" id="buy-add">Add to cart</button>
            <p class="buymsg" id="buy-msg" role="status" aria-live="polite"></p>
          </div>
          <p class="ctas"><a class="btn" href="/#buy">Find a local shop</a></p>
        </div>
      </div>
    </div>
  </section>
  <section class="sec" id="reviews" data-slug="{esc(p['slug'])}">
    <div class="wrap">
      <h2>Customer reviews</h2>
      <p id="rv-summary" aria-live="polite">Loading reviews...</p>
      <div id="rv-list"></div>
      <p><button class="btn" type="button" id="rv-open">Write a review</button></p>
      <form class="rvform" id="rv-form" hidden>
        <div><label for="rv-name">Your name</label><input id="rv-name" type="text" maxlength="40" required autocomplete="given-name"></div>
        <div><label for="rv-rating">Rating</label><select id="rv-rating" name="rating" required><option value="">Choose</option><option value="5">5 stars - Excellent</option><option value="4">4 stars - Good</option><option value="3">3 stars - Okay</option><option value="2">2 stars - Poor</option><option value="1">1 star - Bad</option></select></div>
        <div><label for="rv-title">Headline (optional)</label><input id="rv-title" type="text" maxlength="80"></div>
        <div><label for="rv-text">Your review</label><textarea id="rv-text" maxlength="1000" required></textarea></div>
        <div><label for="rv-email">Email (optional, never shown)</label><input id="rv-email" type="email" maxlength="120" autocomplete="email"></div>
        <input class="hp" id="rv-hp" type="text" tabindex="-1" autocomplete="off" aria-hidden="true">
        <div><button class="btn solid" type="submit">Send review</button></div>
      </form>
      {google_review()}
      <p class="rv-msg" id="rv-msg" role="status"></p>
    </div>
  </section>
  <script src="/assets/reviews.js?v=1" defer></script>
  <section class="sec">
    <div class="wrap">
      <h2>More from Mario's Super Soil</h2>
      <ul class="picker five" aria-label="Other products">{more}</ul>
    </div>
  </section>
"""
    out += footer()
    return out


def build_calculator():
    title = "Organic Fertilizer Calculator for Gardens | Mario's Super Soil"
    desc = "Free organic fertilizer calculator. Pick your plant, bed size or pot size and growing zone to get amounts of Mario's Super Soil amendments to use."
    path = "/soil-calculator/"
    ld = [{"@context": "https://schema.org", "@type": "WebApplication", "name": "Soil Amendment Calculator",
           "url": abs_url(path), "description": desc, "applicationCategory": "LifestyleApplication",
           "operatingSystem": "Any", "inLanguage": "en-CA",
           "publisher": {"@type": "Organization", "name": SITE["name"], "url": BASE}},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
              {"@type": "ListItem", "position": 2, "name": "Soil amendment calculator", "item": abs_url(path)}]}]
    out = head(title, desc, path, jsonld=ld).replace('<link rel="stylesheet" href="/assets/style.css?v=10">', '<link rel="stylesheet" href="/assets/style.css?v=10">\n<link rel="stylesheet" href="/assets/calculator.css">')
    out += header()
    body = (ROOT / "data/calculator-body.inc").read_text()
    out += f"""  <section class="sec"><div class="wrap">
    <h1 class="nm" style="font-size:clamp(40px,7vw,88px)"><b>Soil amendment</b> <i>calculator</i></h1>
    <p class="lede" style="margin-bottom:32px">Tell us what you are growing, the size of your bed or pot and where you are in Canada. The calculator shows how much of each Mario's Super Soil organic amendment to use, with a planting and feeding calendar for your zone.</p>
    <div class="calc-panel">
{body}    </div>
    <p class="lede" style="margin-top:28px">Amounts are a guide based on the label rates. Read the bag for full directions. Worm castings and compost are sold in litres and gallons, not by weight, because the weight changes with moisture (4 gallons is about 15 to 20 lb). Every product is also on the <a href="/#products">products list</a>.</p>
  </div></section>
<script src="/assets/calculator.js" defer></script>
"""
    out += footer()
    return out


def build_drmario():
    title = "Plant Dr. Mario: Free Plant Problem Diagnosis from a Photo"
    desc = "Upload a photo of your plant and get a free AI diagnosis of yellow leaves, spots and other problems, with organic amendments that may help."
    path = "/plant-drmario/"
    ld = [{"@context": "https://schema.org", "@type": "WebApplication", "name": "Plant Dr. Mario",
           "url": abs_url(path), "description": desc, "applicationCategory": "LifestyleApplication",
           "operatingSystem": "Any", "inLanguage": "en-CA",
           "publisher": {"@type": "Organization", "name": SITE["name"], "url": BASE}},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
              {"@type": "ListItem", "position": 2, "name": "Plant Dr. Mario", "item": abs_url(path)}]}]
    out = head(title, desc, path, jsonld=ld).replace('<link rel="stylesheet" href="/assets/style.css?v=10">', '<link rel="stylesheet" href="/assets/style.css?v=10">\n<link rel="stylesheet" href="/assets/drmario.css?v=1">')
    out += header()
    out += """  <section class="sec"><div class="wrap">
    <h1 class="nm" style="font-size:clamp(40px,7vw,88px)"><b>Plant</b> <i>Dr. Mario</i></h1>
    <p class="lede" style="margin-bottom:32px">Yellow leaves? Spots? Drooping? Take a photo of your plant and Dr. Mario will tell you what is most likely wrong and which Mario's Super Soil organic amendments may help. Free, and it works on phones and computers.</p>
    <div class="dm" id="dm"><div class="dm-card">
      <div id="dm-form">
        <div class="dm-drop" id="dm-drop">
          <div class="dm-big">Add a photo of your plant</div>
          <p>Show the whole plant, plus a close-up of the leaves that look wrong. Up to 3 photos.</p>
          <div class="dm-actions">
            <button class="btn solid" type="button" id="dm-btn-cam">Take a photo</button>
            <button class="btn" type="button" id="dm-btn-pick">Choose from files</button>
          </div>
          <p style="margin-top:14px;font-size:14px">On a computer you can also drag photos here.</p>
          <input class="dm-file" type="file" id="dm-camera" accept="image/*" capture="environment" tabindex="-1" aria-hidden="true">
          <input class="dm-file" type="file" id="dm-files" accept="image/*,.heic,.heif" multiple tabindex="-1" aria-hidden="true">
        </div>
        <ul class="dm-thumbs" id="dm-thumbs" aria-label="Your photos"></ul>
        <div class="dm-fields">
          <div class="dm-row">
            <div><label for="dm-plant">Plant (optional)</label><input id="dm-plant" type="text" maxlength="80" placeholder="For example: tomato, monstera, rose" autocomplete="off"></div>
            <div><label for="dm-where">Where is it growing? (optional)</label><select id="dm-where"><option value="">Not sure</option><option value="outdoor">Outdoor garden</option><option value="container">Outdoor pot or planter</option><option value="indoor">Indoors</option><option value="greenhouse">Greenhouse</option></select></div>
          </div>
          <div><label for="dm-note">What have you noticed? (optional)</label><textarea id="dm-note" maxlength="600" placeholder="For example: lower leaves turning yellow for two weeks, watering every 3 days"></textarea></div>
        </div>
        <div class="dm-msg" id="dm-msg" role="alert"></div>
        <div class="dm-go"><button class="btn solid" type="button" id="dm-go" disabled>Diagnose my plant</button></div>
      </div>
      <div class="dm-busy" id="dm-busy" role="status" aria-live="polite"><div class="dm-spin"></div><p class="lede" style="margin:0 auto">Dr. Mario is looking at your plant. This takes about 15 seconds.</p></div>
      <div class="dm-res" id="dm-res" aria-live="polite"></div>
    </div></div>
    <p class="lede" style="margin-top:28px">Photos are sent to an AI service to get your diagnosis and are not saved on this site. For amounts, follow the bag or use the <a href="/soil-calculator/">soil amendment calculator</a>.</p>
  </div></section>
<script src="/assets/drmario.js?v=1" defer></script>
"""
    out += footer()
    return out


def build_cart():
    out = head("Your cart | Mario's Super Soil", "Review your Mario's Super Soil order and check out securely.", "/cart/", noindex=True)
    out += header()
    out += """  <section class="sec"><div class="wrap">
    <h1 class="nm" style="font-size:clamp(40px,7vw,88px)"><b>Your</b> <i>cart</i></h1>
    <div id="cart-root" class="cartbox"><p class="lede">Loading your cart...</p></div>
    <p class="lede" style="margin-top:24px">Prices are in Canadian dollars. Shipping and tax are shown at checkout. Delivery takes 2 to 10 business days. Payment is handled securely by Stripe; we never see your card number. See our <a href="/shipping-returns/">shipping and returns</a> policy.</p>
  </div></section>
"""
    out += footer()
    return out


def build_order_complete():
    out = head("Order received | Mario's Super Soil", "Thank you for your Mario's Super Soil order.", "/order-complete/", noindex=True)
    out += header()
    out += """  <section class="sec"><div class="wrap">
    <h1 class="nm" style="font-size:clamp(40px,7vw,88px)"><b>Thank</b> <i>you</i></h1>
    <p class="lede" id="order-done">Your order has been received. Stripe will email your receipt. Questions? Email <a href="mailto:__EMAIL__">__EMAIL__</a> or call __PHONE__.</p>
    <p class="ctas" style="margin-top:28px"><a class="btn solid" href="/">Back to the home page</a></p>
    __GR__
  </div></section>
""".replace("__GR__", google_review()).replace("__EMAIL__", SITE["email"]).replace("__PHONE__", SITE["phone"])
    out += footer()
    return out


def build_admin():
    out = head("Owner admin | Mario's Super Soil", "Owner admin page.", "/admin/", noindex=True).replace('<link rel="stylesheet" href="/assets/style.css?v=10">', '<link rel="stylesheet" href="/assets/style.css?v=10">\n<link rel="stylesheet" href="/assets/admin.css?v=2">')
    out = out.replace('<meta name="robots" content="noindex, nofollow">\n', '').replace('<meta name="viewport"', '<meta name="robots" content="noindex, nofollow">\n<meta name="viewport"', 1) if 'noindex' not in out else out
    out += header()
    out += """  <section class="sec"><div class="wrap">
    <h1 class="nm" style="font-size:clamp(36px,6vw,72px)"><b>Owner</b> <i>admin</i></h1>
    <div class="ad" id="ad-root"><p class="lede">Loading...</p></div>
  </div></section>
<script src="/assets/admin.js?v=6" defer></script>
"""
    out += footer()
    return out


def contact_block():
    a = SITE["address"]
    hrs = "".join(f"<li>{esc(d)}: {esc(h)}</li>" for d, h in SITE["hours"])
    return f"""<p>Email <a href="mailto:{esc(SITE['email'])}">{esc(SITE['email'])}</a> or call <a href="tel:{esc(SITE['phone'].replace('-', ''))}">{esc(SITE['phone'])}</a>.</p><ul>{hrs}</ul>"""


def build_policy():
    title = "Shipping and Returns Policy | Mario's Super Soil"
    desc = "Shipping rates, delivery and return policy for Mario's Super Soil orders within Canada: 30 day returns, refunds and exchanges, and who to contact."
    path = "/shipping-returns/"
    ld = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
              {"@type": "ListItem", "position": 2, "name": "Shipping and returns", "item": abs_url(path)}]}]
    out = head(title, desc, path, jsonld=ld) + header()
    out += f"""  <section class="sec"><div class="wrap policy">
    <h1 class="nm" style="font-size:clamp(40px,7vw,88px)"><b>Shipping</b> <i>and returns</i></h1>
    <h2>Shipping</h2>
    <ul>
      <li>We ship across Canada from Mississauga, Ontario. We do not ship outside Canada at this time.</li>
      <li>Orders of $120 or more include a free 2 lb bag of Level Up 3-3-3 or Flower Power 2-6-4. You choose which one in your cart.</li>
      <li>Shipping is a flat rate based on the total weight of your order. You see the exact amount in your cart before you pay, and again at checkout.</li>
      <li>Sales tax is worked out at checkout from your shipping address.</li>
      <li>Most orders arrive in 2 to 3 business days. Please allow 2 to 10 business days, because delivery depends on the carrier, the weather and where you live. If you want to know where your order is, email or call us and we will help.</li>
      <li>If an order is too heavy for online checkout, email us and we will arrange the shipping with you.</li>
    </ul>
    <h2>Returns and refunds</h2>
    <ul>
      <li>You have 30 days after you receive your order to ask for a return.</li>
      <li>Items must be unused, in the same condition you received them and in the original packaging. Please keep your receipt or order email as proof of purchase.</li>
      <li>Email us before you send anything back. Returns sent without our approval cannot be accepted.</li>
      <li>You pay the shipping to send an item back, because shipping costs are high for heavy products.</li>
      <li>Once we receive and inspect your return, we will email you to say whether it is approved. Approved refunds go back to the original payment method. How long it takes to show up depends on your bank or card company.</li>
    </ul>
    <h2>Damaged, defective or wrong items</h2>
    <p>Please check your order as soon as it arrives. If something is damaged, defective or not what you ordered, contact us right away. Photos help us sort it out quickly, and we will work with you to fix it.</p>
    <h2>Items we cannot take back</h2>
    <ul>
      <li>Perishable goods</li>
      <li>Custom or special-order products</li>
      <li>Clearance items, which are final sale</li>
      <li>Hazardous materials</li>
    </ul>
    <p>Not sure whether something qualifies? Ask us.</p>
    <h2>Exchanges</h2>
    <p>The fastest way to exchange an item is to start a return for it. Once the return is accepted, place a new order for the item you want.</p>
    <h2>Warranty</h2>
    <p>If you have a warranty question, contact us and we will help work out the next step. Some manufacturers ask you to deal with them directly. Clearance items are final sale and cannot be returned, exchanged or refunded.</p>
    <h2>Contact us</h2>
    {contact_block()}
    <hr style="border:0;border-top:1px solid var(--line);margin:48px 0 8px">
    <div lang="fr">
    <h2>Livraison et retours</h2>
    <p><strong>Livraison.</strong> Nous livrons partout au Canada depuis Mississauga, en Ontario. Les frais d'expédition sont un tarif fixe selon le poids total de votre commande. Vous voyez le montant exact dans votre panier avant de payer, puis à la caisse. Les taxes de vente sont calculées à la caisse selon votre adresse de livraison. Le délai de livraison dépend du transporteur et de votre région. Si une commande est trop lourde pour la caisse en ligne, écrivez-nous et nous organiserons l'expédition avec vous.</p>
    <p><strong>Retours et remboursements.</strong> Vous avez 30 jours après la réception de votre commande pour demander un retour. Les articles doivent être inutilisés, dans le même état qu'à la réception et dans leur emballage d'origine. Conservez votre reçu ou votre courriel de commande comme preuve d'achat. Écrivez-nous avant de renvoyer quoi que ce soit : les retours envoyés sans notre autorisation ne peuvent pas être acceptés. Les frais de retour sont à votre charge. Une fois le retour reçu et inspecté, nous vous écrirons pour confirmer s'il est approuvé. Les remboursements approuvés sont versés au mode de paiement d'origine; le délai dépend de votre banque ou de votre émetteur de carte.</p>
    <p><strong>Articles endommagés, défectueux ou erronés.</strong> Vérifiez votre commande dès son arrivée. Si un article est endommagé, défectueux ou différent de ce que vous avez commandé, communiquez avec nous tout de suite. Des photos nous aident à régler le problème rapidement.</p>
    <p><strong>Articles non retournables.</strong> Denrées périssables, produits sur mesure ou commandes spéciales, articles en liquidation (vente finale) et matières dangereuses. En cas de doute, posez-nous la question.</p>
    <p><strong>Échanges.</strong> Le plus simple est de demander le retour de l'article. Une fois le retour accepté, passez une nouvelle commande pour l'article souhaité.</p>
    <p><strong>Garantie.</strong> Pour toute question de garantie, communiquez avec nous. Certains fabricants demandent que vous les contactiez directement. Les articles en liquidation sont en vente finale et ne peuvent être ni retournés, ni échangés, ni remboursés.</p>
    <p><strong>Nous joindre.</strong> {esc(SITE['email'])} ou {esc(SITE['phone'])}.</p>
    </div>
  </div></section>
"""
    return out + footer()


def build_wholesale():
    title = "Wholesale Organic Fertilizer for Stores | Mario's Super Soil"
    desc = "Stock Mario's Super Soil organic dry fertilizers and soil amendments in your garden centre or store. Volume pricing and Net 30 terms. Apply online."
    path = "/wholesale/"
    ld = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
              {"@type": "ListItem", "position": 2, "name": "Wholesale", "item": abs_url(path)}]}]
    out = head(title, desc, path, jsonld=ld) + header()
    out += """  <section class="sec"><div class="wrap">
    <h1 class="nm" style="font-size:clamp(40px,7vw,88px)"><b>Wholesale</b> <i>for stores</i></h1>
    <p class="lede">Run a garden centre, hydroponics shop, feed store or independent retailer? Mario's Super Soil makes organic dry fertilizers and soil amendments in Mississauga, Ontario, and we would like to hear from you.</p>
    <ul class="perks">
      <li><strong>Canadian made</strong><br>Organic dry fertilizers and soil amendments made in Ontario: bone, crab, feather, kelp and alfalfa meal, worm castings and blends.</li>
      <li><strong>Volume pricing</strong><br>Wholesale pricing that improves as your order size grows, with minimum order quantities per tier.</li>
      <li><strong>Net 30 terms</strong><br>Payment terms are available for approved stores.</li>
      <li><strong>Retail-ready bags</strong><br>Stand-up pouches with clear directions in English and French, in 2 lb and 5 lb sizes. Bulk sacks are available on request.</li>
    </ul>
    <h2>Apply for a wholesale account</h2>
    <p class="lede">Tell us about your store. We will review your application and contact you by email or phone with the price list and next steps.</p>
    <form class="wsform" id="ws-form">
      <div class="wsgrid">
        <div><label for="ws-business">Business name</label><input id="ws-business" name="business" type="text" maxlength="100" required autocomplete="organization"></div>
        <div><label for="ws-contact">Your name</label><input id="ws-contact" name="contact" type="text" maxlength="80" required autocomplete="name"></div>
        <div><label for="ws-email">Email</label><input id="ws-email" name="email" type="email" maxlength="120" required autocomplete="email"></div>
        <div><label for="ws-phone">Phone</label><input id="ws-phone" name="phone" type="tel" maxlength="30" required autocomplete="tel"></div>
        <div><label for="ws-city">City and province</label><input id="ws-city" name="city" type="text" maxlength="80" autocomplete="address-level2"></div>
        <div><label for="ws-site">Website (optional)</label><input id="ws-site" name="site" type="text" maxlength="120"></div>
        <div><label for="ws-type">Type of store</label><select id="ws-type" name="type"><option value="">Choose</option><option>Garden centre</option><option>Hydroponics shop</option><option>Farm or feed store</option><option>Hardware or general store</option><option>Online retailer</option><option>Other</option></select></div>
        <div><label for="ws-volume">Expected order size</label><select id="ws-volume" name="volume"><option value="">Choose</option><option>Not sure yet</option><option>1 to 24 units</option><option>25 to 75 units</option><option>More than 75 units</option></select></div>
      </div>
      <div><label for="ws-message">Anything else we should know? (optional)</label><textarea id="ws-message" name="message" maxlength="1500"></textarea></div>
      <input class="hp" name="website" type="text" tabindex="-1" autocomplete="off" aria-hidden="true">
      <div><button class="btn solid" type="submit">Send application</button></div>
    </form>
    <p class="ws-msg" id="ws-msg" role="status"></p>
  </div></section>
<script src="/assets/wholesale.js?v=1" defer></script>
"""
    return out + footer()


def build_404():
    out = head("Page not found | Mario's Super Soil", "This page could not be found.", "/404.html", noindex=True)
    out += header()
    out += """  <section class="sec"><div class="wrap"><h1 class="nm" style="font-size:clamp(44px,8vw,96px)"><b>Page</b> <i>not found</i></h1>
  <p class="lede">The page you are looking for does not exist. Start from the <a href="/">home page</a> or browse the <a href="/#products">products</a>.</p></div></section>
"""
    out += footer()
    return out


# ---------------------------------------------------------------- write
def main():
    sync_prices()
    pages = {"index.html": build_home(), "404.html": build_404(), "soil-calculator/index.html": build_calculator(), "plant-drmario/index.html": build_drmario(), "cart/index.html": build_cart(), "order-complete/index.html": build_order_complete(), "admin/index.html": build_admin(), "wholesale/index.html": build_wholesale(), "shipping-returns/index.html": build_policy()}
    for p in PRODUCTS:
        pages[f"products/{p['slug']}/index.html"] = build_product(p)

    old = json.loads(HASH_FILE.read_text()) if HASH_FILE.exists() else {}
    new = {}
    for rel, content in pages.items():
        f = ROOT / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content)
        h = hashlib.sha1(content.encode()).hexdigest()
        lastmod = old.get(rel, {}).get("lastmod", TODAY) if old.get(rel, {}).get("hash") == h else TODAY
        new[rel] = {"hash": h, "lastmod": lastmod}
    HASH_FILE.write_text(json.dumps(new, indent=2, sort_keys=True) + "\n")

    # sitemap (indexable pages only)
    urls = ""
    for rel in ["index.html", "soil-calculator/index.html", "plant-drmario/index.html", "wholesale/index.html", "shipping-returns/index.html"] + [f"products/{p['slug']}/index.html" for p in PRODUCTS]:
        loc = BASE + "/" + rel.replace("index.html", "")
        prio = "1.0" if rel == "index.html" else "0.8"
        urls += f"  <url><loc>{loc}</loc><lastmod>{new[rel]['lastmod']}</lastmod><priority>{prio}</priority></url>\n"
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")

    if SITE["staging"]:
        robots = "User-agent: *\nDisallow: /\n"
    else:
        robots = f"User-agent: *\nAllow: /\nDisallow: /data/\nDisallow: /tools/\nDisallow: /admin/\nDisallow: /api/\nDisallow: /cart/\n\nSitemap: {BASE}/sitemap.xml\n"
    (ROOT / "robots.txt").write_text(robots)
    print(f"built {len(pages)} pages; staging={SITE['staging']}")


if __name__ == "__main__":
    main()
