<?php
// Shared shop code: catalog (base prices.json + admin overrides in store.json), shipping tiers, discount codes.
declare(strict_types=1);
const STORE_FILE = __DIR__ . '/store.json';

function cfg(): array {
    static $c = null;
    if ($c === null) { $f = __DIR__ . '/config.php'; $c = is_file($f) ? (require $f) : []; }
    return $c;
}
function jread(string $f): array { $d = json_decode((string)@file_get_contents($f), true); return is_array($d) ? $d : []; }
function out_json(array $a, int $code = 200): void {
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8'); header('Cache-Control: no-store'); header('X-Content-Type-Options: nosniff');
    echo json_encode($a, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES); exit;
}
function fail(int $code, string $msg): void { out_json(['error' => $msg], $code); }
function store(): array { return jread(STORE_FILE); }

/** Read-modify-write under a lock. $fn receives the current store array and returns the new one. */
function store_update(callable $fn): bool {
    $fp = @fopen(STORE_FILE . '.lock', 'c'); if (!$fp) return false;
    flock($fp, LOCK_EX);
    $new = $fn(store());
    if (is_file(STORE_FILE)) @copy(STORE_FILE, STORE_FILE . '.bak');
    $json = json_encode($new, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    $tmp = STORE_FILE . '.tmp';
    $ok = file_put_contents($tmp, $json) !== false && rename($tmp, STORE_FILE);
    flock($fp, LOCK_UN); fclose($fp);
    return $ok;
}

function today_toronto(): string { return (new DateTime('now', new DateTimeZone('America/Toronto')))->format('Y-m-d'); }

/** Sales running today that apply to this product+size. Returns the best (lowest resulting price) or null. */
function best_sale(array $sales, string $slug, string $key, float $price): ?array {
    $today = today_toronto(); $best = null;
    foreach ($sales as $s) {
        if (empty($s['active'])) continue;
        if (($s['product'] ?? 'all') !== 'all' && $s['product'] !== $slug) continue;
        if (($s['size'] ?? 'all') !== 'all' && $s['size'] !== $key) continue;
        if (!empty($s['starts']) && $today < $s['starts']) continue;
        if (!empty($s['ends']) && $today > $s['ends']) continue;
        $v = (float)($s['value'] ?? 0); if ($v <= 0) continue;
        $np = ($s['type'] ?? '') === 'fixed' ? $price - $v : $price * (1 - min($v, 99) / 100);
        $np = round(max(0.5, $np), 2);
        if ($np >= $price) continue;
        if ($best === null || $np < $best['price']) $best = ['price' => $np, 'label' => (string)($s['label'] ?? ''), 'ends' => (string)($s['ends'] ?? '')];
    }
    return $best;
}

function catalog(bool $admin = false): array {
    $base = jread(__DIR__ . '/prices.json')['products'] ?? [];
    $st = store(); $out = []; $sales = $st['sales'] ?? [];
    foreach ($base as $slug => $p) {
        $sizes = [];
        foreach ($p['sizes'] as $k => $s) {
            $price = $s['price'] ?? null;
            if (isset($st['prices'][$slug]) && array_key_exists($k, $st['prices'][$slug])) $price = $st['prices'][$slug][$k];
            $price = (is_numeric($price) && $price > 0) ? round((float)$price, 2) : null;
            $avail = !in_array($k, $st['unavailable_sizes'][$slug] ?? [], true);
            if (!$admin && !$avail) continue;
            $sale = $price !== null ? best_sale($sales, $slug, $k, $price) : null;
            $sizes[$k] = ['label' => $s['label'], 'price' => $price, 'sale_price' => $sale['price'] ?? null, 'sale_label' => $sale['label'] ?? '', 'sale_ends' => $sale['ends'] ?? '', 'weight_kg' => (float)($s['weight_kg'] ?? 0), 'available' => $avail];
        }
        $out[$slug] = ['name' => $p['name'], 'img' => $p['img'], 'enabled' => !in_array($slug, $st['disabled_products'] ?? [], true), 'sizes' => $sizes];
    }
    return $out;
}

function tiers(): array {
    $st = store();
    $t = $st['shipping_tiers'] ?? (jread(__DIR__ . '/shipping.json')['tiers'] ?? []);
    $t = array_values(array_filter($t, fn($x) => is_array($x) && isset($x['max_kg'], $x['price'])));
    usort($t, fn($a, $b) => $a['max_kg'] <=> $b['max_kg']);
    return $t;
}
function ship_price(float $kg, array $tiers): ?float {
    foreach ($tiers as $t) { if ($kg <= $t['max_kg']) return (float)$t['price']; }
    return null;
}

function norm_code(string $c): string { return strtoupper(preg_replace('/[^A-Za-z0-9_-]/', '', trim($c))); }

/** Validate cart items against the catalog. Returns lines + totals, or fails with a message. */
function price_cart(array $items, array $cat): array {
    $items = array_slice($items, 0, 30); if (!$items) fail(400, 'Your cart is empty.');
    $lines = []; $sub = 0; $kg = 0.0;
    foreach ($items as $it) {
        $slug = (string)($it['slug'] ?? ''); $key = (string)($it['size'] ?? ''); $qty = (int)($it['qty'] ?? 0);
        $p = $cat[$slug] ?? null; $s = $p['sizes'][$key] ?? null;
        if (!$p || !$s || !$p['enabled']) fail(400, 'An item in your cart is no longer available. Please refresh the page.');
        if ($s['price'] === null) fail(400, $p['name'] . ' (' . $s['label'] . ') does not have a price yet.');
        if ($qty < 1 || $qty > 20) fail(400, 'Quantity must be between 1 and 20.');
        $cents = (int)round(($s['sale_price'] ?? $s['price']) * 100);
        $lines[] = ['name' => $p['name'] . ' - ' . $s['label'], 'unit_cents' => $cents, 'qty' => $qty];
        $sub += $cents * $qty; $kg += $s['weight_kg'] * $qty;
    }
    return ['lines' => $lines, 'subtotal_cents' => $sub, 'kg' => round($kg, 2)];
}

/** Check a discount code against the store. Returns ['d'=>discount row,'amount_cents'=>int,'free_shipping'=>bool] or fails. */
function apply_code(string $raw, int $subtotalCents): array {
    $code = norm_code($raw);
    $d = null;
    foreach (store()['discounts'] ?? [] as $x) { if (norm_code((string)($x['code'] ?? '')) === $code && $code !== '') { $d = $x; break; } }
    if (!$d || empty($d['active'])) fail(400, 'That discount code is not valid.');
    $today = (new DateTime('now', new DateTimeZone('America/Toronto')))->format('Y-m-d');
    if (!empty($d['expires']) && $today > $d['expires']) fail(400, 'That discount code has expired.');
    if (!empty($d['max_uses']) && (int)($d['uses'] ?? 0) >= (int)$d['max_uses']) fail(400, 'That discount code has been fully used.');
    $min = (float)($d['min_subtotal'] ?? 0);
    if ($min > 0 && $subtotalCents < $min * 100) fail(400, 'That code needs an order of at least $' . number_format($min, 2) . ' before shipping and tax.');
    $val = (float)($d['value'] ?? 0);
    $amount = ($d['type'] ?? '') === 'percent' ? (int)round($subtotalCents * min($val, 100) / 100) : (int)round($val * 100);
    $amount = max(0, min($amount, $subtotalCents));
    return ['d' => $d, 'code' => $code, 'amount_cents' => $amount, 'free_shipping' => !empty($d['free_shipping'])];
}

function stripe_call(string $method, string $path, array $params = []): array {
    $c = cfg(); $sk = $c['stripe_secret_key'] ?? '';
    $base = $c['stripe_base'] ?? 'https://api.stripe.com';
    $ch = curl_init($base . $path . ($method === 'GET' && $params ? '?' . http_build_query($params) : ''));
    $o = [CURLOPT_USERPWD => $sk . ':', CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 30];
    if ($method === 'POST') { $o[CURLOPT_POST] = true; $o[CURLOPT_POSTFIELDS] = http_build_query($params); }
    curl_setopt_array($ch, $o);
    $resp = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
    $data = is_string($resp) ? json_decode($resp, true) : null;
    if ($code < 200 || $code >= 300 || !is_array($data)) { error_log("stripe $method $path $code: " . substr((string)$resp, 0, 300)); return []; }
    return $data;
}
