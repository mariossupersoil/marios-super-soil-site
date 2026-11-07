<?php
// GET ?slug=bone-meal -> approved reviews. POST -> a customer review, held for the owner to approve.
require __DIR__ . '/lib.php';
$base = jread(__DIR__ . '/prices.json')['products'] ?? [];
if (($_SERVER['REQUEST_METHOD'] ?? '') === 'GET') {
    $slug = (string)($_GET['slug'] ?? ''); if (!isset($base[$slug])) fail(404, 'Unknown product.');
    $out = [];
    foreach (store()['reviews'] ?? [] as $r) {
        if ($r['slug'] !== $slug || ($r['status'] ?? '') !== 'approved') continue;
        $out[] = ['name' => $r['name'], 'rating' => (int)$r['rating'], 'title' => $r['title'] ?? '', 'text' => $r['text'], 'date' => $r['date']];
    }
    usort($out, fn($a, $b) => strcmp($b['date'], $a['date']));
    header('Cache-Control: no-cache'); out_json(['reviews' => array_slice($out, 0, 50)]);
}
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') fail(405, 'Use GET or POST.');
$in = json_decode((string)file_get_contents('php://input', false, null, 0, 16384), true) ?: [];
if (!empty($in['website'])) out_json(['ok' => true]);
if (!rate_ok('rev', 3, 3600)) fail(429, 'Too many tries. Please try again later.');
$slug = (string)($in['slug'] ?? ''); if (!isset($base[$slug])) fail(400, 'Unknown product.');
$name = clean_line((string)($in['name'] ?? ''), 40); $rating = (int)($in['rating'] ?? 0);
$title = clean_line((string)($in['title'] ?? ''), 80); $text = trim((string)($in['text'] ?? ''));
$contact = strtolower(clean_line((string)($in['email'] ?? ''), 120));
if ($name === '') fail(400, 'Please enter your name.');
if ($rating < 1 || $rating > 5) fail(400, 'Please choose a star rating.');
if (mb_strlen($text) < 15) fail(400, 'Please write at least a sentence or two.');
if (mb_strlen($text) > 1000) fail(400, 'Please keep your review under 1000 characters.');
if (preg_match('#https?://|www\.|<a\s#i', $title . ' ' . $text . ' ' . $name)) fail(400, 'Please leave links out of your review.');
if ($contact !== '' && !valid_email($contact)) fail(400, 'That email address does not look right.');
$r = ['id' => bin2hex(random_bytes(5)), 'slug' => $slug, 'name' => $name, 'rating' => $rating, 'title' => $title, 'text' => $text, 'date' => today_toronto(), 'status' => 'pending', 'source' => 'customer', 'contact' => $contact];
store_update(function (array $st) use ($r) { $st['reviews'][] = $r; $st['reviews'] = array_slice($st['reviews'], -2000); return $st; });
send_mail(owner_email(), 'New review waiting for approval', "{$r['name']} left {$r['rating']} stars on {$base[$slug]['name']}:\n\n{$r['text']}\n\nApprove or delete it in your admin page: " . site_url() . "/admin/\n");
out_json(['ok' => true]);
