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
def head(title, description, path, og_image="/img/og-image.jpg", jsonld=None, noindex=False):
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
<link rel="icon" type="image/png" sizes="32x32" href="/img/favicon-32.png">
<link rel="apple-touch-icon" href="/img/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/anton-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/oswald-latin-300-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/style.css">
{ld}</head>
<body id="top">
"""


def header():
    return f"""<header>
  <div class="wrap">
    <a class="brand" href="/"><img src="/img/logo.png" width="54" height="54" alt="Mario's Super Soil logo"><span>Mario's Super Soil</span></a>
    <nav aria-label="Main">
      <a href="/#products">Products</a>
      <a href="/#blends">Blends</a>
      <a href="/#buy">Where to buy</a>
      <a href="/soil-calculator/">Calculator</a>
      <a href="/#faq">FAQ</a>
      <a href="/#mission">About</a>
      <a href="/#contact">Contact</a>
    </nav>
    <a class="btn solid" href="{esc(SITE['store_url'])}" target="_blank" rel="noopener">Shop online</a>
  </div>
</header>
<main>
"""


def footer():
    L = SITE["links"]
    return f"""</main>
<footer>
  <div class="wrap">
    <strong>A Canadian company, Mississauga, Ontario</strong>
    <p>Store in a cool, dry place, away from moisture. <span lang="fr">Conserver dans un endroit frais et sec, à l'abri de l'humidité.</span></p>
    <p>Dust hazard. Wear an appropriate dust mask when handling.</p>
    <nav class="flinks" aria-label="More from Mario's Super Soil">
      <a href="{esc(L['blog'])}" target="_blank" rel="noopener">Blog</a>
      <a href="{esc(L['refund'])}" target="_blank" rel="noopener">Refund policy</a>
      <a href="{esc(L['privacy'])}" target="_blank" rel="noopener">Privacy policy</a>
    </nav>
  </div>
</footer>
<script src="/assets/app.js" defer></script>
</body>
</html>
"""


def picker_item(p, eager=False):
    load = "" if eager else ' loading="lazy"'
    return (f'<li><a class="pick" href="/products/{p["slug"]}/" style="--accent:{p["accent"]}">'
            f'<img src="/img/{p["f"]}-front.webp" width="170" height="250"{load} alt="{esc(plain_name(p))} {esc(npk_dash(p))} organic fertilizer, {esc(p["net"])} stand-up pouch">'
            f'<span class="nm">{name_html(p)}</span><span class="npk">{esc(npk_text(p))}</span></a></li>')


def org_ld():
    a = SITE["address"]
    return {
        "@context": "https://schema.org", "@type": "Organization",
        "name": SITE["name"], "url": BASE + "/", "logo": abs_url("/img/logo.png"),
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
            <a class="btn solid" href="{esc(SITE['store_url'])}" target="_blank" rel="noopener">Shop online</a>
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
                 f'<td class="a">{esc(p["when"])}</td><td class="a">{esc(p["net"])}</td></tr>')
    out += f"""  <section id="products" class="sec">
    <div class="wrap">
      <h2>Organic fertilizers and soil amendments</h2>
      <p class="lede">Six single-ingredient bags, each with a clear job. Guaranteed analysis in percent; bars share one scale so you can see which product leads in nitrogen, phosphorus or potassium.</p>
      <div class="tablewrap">
        <table>
          <caption class="sr">Nutrient comparison of Mario's Super Soil organic amendments</caption>
          <thead><tr><th scope="col">Product</th><th scope="col">Nitrogen (N)</th><th scope="col">Phosphorus (P)</th><th scope="col">Potassium (K)</th><th scope="col">How much and when</th><th scope="col">Bag</th></tr></thead>
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
        link = f'<a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(re.sub(r"^https?://|/$", "", s["url"]))}</a>' if s["url"] else ""
        stores += f'<li><strong>{esc(s["name"])}</strong><span>{esc(s["address"])}</span><span>{esc(s["phone"])}</span>{link}</li>'
    out += f"""  <section id="buy" class="sec">
    <div class="wrap buy">
      <div>
        <h2>Where to buy</h2>
        <p class="lede">Order online and we ship within Canada. USA shipping is planned. You can also pick up from a local shop.</p>
        <p class="ctas"><a class="btn solid" href="{esc(SITE['store_url'])}" target="_blank" rel="noopener">Shop online</a></p>
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
            <li>Lower cost per application than leading brands</li>
            <li>Fully recyclable, reusable bags</li>
            <li>Used by home gardeners and commercial farmers</li>
          </ul>
        </div>
      </div>
      <div class="quotes">{quotes}</div>
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
    ld = [org_ld(),
          {"@context": "https://schema.org", "@type": "Product",
           "name": f"{plain_name(p)} {npk_dash(p)}", "description": p["meta"], "url": abs_url(path),
           "image": [abs_url(f"/img/{p['f']}-front.webp"), abs_url(f"/img/{p['f']}-back.webp")],
           "brand": {"@type": "Brand", "name": SITE["name"]}, "category": "Organic fertilizer",
           "weight": {"@type": "QuantitativeValue", "value": p["grams"], "unitCode": "GRM"},
           "countryOfOrigin": {"@type": "Country", "name": "Canada"}},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
              {"@type": "ListItem", "position": 2, "name": "Products", "item": BASE + "/#products"},
              {"@type": "ListItem", "position": 3, "name": plain_name(p), "item": abs_url(path)}]}]
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
            <img src="/img/{p['f']}-front.webp" width="380" height="560" alt="{esc(plain_name(p))} {esc(npk_dash(p))} organic fertilizer, {esc(p['net'])} stand-up pouch, front">
            <img src="/img/{p['f']}-back.webp" width="380" height="560" loading="lazy" alt="Back of the {esc(plain_name(p))} pouch with ingredients and directions">
          </div></div>
        </div>
        <div class="info">
          <h1 class="nm">{name_html(p)}</h1>
          <span class="pq">Premium quality</span>
          <div class="npkline"><span class="big">{esc(npk_text(p))}</span><span class="net">Net wt. {esc(p['net'])}</span></div>
          <div class="desc">{desc}</div>
          <ul class="benefits">{ben}</ul>
          <div class="facts">
            <div><h2>Ingredients <small lang="fr">Ingrédients</small></h2><dl>{ing}</dl></div>
            <div><h2>How to use <small lang="fr">Comment utiliser</small></h2><p>{esc(p['how_en'])}</p><p lang="fr">{esc(p['how_fr'])}</p></div>
          </div>
          <p class="store">Store in a cool, dry place, away from moisture.</p>
          <p class="ctas"><a class="btn solid" href="{esc(SITE['store_url'])}" target="_blank" rel="noopener">Buy {esc(plain_name(p))} online</a><a class="btn" href="/#buy">Find a local shop</a></p>
        </div>
      </div>
    </div>
  </section>
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
    out = head(title, desc, path, jsonld=ld).replace('<link rel="stylesheet" href="/assets/style.css">', '<link rel="stylesheet" href="/assets/style.css">\n<link rel="stylesheet" href="/assets/calculator.css">')
    out += header()
    body = (ROOT / "data/calculator-body.inc").read_text()
    out += f"""  <section class="sec"><div class="wrap">
    <h1 class="nm" style="font-size:clamp(40px,7vw,88px)"><b>Soil amendment</b> <i>calculator</i></h1>
    <p class="lede" style="margin-bottom:32px">Tell us what you are growing, the size of your bed or pot and where you are in Canada. The calculator shows how much of each Mario's Super Soil organic amendment to use, with a planting and feeding calendar for your zone.</p>
    <div class="calc-panel">
{body}    </div>
    <p class="lede" style="margin-top:28px">Amounts are a guide based on the label rates. Read the bag for full directions. Every product is also on the <a href="/#products">products list</a>.</p>
  </div></section>
<script src="/assets/calculator.js" defer></script>
"""
    out += footer()
    return out


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
    pages = {"index.html": build_home(), "404.html": build_404(), "soil-calculator/index.html": build_calculator()}
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
    for rel in ["index.html", "soil-calculator/index.html"] + [f"products/{p['slug']}/index.html" for p in PRODUCTS]:
        loc = BASE + "/" + rel.replace("index.html", "")
        prio = "1.0" if rel == "index.html" else "0.8"
        urls += f"  <url><loc>{loc}</loc><lastmod>{new[rel]['lastmod']}</lastmod><priority>{prio}</priority></url>\n"
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")

    if SITE["staging"]:
        robots = "User-agent: *\nDisallow: /\n"
    else:
        robots = f"User-agent: *\nAllow: /\nDisallow: /data/\nDisallow: /tools/\n\nSitemap: {BASE}/sitemap.xml\n"
    (ROOT / "robots.txt").write_text(robots)
    print(f"built {len(pages)} pages; staging={SITE['staging']}")


if __name__ == "__main__":
    main()
