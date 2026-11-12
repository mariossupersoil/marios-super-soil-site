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
    """Mineral amendments with negligible N-P-K carry an npk_label (e.g. "Soil amendment") instead of numbers."""
    return p.get("npk_label") or " - ".join(str(x) for x in p["npk"])


def npk_dash(p):
    return "" if p.get("npk_label") else "-".join(str(x) for x in p["npk"])


def name_html(p):
    return f'<b>{esc(p["a"])}</b>' + (f' <i>{esc(p["b"])}</i>' if p.get("b") else "")


def plain_name(p):
    return f'{p["a"]} {p.get("b", "")}'.strip()


def full_name(p):
    return f"{plain_name(p)} {npk_dash(p)}".strip()


def abs_url(path):
    return BASE + path


# ---------------------------------------------------------------- shared pieces
def head(title, description, path, og_image="/img/og-image.jpg?v=3", jsonld=None, noindex=False):
    robots = '<meta name="robots" content="noindex, nofollow">\n' if (SITE["staging"] or noindex) else ""
    ld = ""
    for obj in (jsonld or []):
        ld += '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>\n"
    return f"""<!doctype html>
<html lang="en-CA">
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
<link rel="stylesheet" href="/assets/style.css?v=51">
{ld}</head>
<body id="top">
"""


def header():
    gu = (SITE.get("google_review_url") or "").strip()
    gl = f'<a class="tb-g" href="{esc(gu)}" target="_blank" rel="noopener">&#9733; Review us on Google</a>' if gu else ""
    return f"""<div class="topbar"><div class="wrap"><span>Free 2 lb Level Up or Flower Power on orders over $120</span><a href="/wholesale/">Wholesale</a>{gl}<a class="tb-s" href="#signup">&#9993; Sign up for deals</a></div></div>
<header>
  <div class="wrap">
    <a class="brand" href="/"><img src="/img/logo.png?v=3" width="54" height="54" alt="Mario's Super Soil logo"><span>Mario's Super Soil</span></a>
    <form class="hsearch" role="search" action="/#products" autocomplete="off">
      <label class="sr" for="hs-q">Search products</label>
      <input id="hs-q" type="search" placeholder="Search products, e.g. bone meal, calcium, tomatoes" maxlength="60" role="combobox" aria-expanded="false" aria-controls="hs-list" aria-autocomplete="list">
      <button type="submit" aria-label="Search"><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2.4"/><path d="M15.5 15.5 21 21" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg></button>
      <ul id="hs-list" class="hs-list" role="listbox" hidden></ul>
    </form>
    <nav aria-label="Main">
      <a href="/#products">Products</a>
      <a href="/#buy">Where to buy</a>
      <a href="/plant-drmario/">Plant Dr. Mario</a>
      <a href="/soil-calculator/">Calculator</a>
      <a href="/guides/">Guides</a>
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
    <div class="sigbox" id="signup">
      <h2>Get deals and restock reminders</h2>
      <p>Sale alerts, planting tips and restock reminders from Mario&rsquo;s Super Soil. No spam, and you can unsubscribe any time.</p>
      <form class="pop-form" id="sigform" novalidate>
        <label class="sr" for="sig-email">Email address</label>
        <input type="email" id="sig-email" placeholder="you@example.com" autocomplete="email" required maxlength="120">
        <input type="text" id="sig-hp" class="pop-hp" tabindex="-1" autocomplete="off" aria-hidden="true">
        <button class="btn solid" type="submit">Sign me up</button>
      </form>
      <p class="pop-msg" id="sig-msg" role="status"></p>
    </div>
    <strong>A Canadian company, Mississauga, Ontario</strong>
    <p>Store in a cool, dry place, away from moisture. <span lang="fr">Conserver dans un endroit frais et sec, à l'abri de l'humidité.</span></p>
    <p>Dust hazard. Wear an appropriate dust mask when handling.</p>
    <nav class="flinks" aria-label="More from Mario's Super Soil">
      <a href="#signup">Sign up for deals</a>
      <a href="/guides/">Guides</a>
      <a href="/wholesale/">Wholesale</a>
      <a href="/shipping-returns/">Shipping &amp; returns</a>
{GR_FOOT}      <a href="{esc(L['blog'])}" target="_blank" rel="noopener">Blog</a>
      <a href="/shipping-returns/">Refund policy</a>
      <a href="/privacy/">Privacy policy</a>
    </nav>
  </div>
</footer>
<script src="/assets/app.js" defer></script>
<script src="/assets/ring.js?v=8" defer></script>
<script src="/assets/room.js?v=1" defer></script>
<script src="/assets/guide.js?v=1" defer></script>
<script src="/assets/rail.js?v=1" defer></script>
<script src="/assets/cart.js?v=7" defer></script>
<script src="/assets/social.js?v=1" defer></script>
<script src="/assets/signup.js?v=1" defer></script>
<script src="/assets/promo.js?v=2" defer></script>
<script src="/assets/popup.js?v=4" defer></script>
<script src="/assets/chat.js?v=2" defer></script>
<script src="/assets/search.js?v=2" defer></script>
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
        prods[p["slug"]] = {"name": full_name(p), "img": f"/img/{p['f']}-front.webp", "sizes": sizes}
    kit = next((b for b in SITE["blends"] if b["id"] == "starter-pack"), None)
    if kit and kit.get("kit_sizes"):
        ks = {}
        for z in kit["kit_sizes"]:
            o = oldp.get("super-starter-pack", {}).get("sizes", {}).get(z["key"], {})
            ks[z["key"]] = {"label": z["label"], "price": o.get("price", z["price"]), "weight_kg": o.get("weight_kg", z["weight_kg"])}
        prods["super-starter-pack"] = {"name": "Super Starter Pack", "img": "/img/starter-kit.webp", "sizes": ks}
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


CATS = [("blends", "Blends"), ("meals", "Meals"), ("minerals", "Rock dusts & minerals"), ("soil", "Castings & compost")]


def rail_html():
    """One slowly drifting row of every product, grouped by category. rail.js adds the motion; without it this is a plain swipeable row."""
    chips = "".join(f'<button type="button" class="chip" data-go="{k}">{esc(l)}</button>' for k, l in CATS)
    groups = ""
    for k, l in CATS:
        items = "".join(picker_item(p, eager=True) for p in PRODUCTS if p.get("cat") == k)
        if items:
            groups += f'<div class="rgroup" data-cat="{k}"><h3 class="rlabel">{esc(l)}</h3><ul class="railrow">{items}</ul></div>'
    return f"""<div class="rail" id="rail">
        <div class="railbar"><div class="chips" role="group" aria-label="Jump to a product type">{chips}</div>
          <div class="railbtns"><button type="button" class="rbtn" data-dir="-1" aria-label="Scroll products left">&#8592;</button><button type="button" class="rbtn" data-dir="1" aria-label="Scroll products right">&#8594;</button></div></div>
        <div class="railtrack" tabindex="0" aria-label="Our products. Scroll sideways to see more.">{groups}</div>
        <p class="railhint">Moves on its own. Hover or touch to stop it, or swipe.</p>
      </div>"""


def blend_cards():
    """Big featured cards for the blends and the starter kit."""
    cards = ""
    for b in SITE["blends"]:
        if b["id"] not in ("level-up", "flower-power", "starter-pack"):
            continue
        prod = next((q for q in PRODUCTS if q["slug"] == b["id"]), None)
        if prod:
            rows = price_rows(prod["slug"])
            fr = f'<span class="from">From ${min(x[1] for x in rows):,.2f}</span>' if rows else ""
            cards += (f'<a class="bcard" href="/products/{prod["slug"]}/" style="--accent:{b["accent"]}"><span class="pair" aria-hidden="true"><img class="pb" src="/img/{prod["f"]}-back.webp" width="170" height="220" alt=""><img class="pf" src="/img/{prod["f"]}-front.webp" width="170" height="220" alt=""></span><span class="sr">{esc(full_name(prod))} organic dry amendment pouch, front and back</span>'
                      f'<span class="bt"><span class="nm"><b>{esc(b["a"])}</b> <i>{esc(b["b"])}</i></span><span class="bsub">{esc(b["tagline"])}</span>{fr}<span class="btn solid">See the bag</span></span></a>')
        else:
            fr = (f'<span class="from">{esc(b["price_label"])}</span>' if b.get("price_label") else f'<span class="from">From ${b["from"]:,.2f}</span>' if b.get("from") else "")
            if b["id"] == "starter-pack":
                kr = price_rows("super-starter-pack")
                if kr:
                    fr = '<span class="from">' + " · ".join(f"{l}: ${v:,.2f}" for l, v in kr) + "</span>"
                bags = ""
                for sl in ("level-up", "flower-power", "kelp-meal", "alfalfa-meal", "compost-blend", "worm-castings"):
                    q = next(x for x in PRODUCTS if x["slug"] == sl)
                    bags += (f'<li style="--i:{len(bags.split("<li")) - 1}"><a href="/products/{sl}/"><img src="/img/{q["f"]}-front.webp" width="90" height="117" loading="lazy" alt="{esc(full_name(q))} bag">'
                             f'<span>{esc(full_name(q))}</span></a></li>')
                cards += (f'<div class="bcard kit" style="--accent:{b["accent"]}"><span class="bt"><a class="nm kitname" href="/products/super-starter-pack/"><b>{esc(b["a"])}</b> <i>{esc(b["b"])}</i></a>'
                          f'<span class="bsub">{esc(b["tagline"])} Six bags in one kit:</span></span><div class="kitwrap kitwrap6"><span class="kbox kbb" aria-hidden="true"><span class="kb-back"></span></span><ul class="kitbags">{bags}</ul><span class="kbox kbf" aria-hidden="true"><span class="kb-lid l1"></span><span class="kb-lid l2"></span><span class="kb-front"><b>Super Starter</b> Pack</span></span></div>'
                          f'<span class="bt">{fr}<a class="btn" href="/products/super-starter-pack/">See the kit</a></span></div>')
            else:
                cards += (f'<a class="bcard noimg" href="/#contact" style="--accent:{b["accent"]}"><span class="bt"><span class="nm"><b>{esc(b["a"])}</b> <i>{esc(b["b"])}</i></span>'
                          f'<span class="bsub">{esc(b["tagline"])}</span>{fr}<span class="btn">Ask us about it</span></span></a>')
    return cards


def room_html():
    """The product wall: bags hang on a rail in a dark room. Drag sideways to slide along it, tap a bag to take it down (room.js)."""
    groups, details = "", ""
    for k, l in CATS:
        bags = ""
        for n, p in enumerate(q for q in PRODUCTS if q.get("cat") == k):
            bags += (f'<li class="rbag" style="--accent:{p["accent"]};--k:{(0.8 + (len(groups) + n * 7) % 5 * 0.1):.1f}"><button type="button" data-slug="{p["slug"]}" aria-label="Take down {esc(full_name(p))}">'
                     f'<span class="hook" aria-hidden="true"></span><img src="/img/{p["f"]}-front.webp" width="230" height="298" loading="eager" alt="">'
                     f'<span class="rn">{name_html(p)}</span></button></li>')
            rows = price_rows(p["slug"])
            fr = f'From ${min(x[1] for x in rows):,.2f}' if rows else ""
            chips = "".join(f"<li>{esc(x)}</li>" for x in p["ben"])
            chip = "" if p.get("npk_label") else f'<span class="gk">{esc(npk_dash(p))}</span>'
            details += (f'<div class="dtpl" data-slug="{p["slug"]}" hidden style="--accent:{p["accent"]}"><img src="/img/{p["f"]}-front.webp" width="380" height="492" alt="{esc(full_name(p))} pouch, front">'
                        f'<div class="dbody"><h3 class="nm">{name_html(p)} {chip}</h3><p class="dline">{esc(p.get("use", ""))}</p><ul class="dchips">{chips}</ul>'
                        f'<p class="dprice">{esc(fr)}</p><p class="dact"><a class="btn solid" href="/products/{p["slug"]}/">View and buy</a></p></div></div>')
        if bags:
            groups += f'<div class="rg"><div class="rplaque"><span>{esc(l)}</span></div><ul class="rrow">{bags}</ul></div>'
    return f"""<div class="roomsec" id="room">
        <div class="bcards">{blend_cards()}</div>
        <div class="room" aria-label="Product wall. Drag sideways to slide along the rail, tap a bag to take it down.">
          <div class="roomwall" aria-hidden="true"></div><div class="roomlight" aria-hidden="true"></div>
          <div class="rrail" aria-hidden="true"></div>
          <div class="roomtrack" tabindex="0"><div class="rtrack">{groups}</div></div>
          <div class="roomfloor" aria-hidden="true"></div>
        </div>
        <div class="roomctl"><button type="button" class="rbtn" data-dir="-1" aria-label="Slide the rail left">&#8592;</button><button type="button" class="rbtn" data-dir="1" aria-label="Slide the rail right">&#8594;</button><button type="button" class="rbtn playbtn" aria-label="Pause sliding" aria-pressed="false">&#10074;&#10074;</button>
          <span class="railhint">Drag to slide along the rail. Tap a bag to take it down.</span></div>
        <div class="roomdetail" id="roomdetail" aria-live="polite" hidden></div>
        <div class="dstore" hidden>{details}</div>
      </div>"""


def ring_html():
    """Blends as two big static cards, then tabs; each tab holds a slowly turning ring of bags (ring.js). Without JS it is a plain row."""
    cards = blend_cards()
    tabs, panels = "", ""
    cats = [(k, l) for k, l in CATS if k != "blends" and any(p.get("cat") == k for p in PRODUCTS)]
    for n, (k, l) in enumerate(cats):
        sel = "true" if n == 0 else "false"
        tabs += f'<button type="button" role="tab" class="chip" id="tab-{k}" aria-controls="ring-{k}" aria-selected="{sel}" data-cat="{k}">{esc(l)}</button>'
        items = "".join(f'<li class="rit">{picker_item(p, eager=True)[4:-5]}</li>' for p in PRODUCTS if p.get("cat") == k)
        panels += (f'<div class="ringpanel" role="tabpanel" id="ring-{k}" aria-labelledby="tab-{k}"{"" if n == 0 else " hidden"}>'
                   f'<div class="ringstage"><ul class="ringlist">{items}</ul></div>'
                   f'<input class="ringbar" type="range" min="0" max="{sum(1 for p in PRODUCTS if p.get("cat") == k) - 1}" value="0" step="1" aria-label="Slide through {esc(l)}">'
                   f'<div class="ringnav"><button type="button" class="rbtn" data-dir="-1" aria-label="Previous product">&#8592;</button><button type="button" class="rbtn" data-dir="1" aria-label="Next product">&#8594;</button><button type="button" class="rbtn playbtn" aria-label="Pause turning" aria-pressed="false">&#10074;&#10074;</button></div></div>')
    return f"""<div class="ringsec" id="ring">
        <div class="bcards">{cards}</div>
        <div class="chips" role="tablist" aria-label="Product types">{tabs}</div>
        {panels}
        <p class="railhint">Turns on its own. Hover or touch to stop it, or use the pause button. Tap a bag to bring it to the front.</p>
      </div>"""


def picker_item(p, eager=False):
    load = "" if eager else ' loading="lazy"'
    return (f'<li><a class="pick" data-slug="{p["slug"]}" href="/products/{p["slug"]}/" style="--accent:{p["accent"]}">'
            f'<img src="/img/{p["f"]}-front.webp" width="170" height="250"{load} alt="{esc(full_name(p))} organic dry amendment stand-up pouch">'
            f'<span class="nm">{name_html(p)}</span><span class="npk">{esc(npk_text(p))}</span>'
            + (f'<span class="from">From ${min(x[1] for x in price_rows(p["slug"])):,.2f}</span>' if price_rows(p["slug"]) else '')
            + '</a></li>')


def org_ld():
    a = SITE["address"]
    return {
        "@context": "https://schema.org", "@type": "Organization",
        "name": SITE["name"], "url": BASE + "/", "logo": abs_url("/img/logo.png?v=3"),
        "email": SITE["email"], "telephone": "+1-" + SITE["phone"],
        "@id": BASE + "/#organization",
        "description": "Canadian company in Mississauga, Ontario making organic dry soil amendments: meals, rock dusts, worm castings, compost and blends. Ships across Canada.",
        "slogan": "Grow great plants. Skip the guesswork.",
        "areaServed": {"@type": "Country", "name": "Canada"},
        "knowsAbout": ["organic dry amendments", "organic soil amendments", "bone meal", "crab meal", "feather meal", "kelp meal", "alfalfa meal", "worm castings", "NPK", "organic gardening in Canada"],
        "contactPoint": [{"@type": "ContactPoint", "contactType": "customer service", "telephone": "+1-" + SITE["phone"], "email": SITE["email"], "areaServed": "CA", "availableLanguage": ["English", "French"]}],
        "foundingDate": "2019",
        "address": {"@type": "PostalAddress", **({"streetAddress": a["street"]} if a.get("street", "").strip() else {}),
                    "addressLocality": a["city"], "addressRegion": a["region"], "addressCountry": a["country"]},
        "sameAs": [u for _, u in SITE["social"]],
    }


# ---------------------------------------------------------------- home
def build_home():
    H = SITE["home"]
    ld = [org_ld(),
          {"@context": "https://schema.org", "@type": "WebSite", "name": SITE["name"], "url": BASE + "/", "inLanguage": "en-CA", "publisher": {"@id": BASE + "/#organization"}},
          {"@context": "https://schema.org", "@type": "ItemList", "name": "Organic dry amendments", "itemListElement": [
              {"@type": "ListItem", "position": i + 1, "name": full_name(q), "url": abs_url(f"/products/{q['slug']}/")} for i, q in enumerate(PRODUCTS)]},
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
      {room_html() if SITE.get('home_style', 'room') == 'room' else ring_html() if SITE.get('home_style') == 'ring' else rail_html()}
    </div>
  </section>
"""
    # simple guide: grouped by what the grower wants to achieve (a bag can appear under more than one goal)
    GUIDE = [
        ("All-in-one blends", "A balanced mix, ready to use", ["level-up", "flower-power"]),
        ("Nitrogen (N)", "For green, leafy growth", ["blood-meal", "feather-meal", "crab-meal", "alfalfa-meal"]),
        ("Phosphorus (P)", "For strong roots, blooms and fruit", ["bone-meal", "soft-rock-phosphate"]),
        ("Potassium (K)", "For plant strength and fruit quality", ["kelp-meal", "alfalfa-meal"]),
        ("Calcium, magnesium and trace minerals", "For soil structure, pH and plant health", ["oyster-shell-flour", "dolomite-lime", "gypsum", "basalt-rock-dust"]),
        ("Living soil", "Live biology and organic matter", ["worm-castings", "compost-blend"]),
    ]
    byslug = {p["slug"]: p for p in PRODUCTS}
    blocks = ""
    for title, desc, slugs in GUIDE:
        lis = ""
        for sl in slugs:
            p = byslug.get(sl)
            if not p:
                continue
            rows = price_rows(p["slug"])
            fr = f'<span class="gp">From ${min(x[1] for x in rows):,.2f}</span>' if rows else ""
            chip = "" if p.get("npk_label") else f'<span class="gk">{esc(npk_dash(p))}</span>'
            lis += (f'<li><a href="/products/{p["slug"]}/" style="--accent:{p["accent"]}"><span class="gd" aria-hidden="true"></span>'
                    f'<span class="gn"><span class="nm">{name_html(p)} {chip}</span><span class="gu">{esc(p.get("use", ""))}</span></span>{fr}</a></li>')
        if lis:
            blocks += f'<div class="gblock"><h3>{esc(title)}</h3><p class="gdesc">{esc(desc)}</p><ul>{lis}</ul></div>'
    sp = next((b for b in SITE["blends"] if b["id"] == "starter-pack"), None)
    if sp:
        kit = [("Level Up 3-3-3", "level-up"), ("Flower Power 2-6-4", "flower-power"), ("Kelp Meal", "kelp-meal"), ("Alfalfa Meal", "alfalfa-meal"), ("Compost", "compost-blend"), ("Worm Castings", "worm-castings")]
        items = "".join((f'<li><a href="/products/{sl}/">{esc(n)}</a></li>' if sl else f"<li>{esc(n)}</li>") for n, sl in kit)
        kitblock = (f'<div class="gblock"><h3>Starter kit</h3><p class="gdesc">Everything in one box, for new gardeners</p><ul>'
                    f'<li><a href="/products/super-starter-pack/" style="--accent:{sp["accent"]}"><span class="gd" aria-hidden="true"></span><span class="gn"><span class="nm"><b>Super Starter</b> <i>Pack</i></span>'
                    f'<span class="gu">{esc(sp["tagline"])} Kit sizes: 2 lb and 5 lb.</span></span><span class="gp">{esc(sp.get("price_label") or "From $%.2f" % sp["from"])}</span></a></li>'
                    f'<li class="kitin"><span class="gu">What comes in the kit</span><ul class="kitlist">{items}</ul></li></ul></div>')
        i = blocks.index('<div class="gblock"><h3>Nitrogen')
        blocks = blocks[:i] + kitblock + blocks[i:]
    out += f"""  <section id="deal" class="sec dealsec" hidden></section>
  <section id="products" class="sec">
    <div class="wrap">
      <h2>What do you want to achieve?</h2>
      <p class="lede">Pick the goal, then tap a bag to see the dose, ingredients and price. The numbers after a name are its nitrogen, phosphorus and potassium.</p>
      <div class="guide">{blocks}</div>
    </div>
  </section>
"""
    # feeding calculator (the blends themselves are shown in the featured cards above)
    out += f"""  <section id="feed" class="sec">
    <div class="wrap">
      <div class="calc" id="calc">
        <h2>Feeding calculator</h2>
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
    PROV = ["Ontario", "British Columbia", "Alberta", "Saskatchewan", "Manitoba", "Quebec", "New Brunswick", "Nova Scotia", "Prince Edward Island", "Newfoundland and Labrador", "Yukon", "Northwest Territories", "Nunavut"]
    byprov = {}
    for s_ in SITE["stores"]:
        byprov.setdefault(s_.get("province", "Ontario"), []).append(s_)
    stores = ""
    for pv in sorted(byprov, key=lambda x: PROV.index(x) if x in PROV else 99):
        cards = ""
        for s_ in sorted(byprov[pv], key=lambda x: x["name"]):
            host = re.sub(r"^https?://(www\.)?|/.*$", "", s_["url"]) if s_.get("url") else ""
            extra = (f'<span class="sx">Hours: {esc(s_["hours"])}</span>' if s_.get("hours") else "") + (f'<span class="sx">Carries: {esc(s_["carries"])}</span>' if s_.get("carries") else "")
            name = (f'<a class="sname" href="{esc(s_["url"])}" target="_blank" rel="noopener">{esc(s_["name"])}</a>' if s_.get("url") else f'<span class="sname">{esc(s_["name"])}</span>')
            tel = f'<a class="stel" href="tel:{re.sub(r"[^0-9+]", "", s_["phone"])}">{esc(s_["phone"])}</a>' if s_.get("phone") else ""
            go = f'<span class="sgo" aria-hidden="true">Visit {esc(host)} &#8594;</span>' if host else ""
            cards += f'<li class="scard"><strong>{name}</strong><span class="sx">{esc(s_["address"])}</span>{extra}{tel}{go}</li>'
        stores += f'<div class="prov"><h4>{esc(pv)}</h4><ul class="stores">{cards}</ul></div>'
    out += f"""  <section id="buy" class="sec">
    <div class="wrap buy">
      <div>
        <h2>Where to buy</h2>
        <p class="lede">Order online and we ship within Canada. You can also pick up from a local shop.</p>
        <p class="ctas"><a class="btn solid" href="/#products">Shop online</a></p>
      </div>
      <div>
        <h3 class="subh">Local shops by province</h3>
        {stores}
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
        <h2>Our story</h2>
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
    # guides
    out += """  <section id="guides" class="sec">
    <div class="wrap">
      <h2>Learn before you grow</h2>
      <p class="lede">Plain-language guides to organic dry amendments in Canada.</p>
      <ul class="gl">""" + "".join(f'<li><a href="/guides/{g["slug"]}/"><strong>{esc(g["h1"][0])} {esc(g["h1"][1])}</strong></a><br>{esc(g["short"])}</li>' for g in guides()) + """</ul>
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
        <p class="site">{esc(SITE['phone'])}<br>{(esc(a['street']) + ', ') if a.get('street', '').strip() else ''}{esc(a['city'])}, Ontario</p>
        <p class="site">Local pickup in Mississauga is by arrangement. Call or email us to set it up.</p>
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
           "name": full_name(p), "description": p["meta"], "url": abs_url(path),
           "image": [abs_url(f"/img/{p['f']}-front.webp"), abs_url(f"/img/{p['f']}-back.webp")],
           "brand": {"@type": "Brand", "name": SITE["name"]}, "category": "Organic dry amendment",
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
    ing = ('<dt>Nitrogen, phosphorus, potassium <small lang="fr">Azote, phosphore, potassium</small></dt><dd>Negligible <small lang="fr">Négligeable</small></dd>'
           if p.get("macro_note") else
           f'<dt>Nitrogen (N) <small lang="fr">Azote (N)</small></dt><dd>{n}%</dd>'
           f'<dt>Phosphorus (P) <small lang="fr">Phosphore (P)</small></dt><dd>{ph}%</dd>'
           f'<dt>Potassium (K) <small lang="fr">Potassium (K)</small></dt><dd>{k}%</dd>')
    ing += (f'<dt class="sub">Micronutrients <small lang="fr">Micronutriments</small></dt><dd class="sub"></dd>')
    for en, fr, val in p["micro"]:
        ing += f'<dt>{esc(en)}{"" if en == fr else f" <small lang=fr>{esc(fr)}</small>"}</dt><dd>{esc(val)}</dd>'
    more = "".join(picker_item(q) for q in others)
    out += f"""  <section class="pdp" style="--accent:{p['accent']}">
    <div class="wrap">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/#products">Products</a> / <span aria-current="page">{esc(plain_name(p))}</span></nav>
      <div class="viewer">
        <div class="stage">
          <div class="glow"><div class="pair">
            <img src="/img/{p['f']}-front.webp" width="380" height="560" alt="{esc(full_name(p))} organic dry amendment stand-up pouch, front">
            <img src="/img/{p['f']}-back.webp" width="380" height="560" loading="lazy" alt="Back of the {esc(plain_name(p))} pouch with ingredients and directions">
          </div></div>
        </div>
        <div class="info">
          <h1 class="nm">{name_html(p)}</h1>
          <span class="pq">Premium quality</span>
          <div class="npkline"><span class="big{" lab" if p.get("npk_label") else ""}">{esc(npk_text(p))}</span><span class="net">Sizes: {esc(sizes_text(p))}</span></div>
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
      <p>New to organic dry amendments? Read our <a href="/guides/organic-soil-amendments-canada/">Canadian guide</a> or <a href="/guides/npk-organic-gardening/">NPK explained</a>.</p>
      <ul class="picker five" aria-label="Other products">{more}</ul>
    </div>
  </section>
"""
    out += footer()
    return out


def build_calculator():
    title = "Organic Amendment Calculator for Gardens | Mario's Super Soil"
    desc = "Free organic amendment calculator. Pick your plant, bed size or pot size and growing zone to get amounts of Mario's Super Soil amendments to use."
    path = "/soil-calculator/"
    ld = [{"@context": "https://schema.org", "@type": "WebApplication", "name": "Soil Amendment Calculator",
           "url": abs_url(path), "description": desc, "applicationCategory": "LifestyleApplication",
           "operatingSystem": "Any", "inLanguage": "en-CA",
           "publisher": {"@type": "Organization", "name": SITE["name"], "url": BASE}},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
              {"@type": "ListItem", "position": 2, "name": "Soil amendment calculator", "item": abs_url(path)}]}]
    out = head(title, desc, path, jsonld=ld).replace('<link rel="stylesheet" href="/assets/style.css?v=51">', '<link rel="stylesheet" href="/assets/style.css?v=18">\n<link rel="stylesheet" href="/assets/calculator.css">')
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
    out = head(title, desc, path, jsonld=ld).replace('<link rel="stylesheet" href="/assets/style.css?v=51">', '<link rel="stylesheet" href="/assets/style.css?v=18">\n<link rel="stylesheet" href="/assets/drmario.css?v=1">')
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
    out = head("Owner admin | Mario's Super Soil", "Owner admin page.", "/admin/", noindex=True).replace('<link rel="stylesheet" href="/assets/style.css?v=51">', '<link rel="stylesheet" href="/assets/style.css?v=18">\n<link rel="stylesheet" href="/assets/owner.css?v=1">')
    out = out.replace('<meta name="robots" content="noindex, nofollow">\n', '').replace('<meta name="viewport"', '<meta name="robots" content="noindex, nofollow">\n<meta name="viewport"', 1) if 'noindex' not in out else out
    out += header()
    out += """  <section class="sec"><div class="wrap">
    <h1 class="nm" style="font-size:clamp(36px,6vw,72px)"><b>Owner</b> <i>admin</i></h1>
    <p id="own-ver" style="color:#a7a7a3;font:14px sans-serif;margin:6px 0">Admin page build 16</p>
    <div class="own" id="own-root"><p class="lede">Loading...</p>
    <form id="own-static" style="display:none;max-width:420px;padding:22px;border:2px solid #d8c98b;border-radius:14px;background:#1b1b1d;color:#fff">
      <h2 style="margin:0 0 12px;font:700 28px sans-serif;color:#fff">Owner login</h2>
      <label for="own-pw" style="display:block;margin-bottom:6px;color:#fff;font:600 16px sans-serif">Password</label>
      <input id="own-pw" type="password" autocomplete="current-password" placeholder="Type your password here" style="display:block;width:100%;box-sizing:border-box;padding:12px;font-size:18px;background:#fff;color:#000;border:2px solid #d8c98b;border-radius:8px">
      <button id="own-go" type="submit" style="margin-top:14px;padding:12px 22px;font-size:18px;font-weight:700;background:#7fc66a;color:#000;border:0;border-radius:6px;cursor:pointer">Log in</button>
      <p id="own-msg" style="color:#ffb4a8;margin:10px 0 0;font:16px sans-serif"></p>
    </form></div>
  </div></section>
<script src="/assets/owner-app.js?v=5" defer></script>
"""
    out += footer()
    return out


def contact_block():
    a = SITE["address"]
    hrs = "".join(f"<li>{esc(d)}: {esc(h)}</li>" for d, h in SITE["hours"])
    return f"""<p>Email <a href="mailto:{esc(SITE['email'])}">{esc(SITE['email'])}</a> or call <a href="tel:{esc(SITE['phone'].replace('-', ''))}">{esc(SITE['phone'])}</a>.</p><ul>{hrs}</ul>"""


def build_privacy():
    title = "Privacy Policy | Mario's Super Soil"
    desc = "How Mario's Super Soil collects, uses and protects your personal information when you shop, sign up for emails, use Plant Dr. Mario or apply for wholesale."
    path = "/privacy/"
    ld = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
              {"@type": "ListItem", "position": 2, "name": "Privacy policy", "item": abs_url(path)}]}]
    out = head(title, desc, path, jsonld=ld) + header()
    out += f"""  <section class="sec"><div class="wrap policy">
    <h1 class="nm" style="font-size:clamp(40px,7vw,88px)"><b>Privacy</b> <i>policy</i></h1>
    <p>Last updated: November 8, 2026</p>
    <p>Mario&rsquo;s Super Soil is a Canadian company based in Mississauga, Ontario. This policy explains what personal information we collect on this website, why we collect it, who we share it with and what choices you have. We keep it to what we need to run the shop. We never sell your information.</p>

    <h2>What we collect and why</h2>
    <ul>
      <li><strong>When you place an order:</strong> your name, email address, phone number, shipping address and what you ordered. We use it to take payment, pack and ship your order, send receipts and shipping updates, handle returns and keep our business and tax records.</li>
      <li><strong>When you sign up for emails</strong> (the sign-up box or pop-up): your email address. We use it to send you deals, planting tips and restock news, only because you asked us to.</li>
      <li><strong>After you order:</strong> we send one restock reminder email about two months later, suggesting you reorder what you bought. Every one of these emails has an unsubscribe link.</li>
      <li><strong>When you leave a review:</strong> the name, rating and comment you submit, and your email if you give it. Reviews are checked by us before they appear on the site.</li>
      <li><strong>When you apply for wholesale:</strong> your business name, contact name, email, phone and the details you give about your business. We use it to reply to you and set up an account.</li>
      <li><strong>When you use Plant Dr. Mario:</strong> the plant photos and the notes you send. They are sent to an AI service to produce the diagnosis you see on screen. We do not save your photos on our website.</li>
      <li><strong>When you contact us:</strong> whatever you send us by email or phone, so we can answer you.</li>
      <li><strong>Technical information:</strong> like most websites, our hosting company keeps basic server logs (such as your IP address, browser and the pages requested) for security and to keep the site running. We also use your IP address in a scrambled form to limit how often forms and Plant Dr. Mario can be used, so that nobody can flood them.</li>
    </ul>

    <h2>Payments</h2>
    <p>Payments are handled by Stripe. You enter your card details on Stripe&rsquo;s secure page, and we never see or store your full card number. Stripe gives us your name, email, phone, address and the order total so we can fulfil your order. Stripe&rsquo;s own privacy policy explains how it handles your information.</p>

    <h2>Cookies and browser storage</h2>
    <p>We do not use advertising or tracking cookies, and we do not run analytics tools on this site. We store a few things in your own browser so the site works: your shopping cart, a discount code you were given, whether you have closed the sign-up pop-up or the deal tab, and your choice of free gift. These stay on your device and you can clear them any time in your browser settings. The owner&rsquo;s admin page uses a login cookie that is only for the owner.</p>
    <p>The Instagram feed on our home page is provided by Behold and shows posts from Instagram. It loads only when you scroll down to it, and those services may set their own cookies or collect information as described in their policies. If you follow a link to Instagram, Facebook, Google or another site, that site&rsquo;s own policy applies.</p>

    <h2>Who we share information with</h2>
    <p>We share information only with the services that help us run the shop, and only what they need:</p>
    <ul>
      <li>Stripe, to take payments.</li>
      <li>Shipping carriers such as Canada Post, Purolator or UPS, who receive your name, address and phone number so they can deliver your order.</li>
      <li>Our website hosting company (Hostinger), which stores the site and our order records.</li>
      <li>Our email provider (Google), which sends and receives our emails.</li>
      <li>The AI service that analyses plant photos for Plant Dr. Mario (Anthropic), which receives only the photos and notes you send.</li>
      <li>Behold, which supplies the Instagram feed.</li>
      <li>The authorities, if the law requires it.</li>
    </ul>
    <p>Some of these providers process information outside Canada, including in the United States, so your information may be subject to the laws of those places.</p>

    <h2>How long we keep it</h2>
    <ul>
      <li>Order records: as long as we need them for accounting, tax and legal reasons. Canadian tax rules generally require businesses to keep records for six years.</li>
      <li>Email list: until you unsubscribe.</li>
      <li>Reviews: until you ask us to remove them or we take them down.</li>
      <li>Wholesale applications: as long as we need them to deal with your application and any account that follows.</li>
      <li>Plant photos: we do not keep them.</li>
    </ul>

    <h2>Your choices and rights</h2>
    <ul>
      <li><strong>Unsubscribe:</strong> use the link at the bottom of any marketing email, or email us and we will remove you.</li>
      <li><strong>See or fix your information:</strong> ask us what we hold about you, and we will tell you and correct anything that is wrong.</li>
      <li><strong>Delete your information:</strong> ask us to delete it. We will do so unless we need to keep some of it for tax, accounting or legal reasons.</li>
      <li><strong>Withdraw consent:</strong> you can change your mind about emails or other uses at any time.</li>
    </ul>
    <p>If you are not happy with how we handled your information, you can contact us first. You can also contact the Office of the Privacy Commissioner of Canada at priv.gc.ca.</p>

    <h2>Keeping your information safe</h2>
    <p>Our site uses HTTPS, orders and admin access are protected by a password, and card payments stay with Stripe. No website is completely risk free, but we take reasonable steps to protect what you give us and we only collect what we need.</p>

    <h2>Children</h2>
    <p>This website is for adults and is not meant for children. We do not knowingly collect information from children.</p>

    <h2>Changes to this policy</h2>
    <p>If we change how we handle your information, we will update this page and the date at the top.</p>

    <h2>Contact us</h2>
    <p>For any privacy question or request, contact our privacy contact, Mario, at:</p>
    {contact_block()}
    <hr style="border:0;border-top:1px solid var(--line);margin:48px 0 8px">
    </div></section>
"""
    out += footer()
    return out


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
    title = "Wholesale Organic Dry Amendments for Stores | Mario's Super Soil"
    desc = "Stock Mario's Super Soil organic dry amendments in your garden centre or store. Volume pricing from a Canadian maker. Apply online."
    path = "/wholesale/"
    ld = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
              {"@type": "ListItem", "position": 2, "name": "Wholesale", "item": abs_url(path)}]}]
    out = head(title, desc, path, jsonld=ld) + header()
    out += """  <section class="sec"><div class="wrap">
    <h1 class="nm" style="font-size:clamp(40px,7vw,88px)"><b>Wholesale</b> <i>for stores</i></h1>
    <p class="lede">Run a garden centre, hydroponics shop, feed store or independent retailer? Mario's Super Soil makes organic dry amendments in Mississauga, Ontario, and we would like to hear from you.</p>
    <ul class="perks">
      <li><strong>Canadian made</strong><br>Canadian made.</li>
      <li><strong>Volume pricing</strong><br>Wholesale pricing that improves as your order size grows, with minimum order quantities per tier.</li>
      <li><strong>Direct from the maker</strong><br>Order straight from us in Mississauga, Ontario, and talk to a real person.</li>
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



KIT_SLUGS = ["level-up", "flower-power", "kelp-meal", "alfalfa-meal", "compost-blend", "worm-castings"]
KIT_PATH = "/products/super-starter-pack/"


def build_kit_page():
    sp = next(b for b in SITE["blends"] if b["id"] == "starter-pack")
    prods = [next(q for q in PRODUCTS if q["slug"] == k) for k in KIT_SLUGS]
    title = "Super Starter Pack: Organic Gardening Kit | Mario's Super Soil"
    meta = "The Super Starter Pack is a six-bag organic gardening kit: Level Up, Flower Power, Kelp Meal, Alfalfa Meal, Compost and Worm Castings. 2 lb and 5 lb kits."
    kp = price_rows("super-starter-pack") or [(z["short"], z["price"]) for z in sp["kit_sizes"]]
    lo = min(v for _, v in kp); hi = max(v for _, v in kp)
    ld = [org_ld(),
          {"@context": "https://schema.org", "@type": "Product", "name": "Super Starter Pack", "description": meta, "url": abs_url(KIT_PATH),
           "image": [abs_url("/img/starter-kit.webp")] + [abs_url(f"/img/{q['f']}-front.webp") for q in prods],
           "brand": {"@type": "Brand", "name": SITE["name"]}, "category": "Organic dry amendment kit",
           "countryOfOrigin": {"@type": "Country", "name": "Canada"},
           "offers": {"@type": "AggregateOffer", "priceCurrency": "CAD", "lowPrice": f"{lo:.2f}", "highPrice": f"{hi:.2f}", "offerCount": len(kp), "url": abs_url(KIT_PATH)}},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
              {"@type": "ListItem", "position": 2, "name": "Products", "item": BASE + "/#products"},
              {"@type": "ListItem", "position": 3, "name": "Super Starter Pack", "item": abs_url(KIT_PATH)}]}]
    bags = "".join(f'<li style="--i:{n};--c:{n % 3};--r:{n // 3}"><a href="/products/{q["slug"]}/"><img src="/img/{q["f"]}-front.webp" width="170" height="220" alt="{esc(full_name(q))} bag"><span>{esc(full_name(q))}</span></a></li>' for n, q in enumerate(prods))
    rows = "".join(
        f'<li><a href="/products/{q["slug"]}/"><img src="/img/{q["f"]}-front.webp" width="64" height="83" loading="lazy" alt=""><span class="kt"><strong>{name_html(q)}</strong>'
        f'<small>{esc(q["use"])}. {esc(q["when"])}</small></span></a></li>' for q in prods)
    prices = "".join(f'<li><span>{esc(z["label"])}</span><strong>${next((v for l, v in kp if l.replace(" kit", "") == z["key"].replace("lb", " lb")), z["price"]):,.2f} CAD</strong></li>' for z in sp["kit_sizes"])
    size_opts = "".join(f'<option value="{z["key"]}">{esc(z["label"])}</option>' for z in sp["kit_sizes"])
    sub = "Super Starter Pack order"
    mail = f"mailto:{SITE['email']}?subject={sub.replace(' ', '%20')}&body=Hi%20Mario%2C%0A%0AI%20would%20like%20to%20order%20the%20Super%20Starter%20Pack.%0AKit%20size%20(2%20lb%20or%205%20lb)%3A%20%0AName%3A%20%0AShipping%20address%3A%20%0A"
    out = head(title, meta, KIT_PATH, og_image="/img/levelup-front.webp", jsonld=ld) + header()
    out += f"""  <section class="pdp kitpage" style="--accent:{sp['accent']}">
    <div class="wrap">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/#products">Products</a> / <span aria-current="page">Super Starter Pack</span></nav>
      <div class="kithero">
        <div class="kitwrap kitwrap3"><span class="kbox kbb" aria-hidden="true"><span class="kb-back"></span></span><ul class="kitgrid">{bags}</ul><span class="kbox kbf" aria-hidden="true"><span class="kb-lid l1"></span><span class="kb-lid l2"></span><span class="kb-front"><b>Super Starter</b> Pack</span></span></div>
        <div class="info">
          <h1 class="nm"><b>Super Starter</b> <i>Pack</i></h1>
          <span class="pq">Everything you need to have a successful grow</span>
          <ul class="kitprices">{prices}</ul>
          <div class="shopbox" id="buy-box" data-slug="super-starter-pack">
            <div class="buyrow">
              <div><label for="buy-size">Kit size</label><select id="buy-size">{size_opts}</select></div>
              <div><label for="buy-qty">Quantity</label><input id="buy-qty" type="number" min="1" max="20" value="1" inputmode="numeric"></div>
            </div>
            <p class="buyprice" id="buy-price" aria-live="polite">Choose a size</p>
            <button class="btn solid" type="button" id="buy-add">Add to cart</button>
            <p class="buymsg" id="buy-msg" role="status" aria-live="polite"></p>
          </div>
          <p class="ctas"><a class="btn" href="/#buy">Find a local shop</a></p>
          <p>A complete organic gardening kit for new gardeners. It brings together six of our organic dry amendments, so you can feed every stage of growth without choosing one product at a time. The bags are the same ones we sell on their own, with the dose printed on every bag.</p>
          <p class="store">Each kit has six bags: 6 x 2 lb in the 2 lb kit and 6 x 5 lb in the 5 lb kit. Ships across Canada.</p>
        </div>
      </div>
      <h2>What is in the kit</h2>
      <ul class="kitrows">{rows}</ul>
      <h2>Who it is for</h2>
      <p>New gardeners who want one box that covers the basics: an all-round blend (Level Up 3-3-3), a bloom blend (Flower Power 2-6-4), potassium and trace minerals from Kelp Meal, a gentle growth boost from Alfalfa Meal, and living soil from Compost and Worm Castings.</p>
      <p>Not sure how much to use? Try the free <a href="/soil-calculator/">soil amendment calculator</a>, or read <a href="/guides/organic-soil-amendments-canada/">our Canadian guide to organic soil amendments</a>.</p>
    </div>
  </section>
"""
    return out + footer()

# ---------------------------------------------------------------- guides (long-form, answer-first content for search and AI assistants)
def _pl(slug):
    p = next(q for q in PRODUCTS if q["slug"] == slug)
    return f'<a href="/products/{slug}/">{esc(plain_name(p))}</a>'


def _npk_table(slugs):
    rows = ""
    for s in slugs:
        p = next(q for q in PRODUCTS if q["slug"] == s)
        rows += f'<tr><td><a href="/products/{s}/">{esc(plain_name(p))}</a></td><td>{esc(npk_text(p))}</td><td>{esc(p["use"])}</td></tr>'
    return '<div class="tblwrap"><table class="gtable"><thead><tr><th>Amendment</th><th>NPK</th><th>Best known for</th></tr></thead><tbody>' + rows + "</tbody></table></div>"


def guides():
    G = []
    G.append({
        "slug": "organic-soil-amendments-canada",
        "title": "Organic Soil Amendments in Canada | Mario's Super Soil",
        "desc": "What organic dry soil amendments are, how to choose between meals, rock dusts and castings, and how to use them. Made in Ontario, shipped across Canada.",
        "h1": ("Organic soil", "amendments in Canada"),
        "short": "A plain-language guide to organic dry amendments: what they are, how to pick one, and how to use them.",
        "answer": "Organic dry amendments are natural, slow-acting ingredients (meals, rock dusts, castings and compost) that you mix into soil to feed plants and soil life over weeks and months. Mario's Super Soil makes them in Mississauga, Ontario, and ships across Canada.",
        "sections": [
            ("What are organic dry amendments?",
             "<p>Organic dry amendments are natural materials, such as ground bone, crab shell, feathers, seaweed, alfalfa, crushed rock and worm castings, that you work into soil or potting mix. They do not dissolve straight into the soil water like a salt. Soil microbes break them down gradually, so plants are fed steadily over weeks or months.</p>"
             "<p>Because they are dry and slow-acting, they are forgiving. They also feed the living soil, not only the plant.</p>"),
            ("The four groups of amendments",
             "<ul>"
             f"<li><strong>Meals</strong> are nutrient sources: {_pl('blood-meal')}, {_pl('bone-meal')}, {_pl('crab-meal')}, {_pl('feather-meal')}, {_pl('kelp-meal')} and {_pl('alfalfa-meal')}.</li>"
             f"<li><strong>Rock dusts and minerals</strong> supply calcium, magnesium, sulfur, phosphorus and trace minerals: {_pl('soft-rock-phosphate')}, {_pl('gypsum')}, {_pl('oyster-shell-flour')}, {_pl('dolomite-lime')} and {_pl('basalt-rock-dust')}.</li>"
             f"<li><strong>Castings and compost</strong> add live biology and organic matter: {_pl('worm-castings')} and {_pl('compost-blend')}.</li>"
             f"<li><strong>Blends</strong> combine several ingredients in one bag: {_pl('flower-power')} (2-6-4) and Level Up (3-3-3).</li>"
             "</ul>"),
            ("How to choose by what you want to achieve",
             "<ul>"
             f"<li><strong>Leafy, green growth (nitrogen):</strong> {_pl('blood-meal')} (12-0-0) for fast results, {_pl('feather-meal')} (11-0-0) for a slow, strong source, {_pl('alfalfa-meal')} for a gentler boost, {_pl('crab-meal')} (4-3-0) for nitrogen plus calcium.</li>"
             f"<li><strong>Roots, flowers and fruit (phosphorus):</strong> {_pl('bone-meal')} (4-10-0) or the slower {_pl('soft-rock-phosphate')}.</li>"
             f"<li><strong>All-round plant strength (potassium):</strong> {_pl('kelp-meal')} (1-0-4) and {_pl('alfalfa-meal')}.</li>"
             f"<li><strong>Calcium, magnesium and trace minerals:</strong> {_pl('oyster-shell-flour')}, {_pl('dolomite-lime')}, {_pl('gypsum')} and {_pl('basalt-rock-dust')}.</li>"
             f"<li><strong>Living, healthy soil:</strong> {_pl('worm-castings')} and {_pl('compost-blend')}.</li>"
             "</ul>"
             "<p>Not sure? Try the free <a href=\"/soil-calculator/\">soil amendment calculator</a>, or send a photo of a struggling plant to <a href=\"/plant-drmario/\">Plant Dr. Mario</a>.</p>"),
            ("How to use them",
             "<p>Every bag prints the dose, usually in tablespoons per gallon of soil, so there is no guesswork. Mix the amendment into the soil, water it in, and start with the lower end of the range on the bag. Slow-acting meals can take a few weeks to show an effect, so avoid adding more too soon.</p>"
             f"<p>For example, {_pl('bone-meal')} is used at 1 to 2 tablespoons per gallon of soil and releases its nutrients over about 4 months.</p>"),
            ("Buying organic dry amendments in Canada",
             "<p>Mario's Super Soil is a Canadian company based in Mississauga, Ontario. Bags come in 2 lb and 5 lb sizes, with directions in English and French, and orders ship across Canada. Orders of $120 or more include a free 2 lb bag of Level Up or Flower Power. See <a href=\"/shipping-returns/\">shipping and returns</a> for details, or find a <a href=\"/#buy\">local shop</a> that carries us.</p>"),
        ],
        "faq": [
            ("What are organic dry amendments?", "Natural, slow-acting ingredients such as meals, rock dusts, worm castings and compost that you mix into soil. They feed plants and soil life gradually."),
            ("Where can I buy organic soil amendments in Canada?", "Mario's Super Soil sells organic dry amendments online from Mississauga, Ontario, shipping across Canada, and through independent garden shops listed on the home page."),
            ("How much should I use?", "Follow the dose printed on the bag, usually 1 to 2 tablespoons per gallon of soil, and start at the lower end."),
            ("Can I use them indoors and outdoors?", "Yes. They are used in pots, raised beds, in-ground gardens and lawns. Follow the directions on each bag."),
        ],
    })
    G.append({
        "slug": "npk-organic-gardening",
        "title": "NPK Explained for Organic Gardeners | Mario's Super Soil",
        "desc": "What the three NPK numbers mean, how organic amendments differ, and which amendment supplies nitrogen, phosphorus or potassium. Includes a quick NPK chart.",
        "h1": ("NPK explained", "for organic gardeners"),
        "short": "What N-P-K means and which organic amendment supplies each nutrient.",
        "answer": "NPK stands for nitrogen (N), phosphorus (P) and potassium (K), the three main nutrients plants use. The three numbers on a bag, such as 4-10-0 for bone meal, are the percentages of each by weight.",
        "sections": [
            ("What do the three numbers mean?",
             "<p>The first number is nitrogen, the second is phosphorus and the third is potassium. Bone meal at 4-10-0 contains 4% nitrogen, 10% phosphorus and 0% potassium.</p>"
             "<ul><li><strong>Nitrogen (N)</strong> drives leaf and stem growth and a deep green colour.</li>"
             "<li><strong>Phosphorus (P)</strong> supports roots, flowers and fruit.</li>"
             "<li><strong>Potassium (K)</strong> supports overall plant strength and water balance.</li></ul>"),
            ("Why organic NPK numbers look lower",
             "<p>Organic amendments release nutrients as soil life breaks them down, so the numbers are lower than in fast-dissolving products. They also carry calcium, magnesium, trace minerals and organic matter that the numbers do not show. Mineral amendments such as gypsum, dolomite lime, oyster shell flour and basalt rock dust show little or no NPK because their job is calcium, magnesium, sulfur and trace minerals.</p>"),
            ("NPK chart for Mario's Super Soil amendments",
             _npk_table(["blood-meal", "feather-meal", "crab-meal", "alfalfa-meal", "bone-meal", "soft-rock-phosphate", "kelp-meal", "worm-castings", "compost-blend", "flower-power"]) +
             "<p>Level Up is a 3-3-3 all-round blend. See the <a href=\"/#products\">full range</a> for every bag.</p>"),
            ("Matching the amendment to the job",
             f"<p>For leafy growth, use a nitrogen source like {_pl('feather-meal')} or {_pl('alfalfa-meal')}. For roots and blooms, choose {_pl('bone-meal')} or {_pl('soft-rock-phosphate')}. For overall strength, add {_pl('kelp-meal')}. Round it out with {_pl('worm-castings')} to feed soil life. The free <a href=\"/soil-calculator/\">calculator</a> works out amounts for your bed or pot.</p>"),
        ],
        "faq": [
            ("What does NPK mean?", "Nitrogen, phosphorus and potassium. The numbers on a bag are the percentage of each by weight."),
            ("Which organic amendment is highest in nitrogen?", "Blood meal at 12-0-0 is the highest nitrogen amendment we make, followed by feather meal at 11-0-0."),
            ("Which organic amendment is highest in phosphorus?", "Bone meal at 4-10-0 is the highest phosphorus amendment we make."),
            ("Why do some amendments show 0-0-0?", "Mineral amendments such as gypsum, dolomite lime, oyster shell flour and basalt rock dust are used for calcium, magnesium, sulfur and trace minerals, not for NPK."),
        ],
    })
    G.append({
        "slug": "bone-crab-feather-meal",
        "title": "Bone vs Crab vs Feather Meal | Mario's Super Soil",
        "desc": "Compare bone meal, crab meal, feather meal, kelp meal and alfalfa meal: NPK, what each is best for, how much to use and how fast it works.",
        "h1": ("Bone, crab, feather,", "kelp and alfalfa meal compared"),
        "short": "How the five meal amendments differ and when to use each one.",
        "answer": "Blood meal (12-0-0) is fast nitrogen, feather meal (11-0-0) is slower nitrogen, bone meal (4-10-0) is for phosphorus, crab meal (4-3-0) adds nitrogen with calcium, kelp meal (1-0-4) adds potassium and ocean minerals, and alfalfa meal (3-0.5-3) is a gentle all-round boost.",
        "sections": [
            ("At a glance", _npk_table(["blood-meal", "feather-meal", "bone-meal", "crab-meal", "kelp-meal", "alfalfa-meal"])),
            ("Blood meal: fast nitrogen",
             f"<p>{_pl('blood-meal')} is 12-0-0 and is a fast-release nitrogen source that may take about a month to show results. Use 1 to 2 teaspoons per gallon of soil, in spring and again every 2 to 3 months. Yellow leaves may indicate a nitrogen deficiency.</p>"),
            ("Feather meal: strong, slow nitrogen",
             f"<p>{_pl('feather-meal')} is 11-0-0 and releases over 2 to 4 months, for lush leaves. Use 1 to 2 tablespoons per gallon of soil or coco and avoid overapplying.</p>"),
            ("Bone meal: phosphorus for roots, blooms and fruit",
             f"<p>{_pl('bone-meal')} is 4-10-0. Use 1 to 2 tablespoons per gallon of soil, mix in and water lightly. Its nutrients release over about 4 months.</p>"),
            ("Crab meal: nitrogen plus calcium",
             f"<p>{_pl('crab-meal')} is 4-3-0 and brings calcium from the shell. Use 1 to 2 teaspoons per gallon of soil, applied in spring and again every 2 to 3 months.</p>"),
            ("Kelp meal: potassium and ocean minerals",
             f"<p>{_pl('kelp-meal')} is 1-0-4 and supplies trace minerals from the sea. Mix 1 to 2 tablespoons per gallon of soil and apply monthly in the growing season.</p>"),
            ("Alfalfa meal: a gentle growth boost",
             f"<p>{_pl('alfalfa-meal')} is 3-0.5-3. Mix 2 tablespoons per gallon of soil and repeat in spring as needed.</p>"),
            ("Which one should I start with?",
             f"<p>If you want one bag for general use, a balanced blend like Level Up 3-3-3 or {_pl('flower-power')} 2-6-4 combines several of these. If you want to target a gap, pick the single meal that matches it. The <a href=\"/soil-calculator/\">calculator</a> can help you decide.</p>"),
        ],
        "faq": [
            ("What is the difference between bone meal and crab meal?", "Bone meal (4-10-0) is mostly a phosphorus source. Crab meal (4-3-0) gives nitrogen with calcium from crab shell."),
            ("Which meal has the most nitrogen?", "Blood meal, at 12-0-0. Feather meal is next at 11-0-0 and releases more slowly."),
            ("How long does bone meal last in soil?", "Our bone meal releases its nutrients over about 4 months."),
            ("Can I combine different meals?", "Yes. Many gardeners combine a nitrogen, a phosphorus and a potassium source. Follow each bag's dose and avoid overapplying."),
        ],
    })
    G.append({
        "slug": "vegetable-garden-ontario",
        "title": "Ontario Vegetable Garden Amendments | Mario's Super Soil",
        "desc": "A simple plan for feeding an organic vegetable garden in Ontario: what to add in spring, which amendment does what, and how much to use per bed.",
        "h1": ("Organic amendments", "for Ontario vegetable gardens"),
        "short": "A simple spring-to-summer plan for feeding an organic vegetable bed.",
        "answer": "Test your soil first, then mix in organic matter (worm castings or compost), add a calcium source and a phosphorus source at planting, and top up with a nitrogen meal during the season. Follow the dose printed on each bag.",
        "sections": [
            ("Start with the soil you have",
             "<p>Soil across Ontario ranges from heavy clay to sandy loam, and the right amendments depend on yours. A simple soil test (pH and basic nutrients) tells you whether to raise pH, add calcium or magnesium, or just add organic matter. Without a test, building the soil with organic matter is the safe first step.</p>"),
            ("A simple plan for a vegetable bed",
             "<ol>"
             f"<li><strong>Build the soil.</strong> Mix {_pl('compost-blend')} (1 part compost to 4 parts soil) or {_pl('worm-castings')} into the bed.</li>"
             f"<li><strong>Add calcium and fix pH if needed.</strong> {_pl('oyster-shell-flour')} (2.5 to 5 lb per 100 sq ft) gives slow calcium. {_pl('dolomite-lime')} raises pH and adds magnesium: about 5 lb per 100 sq ft raises pH from 5.5 to 6.5. Use one or the other based on your soil test, not both blindly.</li>"
             f"<li><strong>Feed roots and fruit.</strong> Add {_pl('bone-meal')} (1 to 2 tablespoons per gallon of soil) or {_pl('soft-rock-phosphate')} at planting.</li>"
             f"<li><strong>Feed leaves.</strong> For leafy crops, mix in {_pl('feather-meal')} or {_pl('alfalfa-meal')} and repeat as the bag directs.</li>"
             f"<li><strong>Finish with minerals.</strong> {_pl('kelp-meal')} and {_pl('basalt-rock-dust')} add potassium and trace minerals.</li>"
             "</ol>"
             "<p>Prefer one bag? <a href=\"/products/flower-power/\">Flower Power 2-6-4</a> or Level Up 3-3-3 combine several of these. The <a href=\"/soil-calculator/\">calculator</a> works out amounts for your bed size.</p>"),
            ("Heavy clay soil",
             f"<p>{_pl('gypsum')} supplies calcium and sulfur and is known for helping loosen clay. Mix 1 to 2 tablespoons per gallon of soil in pots or follow the bag for beds. Adding compost every year also improves clay structure.</p>"),
            ("Containers and raised beds",
             "<p>In pots and raised beds, the doses are given per gallon of soil, so it is easy to scale. Mix the amendment into the soil before planting and water it in.</p>"),
        ],
        "faq": [
            ("When should I add organic amendments to my garden?", "Mix them into the soil at planting in spring, and top up during the growing season as each bag directs."),
            ("How do I raise soil pH organically?", "Dolomite lime raises pH and adds calcium and magnesium. About 5 lb per 100 sq ft raises pH from 5.5 to 6.5, according to the bag."),
            ("What helps heavy clay soil?", "Gypsum and regular additions of compost or worm castings help improve clay soil."),
            ("Do I need a soil test?", "It is recommended. A test shows your pH and helps you choose between lime, oyster shell flour and other minerals."),
        ],
    })
    G.append({
        "slug": "worm-castings-vs-compost",
        "title": "Worm Castings vs Compost | Mario's Super Soil",
        "desc": "How worm castings and compost differ, what each does for soil, how much to use, and when to use both. Canadian-made worm castings and compost blend.",
        "h1": ("Worm castings", "vs compost"),
        "short": "What each one does, how to use them, and why many gardeners use both.",
        "answer": "Compost adds bulk organic matter that improves soil structure, while worm castings are a concentrated, biologically active amendment used in smaller amounts. Many gardeners use both.",
        "sections": [
            ("At a glance", _npk_table(["worm-castings", "compost-blend"])),
            ("Worm castings",
             f"<p>{_pl('worm-castings')} are the finished waste of earthworms, often called vermicast. They add live biology and small amounts of iron, calcium, magnesium, sulfur and other minerals. Mix them into potting soil, or use 1 to 2 cups around established plants and water thoroughly.</p>"),
            ("Compost",
             f"<p>{_pl('compost-blend')} is a balanced mix of decomposed organic materials that improves the physical, chemical and biological properties of soil. Mix 1 part compost with 4 parts soil, or spread it on beds and lawns. It can also be steeped as compost tea by aerating it in water for 24 to 48 hours.</p>"),
            ("Which should I use?",
             "<ul><li>Use <strong>compost</strong> in bulk to improve a bed's structure and water holding.</li>"
             "<li>Use <strong>worm castings</strong> for a concentrated boost of living material in pots, seed starting mixes and around plants.</li>"
             "<li>Use <strong>both</strong> with a nutrient amendment such as a <a href=\"/guides/bone-crab-feather-meal/\">meal</a> for a complete plan.</li></ul>"),
        ],
        "faq": [
            ("Are worm castings the same as compost?", "No. Worm castings are earthworm waste. Compost is decomposed organic matter. Both improve soil, but castings are more concentrated."),
            ("How much worm castings should I use?", "Mix into potting soil, or use 1 to 2 cups around established plants and water thoroughly."),
            ("Can I use worm castings and compost together?", "Yes. Use compost to build the bed and castings as a concentrated boost."),
            ("Does compost have an NPK number?", "Our compost blend is about 0.7-0.3-0.6. Its main value is organic matter and soil life, not NPK."),
        ],
    })
    G.append({
        "slug": "dolomite-lime-oyster-shell-gypsum",
        "title": "Dolomite vs Oyster Shell Flour vs Gypsum | Mario's Super Soil",
        "desc": "Compare three organic calcium sources: dolomite lime, oyster shell flour and gypsum. What each adds, how each affects pH, and how much to use.",
        "h1": ("Dolomite lime, oyster shell", "and gypsum compared"),
        "short": "Three calcium sources compared: which one raises pH and which one does not.",
        "answer": "Dolomite lime raises pH and adds calcium and magnesium. Oyster shell flour gives slow calcium and helps keep pH steady. Gypsum adds calcium and sulfur with little effect on pH.",
        "sections": [
            ("At a glance",
             "<div class=\"tblwrap\"><table class=\"gtable\"><thead><tr><th>Amendment</th><th>Calcium</th><th>Also provides</th><th>Effect on pH</th></tr></thead><tbody>"
             f"<tr><td>{_pl('dolomite-lime')}</td><td>21%</td><td>Magnesium 12%</td><td>Raises pH</td></tr>"
             f"<tr><td>{_pl('oyster-shell-flour')}</td><td>34%</td><td>96% calcium carbonate, micronutrients</td><td>Helps keep pH balanced</td></tr>"
             f"<tr><td>{_pl('gypsum')}</td><td>22%</td><td>Sulfur 17%</td><td>Little effect</td></tr>"
             "</tbody></table></div>"),
            ("Dolomite lime",
             f"<p>{_pl('dolomite-lime')} raises soil pH and adds calcium and magnesium. Use 1 to 2 tablespoons per gallon of soil. To raise pH from 5.5 to 6.5, use about 5 lb per 100 square feet.</p>"),
            ("Oyster shell flour",
             f"<p>{_pl('oyster-shell-flour')} is 96% calcium carbonate and breaks down gradually, giving lasting calcium. Use 1 to 2 tablespoons per gallon for new pots and 1 tablespoon for established plants, or 2.5 to 5 lb per 100 square feet in beds, mixed into the top 3 inches.</p>"),
            ("Gypsum",
             f"<p>{_pl('gypsum')} supplies calcium and sulfur with little effect on soil pH, so it suits soil that already has the right pH. It is also used to help loosen clay. Use 1 to 2 tablespoons per gallon of soil or coco.</p>"),
            ("How to choose",
             "<ul><li>Soil is acidic and you want to raise pH: <strong>dolomite lime</strong>.</li>"
             "<li>You want steady calcium without a big pH swing: <strong>oyster shell flour</strong>.</li>"
             "<li>pH is fine but you want calcium and sulfur, or you have heavy clay: <strong>gypsum</strong>.</li></ul>"
             "<p>A soil test tells you which applies. See also our <a href=\"/guides/vegetable-garden-ontario/\">vegetable garden plan</a>.</p>"),
        ],
        "faq": [
            ("Which amendment raises soil pH?", "Dolomite lime raises pH. Oyster shell flour helps keep pH balanced. Gypsum has little effect on pH."),
            ("What is the difference between lime and gypsum?", "Lime raises pH. Gypsum adds calcium and sulfur without changing pH much."),
            ("How much dolomite lime do I need?", "About 5 lb per 100 sq ft raises pH from 5.5 to 6.5, according to the bag. For pots use 1 to 2 tablespoons per gallon of soil."),
            ("Can I use oyster shell flour in pots?", "Yes. Use 1 to 2 tablespoons per gallon of soil in new pots and 1 tablespoon for established plants."),
        ],
    })
    G.append({
        "slug": "potted-plants-containers",
        "title": "Organic Amendments for Pots and Containers | Mario's Super Soil",
        "desc": "How to feed potted plants and container gardens organically: which dry amendments to mix into potting soil, how much per gallon, and how often.",
        "h1": ("Organic amendments", "for pots and containers"),
        "short": "Per-gallon doses for feeding potted plants and container gardens.",
        "answer": "Mix dry amendments into your potting soil before planting, using the per-gallon dose on the bag, usually 1 to 2 tablespoons per gallon, and add more only as each bag directs.",
        "sections": [
            ("Why dry amendments suit containers",
             "<p>Pots hold a limited amount of soil, so the dose is given per gallon of soil. Dry amendments are mixed in once and break down slowly, which means less frequent feeding and a gentler result.</p>"),
            ("Per-gallon doses",
             "<div class=\"tblwrap\"><table class=\"gtable\"><thead><tr><th>Amendment</th><th>Dose per gallon of soil</th></tr></thead><tbody>"
             f"<tr><td>{_pl('flower-power')}</td><td>1 tbsp (mature plants 2 tbsp, seedlings 1/2 tbsp)</td></tr>"
             f"<tr><td>{_pl('bone-meal')}</td><td>1 to 2 tbsp</td></tr>"
             f"<tr><td>{_pl('feather-meal')}</td><td>1 to 2 tbsp</td></tr>"
             f"<tr><td>{_pl('kelp-meal')}</td><td>1 to 2 tbsp, monthly in the growing season</td></tr>"
             f"<tr><td>{_pl('alfalfa-meal')}</td><td>2 tbsp</td></tr>"
             f"<tr><td>{_pl('crab-meal')}</td><td>1 to 2 tsp</td></tr>"
             f"<tr><td>{_pl('oyster-shell-flour')}</td><td>1 to 2 tbsp (new pots)</td></tr>"
             f"<tr><td>{_pl('gypsum')}</td><td>1 to 2 tbsp</td></tr>"
             f"<tr><td>{_pl('dolomite-lime')}</td><td>1 to 2 tbsp</td></tr>"
             f"<tr><td>{_pl('soft-rock-phosphate')}</td><td>2 tbsp</td></tr>"
             f"<tr><td>{_pl('basalt-rock-dust')}</td><td>1 tbsp</td></tr>"
             "</tbody></table></div>"
             "<p>Doses come from the bags. Start at the low end and do not stack several amendments without checking the calculator.</p>"),
            ("A simple potting mix recipe",
             f"<p>Mix {_pl('worm-castings')} into your potting soil, then add one nutrient amendment that matches your plant: a nitrogen meal for leafy plants, or bone meal or Flower Power for flowering and fruiting plants. Water it in well.</p>"
             "<p>Use the <a href=\"/soil-calculator/\">soil amendment calculator</a> to get amounts for your pot size.</p>"),
        ],
        "faq": [
            ("How much amendment do I put in a pot?", "Usually 1 to 2 tablespoons per gallon of soil. Check the bag for each product."),
            ("How often should I feed potted plants?", "Mix once at planting, and top up as each bag directs. Kelp meal is applied monthly in the growing season."),
            ("Can I use these indoors?", "Yes. They are used indoors and outdoors. Follow the directions on each bag."),
            ("Can I plant in the empty bag?", "Yes. The pouches are recyclable and reusable."),
        ],
    })
    return G


def build_guide(g, G):
    path = f"/guides/{g['slug']}/"
    faq = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in g["faq"])
    body = "".join(f"<h2>{esc(h)}</h2>{html}" for h, html in g["sections"])
    others = "".join(f'<li><a href="/guides/{x["slug"]}/">{esc(x["h1"][0])} {esc(x["h1"][1])}</a></li>' for x in G if x["slug"] != g["slug"])
    ld = [org_ld(),
          {"@context": "https://schema.org", "@type": "Article", "headline": g["title"].split(" | ")[0], "description": g["desc"],
           "mainEntityOfPage": abs_url(path), "inLanguage": "en-CA",
           "datePublished": "2026-11-09", "dateModified": TODAY,
           "author": {"@type": "Organization", "name": SITE["name"], "url": BASE + "/"},
           "publisher": {"@type": "Organization", "name": SITE["name"], "url": BASE + "/", "logo": {"@type": "ImageObject", "url": abs_url("/img/logo.png?v=3")}},
           "image": abs_url("/img/og-image.jpg?v=3")},
          {"@context": "https://schema.org", "@type": "FAQPage",
           "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in g["faq"]]},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
              {"@type": "ListItem", "position": 2, "name": "Guides", "item": abs_url("/guides/")},
              {"@type": "ListItem", "position": 3, "name": g["h1"][0] + " " + g["h1"][1], "item": abs_url(path)}]}]
    out = head(g["title"], g["desc"], path, jsonld=ld) + header()
    out += f"""  <section class="sec"><div class="wrap policy gpage">
    <p class="crumbs"><a href="/">Home</a> / <a href="/guides/">Guides</a></p>
    <h1 class="nm" style="font-size:clamp(34px,6vw,76px)"><b>{esc(g['h1'][0])}</b> <i>{esc(g['h1'][1])}</i></h1>
    <p class="lede"><strong>Short answer:</strong> {esc(g['answer'])}</p>
    {body}
    <h2>Questions</h2>
    <div class="faq">{faq}</div>
    <h2>Keep reading</h2>
    <ul>{others}<li><a href="/#products">Shop all organic dry amendments</a></li></ul>
    <p class="small">Written by the team at {esc(SITE['name'])}, Mississauga, Ontario. Last updated {TODAY}.</p>
  </div></section>
"""
    return out + footer()


def build_guides_index(G):
    path = "/guides/"
    title = "Organic Gardening Guides | Mario's Super Soil"
    desc = "Plain-language guides to organic dry amendments in Canada: NPK, choosing between meals, rock dusts and castings, and how much to use."
    items = "".join(f'<li><a href="/guides/{g["slug"]}/"><strong>{esc(g["h1"][0])} {esc(g["h1"][1])}</strong></a><br>{esc(g["short"])}</li>' for g in G)
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Organic gardening guides", "url": abs_url(path),
           "hasPart": [{"@type": "Article", "headline": g["title"].split(" | ")[0], "url": abs_url(f"/guides/{g['slug']}/")} for g in G]},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
              {"@type": "ListItem", "position": 2, "name": "Guides", "item": abs_url(path)}]}]
    out = head(title, desc, path, jsonld=ld) + header()
    out += f"""  <section class="sec"><div class="wrap policy gpage">
    <h1 class="nm" style="font-size:clamp(40px,7vw,88px)"><b>Gardening</b> <i>guides</i></h1>
    <p class="lede">Straight answers on organic dry amendments, from a Canadian company that makes them. Every guide links to the exact products and doses on our bags.</p>
    <ul class="gl">{items}</ul>
    <p>Also try the free <a href="/soil-calculator/">soil amendment calculator</a> and <a href="/plant-drmario/">Plant Dr. Mario</a> photo diagnosis.</p>
  </div></section>
"""
    return out + footer()


def llms_txt():
    prods = "\n".join(f"- [{full_name(p)}]({abs_url('/products/' + p['slug'] + '/')}): {p['use']}. Sizes 2 lb and 5 lb." for p in PRODUCTS)
    gl = "\n".join(f"- [{g['h1'][0]} {g['h1'][1]}]({abs_url('/guides/' + g['slug'] + '/')}): {g['short']}" for g in guides())
    return f"""# {SITE['name']}

> {SITE['name']} is a Canadian company in Mississauga, Ontario that makes organic dry soil amendments (meals, rock dusts, worm castings, compost and blends) for gardeners and growers. Orders ship across Canada. Wholesale is available to garden centres and stores.

Key facts:
- Location: {SITE['address']['city']}, {SITE['address']['region']}, Canada. Phone {SITE['phone']}. Email {SITE['email']}.
- Products are organic dry amendments in 2 lb and 5 lb bags with directions in English and French; larger orders are packed as multiple 5 lb bags.
- Ships within Canada only. Orders of $120 or more include a free 2 lb bag of Level Up 3-3-3 or Flower Power 2-6-4. 30 day returns on unused items.
- Main blends: Level Up 3-3-3 and Flower Power 2-6-4. A Super Starter Pack is available in 2 lb and 5 lb sizes.

## Products
{prods}

## Guides and tools
{gl}
- [Soil amendment calculator]({abs_url('/soil-calculator/')}): free tool that works out amounts by plant, bed or pot size.
- [Plant Dr. Mario]({abs_url('/plant-drmario/')}): upload a plant photo for amendment suggestions.

## Business
- [Wholesale for stores]({abs_url('/wholesale/')})
- [Shipping and returns]({abs_url('/shipping-returns/')})
- [Privacy policy]({abs_url('/privacy/')})
"""


def llms_full_txt():
    parts = [llms_txt(), "\n## Product details\n"]
    for p in PRODUCTS:
        parts.append(f"### {full_name(p)}\nURL: {abs_url('/products/' + p['slug'] + '/')}\nNPK: {npk_text(p)}\nBest for: {p['use']}\n" + " ".join(p["desc"]) + f"\nHow to use: {p['how_en']}\nSizes: " + "; ".join(p["sizes"]) + "\n")
    parts.append("\n## FAQ\n")
    for q, a in SITE["faq"]:
        parts.append(f"Q: {q}\nA: {a}\n")
    return "\n".join(parts)


AI_BOTS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot", "Perplexity-User", "Google-Extended", "Applebot-Extended", "Bingbot", "Googlebot"]


# ---------------------------------------------------------------- write


SEARCH_KW = {
    "level-up": "all purpose balanced vegetables herbs flowers beginner blend",
    "flower-power": "bloom flowers fruit phosphorus tomatoes peppers blend",
    "crab-meal": "calcium chitin nitrogen shell",
    "bone-meal": "phosphorus roots blooms fruit bulbs",
    "kelp-meal": "potassium seaweed trace minerals",
    "alfalfa-meal": "nitrogen potassium growth triacontanol",
    "feather-meal": "nitrogen leaves green lawn",
    "blood-meal": "nitrogen fast yellow leaves deer rabbits repel bloodmeal",
    "soft-rock-phosphate": "phosphorus colloidal slow release",
    "gypsum": "clay calcium sulfur sulphur loosen soil",
    "oyster-shell-flour": "calcium ph lime shell",
    "dolomite-lime": "lime ph acid calcium magnesium raise",
    "basalt-rock-dust": "minerals silica remineralize rock dust trace",
    "worm-castings": "vermicast worm poop biology microbes seed starting",
    "compost-blend": "organic matter soil improver tea topsoil",
}


# Things people search for that we do not sell: (search words, our similar products, note shown above them)
SEARCH_ALT = [
    (["nitrogen booster", "high nitrogen", "urea"], ["blood-meal", "feather-meal", "alfalfa-meal"], "high-nitrogen organic amendments"),
    (["fish", "fish emulsion", "fish meal", "fish bone", "fish hydrolysate"], ["crab-meal", "bone-meal", "kelp-meal"], "seafood-based organic amendments"),
    (["bat guano", "guano", "rock phosphate", "high phosphorus", "bloom booster", "flower booster", "bloom"], ["flower-power", "bone-meal", "soft-rock-phosphate"], "phosphorus for roots and blooms"),
    (["azomite", "glacial rock dust", "greensand", "rock dust", "trace minerals", "remineralize"], ["basalt-rock-dust", "kelp-meal", "oyster-shell-flour"], "mineral and trace element sources"),
    (["lime", "garden lime", "agricultural lime", "calcium carbonate", "raise ph", "ph up", "sweet soil"], ["dolomite-lime", "oyster-shell-flour"], "calcium sources that help balance pH"),
    (["epsom", "epsom salt", "magnesium sulfate", "magnesium", "langbeinite", "k-mag", "kmag"], ["dolomite-lime", "gypsum", "basalt-rock-dust"], "calcium, magnesium and sulfur sources"),
    (["potash", "sulfate of potash", "potassium", "sul-po-mag"], ["kelp-meal", "alfalfa-meal", "level-up"], "potassium sources"),
    (["manure", "cow manure", "chicken manure", "mushroom compost", "peat", "topsoil", "top soil", "soil conditioner", "humus"], ["compost-blend", "worm-castings"], "soil builders"),
    (["miracle gro", "miracle-gro", "fertilizer", "fertiliser", "plant food", "all purpose", "20-20-20", "synthetic", "npk", "tomato food", "vegetable food"], ["level-up", "flower-power", "worm-castings"], "organic all-purpose options"),
    (["seaweed", "seaweed extract", "sea kelp", "ocean"], ["kelp-meal"], "seaweed-based amendments"),
    (["potting soil", "potting mix", "soil mix", "coco", "seed starting", "seedlings"], ["worm-castings", "compost-blend", "level-up"], "good to mix into your potting soil"),
    (["lawn", "grass", "turf"], ["feather-meal", "level-up", "compost-blend"], "good for lawns"),
    (["bugs", "pests", "aphids", "nematodes", "chitin", "fungus gnats"], ["crab-meal"], "crab meal contains chitin and supports root and pest resilience"),
    (["epsom"], [], ""),
]


def search_index():
    items = []
    for p in PRODUCTS:
        rows = price_rows(p["slug"])
        items.append({"t": full_name(p), "u": f"/products/{p['slug']}/", "i": f"/img/{p['f']}-front.webp",
                      "d": p["use"] + (", from $%.2f" % min(x[1] for x in rows) if rows else ""),
                      "k": " ".join([p["use"], npk_text(p), dict(CATS).get(p.get("cat"), ""), SEARCH_KW.get(p["slug"], ""), " ".join(p["ben"])])})
    sp = next((b for b in SITE["blends"] if b["id"] == "starter-pack"), None)
    if sp:
        items.append({"t": "Super Starter Pack", "u": KIT_PATH, "i": "/img/levelup-front.webp", "d": " · ".join(f"{l} ${v:,.2f}" for l, v in price_rows("super-starter-pack")),
                      "k": "starter kit beginner gift bundle level up flower power kelp alfalfa compost worm castings"})
    for g in guides():
        items.append({"t": g["h1"][0] + " " + g["h1"][1], "u": f"/guides/{g['slug']}/", "g": "Guide", "d": g["short"], "k": g["title"]})
    for t, u, d, k in [("Soil amendment calculator", "/soil-calculator/", "How much to use for your bed or pot", "calculator how much dose"),
                       ("Plant Dr. Mario", "/plant-drmario/", "Upload a plant photo for help", "diagnose problem sick yellow leaves photo"),
                       ("Wholesale for stores", "/wholesale/", "Stock Mario's Super Soil in your shop", "retail store garden centre bulk"),
                       ("Shipping and returns", "/shipping-returns/", "Shipping rates, delivery times, returns", "delivery refund postage")]:
        items.append({"t": t, "u": u, "g": "Page", "d": d, "k": k})
    alt = [{"w": w, "u": [f"/products/{x}/" for x in sl], "n": n} for w, sl, n in SEARCH_ALT if sl]
    return {"items": items, "alt": alt, "pop": ["/products/level-up/", "/products/flower-power/", "/products/worm-castings/"]}


def chat_kb():
    """Knowledge for the Ask Mario chat assistant (api/chat_kb.json). Only facts that already appear on the site."""
    L, prods = [], []
    for p in PRODUCTS:
        pr = price_rows(p["slug"])
        price = ("from $%.2f" % min(x[1] for x in pr)) if pr else ""
        prods.append({"slug": p["slug"], "name": full_name(p), "url": f"/products/{p['slug']}/", "price": price})
        L.append(f"[{p['slug']}] {full_name(p)} | NPK {npk_text(p)} | {p['use']}\n  About: " + " ".join(p["desc"]) + f"\n  How to use: {p['how_en']}\n  Sizes: " + "; ".join(p["sizes"]) + (f"\n  Prices (CAD, before tax and shipping): " + ", ".join(f"{a} ${b:.2f}" for a, b in pr) if pr else ""))
    for b in SITE["blends"]:
        slug = b["id"]
        if any(q["slug"] == slug for q in PRODUCTS):
            continue
        name = (b["a"] + " " + b["b"]).strip()
        prods.append({"slug": slug, "name": name, "url": KIT_PATH if slug == "starter-pack" else "/#products", "price": ("from $%.2f" % b["from"]) if b.get("from") else ""})
        rows = "; ".join(f"{k}: {v}" for k, v in b.get("rows", []))
        L.append(f"[{slug}] {name} | blend | {b['tagline']} {b['text']}\n  {rows}" + (f"\n  Price: {b['price_label']}" if b.get("price_label") else (f"\n  Price: from ${b['from']:.2f} CAD" if b.get("from") else "")))
    L.append("GOOD TO KNOW\n- We ship across Canada only, from Mississauga, Ontario. Shipping is a flat rate by order weight, shown in the cart before paying. Tax is worked out at checkout. Most orders arrive in 2 to 3 business days; allow 2 to 10.\n- Orders of $120 or more include a free 2 lb bag of Level Up 3-3-3 or Flower Power 2-6-4 (chosen in the cart).\n- Returns: within 30 days of receiving, unused and in original packaging; email us first; the customer pays return shipping. Damaged or wrong items: contact us with photos.\n- Bag sizes are 2 lb and 5 lb. 10 lb and 20 lb orders are packed as 2 or 4 of the 5 lb bags.\n- Directions are printed in English and French.\n- Stores and wholesale: stores can apply at /wholesale/. A list of shops that carry us is in the Where to buy section on the home page.\n- Tools: soil amendment calculator at /soil-calculator/, plant photo help at /plant-drmario/, guides at /guides/.\n- Contact: " + SITE["email"] + ", phone " + SITE["phone"] + ". Hours: " + "; ".join(f"{a} {b}" for a, b in SITE["hours"]) + " (Eastern time).")
    L.append("FAQ\n" + "\n".join(f"Q: {q}\nA: {a}" for q, a in SITE["faq"]))
    return {"products": prods, "text": "\n\n".join(L)}

def main():
    sync_prices()
    pages = {"index.html": build_home(), "404.html": build_404(), "soil-calculator/index.html": build_calculator(), "plant-drmario/index.html": build_drmario(), "cart/index.html": build_cart(), "order-complete/index.html": build_order_complete(), "admin/index.html": build_admin(), "wholesale/index.html": build_wholesale(), "shipping-returns/index.html": build_policy(), "privacy/index.html": build_privacy()}
    for p in PRODUCTS:
        pages[f"products/{p['slug']}/index.html"] = build_product(p)
    G = guides()
    pages["products/super-starter-pack/index.html"] = build_kit_page()
    pages["guides/index.html"] = build_guides_index(G)
    for g in G:
        pages[f"guides/{g['slug']}/index.html"] = build_guide(g, G)

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
    (ROOT / "assets/search-index.json").write_text(json.dumps(search_index(), ensure_ascii=False, separators=(",", ":")))
    (ROOT / "api/chat_kb.json").write_text(json.dumps(chat_kb(), ensure_ascii=False, indent=1) + "\n")

    # sitemap (indexable pages only)
    urls = ""
    for rel in ["index.html", "soil-calculator/index.html", "plant-drmario/index.html", "wholesale/index.html", "shipping-returns/index.html", "privacy/index.html", "guides/index.html"] + [f"guides/{g['slug']}/index.html" for g in G] + [f"products/{p['slug']}/index.html" for p in PRODUCTS] + ["products/super-starter-pack/index.html"]:
        loc = BASE + "/" + rel.replace("index.html", "")
        prio = "1.0" if rel == "index.html" else "0.8"
        urls += f"  <url><loc>{loc}</loc><lastmod>{new[rel]['lastmod']}</lastmod><priority>{prio}</priority></url>\n"
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")

    if SITE["staging"]:
        robots = "User-agent: *\nDisallow: /\n"
    else:
        robots = f"User-agent: *\nAllow: /\nDisallow: /data/\nDisallow: /tools/\nDisallow: /admin/\nDisallow: /api/\nDisallow: /cart/\n\nSitemap: {BASE}/sitemap.xml\n"
        robots += "\n# AI assistants and search engines are welcome to read and recommend this site.\n" + "".join(f"User-agent: {b}\nAllow: /\nDisallow: /api/\nDisallow: /admin/\nDisallow: /cart/\n\n" for b in AI_BOTS)
    (ROOT / "robots.txt").write_text(robots)
    (ROOT / "llms.txt").write_text(llms_txt())
    (ROOT / "llms-full.txt").write_text(llms_full_txt())
    print(f"built {len(pages)} pages; staging={SITE['staging']}")


if __name__ == "__main__":
    main()
