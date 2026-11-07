<?php
// Email signup (pop-up). Stores the address for the owner's list. Returns ok even for duplicates.
require __DIR__ . '/lib.php';
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') fail(405, 'Use POST.');
$in = json_decode((string)file_get_contents('php://input', false, null, 0, 8192), true) ?: [];
if (!empty($in['website'])) out_json(['ok' => true]); // honeypot
if (!rate_ok('sub', 6, 3600)) fail(429, 'Too many tries. Please try again later.');
$email = strtolower(trim((string)($in['email'] ?? '')));
if (!valid_email($email)) fail(400, 'Please enter a valid email address.');
store_update(function (array $st) use ($email) {
    foreach ($st['subscribers'] ?? [] as $s) { if ($s['email'] === $email) return $st; }
    $st['subscribers'][] = ['email' => $email, 'date' => today_toronto(), 'token' => bin2hex(random_bytes(12)), 'unsub' => false, 'source' => 'popup'];
    return $st;
});
out_json(['ok' => true]);
