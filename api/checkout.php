<?php
// Cart -> Stripe Checkout. Everything is priced on the server; the browser is never trusted for prices.
declare(strict_types=1);
require __DIR__ . '/lib.php';
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') fail(405, 'Use POST.');
$cfg = cfg();
$sk = $cfg['stripe_secret_key'] ?? '';
if ($sk === '' || str_contains($sk, 'PASTE')) fail(503, 'Checkout is not set up yet. Please contact us to order.');
$tiers = tiers();
if (!$tiers) fail(503, 'Checkout is not set up yet. Please contact us to order.');
$autoTax = (bool)($cfg['automatic_tax'] ?? true);
$allowedHosts = $cfg['allowed_hosts'] ?? ['mariossupersoil.ca', 'www.mariossupersoil.ca'];

$host = strtolower(preg_replace('/:\d+$/', '', $_SERVER['HTTP_HOST'] ?? ''));
$hostOk = in_array($host, $allowedHosts, true) || str_ends_with($host, '.hostingersite.com') || $host === 'localhost';
if (!$hostOk) fail(403, 'Not allowed.');
$origin = $_SERVER['HTTP_ORIGIN'] ?? ($_SERVER['HTTP_REFERER'] ?? '');
if ($origin !== '' && (parse_url($origin, PHP_URL_HOST) ?: '') !== $host) fail(403, 'Not allowed.');
$base = (($host === 'localhost') ? 'http' : 'https') . '://' . ($_SERVER['HTTP_HOST'] ?? $host);

$in = json_decode((string)file_get_contents('php://input', false, null, 0, 65536), true) ?: [];
$cart = price_cart(is_array($in['items'] ?? null) ? $in['items'] : [], catalog());

$disc = null; $codeRaw = trim((string)($in['code'] ?? ''));
if ($codeRaw !== '') $disc = apply_code($codeRaw, $cart['subtotal_cents']);

$shipPrice = ship_price($cart['kg'], $tiers);
if ($shipPrice === null) fail(400, 'This order is too heavy for online checkout. Please email us to arrange shipping.');
if ($disc && $disc['free_shipping']) $shipPrice = 0.0;

$params = [
    'mode' => 'payment',
    'success_url' => $base . '/order-complete/?session_id={CHECKOUT_SESSION_ID}',
    'cancel_url' => $base . '/cart/',
    'shipping_address_collection' => ['allowed_countries' => ['CA']],
    'phone_number_collection' => ['enabled' => 'true'],
    'billing_address_collection' => 'auto',
    'line_items' => [],
    'shipping_options' => [[
        'shipping_rate_data' => [
            'type' => 'fixed_amount',
            'fixed_amount' => ['amount' => (int)round($shipPrice * 100), 'currency' => 'cad'],
            'display_name' => ($shipPrice == 0.0 && $disc ? 'Free shipping' : 'Shipping within Canada') . ' (' . rtrim(rtrim(number_format($cart['kg'], 1), '0'), '.') . ' kg)',
            'tax_behavior' => 'exclusive',
        ],
    ]],
];
if ($autoTax) $params['automatic_tax'] = ['enabled' => 'true'];
foreach ($cart['lines'] as $l) {
    $params['line_items'][] = ['quantity' => $l['qty'], 'price_data' => [
        'currency' => 'cad', 'unit_amount' => $l['unit_cents'], 'tax_behavior' => 'exclusive', 'product_data' => ['name' => $l['name']]]];
}
if ($disc) {
    $params['metadata'] = ['discount_code' => $disc['code']];
    if ($disc['amount_cents'] > 0) {
        $coupon = ['duration' => 'once', 'name' => $disc['code'], 'max_redemptions' => 1];
        if (($disc['d']['type'] ?? '') === 'percent') $coupon['percent_off'] = (float)min((float)$disc['d']['value'], 100);
        else { $coupon['amount_off'] = $disc['amount_cents']; $coupon['currency'] = 'cad'; }
        $c = stripe_call('POST', '/v1/coupons', $coupon);
        if (empty($c['id'])) fail(502, 'Could not apply the discount. Please try again.');
        $params['discounts'] = [['coupon' => $c['id']]];
    }
}
$s = stripe_call('POST', '/v1/checkout/sessions', $params);
if (empty($s['url'])) fail(502, 'Could not start checkout. Please try again, or contact us to order.');
out_json(['url' => $s['url']]);
