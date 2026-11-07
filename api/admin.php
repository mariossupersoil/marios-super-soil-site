<?php
// Owner admin API: edit prices, availability, shipping tiers and discount codes. Password from config.php ('admin_password').
declare(strict_types=1);
require __DIR__ . '/lib.php';

$cfg = cfg();
$pw = (string)($cfg['admin_password'] ?? '');
if (strlen($pw) < 10 || str_contains($pw, 'PASTE')) fail(503, 'Admin is not set up. Add a password of at least 10 characters to config.php.');

session_name('mss_admin');
session_set_cookie_params(['lifetime' => 0, 'path' => '/', 'secure' => (($_SERVER['HTTPS'] ?? '') !== '' && $_SERVER['HTTPS'] !== 'off') || (($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https'), 'httponly' => true, 'samesite' => 'Strict']);
session_start();

$action = (string)($_GET['action'] ?? '');
$in = [];
if (($_SERVER['REQUEST_METHOD'] ?? '') === 'POST') $in = json_decode((string)file_get_contents('php://input', false, null, 0, 1048576), true) ?: [];

if ($action === 'login') {
    $dir = __DIR__ . '/.rl'; if (!is_dir($dir)) @mkdir($dir, 0700, true);
    $f = $dir . '/adm-' . substr(hash('sha256', $_SERVER['REMOTE_ADDR'] ?? 'x'), 0, 16);
    $rec = is_file($f) ? (json_decode((string)file_get_contents($f), true) ?: []) : [];
    $rec = array_values(array_filter($rec, fn($t) => $t > time() - 900));
    if (count($rec) >= 8) fail(429, 'Too many attempts. Try again in 15 minutes.');
    if (!hash_equals($pw, (string)($in['password'] ?? ''))) {
        $rec[] = time(); file_put_contents($f, json_encode($rec)); usleep(400000);
        fail(401, 'Wrong password.');
    }
    session_regenerate_id(true);
    $_SESSION['ok'] = true; $_SESSION['csrf'] = bin2hex(random_bytes(16)); $_SESSION['t'] = time();
    out_json(['ok' => true]);
}
if (empty($_SESSION['ok']) || (time() - ($_SESSION['t'] ?? 0)) > 43200) out_json(['auth' => false], 401);
if ($action === 'logout') { session_destroy(); out_json(['ok' => true]); }

if ($action === 'state') {
    $st = store();
    out_json(['auth' => true, 'csrf' => $_SESSION['csrf'], 'catalog' => catalog(true), 'tiers' => tiers(), 'discounts' => $st['discounts'] ?? [], 'sales' => $st['sales'] ?? []]);
}

// everything below changes data: POST + CSRF token
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST' || !hash_equals($_SESSION['csrf'], (string)($_SERVER['HTTP_X_CSRF'] ?? ''))) fail(403, 'Session expired. Reload the page.');

if ($action === 'save_products') {
    $base = jread(__DIR__ . '/prices.json')['products'] ?? [];
    $prices = []; $unavail = []; $disabled = []; $stockSet = [];
    foreach ($base as $slug => $p) {
        $row = $in['products'][$slug] ?? null; if (!is_array($row)) continue;
        if (empty($row['enabled'])) $disabled[] = $slug;
        foreach ($p['sizes'] as $k => $_) {
            $s = $row['sizes'][$k] ?? null; if (!is_array($s)) continue;
            $v = $s['price'] ?? null;
            if ($v === '' || $v === null) $v = null;
            elseif (!is_numeric($v) || $v < 0 || $v > 100000) fail(400, "Price for {$p['name']} {$k} is not a valid number.");
            else $v = round((float)$v, 2) ?: null;
            $prices[$slug][$k] = $v;
            if (empty($s['available'])) $unavail[$slug][] = $k;
            if (!empty($s['stock_changed'])) {
                $sv = $s['stock'] ?? '';
                if ($sv === '' || $sv === null) $stockSet[$slug][$k] = null;
                elseif (!is_numeric($sv) || $sv < 0 || $sv > 1000000 || (int)$sv != $sv) fail(400, "Stock for {$p['name']} {$k} must be a whole number.");
                else $stockSet[$slug][$k] = (int)$sv;
            }
        }
    }
    $ok = store_update(function ($st) use ($prices, $unavail, $disabled, $stockSet) {
        $st['prices'] = $prices; $st['unavailable_sizes'] = $unavail; $st['disabled_products'] = $disabled;
        foreach ($stockSet as $slug => $row) foreach ($row as $k => $v) { if ($v === null) unset($st['stock'][$slug][$k]); else $st['stock'][$slug][$k] = $v; }
        return $st; });
    $ok ? out_json(['ok' => true]) : fail(500, 'Could not save. Check folder permissions.');
}
if ($action === 'save_shipping') {
    $t = [];
    foreach (is_array($in['tiers'] ?? null) ? $in['tiers'] : [] as $r) {
        if (!is_numeric($r['max_kg'] ?? null) || !is_numeric($r['price'] ?? null) || $r['max_kg'] <= 0 || $r['price'] < 0) fail(400, 'Each shipping row needs a weight and a price.');
        $t[] = ['max_kg' => round((float)$r['max_kg'], 2), 'price' => round((float)$r['price'], 2)];
    }
    if (!$t) fail(400, 'Add at least one shipping row.');
    usort($t, fn($a, $b) => $a['max_kg'] <=> $b['max_kg']);
    store_update(function ($st) use ($t) { $st['shipping_tiers'] = $t; return $st; }) ? out_json(['ok' => true]) : fail(500, 'Could not save.');
}
if ($action === 'save_discounts') {
    $old = []; foreach (store()['discounts'] ?? [] as $d) $old[norm_code((string)$d['code'])] = $d;
    $new = []; $seen = [];
    foreach (is_array($in['discounts'] ?? null) ? $in['discounts'] : [] as $r) {
        $code = norm_code((string)($r['code'] ?? '')); if ($code === '') continue;
        if (isset($seen[$code])) fail(400, "Code $code is listed twice.");
        $seen[$code] = 1;
        $type = ($r['type'] ?? '') === 'fixed' ? 'fixed' : 'percent';
        $val = (float)($r['value'] ?? 0); $free = !empty($r['free_shipping']);
        if ($val < 0 || ($type === 'percent' && $val > 100)) fail(400, "Code $code has an invalid amount.");
        if ($val == 0 && !$free) fail(400, "Code $code needs an amount or free shipping.");
        $exp = (string)($r['expires'] ?? ''); if ($exp !== '' && !preg_match('/^\d{4}-\d{2}-\d{2}$/', $exp)) fail(400, "Code $code has a bad expiry date.");
        $new[] = ['code' => $code, 'type' => $type, 'value' => $val, 'free_shipping' => $free,
            'min_subtotal' => max(0, (float)($r['min_subtotal'] ?? 0)), 'expires' => $exp,
            'max_uses' => ((int)($r['max_uses'] ?? 0)) > 0 ? (int)$r['max_uses'] : null,
            'uses' => (int)($old[$code]['uses'] ?? 0), 'active' => !empty($r['active']), 'note' => mb_substr((string)($r['note'] ?? ''), 0, 120)];
    }
    store_update(function ($st) use ($new) { $st['discounts'] = $new; return $st; }) ? out_json(['ok' => true, 'discounts' => $new]) : fail(500, 'Could not save.');
}
if ($action === 'save_sales') {
    $base = jread(__DIR__ . '/prices.json')['products'] ?? [];
    $out = [];
    foreach (is_array($in['sales'] ?? null) ? $in['sales'] : [] as $r) {
        $prod = (string)($r['product'] ?? 'all'); if ($prod !== 'all' && !isset($base[$prod])) fail(400, 'Unknown product in a sale.');
        $size = (string)($r['size'] ?? 'all');
        if ($size !== 'all') { $ok = false; foreach ($base as $b) { if (isset($b['sizes'][$size])) $ok = true; } if (!$ok) fail(400, 'Unknown size in a sale.'); }
        $type = ($r['type'] ?? '') === 'fixed' ? 'fixed' : 'percent';
        $val = (float)($r['value'] ?? 0);
        if ($val <= 0 || ($type === 'percent' && $val > 90)) fail(400, 'Each sale needs an amount above 0 (percent sales: up to 90).');
        foreach (['starts', 'ends'] as $dk) { $dv = (string)($r[$dk] ?? ''); if ($dv !== '' && !preg_match('/^\d{4}-\d{2}-\d{2}$/', $dv)) fail(400, 'A sale has a bad date.'); }
        if (!empty($r['starts']) && !empty($r['ends']) && $r['ends'] < $r['starts']) fail(400, 'A sale ends before it starts.');
        $out[] = ['label' => mb_substr(trim((string)($r['label'] ?? '')), 0, 40), 'product' => $prod, 'size' => $size, 'type' => $type, 'value' => $val,
            'starts' => (string)($r['starts'] ?? ''), 'ends' => (string)($r['ends'] ?? ''), 'active' => !empty($r['active'])];
    }
    store_update(function ($st) use ($out) { $st['sales'] = $out; return $st; }) ? out_json(['ok' => true]) : fail(500, 'Could not save.');
}
fail(404, 'Unknown action.');
