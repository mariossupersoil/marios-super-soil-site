<?php
// Called by the order-complete page: if the Stripe session was paid and used a discount code, count one use (once per session).
require __DIR__ . '/lib.php';
$sid = (string)($_GET['session_id'] ?? '');
if (!preg_match('/^cs_[A-Za-z0-9_]{10,200}$/', $sid)) out_json(['ok' => false]);
$s = stripe_call('GET', '/v1/checkout/sessions/' . $sid);
if (($s['payment_status'] ?? '') !== 'paid') out_json(['ok' => false]);
$code = norm_code((string)($s['metadata']['discount_code'] ?? ''));
store_update(function (array $st) use ($sid, $code) {
    $done = $st['processed_sessions'] ?? [];
    if (in_array($sid, $done, true)) return $st;
    $done[] = $sid; $st['processed_sessions'] = array_slice($done, -500);
    if ($code !== '' && !empty($st['discounts'])) { foreach ($st['discounts'] as &$d) { if (norm_code((string)($d['code'] ?? '')) === $code) $d['uses'] = (int)($d['uses'] ?? 0) + 1; } unset($d); }
    return $st;
});
out_json(['ok' => true]);
