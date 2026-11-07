<?php
// Public: preview a discount code for a cart (nothing is stored or used up here).
require __DIR__ . '/lib.php';
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') fail(405, 'Use POST.');
$in = json_decode((string)file_get_contents('php://input', false, null, 0, 65536), true) ?: [];
$cart = price_cart(is_array($in['items'] ?? null) ? $in['items'] : [], catalog());
$r = apply_code((string)($in['code'] ?? ''), $cart['subtotal_cents']);
out_json(['code' => $r['code'], 'discount' => $r['amount_cents'] / 100, 'free_shipping' => $r['free_shipping']]);
