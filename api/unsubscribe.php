<?php
// One-click unsubscribe from restock reminders / emails. GET ?t=token
require __DIR__ . '/lib.php';
$t = (string)($_GET['t'] ?? '');
$done = false; $unsubEmail = '';
if (preg_match('/^[a-f0-9]{24}$/', $t)) {
    store_update(function (array $st) use ($t, &$done, &$unsubEmail) {
        $email = null;
        foreach (['customers', 'subscribers'] as $k) foreach ($st[$k] ?? [] as $r) { if (hash_equals($r['token'], $t)) $email = $r['email']; }
        if ($email === null) return $st;
        foreach (['customers', 'subscribers'] as $k) foreach ($st[$k] ?? [] as $i => $r) { if ($r['email'] === $email) $st[$k][$i]['unsub'] = true; }
        $done = true; $unsubEmail = $email; return $st;
    });
    // Keep the email bot's Google Sheet in step: mark them Unsubscribed there too (the bot's own unsubscribe webhook). Never breaks the page.
    $c = cfg();
    if ($done && !empty($c['n8n_unsubscribe_url']) && !empty($unsubEmail) && function_exists('curl_init')) {
        $ch = curl_init((string)$c['n8n_unsubscribe_url'] . '?email=' . rawurlencode($unsubEmail));
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 5, CURLOPT_CONNECTTIMEOUT => 3]);
        curl_exec($ch); curl_close($ch);
    }
}
header('Content-Type: text/html; charset=utf-8');
$msg = $done ? 'You have been unsubscribed. You will not get any more emails from us.' : 'This link is not valid or was already used.';
echo '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Unsubscribe</title><body style="font:18px/1.6 system-ui,sans-serif;background:#0e0e0f;color:#f5f4f0;padding:48px 20px;text-align:center"><h1 style="font-weight:600">' . ($done ? 'Unsubscribed' : 'Link problem') . '</h1><p>' . $msg . '</p><p><a style="color:#7fc46b" href="/">Back to Mario\'s Super Soil</a></p></body></html>';
