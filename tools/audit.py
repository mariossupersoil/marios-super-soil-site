#!/usr/bin/env python3
"""Offline SEO audit of the generated site. Run from the repo root: python3 tools/audit.py
Prints FAIL / WARN / ok lines and exits 1 if any FAIL. No network needed.
"""
import json, pathlib, re, sys
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "data/site.json").read_text())
BASE = SITE["base_url"].rstrip("/")

pages = sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts)


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""; self.in_title = False
        self.meta = {}; self.h = {"h1": 0, "h2": 0}; self.canon = ""
        self.imgs = []; self.links = []; self.ld = []; self.in_ld = False; self.text = []
        self.skip = 0

    def handle_starttag(self, t, a):
        a = dict(a)
        if t == "title": self.in_title = True
        elif t == "meta" and a.get("name"): self.meta[a["name"]] = a.get("content", "")
        elif t == "link" and a.get("rel") == "canonical": self.canon = a.get("href", "")
        elif t in self.h: self.h[t] += 1
        elif t == "img": self.imgs.append(a)
        elif t == "a" and a.get("href"): self.links.append(a["href"])
        elif t == "script" and a.get("type") == "application/ld+json": self.in_ld = True; self.ld.append("")
        if t in ("script", "style"): self.skip += 1

    def handle_endtag(self, t):
        if t == "title": self.in_title = False
        if t == "script": self.in_ld = False
        if t in ("script", "style"): self.skip -= 1

    def handle_data(self, d):
        if self.in_title: self.title += d
        if self.in_ld: self.ld[-1] += d
        elif not self.skip: self.text.append(d)


fails = warns = 0
def out(level, page, msg):
    global fails, warns
    if level == "FAIL": fails += 1
    if level == "WARN": warns += 1
    print(f"{level:4} {page}: {msg}")

titles, descs = {}, {}
for f in pages:
    rel = "/" + str(f.relative_to(ROOT)).replace("index.html", "")
    p = P(); p.feed(f.read_text())
    noindex = "noindex" in p.meta.get("robots", "")
    tl = len(p.title.strip())
    if not (20 <= tl <= 65): out("WARN" if tl else "FAIL", rel, f"title length {tl} (aim 20-65)")
    d = p.meta.get("description", "")
    if not d: out("FAIL", rel, "missing meta description")
    elif not (70 <= len(d) <= 165): out("WARN", rel, f"meta description length {len(d)} (aim 70-165)")
    if p.h["h1"] != 1: out("FAIL", rel, f"{p.h['h1']} h1 tags (want exactly 1)")
    if not p.canon: out("FAIL", rel, "missing canonical")
    elif not p.canon.startswith(BASE): out("FAIL", rel, f"canonical not on base url: {p.canon}")
    for im in p.imgs:
        if "alt" not in im: out("FAIL", rel, f"img without alt: {im.get('src')}")
        if not (im.get("width") and im.get("height")): out("WARN", rel, f"img without width/height: {im.get('src')}")
    for j in p.ld:
        try: json.loads(j)
        except Exception as e: out("FAIL", rel, f"invalid JSON-LD: {e}")
    for h in p.links:
        if h.startswith("/") and not h.startswith("//"):
            tgt = h.split("#")[0].split("?")[0]
            fp = ROOT / tgt.lstrip("/")
            if tgt and not (fp.is_file() or (fp / "index.html").is_file()):
                out("FAIL", rel, f"broken internal link {h}")
    words = len(re.findall(r"\w+", " ".join(p.text)))
    if words < 150 and "404" not in rel: out("WARN", rel, f"thin content ({words} words)")
    if not noindex:
        titles.setdefault(p.title.strip(), []).append(rel)
        descs.setdefault(d, []).append(rel)

for t, v in titles.items():
    if len(v) > 1: out("FAIL", ",".join(v), f"duplicate title: {t}")
for t, v in descs.items():
    if len(v) > 1 and t: out("FAIL", ",".join(v), "duplicate meta description")

sm = (ROOT / "sitemap.xml").read_text()
for f in pages:
    rel = "/" + str(f.relative_to(ROOT)).replace("index.html", "")
    if rel == "/404.html": continue
    if BASE + rel not in sm: out("FAIL", rel, "missing from sitemap.xml")

if SITE["staging"]: out("WARN", "site", "staging=true: pages are noindex and robots.txt blocks crawling")
print(f"\n{len(pages)} pages checked: {fails} fail, {warns} warn")
sys.exit(1 if fails else 0)
