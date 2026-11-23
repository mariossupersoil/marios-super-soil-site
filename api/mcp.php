<?php
// Read-only MCP server (Streamable HTTP, stateless JSON-RPC). Lets AI agents search products, read prices and get contact info.
// It never reads or writes orders, customers or the store file. Described by /.well-known/mcp/server-card.json
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type, Accept, Mcp-Session-Id, MCP-Protocol-Version');
header('Access-Control-Allow-Methods: POST, OPTIONS');
$m = $_SERVER['REQUEST_METHOD'] ?? '';
if ($m === 'OPTIONS') { http_response_code(204); exit; }
if ($m !== 'POST') { http_response_code(405); header('Allow: POST, OPTIONS'); echo json_encode(['error' => 'Use POST with a JSON-RPC 2.0 body.']); exit; }
$raw = (string)file_get_contents('php://input', false, null, 0, 16384);
$req = json_decode($raw, true);
if (!is_array($req)) { http_response_code(400); echo json_encode(['jsonrpc' => '2.0', 'id' => null, 'error' => ['code' => -32700, 'message' => 'Parse error']]); exit; }

$site = json_decode((string)@file_get_contents(__DIR__ . '/../data/site.json'), true) ?: [];
$base = 'https://' . ($_SERVER['HTTP_HOST'] ?? 'mariossupersoil.ca');
function ok($id, $result) { echo json_encode(['jsonrpc' => '2.0', 'id' => $id, 'result' => $result], JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE); exit; }
function err($id, $code, $msg) { echo json_encode(['jsonrpc' => '2.0', 'id' => $id, 'error' => ['code' => $code, 'message' => $msg]]); exit; }
function text($o) { return ['content' => [['type' => 'text', 'text' => json_encode($o, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE)]]]; }

$tools = [
  ['name' => 'search_products', 'description' => "Search Mario's Super Soil natural dry soil amendments by need or name (e.g. bloom, nitrogen, clay soil, tomatoes). Returns names, links and a starting price in CAD.",
   'inputSchema' => ['type' => 'object', 'properties' => ['query' => ['type' => 'string', 'description' => 'What the grower needs or a product name']], 'required' => ['query']], 'annotations' => ['readOnlyHint' => true]],
  ['name' => 'get_prices', 'description' => 'Current list prices in CAD by bag size for every product, and which sizes are coming soon. Tax and shipping are added at checkout.',
   'inputSchema' => ['type' => 'object', 'properties' => new stdClass()], 'annotations' => ['readOnlyHint' => true]],
  ['name' => 'get_store_info', 'description' => 'Contact details, hours, location and shipping area.',
   'inputSchema' => ['type' => 'object', 'properties' => new stdClass()], 'annotations' => ['readOnlyHint' => true]],
];

$batch = isset($req[0]) ? $req : [$req];
$replies = [];
foreach ($batch as $r) {
    $id = $r['id'] ?? null; $method = (string)($r['method'] ?? ''); $p = $r['params'] ?? [];
    ob_start();
    if ($method === 'initialize') {
        ok($id, ['protocolVersion' => '2025-06-18', 'capabilities' => ['tools' => ['listChanged' => false]], 'serverInfo' => ['name' => 'marios-super-soil', 'title' => "Mario's Super Soil", 'version' => '1.0.0'],
                 'instructions' => "Read-only catalog for Mario's Super Soil, a Canadian maker of natural dry soil amendments. Ships across Canada."]);
    } elseif ($method === 'ping') { ok($id, new stdClass());
    } elseif ($method === 'tools/list') { ok($id, ['tools' => $tools]);
    } elseif ($method === 'tools/call') {
        $name = $p['name'] ?? ''; $a = $p['arguments'] ?? [];
        if ($name === 'search_products') {
            $q = preg_split('/\s+/', strtolower(trim((string)($a['query'] ?? ''))), -1, PREG_SPLIT_NO_EMPTY);
            $idx = json_decode((string)@file_get_contents(__DIR__ . '/../assets/search-index.json'), true)['items'] ?? [];
            $hits = [];
            foreach ($idx as $i) {
                $hay = strtolower(($i['t'] ?? '') . ' ' . ($i['k'] ?? '') . ' ' . ($i['d'] ?? ''));
                $all = true; foreach ($q as $w) if (strpos($hay, $w) === false) { $all = false; break; }
                if ($all) $hits[] = ['name' => $i['t'], 'url' => $base . $i['u'], 'summary' => $i['d']];
                if (count($hits) >= 8) break;
            }
            ok($id, text(['results' => $hits]));
        } elseif ($name === 'get_prices') {
            $pr = json_decode((string)@file_get_contents(__DIR__ . '/prices.json'), true)['products'] ?? [];
            $o = [];
            foreach ($pr as $slug => $pp) { $row = [];
                foreach ($pp['sizes'] ?? [] as $k => $z) $row[$k] = !empty($z['coming_soon']) ? 'coming soon' : ($z['price'] ?? null);
                $o[] = ['product' => $slug, 'url' => $base . '/products/' . $slug . '/', 'currency' => 'CAD', 'prices' => $row]; }
            ok($id, text(['prices' => $o, 'note' => 'Tax and shipping added at checkout. Full list: ' . $base . '/prices/']));
        } elseif ($name === 'get_store_info') {
            ok($id, text(['name' => "Mario's Super Soil", 'location' => 'Mississauga, Ontario, Canada', 'ships_to' => 'Canada', 'email' => $site['email'] ?? null, 'phone' => $site['phone'] ?? null, 'hours' => $site['hours'] ?? [], 'contact_page' => $base . '/contact/', 'shop' => $base . '/#products']));
        } else err($id, -32602, 'Unknown tool');
    } elseif (strpos($method, 'notifications/') === 0) { ob_end_clean(); continue;
    } else err($id, -32601, 'Method not found');
    ob_end_clean();
}
http_response_code(202);
