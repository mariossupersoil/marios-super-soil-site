<?php
// Wholesale application form: saved for the admin page and emailed to the owner.
require __DIR__ . '/lib.php';
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') fail(405, 'Use POST.');
$in = json_decode((string)file_get_contents('php://input', false, null, 0, 16384), true) ?: [];
if (!empty($in['website'])) out_json(['ok' => true]);
if (!rate_ok('ws', 4, 3600)) fail(429, 'Too many tries. Please try again later.');
$f = [
    'business' => clean_line((string)($in['business'] ?? ''), 100), 'contact' => clean_line((string)($in['contact'] ?? ''), 80),
    'email' => strtolower(clean_line((string)($in['email'] ?? ''), 120)), 'phone' => clean_line((string)($in['phone'] ?? ''), 30),
    'city' => clean_line((string)($in['city'] ?? ''), 80), 'type' => clean_line((string)($in['type'] ?? ''), 40),
    'volume' => clean_line((string)($in['volume'] ?? ''), 40), 'website_url' => clean_line((string)($in['site'] ?? ''), 120),
    'message' => mb_substr(trim((string)($in['message'] ?? '')), 0, 1500),
];
if ($f['business'] === '' || $f['contact'] === '') fail(400, 'Please enter your business name and your name.');
if (!valid_email($f['email'])) fail(400, 'Please enter a valid email address.');
if ($f['phone'] === '') fail(400, 'Please enter a phone number.');
$f['id'] = bin2hex(random_bytes(5)); $f['date'] = today_toronto(); $f['status'] = 'new';
store_update(function (array $st) use ($f) { $st['wholesale_leads'][] = $f; $st['wholesale_leads'] = array_slice($st['wholesale_leads'], -500); return $st; });
$body = "New wholesale application\n\nBusiness: {$f['business']}\nContact: {$f['contact']}\nEmail: {$f['email']}\nPhone: {$f['phone']}\nCity: {$f['city']}\nType of store: {$f['type']}\nExpected monthly order: {$f['volume']}\nWebsite: {$f['website_url']}\n\nMessage:\n{$f['message']}\n";
send_mail(owner_email(), 'Wholesale application: ' . $f['business'], $body, null, $f['email']);
out_json(['ok' => true]);
