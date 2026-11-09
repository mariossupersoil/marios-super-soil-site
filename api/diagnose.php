<?php
// Plant Dr. Mario: receives 1-3 plant photos (JPEG, base64), asks Claude to diagnose, returns JSON.
// The API key lives in api/config.php, which is NOT in GitHub (see api/config.sample.php).
declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

function fail(int $code, string $msg): void {
    http_response_code($code);
    echo json_encode(['error' => $msg]);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') fail(405, 'Use POST.');

$cfgFile = __DIR__ . '/config.php';
if (!is_file($cfgFile)) fail(503, 'Plant Dr. Mario is not set up yet.');
$cfg = require $cfgFile;
$apiKey = $cfg['api_key'] ?? '';
if ($apiKey === '' || str_contains($apiKey, 'PASTE')) fail(503, 'Plant Dr. Mario is not set up yet.');
$model = $cfg['model'] ?? 'claude-sonnet-5-5';
$perIp = (int)($cfg['per_ip_per_day'] ?? 12);
$global = (int)($cfg['global_per_day'] ?? 400);
$allowedHosts = $cfg['allowed_hosts'] ?? ['mariossupersoil.ca', 'www.mariossupersoil.ca'];

// Same-site requests only (soft check; the daily limits are the real protection).
$origin = $_SERVER['HTTP_ORIGIN'] ?? ($_SERVER['HTTP_REFERER'] ?? '');
if ($origin !== '') {
    $h = parse_url($origin, PHP_URL_HOST) ?: '';
    $ok = in_array($h, $allowedHosts, true) || str_ends_with($h, '.hostingersite.com') || $h === 'localhost';
    if (!$ok) fail(403, 'Not allowed.');
}

// Daily limits (file counters).
$dir = __DIR__ . '/.rl';
if (!is_dir($dir)) @mkdir($dir, 0700, true);
function bump(string $file, int $max): bool {
    $fp = @fopen($file, 'c+');
    if (!$fp) return true; // never block users because of a filesystem problem
    flock($fp, LOCK_EX);
    $n = (int)stream_get_contents($fp);
    if ($n >= $max) { flock($fp, LOCK_UN); fclose($fp); return false; }
    ftruncate($fp, 0); rewind($fp); fwrite($fp, (string)($n + 1));
    flock($fp, LOCK_UN); fclose($fp);
    return true;
}
$day = gmdate('Ymd');
foreach (glob($dir . '/*') ?: [] as $f) { if (!str_contains($f, $day)) @unlink($f); }
$ip = $_SERVER['REMOTE_ADDR'] ?? 'x';
if (!bump("$dir/g-$day", $global)) fail(429, "Dr. Mario has seen a lot of plants today. Please try again tomorrow.");
if (!bump("$dir/i-" . substr(hash('sha256', $ip), 0, 16) . "-$day", $perIp)) fail(429, "You have reached today's limit of diagnoses. Please try again tomorrow.");

// Input.
$raw = file_get_contents('php://input', false, null, 0, 12 * 1024 * 1024);
$in = json_decode($raw ?: '', true);
if (!is_array($in) || !isset($in['images']) || !is_array($in['images'])) fail(400, 'No photo received.');
$images = array_slice($in['images'], 0, 3);
if (!$images) fail(400, 'No photo received.');
$content = [];
foreach ($images as $b64) {
    if (!is_string($b64)) fail(400, 'Bad photo.');
    $bin = base64_decode(preg_replace('#^data:image/\w+;base64,#', '', $b64), true);
    if ($bin === false || strlen($bin) > 4 * 1024 * 1024) fail(413, 'Photo is too large. Try a smaller one.');
    $info = @getimagesizefromstring($bin);
    if (!$info || $info[2] !== IMAGETYPE_JPEG) fail(400, 'Photo could not be read. Try another photo.');
    $content[] = ['type' => 'image', 'source' => ['type' => 'base64', 'media_type' => 'image/jpeg', 'data' => base64_encode($bin)]];
}
$plant = mb_substr(trim((string)($in['plant'] ?? '')), 0, 80);
$note = mb_substr(trim((string)($in['note'] ?? '')), 0, 600);
$where = in_array($in['where'] ?? '', ['indoor', 'outdoor', 'container', 'greenhouse'], true) ? $in['where'] : '';

$catalog = json_decode((string)file_get_contents(__DIR__ . '/catalog.json'), true) ?: [];
$lines = [];
$byKey = [];
foreach ($catalog as $p) {
    $byKey[$p['key']] = $p;
    $lines[] = "- {$p['key']}: {$p['name']} ({$p['npk']}) — {$p['use']}";
}

$system = <<<TXT
You are Plant Dr. Mario, the plant-health assistant for Mario's Super Soil, a Canadian maker of organic dry amendments. You look at photos of plants and explain what is most likely wrong, in plain, friendly language for home gardeners.

Rules:
- Be honest about uncertainty. A photo cannot prove a diagnosis. Nutrient problems look like overwatering, underwatering, root problems, light stress, heat or cold stress, pH problems and pests; say so and give the quick checks that tell them apart.
- If the photo is not a plant, is too blurry or dark, or shows too little to judge, set is_plant or health accordingly and say how to take a better photo (leaf top and underside, whole plant, the soil surface, natural light).
- List at most 3 problems, most likely first. Describe what you actually see in the photo that points to each one.
- Recommend products ONLY from the catalog below, using the exact key, and only when an amendment really helps with the problem. If the issue is watering, light, temperature, pests or disease that no amendment fixes, give practical steps and recommend no product or only a supportive one. Maximum 5 products. Never recommend synthetic pesticides, fungicides or chemical inputs.
- Do not give doses or amounts. Tell the person to follow the bag directions or use the Mario's Super Soil calculator.
- Do not promise cures, yields or results. Say "may help" and "supports".
- If the plant looks seriously diseased, or the person may be dealing with something dangerous (for example a pet or child ate a plant or product), tell them to contact a local garden centre, extension service, vet or poison control as appropriate.
- Answer in English with no emoji. Keep each text field short (1-3 sentences).

Catalog:
__LINES__
TXT;
$system = str_replace('__LINES__', implode("\n", $lines), $system);

$ctx = [];
if ($plant !== '') $ctx[] = "Plant (from the person): $plant";
if ($where !== '') $ctx[] = "Growing: $where";
if ($note !== '') $ctx[] = "What they have noticed: $note";
$ctx[] = count($images) . ' photo(s) attached.';
$ask = implode("\n", $ctx) . <<<TXT


Reply with ONLY a JSON object, no markdown, in exactly this shape:
{
 "is_plant": true,
 "plant": "best guess of the plant, or null",
 "confidence": "low" | "medium" | "high",
 "health": "healthy" | "minor_issues" | "needs_attention" | "cannot_tell",
 "summary": "1-2 sentence overall read",
 "problems": [ {"name": "...", "likelihood": "likely" | "possible", "signs": "what in the photo points to this", "fix": "practical steps to confirm and fix it"} ],
 "products": [ {"key": "catalog key", "why": "why it helps here"} ],
 "photo_tips": "only if a better photo would help, else null",
 "get_help": "only if outside help is advisable, else null"
}
TXT;
$content[] = ['type' => 'text', 'text' => $ask];

$payload = json_encode([
    'model' => $model,
    'max_tokens' => 1800,
    'system' => $system,
    'messages' => [['role' => 'user', 'content' => $content]],
]);

$ch = curl_init($cfg['api_url'] ?? 'https://api.anthropic.com/v1/messages');
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => $payload,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 75,
    CURLOPT_HTTPHEADER => ['content-type: application/json', 'x-api-key: ' . $apiKey, 'anthropic-version: 2023-06-01'],
]);
$resp = curl_exec($ch);
$code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
$cerr = curl_error($ch);
curl_close($ch);
if ($resp === false) { error_log("drmario curl: $cerr"); fail(502, 'Could not reach the diagnosis service. Please try again.'); }
$data = json_decode($resp, true);
if ($code !== 200 || !is_array($data)) {
    error_log("drmario api $code: " . substr((string)$resp, 0, 300));
    fail(502, 'The diagnosis service had a problem. Please try again in a minute.');
}
$text = '';
foreach ($data['content'] ?? [] as $blk) { if (($blk['type'] ?? '') === 'text') $text .= $blk['text']; }
$s = strpos($text, '{'); $e = strrpos($text, '}');
$out = ($s !== false && $e !== false) ? json_decode(substr($text, $s, $e - $s + 1), true) : null;
if (!is_array($out)) fail(502, 'Dr. Mario could not put together an answer. Please try again.');

// Clean the model output; attach product names and links from our own catalog.
$res = [
    'is_plant' => (bool)($out['is_plant'] ?? true),
    'plant' => is_string($out['plant'] ?? null) ? mb_substr($out['plant'], 0, 80) : null,
    'confidence' => in_array($out['confidence'] ?? '', ['low', 'medium', 'high'], true) ? $out['confidence'] : 'low',
    'health' => in_array($out['health'] ?? '', ['healthy', 'minor_issues', 'needs_attention', 'cannot_tell'], true) ? $out['health'] : 'cannot_tell',
    'summary' => mb_substr((string)($out['summary'] ?? ''), 0, 500),
    'problems' => [], 'products' => [],
    'photo_tips' => is_string($out['photo_tips'] ?? null) ? mb_substr($out['photo_tips'], 0, 400) : null,
    'get_help' => is_string($out['get_help'] ?? null) ? mb_substr($out['get_help'], 0, 400) : null,
];
foreach (array_slice($out['problems'] ?? [], 0, 3) as $p) {
    if (!is_array($p)) continue;
    $res['problems'][] = [
        'name' => mb_substr((string)($p['name'] ?? ''), 0, 120),
        'likelihood' => ($p['likelihood'] ?? '') === 'likely' ? 'likely' : 'possible',
        'signs' => mb_substr((string)($p['signs'] ?? ''), 0, 500),
        'fix' => mb_substr((string)($p['fix'] ?? ''), 0, 600),
    ];
}
$seen = [];
foreach (array_slice($out['products'] ?? [], 0, 5) as $p) {
    $k = is_array($p) ? ($p['key'] ?? '') : '';
    if (!isset($byKey[$k]) || isset($seen[$k])) continue;
    $seen[$k] = 1;
    $res['products'][] = ['key' => $k, 'name' => $byKey[$k]['name'], 'npk' => $byKey[$k]['npk'], 'url' => $byKey[$k]['url'], 'why' => mb_substr((string)($p['why'] ?? ''), 0, 300)];
}
echo json_encode($res, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
