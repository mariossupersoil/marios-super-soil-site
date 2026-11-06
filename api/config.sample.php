<?php
// Copy this file to config.php (same folder) on the server and fill it in.
// config.php is never committed to GitHub and is blocked from the web by .htaccess.
return [
    // Plant Dr. Mario (Anthropic)
    'api_key' => 'PASTE-YOUR-ANTHROPIC-API-KEY-HERE',
    'model' => 'claude-sonnet-5-5',
    'per_ip_per_day' => 12,
    'global_per_day' => 400,

    // Shop checkout (Stripe). Use an sk_test_ key first, then switch to sk_live_.
    'stripe_secret_key' => 'PASTE-YOUR-STRIPE-SECRET-KEY-HERE',
    // Shipping is by order weight: see api/shipping.json
    'automatic_tax' => true,       // needs Stripe Tax turned on in your Stripe dashboard
];
