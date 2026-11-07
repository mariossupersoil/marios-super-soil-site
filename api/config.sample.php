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
    // Shipping is by order weight (set in the admin page).
    'stripe_secret_key' => 'PASTE-YOUR-STRIPE-SECRET-KEY-HERE',
    'stripe_webhook_secret' => 'PASTE-YOUR-STRIPE-WEBHOOK-SECRET-HERE', // whsec_... (see README) so stock is counted down even if a customer closes the tab
    'automatic_tax' => true,   // needs Stripe Tax turned on in your Stripe dashboard

    // Email (reminders, wholesale and review alerts, weekly backup)
    'owner_email' => 'mariossupersoil@mariossupersoil.com',
    // Best way to send: a real mailbox. Hostinger: Emails > create a mailbox, then use these (host smtp.hostinger.com, port 465).
    // 'smtp_host' => 'smtp.hostinger.com', 'smtp_port' => 465, 'smtp_user' => 'orders@yourdomain.ca', 'smtp_pass' => 'MAILBOX-PASSWORD',
    // Brevo (free 300/day): smtp_host smtp-relay.brevo.com, smtp_port 587, smtp_user = your Brevo SMTP login, smtp_pass = SMTP key, and smtp_from = your verified sender address.
    'mail_from' => 'orders@mariossupersoil.ca',   // an address on your own domain sends best
    'site_url' => 'https://mariossupersoil.ca',   // used in email links
    'cron_key' => 'PASTE-A-RANDOM-KEY-OF-20-OR-MORE-CHARACTERS-HERE', // for the daily job (see README)

    // Owner admin page at /admin/ (at least 10 characters; use something long and unique)
    'admin_password' => 'PASTE-A-LONG-ADMIN-PASSWORD-HERE',
];
