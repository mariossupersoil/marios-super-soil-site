<?php
// Stripe webhook: checkout.session.completed -> take stock off and count discount codes (signature checked).
require __DIR__ . '/lib.php';
$secret = (string)(cfg()['stripe_webhook_secret'] ?? '');
if ($secret === '' || str_contains($secret, 'PASTE')) fail(503, 'Webhook not set up.');
$payload = (string)file_get_contents('php://input', false, null, 0, 1048576);
$hdr = (string)($_SERVER['HTTP_STRIPE_SIGNATURE'] ?? '');
$t = ''; $sigs = [];
foreach (explode(',', $hdr) as $part) { $kv = explode('=', trim($part), 2); if (count($kv) === 2) { if ($kv[0] === 't') $t = $kv[1]; if ($kv[0] === 'v1') $sigs[] = $kv[1]; } }
$calc = hash_hmac('sha256', $t . '.' . $payload, $secret);
$ok = false; foreach ($sigs as $s) { if (hash_equals($calc, $s)) $ok = true; }
if (!$ok || $t === '' || abs(time() - (int)$t) > 600) fail(400, 'Bad signature.');
$ev = json_decode($payload, true);
if (is_array($ev) && in_array($ev['type'] ?? '', ['checkout.session.completed', 'checkout.session.async_payment_succeeded'], true)) {
    record_paid_session($ev['data']['object'] ?? []);
}
out_json(['received' => true]);
