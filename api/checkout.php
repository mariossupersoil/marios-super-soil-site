<?php
// Cart -> Stripe Checkout. Receives [{slug,size,qty}], prices everything from api/prices.json on the
// server (the browser is never trusted for prices), creates a Stripe Checkout Session, returns its URL.
declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

function fail(int $code, string $msg): void { http_response_code($code); echo json_encode(['error' => $msg]); exit; }

if ($_SERVER['REQUEST_METHOD'] !== 'POST') fail(405, 'Use POST.');
$cfgFile = __DIR__ . '/config.php';
$cfg = is_file($cfgFile) ? (require $cfgFile) : [];
$sk = $cfg['stripe_secret_key'] ?? '';
if ($sk === '' || str_contains($sk, 'PASTE')) fail(503, 'Checkout is not set up yet. Please contact us to order.');
$ship = json_decode((string)file_get_contents(__DIR__ . '/shipping.json'), true);
$tiers = $ship['tiers'] ?? [];
if (!$tiers) fail(503, 'Checkout is not set up yet. Please contact us to order.');
$autoTax = (bool)($cfg['automatic_tax'] ?? true);
$stripeUrl = $cfg['stripe_url'] ?? 'https://api.stripe.com/v1/checkout/sessions';
$allowedHosts = $cfg['allowed_hosts'] ?? ['mariossupersoil.ca', 'www.mariossupersoil.ca'];

$host = strtolower(preg_replace('/:\d+$/', '', $_SERVER['HTTP_HOST'] ?? ''));
$hostOk = in_array($host, $allowedHosts, true) || str_ends_with($host, '.hostingersite.com') || $host === 'localhost';
if (!$hostOk) fail(403, 'Not allowed.');
$origin = $_SERVER['HTTP_ORIGIN'] ?? ($_SERVER['HTTP_REFERER'] ?? '');
if ($origin !== '' && (parse_url($origin, PHP_URL_HOST) ?: '') !== $host) fail(403, 'Not allowed.');
$scheme = ($host === 'localhost') ? 'http' : 'https';
$base = $scheme . '://' . ($_SERVER['HTTP_HOST'] ?? $host);

$prices = json_decode((string)file_get_contents(__DIR__ . '/prices.json'), true);
$catalog = $prices['products'] ?? [];
$in = json_decode((string)file_get_contents('php://input', false, null, 0, 65536), true);
$items = is_array($in['items'] ?? null) ? array_slice($in['items'], 0, 30) : [];
if (!$items) fail(400, 'Your cart is empty.');

$params = [
    'mode' => 'payment',
    'success_url' => $base . '/order-complete/?session_id={CHECKOUT_SESSION_ID}',
    'cancel_url' => $base . '/cart/',
    'shipping_address_collection' => ['allowed_countries' => ['CA']],
    'phone_number_collection' => ['enabled' => 'true'],
    'billing_address_collection' => 'auto',
    'line_items' => [],
];
if ($autoTax) $params['automatic_tax'] = ['enabled' => 'true'];

$totalKg = 0.0;
foreach ($items as $it) {
    $slug = (string)($it['slug'] ?? ''); $key = (string)($it['size'] ?? ''); $qty = (int)($it['qty'] ?? 0);
    $prod = $catalog[$slug] ?? null; $size = $prod['sizes'][$key] ?? null;
    if (!$prod || !$size) fail(400, 'An item in your cart is no longer available. Please refresh the page.');
    if (!is_numeric($size['price'] ?? null) || $size['price'] <= 0) fail(400, $prod['name'] . ' (' . $size['label'] . ') does not have a price yet.');
    if ($qty < 1 || $qty > 20) fail(400, 'Quantity must be between 1 and 20.');
    $totalKg += ((float)($size['weight_kg'] ?? 0)) * $qty;
    $params['line_items'][] = [
        'quantity' => $qty,
        'price_data' => [
            'currency' => 'cad',
            'unit_amount' => (int)round($size['price'] * 100),
            'tax_behavior' => 'exclusive',
            'product_data' => ['name' => $prod['name'] . ' - ' . $size['label']],
        ],
    ];
}

$totalKg = round($totalKg, 2);
$shipPrice = null;
usort($tiers, fn($a, $b) => $a['max_kg'] <=> $b['max_kg']);
foreach ($tiers as $tr) { if ($totalKg <= $tr['max_kg']) { $shipPrice = $tr['price']; break; } }
if ($shipPrice === null) fail(400, 'This order is too heavy for online checkout. Please email us to arrange shipping.');
$params['shipping_options'] = [[
    'shipping_rate_data' => [
        'type' => 'fixed_amount',
        'fixed_amount' => ['amount' => (int)round($shipPrice * 100), 'currency' => 'cad'],
        'display_name' => 'Shipping within Canada (' . rtrim(rtrim(number_format($totalKg, 1), '0'), '.') . ' kg)',
        'tax_behavior' => 'exclusive',
    ],
]];

$ch = curl_init($stripeUrl);
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => http_build_query($params),
    CURLOPT_USERPWD => $sk . ':',
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 30,
]);
$resp = curl_exec($ch);
$code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);
$data = is_string($resp) ? json_decode($resp, true) : null;
if ($code !== 200 || !is_array($data) || empty($data['url'])) {
    error_log('checkout stripe ' . $code . ': ' . substr((string)$resp, 0, 400));
    fail(502, 'Could not start checkout. Please try again, or contact us to order.');
}
echo json_encode(['url' => $data['url']]);
