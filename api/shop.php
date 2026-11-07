<?php
// Public: the catalog (prices, availability) and shipping tiers the cart needs.
require __DIR__ . '/lib.php';
header('Cache-Control: no-cache');
$cat = catalog();
foreach ($cat as $slug => &$p) { foreach ($p['sizes'] as &$s) {
    $n = $s['stock']; unset($s['available'], $s['stock']);
    $s['soldout'] = ($n !== null && $n <= 0); $s['left'] = ($n !== null && $n > 0 && $n <= 5) ? $n : null;
} unset($s); } unset($p);
$g = settings()['gift']; $gift = (!empty($g['enabled']) && ($g['stock'] === null || $g['stock'] > 0)) ? ['threshold' => $g['threshold'], 'name' => $g['name'], 'weight_kg' => $g['weight_kg']] : null;
echo json_encode(['currency' => 'CAD', 'products' => $cat, 'tiers' => tiers(), 'gift' => $gift], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
