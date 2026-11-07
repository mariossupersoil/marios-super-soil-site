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
            $pack = (int)($s['pack_of'] ?? 0); $from = (string)($s['pack_from'] ?? '');
            $price = $s['price'] ?? null;
            if (isset($st['prices'][$slug]) && array_key_exists($k, $st['prices'][$slug])) $price = $st['prices'][$slug][$k];
            if ($pack > 1 && $from !== '') {   // packed as several smaller bags: derived from the base size
                $bp = $p['sizes'][$from]['price'] ?? null;
                if (isset($st['prices'][$slug]) && array_key_exists($from, $st['prices'][$slug])) $bp = $st['prices'][$slug][$from];
                $price = (is_numeric($bp) && $bp > 0) ? round((float)$bp * $pack, 2) : null;
            }
            $price = (is_numeric($price) && $price > 0) ? round((float)$price, 2) : null;
            $avail = !in_array($k, $st['unavailable_sizes'][$slug] ?? [], true);
            if (!$admin && !$avail) continue;
            $sale = $price !== null ? best_sale($sales, $slug, $k, $price) : null;
            $sizes[$k] = ['label' => $s['label'], 'price' => $price, 'sale_price' => $sale['price'] ?? null, 'sale_label' => $sale['label'] ?? '', 'sale_ends' => $sale['ends'] ?? '', 'weight_kg' => (float)($s['weight_kg'] ?? 0), 'available' => $avail, 'derived' => $pack > 1, 'stock' => ($pack > 1 && $from !== '') ? ((isset($st['stock'][$slug][$from]) && is_int($st['stock'][$slug][$from])) ? intdiv($st['stock'][$slug][$from], $pack) : null) : ((isset($st['stock'][$slug][$k]) && is_int($st['stock'][$slug][$k])) ? $st['stock'][$slug][$k] : null)];
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
function price_cart(array $items, array $cat, string $giftChoice = ''): array {
    $items = array_slice($items, 0, 30); if (!$items) fail(400, 'Your cart is empty.');
    $lines = []; $sub = 0; $kg = 0.0;
    foreach ($items as $it) {
        $slug = (string)($it['slug'] ?? ''); $key = (string)($it['size'] ?? ''); $qty = (int)($it['qty'] ?? 0);
        $p = $cat[$slug] ?? null; $s = $p['sizes'][$key] ?? null;
        if (!$p || !$s || !$p['enabled']) fail(400, 'An item in your cart is no longer available. Please refresh the page.');
        if ($s['price'] === null) fail(400, $p['name'] . ' (' . $s['label'] . ') does not have a price yet.');
        if ($qty < 1 || $qty > 20) fail(400, 'Quantity must be between 1 and 20.');
        if ($s['stock'] !== null && $s['stock'] <= 0) fail(400, $p['name'] . ' (' . $s['label'] . ') is out of stock.');
        if ($s['stock'] !== null && $qty > $s['stock']) fail(400, 'Only ' . $s['stock'] . ' of ' . $p['name'] . ' (' . $s['label'] . ') left. Please lower the quantity.');
        $cents = (int)round(($s['sale_price'] ?? $s['price']) * 100);
        $lines[] = ['name' => $p['name'] . ' - ' . $s['label'], 'unit_cents' => $cents, 'qty' => $qty, 'slug' => $slug, 'key' => $key];
        $sub += $cents * $qty; $kg += $s['weight_kg'] * $qty;
    }
    $gift = settings()['gift']; $giftOn = false;
    if (!empty($gift['enabled']) && $sub >= (int)round($gift['threshold'] * 100) && ($gift['stock'] === null || $gift['stock'] > 0)) {
        $giftOn = true; $kg += (float)$gift['weight_kg'];
    }
    $gid = null; $gname = null;
    if ($giftOn) {
        $chs = $gift['choices'];
        $pick = $chs[0];
        foreach ($chs as $ch) { if (($ch['id'] ?? '') === $giftChoice) { $pick = $ch; break; } }
        $gid = $pick['id']; $gname = $pick['name'];
    }
    return ['lines' => $lines, 'subtotal_cents' => $sub, 'kg' => round($kg, 2), 'gift' => $gname, 'gift_id' => $gid];
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

/** A paid Stripe session: count the discount code use and take the items off stock, once per session. */
function record_paid_session(array $s): void {
    if (($s['payment_status'] ?? '') !== 'paid' || empty($s['id'])) return;
    $sid = (string)$s['id']; $md = is_array($s['metadata'] ?? null) ? $s['metadata'] : [];
    $code = norm_code((string)($md['discount_code'] ?? ''));
    $items = [];
    foreach ($md as $k => $v) {
        if (!preg_match('/^items_\d+$/', (string)$k)) continue;
        foreach (explode(';', (string)$v) as $e) { $q = explode(':', $e); if (count($q) === 3) $items[] = [$q[0], $q[1], (int)$q[2]]; }
    }
    $cd = is_array($s['customer_details'] ?? null) ? $s['customer_details'] : [];
    $gift = !empty($md['gift']); $giftId = preg_replace('/[^a-z-]/', '', (string)($md['gift'] ?? ''));
    $new = false; $summary = [];
    store_update(function (array $st) use ($sid, $code, $items, $cd, $gift, $giftId, &$new) {
        $done = $st['processed_sessions'] ?? [];
        if (in_array($sid, $done, true)) return $st;
        $new = true; $done[] = $sid; $st['processed_sessions'] = array_slice($done, -500);
        if ($code !== '' && !empty($st['discounts'])) {
            foreach ($st['discounts'] as &$d) { if (norm_code((string)($d['code'] ?? '')) === $code) $d['uses'] = (int)($d['uses'] ?? 0) + 1; }
            unset($d);
        }
        $baseP = jread(__DIR__ . '/prices.json')['products'] ?? [];
        foreach ($items as [$slug, $key, $qty]) {
            $pk = $baseP[$slug]['sizes'][$key] ?? [];
            if ((int)($pk['pack_of'] ?? 0) > 1 && !empty($pk['pack_from'])) { $key = (string)$pk['pack_from']; $qty *= (int)$pk['pack_of']; }
            if (isset($st['stock'][$slug][$key]) && is_int($st['stock'][$slug][$key])) $st['stock'][$slug][$key] = max(0, $st['stock'][$slug][$key] - $qty);
        }
        if ($gift && isset($st['settings']['gift']['stock']) && is_int($st['settings']['gift']['stock'])) $st['settings']['gift']['stock'] = max(0, $st['settings']['gift']['stock'] - 1);
        $email = strtolower(trim((string)($cd['email'] ?? '')));
        if ($email !== '' && valid_email($email) && $items) {
            $days = (int)(($st['settings']['reminders']['days'] ?? 60));
            $st['customers'][] = ['email' => $email, 'name' => clean_line((string)($cd['name'] ?? ''), 60), 'date' => today_toronto(),
                'remind_on' => (new DateTime('now', new DateTimeZone('America/Toronto')))->modify('+' . max(7, $days) . ' days')->format('Y-m-d'),
                'gift' => $gift ? $giftId : '', 'items' => array_map(fn($i) => ['slug' => $i[0], 'size' => $i[1], 'qty' => $i[2]], $items), 'reminded' => false, 'unsub' => false, 'token' => bin2hex(random_bytes(12))];
            $st['customers'] = array_slice($st['customers'], -5000);
        }
        return $st;
    });
    if ($new) {   // tell the owner about the order, including which free gift was picked
        $cat = catalog(true); $lines = [];
        foreach ($items as [$slug, $key, $qty]) $lines[] = $qty . ' x ' . ($cat[$slug]['name'] ?? $slug) . ' - ' . ($cat[$slug]['sizes'][$key]['label'] ?? $key);
        $gname = '';
        if ($gift) { foreach (settings()['gift']['choices'] as $ch) { if ($ch['id'] === $giftId) $gname = $ch['name']; } if ($gname === '') $gname = $giftId ?: 'free gift'; }
        $body = "New paid order" . ($cd['name'] ?? '' ? ' from ' . clean_line((string)$cd['name'], 60) : '') . ".\n\n" . implode("\n", $lines) . "\n"
            . ($gift ? "\nFREE GIFT TO PACK: " . $gname . "\n" : '') . "\nCustomer email: " . ($cd['email'] ?? '') . "\nStripe order: " . $sid . "\nFull details and shipping address are in your Stripe dashboard.\n";
        send_mail(owner_email(), ($gift ? 'New order (free gift: ' . $gname . ')' : 'New order'), $body);
    }
}


// ---------------------------------------------------------------- settings, mail, rate limits
function settings(): array {
    $d = [
        'gift' => ['enabled' => true, 'threshold' => 120.0, 'name' => 'Free 2 lb bag', 'weight_kg' => 0.91, 'stock' => null,
            'choices' => [['id' => 'level-up', 'name' => 'Level Up 3-3-3 (2 lb)'], ['id' => 'flower-power', 'name' => 'Flower Power 2-6-4 (2 lb)']]],
        'reminders' => ['enabled' => true, 'days' => 60],
    ];
    $s = store()['settings'] ?? [];
    foreach ($d as $k => $v) $d[$k] = array_merge($v, is_array($s[$k] ?? null) ? $s[$k] : []);
    return $d;
}
function site_url(): string { return rtrim((string)(cfg()['site_url'] ?? 'https://mariossupersoil.ca'), '/'); }
function owner_email(): string { return (string)(cfg()['owner_email'] ?? 'mariossupersoil@mariossupersoil.com'); }

/** Allow at most $max hits per $window seconds for this key (per visitor). Returns false when over the limit. */
function rate_ok(string $name, int $max, int $window = 3600): bool {
    $dir = __DIR__ . '/.rl'; if (!is_dir($dir)) @mkdir($dir, 0700, true);
    $f = $dir . '/' . $name . '-' . substr(hash('sha256', $_SERVER['REMOTE_ADDR'] ?? 'x'), 0, 16);
    $fp = @fopen($f, 'c+'); if (!$fp) return true;
    flock($fp, LOCK_EX);
    $rec = json_decode((string)stream_get_contents($fp), true) ?: [];
    $rec = array_values(array_filter($rec, fn($t) => $t > time() - $window));
    $ok = count($rec) < $max;
    if ($ok) $rec[] = time();
    ftruncate($fp, 0); rewind($fp); fwrite($fp, json_encode($rec));
    flock($fp, LOCK_UN); fclose($fp);
    return $ok;
}

function valid_email(string $e): bool { return strlen($e) <= 120 && filter_var($e, FILTER_VALIDATE_EMAIL) !== false && !preg_match('/[\r\n]/', $e); }
function clean_line(string $s, int $max): string { return mb_substr(trim(preg_replace('/[\r\n\t]+/', ' ', $s)), 0, $max); }

/** Plain-text email (optionally with one attachment). Uses PHP mail(): fine on Hostinger; set mail_from in config.php. */
function send_mail(string $to, string $subject, string $body, ?array $attach = null, ?string $replyTo = null): bool {
    if (!valid_email($to)) return false;
    $host = parse_url(site_url(), PHP_URL_HOST) ?: 'localhost';
    $from = (string)(cfg()['mail_from'] ?? ('noreply@' . preg_replace('/^www\./', '', $host)));
    $h = ['From: ' . "Mario's Super Soil <$from>", 'MIME-Version: 1.0'];
    if ($replyTo && valid_email($replyTo)) $h[] = 'Reply-To: ' . $replyTo;
    $subj = '=?UTF-8?B?' . base64_encode($subject) . '?=';
    if ($attach) {
        $b = bin2hex(random_bytes(8));
        $h[] = "Content-Type: multipart/mixed; boundary=\"$b\"";
        $msg = "--$b\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" . chunk_split(base64_encode($body))
             . "--$b\r\nContent-Type: application/json; name=\"{$attach['name']}\"\r\nContent-Transfer-Encoding: base64\r\nContent-Disposition: attachment; filename=\"{$attach['name']}\"\r\n\r\n" . chunk_split(base64_encode($attach['data'])) . "--$b--";
    } else {
        $h[] = 'Content-Type: text/plain; charset=UTF-8'; $h[] = 'Content-Transfer-Encoding: base64';
        $msg = chunk_split(base64_encode($body));
    }
    $log = cfg()['mail_log'] ?? null;
    if ($log) { @file_put_contents($log, "TO:$to\nSUBJ:$subject\n$body\n---\n", FILE_APPEND); return true; }
    $c = cfg();
    if (!empty($c['smtp_host']) && !empty($c['smtp_user']) && !empty($c['smtp_pass'])) {
        $fa = !empty($c['smtp_from']) ? $c['smtp_from'] : $c['smtp_user']; $h[0] = 'From: ' . "Mario's Super Soil <$fa>";
        return smtp_deliver($c, $from, $to, "To: $to\r\nSubject: $subj\r\nDate: " . date('r') . "\r\n" . implode("\r\n", $h) . "\r\n\r\n" . $msg);
    }
    return @mail($to, $subj, $msg, implode("\r\n", $h), '-f' . $from);
}

/** Send one message through an authenticated SMTP mailbox (config: smtp_host, smtp_user, smtp_pass, smtp_port). */
function smtp_deliver(array $c, string $from, string $to, string $raw): bool {
    $port = (int)($c['smtp_port'] ?? 465);
    $fp = @stream_socket_client(($port === 465 ? 'ssl://' : 'tcp://') . $c['smtp_host'] . ':' . $port, $en, $es, 15);
    if (!$fp) { $GLOBALS['mail_err'] = "connect: $es"; return false; }
    stream_set_timeout($fp, 15);
    $rd = function() use ($fp) { $o = ''; while (($l = fgets($fp, 1024)) !== false) { $o .= $l; if (strlen($l) < 4 || $l[3] === ' ') break; } return $o; };
    $cmd = function(string $x, string $ok) use ($fp, $rd) { fwrite($fp, $x . "\r\n"); $r = $rd(); if (strpos($r, $ok) !== 0) { $GLOBALS['mail_err'] = trim($r); return false; } return true; };
    $r = $rd(); if (strpos($r, '220') !== 0) { $GLOBALS['mail_err'] = trim($r); return false; }
    $host = parse_url(site_url(), PHP_URL_HOST) ?: 'localhost';
    if (!$cmd("EHLO $host", '250')) return false;
    if ($port !== 465 && $port !== 25) { if (!$cmd('STARTTLS', '220')) return false; stream_socket_enable_crypto($fp, true, STREAM_CRYPTO_METHOD_TLS_CLIENT); if (!$cmd("EHLO $host", '250')) return false; }
    $ok = $cmd('AUTH LOGIN', '334') && $cmd(base64_encode($c['smtp_user']), '334') && $cmd(base64_encode($c['smtp_pass']), '235')
       && $cmd("MAIL FROM:<" . (!empty($c['smtp_from']) ? $c['smtp_from'] : $c['smtp_user']) . ">", '250') && $cmd("RCPT TO:<$to>", '250') && $cmd('DATA', '354');
    if (!$ok) { fclose($fp); return false; }
    fwrite($fp, preg_replace('/^\./m', '..', str_replace("\n", "\r\n", str_replace("\r\n", "\n", $raw))) . "\r\n.\r\n");
    $r = $rd(); $good = strpos($r, '250') === 0; if (!$good) $GLOBALS['mail_err'] = trim($r);
    @fwrite($fp, "QUIT\r\n"); fclose($fp);
    return $good;
}

/** Copy store.json into api/backups/ (keep the newest 12) and optionally email it to the owner. */
function do_backup(bool $email): string {
    $dir = __DIR__ . '/backups'; if (!is_dir($dir)) @mkdir($dir, 0700, true);
    if (!is_file(STORE_FILE)) return 'nothing to back up yet';
    $name = 'store-' . today_toronto() . '.json'; $data = (string)file_get_contents(STORE_FILE);
    file_put_contents($dir . '/' . $name, $data);
    $all = glob($dir . '/store-*.json') ?: []; sort($all);
    foreach (array_slice($all, 0, max(0, count($all) - 12)) as $old) @unlink($old);
    if ($email) {
        $ok = send_mail(owner_email(), "Weekly backup of your shop data ($name)", "Attached is this week's backup of your shop data (prices, stock, sales, discount codes, subscribers, reviews, wholesale leads, customers). Keep it somewhere safe; it contains customer email addresses.\n", ['name' => $name, 'data' => $data]);
        return $ok ? "saved $name and emailed it" : "saved $name (email failed)";
    }
    return "saved $name";
}
