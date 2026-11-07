# Mario's Super Soil website

Static site for Mario's Super Soil (organic dry fertilizers and soil amendments, Mississauga, Ontario).

- `index.html` and `products/*/index.html` are generated. Do not edit them by hand.
- Edit `data/site.json`, `data/products.json` or `tools/build.py`, then run `python3 tools/build.py` and `python3 tools/audit.py`.
- `SEO.md` explains the weekly SEO process and its rules.

## Deploy (Hostinger)
Hostinger hPanel -> Websites -> Manage -> Advanced -> Git. Install the Hostinger GitHub app, pick this repository and the `main` branch, and set the target folder to the folder of the site you want to publish to. Auto-deploy is on by default, so each push to `main` republishes the site.

Do not point the target at the folder of the live mariossupersoil.ca site until you are ready to replace it. Use a subdomain folder (for example `new.mariossupersoil.ca`) for preview.

## Go live checklist
1. Set `"staging": false` in `data/site.json`, run `python3 tools/build.py`, commit and merge.
2. Submit `https://mariossupersoil.ca/sitemap.xml` in Google Search Console.
3. Keep the store: the "Shop online" buttons link to the current store pages.

## Plant Dr. Mario setup (one time, on Hostinger)
1. In hPanel open File Manager, go to `public_html/api/` (after the first deploy).
2. Copy `config.sample.php` to `config.php` and paste the Anthropic API key from console.anthropic.com. Never put the key in GitHub or chat.
3. Open `/plant-drmario/` and diagnose a test photo. Limits (12 per person and 400 total per day) are set in `config.php`.

## Shop: cart and checkout (Stripe)
- Prices live in `api/prices.json` (CAD, before tax and shipping, for example `24.99`). `null` means no price yet and that size can't be bought. `tools/build.py` keeps the file's structure in step with `data/products.json` and never changes a price.
- Shipping is by total order weight from `api/shipping.json` (CAD tiers). Each size's shipping weight is `weight_kg` in `api/prices.json`. Add to `api/config.php` on the server: `stripe_secret_key` (sk_test_... first, then sk_live_...), and `automatic_tax` (needs Stripe Tax enabled in Stripe). Never commit config.php.
- The cart is stored in the shopper's browser. `api/checkout.php` re-prices everything on the server and creates a Stripe Checkout session; Stripe takes the card and emails receipts.

## Owner admin (`/admin/`)
- Log in with `admin_password` from `api/config.php` (at least 10 characters). Edit prices, hide sizes or products, shipping rates and discount codes. Changes are saved on the server in `api/store.json` (not in GitHub, so deploys never overwrite them) and apply to the shop immediately.
- Once a price is saved in the admin it wins over `api/prices.json`. Use the admin for prices from now on.
- Discount codes are checked on the server and applied through Stripe coupons. A code's "Used" count goes up when a paid order lands on the thank-you page.
- Sales (admin): percent or dollar-off prices for one product, one size or everything, with optional start and end dates. The shop shows the old price crossed out, the sale price and a Sale tag, and checkout charges the sale price. Stored in `api/store.json`.
- Stock (admin): "In stock" per size. Counts down when a paid order is recorded (Stripe webhook `api/webhook.php`, with the thank-you page as a backup), and the shop shows Out of stock at 0. Blank = not tracked. Set `stripe_webhook_secret` in config.php and add the webhook in Stripe (Developers > Webhooks, URL `https://<site>/api/webhook.php`, event `checkout.session.completed`).
