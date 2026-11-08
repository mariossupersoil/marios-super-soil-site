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
    out_json(['auth' => true, 'csrf' => $_SESSION['csrf'], 'catalog' => catalog(true), 'tiers' => tiers(), 'discounts' => $st['discounts'] ?? [], 'sales' => $st['sales'] ?? [],
        'settings' => settings(), 'reviews' => array_reverse($st['reviews'] ?? []), 'leads' => array_reverse($st['wholesale_leads'] ?? []),
        'orders' => array_slice(array_reverse($st['orders'] ?? []), 0, 300), 'subscribers' => count($st['subscribers'] ?? []), 'customers' => count($st['customers'] ?? []), 'last_backup' => $st['last_backup_week'] ?? '']);
}

if ($action === 'export_subscribers') {
    $st = store(); $rows = []; 
    foreach ($st['subscribers'] ?? [] as $s) $rows[$s['email']] = [$s['email'], '', $s['date'], 'signup pop-up', !empty($s['unsub']) ? 'unsubscribed' : 'subscribed'];
    foreach ($st['customers'] ?? [] as $c) { if (!isset($rows[$c['email']])) $rows[$c['email']] = [$c['email'], $c['name'], $c['date'], 'customer', !empty($c['unsub']) ? 'unsubscribed' : 'subscribed']; elseif ($c['name'] !== '' && $rows[$c['email']][1] === '') $rows[$c['email']][1] = $c['name']; }
    header('Content-Type: text/csv; charset=utf-8'); header('Content-Disposition: attachment; filename="mario-email-list-' . today_toronto() . '.csv"');
    $o = fopen('php://output', 'w'); fputcsv($o, ['email', 'name', 'date', 'source', 'status']);
    foreach ($rows as $r) { $r[0] = preg_match('/^[=+\-@]/', $r[0]) ? "'" . $r[0] : $r[0]; fputcsv($o, $r); } exit;
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
if ($action === 'save_settings') {
    $g = $in['gift'] ?? []; $r = $in['reminders'] ?? [];
    $thr = (float)($g['threshold'] ?? 0); if ($thr < 1 || $thr > 100000) fail(400, 'The free gift order amount must be at least $1.');
    $chs = [];
    foreach (($g['choices'] ?? []) as $i => $ch) { $n = clean_line((string)($ch['name'] ?? ''), 80); if ($n === '') continue; $chs[] = ['id' => preg_replace('/[^a-z-]/', '', strtolower((string)($ch['id'] ?? ''))) ?: ('gift-' . ($i + 1)), 'name' => $n]; }
    if (!$chs) fail(400, 'Give the free gift at least one choice.');
    $name = 'Free 2 lb bag';
    $wt = (float)($g['weight_kg'] ?? 0); if ($wt < 0 || $wt > 50) fail(400, 'The gift weight looks wrong.');
    $stk = $g['stock'] ?? ''; $stk = ($stk === '' || $stk === null) ? null : ((is_numeric($stk) && $stk >= 0 && (int)$stk == $stk) ? (int)$stk : fail(400, 'Gift stock must be a whole number or blank.'));
    $days = (int)($r['days'] ?? 60); if ($days < 7 || $days > 365) fail(400, 'Reminder days must be between 7 and 365.');
    $set = ['gift' => ['enabled' => !empty($g['enabled']), 'threshold' => round($thr, 2), 'name' => $name, 'choices' => $chs, 'weight_kg' => round($wt, 2), 'stock' => $stk], 'reminders' => ['enabled' => !empty($r['enabled']), 'days' => $days]];
    store_update(function ($st) use ($set) { $st['settings'] = array_merge($st['settings'] ?? [], $set); return $st; }) ? out_json(['ok' => true]) : fail(500, 'Could not save.');
}
if ($action === 'save_tax') {
    $on = !empty($in['enabled']);
    store_update(function ($st) use ($on) { $st['settings'] = array_merge($st['settings'] ?? [], ['tax' => ['enabled' => $on]]); return $st; }) ? out_json(['ok' => true]) : fail(500, 'Could not save.');
}
if ($action === 'save_promo') {
    $title = clean_line((string)($in['title'] ?? ''), 40); $text = clean_line((string)($in['text'] ?? ''), 100);
    $code = preg_replace('/[^A-Za-z0-9_-]/', '', (string)($in['code'] ?? '')); $ends = trim((string)($in['ends'] ?? ''));
    $on = !empty($in['enabled']);
    if ($ends !== '' && !preg_match('/^\d{4}-\d{2}-\d{2}$/', $ends)) fail(400, 'The end date looks wrong.');
    if ($on) {
        if ($title === '' || $text === '') fail(400, 'Give the deal a title and a short line of text.');
        $found = false; foreach (store()['discounts'] ?? [] as $x) { if (norm_code((string)($x['code'] ?? '')) === norm_code($code) && $code !== '') { $found = true; break; } }
        if (!$found) fail(400, 'That code is not in your Discount codes list yet. Add it there first, then save this again.');
    }
    store_update(function ($st) use ($on, $title, $text, $code, $ends) { $st['settings']['promo'] = ['enabled' => $on, 'title' => $title, 'text' => $text, 'code' => $code, 'ends' => $ends]; return $st; }) ? out_json(['ok' => true]) : fail(500, 'Could not save.');
}
if ($action === 'order_ship' || $action === 'order_unship') {
    $id = (string)($in['id'] ?? ''); $found = null; $notify = !empty($in['notify']);
    $carrier = clean_line((string)($in['carrier'] ?? ''), 30); $tracking = preg_replace('/[^A-Za-z0-9 -]/', '', (string)($in['tracking'] ?? '')); $tracking = substr(trim($tracking), 0, 40);
    store_update(function ($st) use ($id, $action, $carrier, $tracking, &$found) {
        if (!isset($st['orders'])) $st['orders'] = []; foreach ($st['orders'] as &$o) { if (($o['id'] ?? '') !== $id) continue;
            if ($action === 'order_unship') { $o['status'] = 'new'; $o['shipped_at'] = ''; }
            else { $o['status'] = 'shipped'; $o['carrier'] = $carrier; $o['tracking'] = $tracking; if (empty($o['shipped_at'])) $o['shipped_at'] = date('c'); }
            $found = $o; break; }
        unset($o); return $st; });
    if (!$found) fail(404, 'Order not found.');
    $sent = null;
    if ($action === 'order_ship' && $notify) {
        if (!valid_email((string)$found['email'])) fail(400, 'Marked as shipped, but this order has no valid customer email, so nothing was sent.');
        $sent = send_shipped_email($found);
        if ($sent) store_update(function ($st) use ($id) { if (!isset($st['orders'])) $st['orders'] = []; foreach ($st['orders'] as &$o) { if (($o['id'] ?? '') === $id) { $o['notified'] = true; $o['notified_at'] = date('c'); } } unset($o); return $st; });
        else fail(500, 'Marked as shipped, but the email could not be sent.' . (!empty($GLOBALS['mail_err']) ? ' Reason: ' . $GLOBALS['mail_err'] : ''));
    }
    out_json(['ok' => true, 'emailed' => $sent === true]);
}
if ($action === 'review_action') {
    $id = (string)($in['id'] ?? ''); $op = (string)($in['op'] ?? '');
    if (!in_array($op, ['approve', 'reject', 'delete'], true)) fail(400, 'Bad action.');
    store_update(function ($st) use ($id, $op) {
        foreach ($st['reviews'] ?? [] as $i => $r) { if ($r['id'] !== $id) continue;
            if ($op === 'delete') unset($st['reviews'][$i]); else $st['reviews'][$i]['status'] = $op === 'approve' ? 'approved' : 'rejected'; }
        $st['reviews'] = array_values($st['reviews'] ?? []); return $st; });
    out_json(['ok' => true]);
}
if ($action === 'add_review') {
    $base = jread(__DIR__ . '/prices.json')['products'] ?? [];
    $slug = (string)($in['slug'] ?? ''); if (!isset($base[$slug])) fail(400, 'Choose a product.');
    $name = clean_line((string)($in['name'] ?? ''), 40); $rating = (int)($in['rating'] ?? 0); $text = trim((string)($in['text'] ?? ''));
    if ($name === '' || $rating < 1 || $rating > 5 || mb_strlen($text) < 10) fail(400, 'Enter a name, a rating from 1 to 5 and the review text.');
    $r = ['id' => bin2hex(random_bytes(5)), 'slug' => $slug, 'name' => $name, 'rating' => $rating, 'title' => clean_line((string)($in['title'] ?? ''), 80), 'text' => mb_substr($text, 0, 1000),
          'date' => preg_match('/^\d{4}-\d{2}-\d{2}$/', (string)($in['date'] ?? '')) ? $in['date'] : today_toronto(), 'status' => 'approved', 'source' => 'owner', 'contact' => ''];
    store_update(function ($st) use ($r) { $st['reviews'][] = $r; return $st; }) ? out_json(['ok' => true]) : fail(500, 'Could not save.');
}
if ($action === 'lead_action') {
    $id = (string)($in['id'] ?? ''); $op = (string)($in['op'] ?? '');
    if (!in_array($op, ['contacted', 'new', 'delete'], true)) fail(400, 'Bad action.');
    store_update(function ($st) use ($id, $op) {
        foreach ($st['wholesale_leads'] ?? [] as $i => $l) { if ($l['id'] !== $id) continue; if ($op === 'delete') unset($st['wholesale_leads'][$i]); else $st['wholesale_leads'][$i]['status'] = $op; }
        $st['wholesale_leads'] = array_values($st['wholesale_leads'] ?? []); return $st; });
    out_json(['ok' => true]);
}
if ($action === 'test_mail') {
    $ok = send_mail(owner_email(), 'Test email from your shop', "If you can read this, your shop can send email. Reminders, new review alerts, wholesale applications and weekly backups all use the same sending.\n");
    $ok ? out_json(['ok' => true, 'to' => owner_email()]) : fail(500, 'The server could not send email.' . (!empty($GLOBALS['mail_err']) ? ' Reason: ' . $GLOBALS['mail_err'] : ' (No SMTP mailbox is set up in config.php, so it used the server\'s basic mail, which is often blocked.)'));
}
if ($action === 'backup_now') { out_json(['ok' => true, 'result' => do_backup(true)]); }
fail(404, 'Unknown action.');
