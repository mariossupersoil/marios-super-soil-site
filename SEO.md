# SEO playbook for mariossupersoil site

Read this before making any change. It is the rulebook for the weekly SEO review.

## How the site works
- Source of truth: `data/site.json` (home page, contact, FAQ, blends, stores) and `data/products.json` (six product pages).
- Page templates and the sitemap/robots generator: `tools/build.py`. Styles: `assets/style.css`.
- Hostinger serves the repo files as-is with no build step, so generated HTML is committed. After any change run:
  1. `python3 tools/build.py`
  2. `python3 tools/audit.py` (must report 0 FAIL)
- `data/.page-hashes.json` tracks page changes so `sitemap.xml` `lastmod` dates stay honest. Commit it.
- `data/site.json` -> `"staging": true` makes every page `noindex` and `robots.txt` block crawling. Only the owner flips this to `false` when the site goes live on the main domain. Never flip it yourself.

## Target searches (Canada, English)
organic fertilizer Canada, organic soil amendments Canada, organic dry fertilizer, bone meal fertilizer 4-10-0, crab meal fertilizer 4-3-0, feather meal 11-0-0, kelp meal 1-0-4, alfalfa meal fertilizer, worm castings, organic fertilizer for tomatoes, organic fertilizer Mississauga / Ontario.

## What the weekly run may change
- `<title>` and meta description wording (titles 20-65 chars, descriptions 70-165 chars, one unique pair per page).
- Heading wording, image `alt` text, internal links, JSON-LD structured data, sitemap, robots.
- Add or reword FAQ entries (in `data/site.json`) when searches show a real question people ask. Answers must come from facts already on this site or on the product bags.
- Fix anything `tools/audit.py` flags, and broken external links.
- Small copy tweaks that include a target search naturally.

## What it must never change or claim
- Product facts: NPK, ingredients, doses, bag sizes, net weights, prices. These come from the bags and the owner.
- Contact details, hours, store listings, social links.
- No unproven benefit claims (yield, "best", "proven", health or pest-control promises beyond what the bag already says).
- The owner is testing a new Level Up and Flower Power recipe. Never call it better, new or improved, and do not change those two blends' ingredient lists.
- No cannabis-related copy, no giveaways, no competitor names, no invented reviews, no fake ratings or schema `aggregateRating`/`offers` data.
- Holidays and seasonal hooks: Canadian, non-religious or Christian only.
- Do not add pages, change URLs, or rename slugs without owner approval (propose in the PR text instead).

## Process each week
1. Run `python3 tools/audit.py` and note failures.
2. Check the live site (and the staging copy if not yet launched) for broken links and missing pages.
3. Web search the target searches. Note who ranks, which questions are asked, and whether this site appears. Be honest: rankings move slowly and one week of data is noise.
4. Make a small set of safe edits from the list above. Prefer 3-6 well-chosen changes over many.
5. Rebuild, re-audit, commit on a branch named `seo/YYYY-MM-DD`, open a pull request. Describe what changed, why, and what you chose not to change.
6. Never push to `main` directly. The owner approves by merging; Hostinger then deploys automatically.

## Soil calculator page (`/soil-calculator/`)
- Content lives in `data/calculator-body.inc`, `assets/calculator.js` (plant data, rates, product links) and `assets/calculator.css` (scoped under `.calc-panel`). These are the owner's own tool: do not edit rates, product data or plant advice. The weekly run may only touch the page's title, description, intro paragraph (in `build_calculator()`) and JSON-LD.
- The tool contains cannabis plant options (veg, flower, full cycle) that the owner wants kept so cannabis growers can see recommended doses. Leave them in. Do not add cannabis wording to this page's title, description or intro, and do not add cannabis copy anywhere else on the site.

## Plant Dr. Mario (`/plant-drmario/`)
- Photo diagnosis tool: page built by `build_drmario()`, front end in `assets/drmario.js` and `assets/drmario.css`, server script `api/diagnose.php` (calls the Claude API with the owner's key from `api/config.php`, which is not in GitHub).
- The weekly run may only adjust the page's title, description, intro text and JSON-LD. Never touch `api/`, the key or its limits, and never commit `api/config.php`.
- Recommended products come from `api/catalog.json` (same list as the calculator). Keep copy to "may help"; no cure or result promises.

## Shop (cart, checkout, prices)
- Never edit `api/`, `assets/cart.js`, `api/prices.json` or the cart and order pages. They are noindex and outside the weekly SEO scope. Never add `offers`, prices or `aggregateRating` to structured data unless the owner asks.
- Never touch `/admin/`, `assets/admin.js`, `api/admin.php`, `api/lib.php`, `api/store.json` or discount codes.
