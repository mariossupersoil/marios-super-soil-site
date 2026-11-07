<?php
// Daily job (set up in Hostinger hPanel > Advanced > Cron Jobs): restock reminders + weekly backup.
// URL form: https://yoursite/api/cron.php?key=YOUR_CRON_KEY   (cron_key is in config.php)
declare(strict_types=1);
require __DIR__ . '/lib.php';
$key = (string)(cfg()['cron_key'] ?? '');
if (strlen($key) < 12 || str_contains($key, 'PASTE') || !hash_equals($key, (string)($_GET['key'] ?? ''))) fail(403, 'Not allowed.');
$log = [];
$st = store(); $set = settings(); $today = today_toronto();

// ---- restock reminders
if (!empty($set['reminders']['enabled'])) {
    $site = json_decode((string)@file_get_contents(__DIR__ . '/../data/site.json'), true) ?: [];
    $a = $site['address'] ?? []; $addr = trim(($a['street'] ?? '') . ', ' . ($a['city'] ?? '') . ' ' . ($a['region'] ?? '') . ', Canada', ' ,');
    $cat = catalog(); $due = []; $unsub = [];
    foreach (($st['customers'] ?? []) as $c) if (!empty($c['unsub'])) $unsub[$c['email']] = 1;
    foreach (($st['subscribers'] ?? []) as $c) if (!empty($c['unsub'])) $unsub[$c['email']] = 1;
    foreach (($st['customers'] ?? []) as $c) {
        if (!empty($c['reminded']) || isset($unsub[$c['email']]) || $c['remind_on'] > $today) continue;
        $due[$c['email']][] = $c;
    }
    $sent = 0; $emails = [];
    foreach ($due as $email => $orders) {
        if ($sent >= 60) break;
        $names = []; $links = [];
        foreach ($orders as $o) foreach ($o['items'] as $it) {
            $p = $cat[$it['slug']] ?? null; if (!$p) continue;
            $names[$p['name']] = 1; $links[$p['name']] = site_url() . '/products/' . $it['slug'] . '/';
        }
        if (!$names) { $emails[] = $email; continue; }
        $first = trim(explode(' ', $orders[0]['name'])[0] ?? '');
        $days = (int)$set['reminders']['days'];
        $body = 'Hi' . ($first !== '' ? " $first" : '') . ",\n\nIt has been about $days days since your Mario's Super Soil order (" . implode(', ', array_keys($names)) . "). If your plants are ready for another feeding, you can reorder here:\n\n";
        foreach ($links as $n => $u) $body .= "$n: $u\n";
        $body .= "\nNot sure how much to use? The soil amendment calculator works it out for your plants and bed: " . site_url() . "/soil-calculator/\n\nThanks for growing with us.\n\nMario's Super Soil\n$addr\n\nYou are getting this because you bought from us. Unsubscribe any time: " . site_url() . '/api/unsubscribe.php?t=' . $orders[0]['token'] . "\n";
        if (send_mail($email, "Time to restock your garden?", $body, null, owner_email())) { $sent++; $emails[] = $email; }
    }
    if ($emails) store_update(function (array $s) use ($emails) { foreach ($s['customers'] ?? [] as $i => $c) { if (in_array($c['email'], $emails, true) && empty($c['reminded']) && $c['remind_on'] <= today_toronto()) $s['customers'][$i]['reminded'] = true; } return $s; });
    $log[] = "reminders sent: " . ($sent ?? 0);
}

// ---- weekly backup (Sundays, once per week): saved on the server and emailed to the owner
$dow = (new DateTime('now', new DateTimeZone('America/Toronto')))->format('N');
$wk = (new DateTime('now', new DateTimeZone('America/Toronto')))->format('o-W');
if (($dow === '7' || isset($_GET['backup'])) && ($st['last_backup_week'] ?? '') !== $wk) {
    $res = do_backup(true);
    store_update(function (array $s) use ($wk) { $s['last_backup_week'] = $wk; return $s; });
    $log[] = 'backup: ' . $res;
}
out_json(['ok' => true, 'log' => $log]);
