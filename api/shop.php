<?php
// Public: the catalog (prices, availability) and shipping tiers the cart needs.
require __DIR__ . '/lib.php';
header('Cache-Control: no-cache');
$cat = catalog();
foreach ($cat as $slug => &$p) { foreach ($p['sizes'] as &$s) {
    $n = $s['stock']; unset($s['available'], $s['stock']);
    $s['soldout'] = ($n !== null && $n <= 0); $s['left'] = ($n !== null && $n > 0 && $n <= 5) ? $n : null;
} unset($s); } unset($p);
echo json_encode(['currency' => 'CAD', 'products' => $cat, 'tiers' => tiers()], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
