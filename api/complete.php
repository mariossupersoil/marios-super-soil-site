<?php
// Called by the order-complete page. Backup for the Stripe webhook: records the paid order (stock + discount use) once.
require __DIR__ . '/lib.php';
if (!rate_ok('cmp', 60, 600)) out_json(['ok' => false]);
$sid = (string)($_GET['session_id'] ?? '');
if (!preg_match('/^cs_[A-Za-z0-9_]{10,200}$/', $sid)) out_json(['ok' => false]);
$s = stripe_call('GET', '/v1/checkout/sessions/' . $sid);
if (($s['payment_status'] ?? '') !== 'paid') out_json(['ok' => false]);
record_paid_session($s);
out_json(['ok' => true]);
