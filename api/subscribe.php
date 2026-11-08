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
// Also pass the address to the owner's email-bot list (an n8n webhook), if one is set in config.php. Never blocks or breaks the signup.
$c = cfg();
if (!empty($c['n8n_subscribe_url']) && function_exists('curl_init')) {
    $ch = curl_init((string)$c['n8n_subscribe_url']);
    curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 5, CURLOPT_CONNECTTIMEOUT => 3,
        CURLOPT_HTTPHEADER => ['Content-Type: application/json', 'X-Site-Secret: ' . (string)($c['n8n_secret'] ?? '')],
        CURLOPT_POSTFIELDS => json_encode(['email' => $email, 'source' => 'website', 'date' => today_toronto()])]);
    $r = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
    if ($r === false || $code >= 300) error_log("n8n subscribe forward failed: HTTP $code");
}
out_json(['ok' => true]);
