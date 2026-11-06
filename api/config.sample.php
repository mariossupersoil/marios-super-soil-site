<?php
// Copy this file to config.php (same folder) on the server and paste your key.
// config.php is never committed to GitHub and is blocked from the web by .htaccess.
return [
    'api_key' => 'PASTE-YOUR-ANTHROPIC-API-KEY-HERE',
    'model' => 'claude-sonnet-5-5',
    'per_ip_per_day' => 12,
    'global_per_day' => 400,
];
