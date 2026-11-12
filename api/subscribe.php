<?php
// Email signup (pop-up). Stores the address for the owner's list. Returns ok even for duplicates.
require __DIR__ . '/lib.php';
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') fail(405, 'Use POST.');
$in = json_decode((string)file_get_contents('php://input', false, null, 0, 8192), true) ?: [];
if (!empty($in['website'])) out_json(['ok' => true]); // honeypot
if (!rate_ok('sub', 6, 3600)) fail(429, 'Too many tries. Please try again later.');
$email = strtolower(trim((string)($in['email'] ?? '')));
if (!valid_email($email)) fail(400, 'Please enter a valid email address.');
$newToken = null;
store_update(function (array $st) use ($email, &$newToken) {
    foreach ($st['subscribers'] ?? [] as $s) { if ($s['email'] === $email) return $st; }
    $newToken = bin2hex(random_bytes(12));
    $st['subscribers'][] = ['email' => $email, 'date' => today_toronto(), 'token' => $newToken, 'unsub' => false, 'source' => 'popup'];
    return $st;
});
// Welcome email: only for a brand-new address (so repeat sign-ups can't be used to spam someone). A failed send never breaks the signup.
if ($newToken !== null) {
    $u = site_url();
    $a = ['street' => '', 'city' => '', 'region' => ''];
    $site = json_decode((string)@file_get_contents(__DIR__ . '/../data/site.json'), true) ?: [];
    $a = array_merge($a, $site['address'] ?? []);
    $addr = trim($a['street'] . ', ' . $a['city'] . ' ' . $a['region'] . ', Canada', ' ,');
    $promo = active_promo();
    $g = settings()['gift'];
    $body = "Welcome to Mario's Super Soil!\n\n"
        . "Thanks for joining. We make organic dry soil amendments in Mississauga, Ontario, and ship across Canada. Here is how to get started.\n\n"
        . ($promo ? "RIGHT NOW: " . $promo['title'] . ": " . $promo['text'] . ". Use code " . $promo['code'] . " at checkout.\n\n" : '')
        . "NEW TO GROWING?\nThe Super Starter Pack has six of our bags in one kit, so you can feed your plants from seed to harvest:\n" . $u . "/products/super-starter-pack/\n\n"
        . "THE QUICK VERSION\n"
        . "- Level Up 3-3-3 is our all-round blend. Flower Power 2-6-4 is for blooms and fruit.\n"
        . "- Both use about 1 tablespoon per gallon of soil. The directions are printed on every bag, in English and French.\n\n"
        . "NOT SURE HOW MUCH TO USE?\nThe soil amendment calculator works it out for your pots or bed:\n" . $u . "/soil-calculator/\n\n"
        . "GROWING QUESTIONS?\nAsk Mario, the chat on our site, answers growing questions any time. Our guides are here: " . $u . "/guides/\n\n"
        . (!empty($g['enabled']) ? "FREE GIFT\nOrders of $" . number_format((float)$g['threshold'], 0) . " or more include a free 2 lb bag of Level Up or Flower Power.\n\n" : '')
        . "You will hear from us now and then with sale alerts, planting tips and restock reminders. No spam.\n\n"
        . "Happy growing,\nMario's Super Soil\n" . $addr . "\nReply to this email any time. We read every one.\n\n"
        . "Unsubscribe any time: " . $u . '/api/unsubscribe.php?t=' . $newToken . "\n";
    if (!send_mail($email, "Welcome to Mario's Super Soil", $body, null, owner_email())) error_log('welcome email failed');
}
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
