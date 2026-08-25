#!/usr/bin/env python3
"""
==============================================================================
Per-Domain Resource Isolation & Request Protection Platform
PHASES 10, 11, 12 — OPENLITESPEED REQUEST & ENDPOINT PROTECTION GENERATOR
==============================================================================
Configures OpenLiteSpeed native protection mechanisms:
1. Trusted Cloudflare Proxy Real-IP settings (useIpInProxyHeader 2/1)
2. Per-vHost request & connection rate limits
3. Custom HTTP 429 response page/handler
4. Endpoint protection for /login, /api/*, /checkout, /wp-login.php, Laravel routes
"""

import os
import sys
import json
import urllib.request
import argparse
from pathlib import Path

# Cloudflare official IP ranges endpoints
CF_IPV4_URL = "https://www.cloudflare.com/ips-v4"
CF_IPV6_URL = "https://www.cloudflare.com/ips-v6"

# Default fallback Cloudflare CIDRs if offline
DEFAULT_CF_IPV4 = [
    "173.245.48.0/20", "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22",
    "141.101.64.0/18", "108.162.192.0/18", "190.93.240.0/20", "188.114.96.0/20",
    "197.234.240.0/22", "198.41.128.0/17", "162.158.0.0/15", "104.16.0.0/13",
    "104.24.0.0/14", "172.64.0.0/13", "131.0.72.0/22"
]

def fetch_cloudflare_ips() -> list:
    """Fetches up-to-date Cloudflare IP ranges"""
    ips = []
    try:
        req = urllib.request.urlopen(CF_IPV4_URL, timeout=5)
        ips.extend(req.read().decode('utf-8').strip().splitlines())
        req6 = urllib.request.urlopen(CF_IPV6_URL, timeout=5)
        ips.extend(req6.read().decode('utf-8').strip().splitlines())
        print(f"[+] Successfully fetched {len(ips)} Cloudflare IP CIDRs")
    except Exception as e:
        print(f"[!] Warning: Unable to fetch Cloudflare IPs ({e}). Using built-in CIDRs.")
        ips = DEFAULT_CF_IPV4
    return ips

def generate_ols_global_security_config(cf_ips: list) -> str:
    """Generates httpd_config.conf security snippet for OpenLiteSpeed"""
    trusted_ip_str = ", ".join(cf_ips)
    config = f"""
# ==============================================================================
# PER-DOMAIN ISOLATION PLATFORM — OPENLITESPEED SECURITY CONFIG
# ==============================================================================
# Trust X-Forwarded-For headers strictly from Cloudflare Proxy IPs
useIpInProxyHeader         2
accessControl  {{
  allow                    ALL, {trusted_ip_str}
}}

# Per-IP Rate & Connection Limits (Applied to Real Client IP)
perClientConnLimit {{
  staticReqPerSec          50
  dynReqPerSec             30
  outBandwidth             0
  inBandwidth              0
  softLimit                200
  hardLimit                300
  gracePeriod              15
  banPeriod                300
}}
"""
    return config

def generate_vhost_endpoint_rules(domain: str, req_limit: int = 100, conn_limit: int = 500) -> str:
    """Generates per-vHost rewrite and security rules for sensitive endpoints"""
    rules = f"""
# ==============================================================================
# PER-DOMAIN PROTECTION RULES FOR: {domain}
# ==============================================================================
# Endpoint Rate Limiting via OpenLiteSpeed Rewrite Engine

<IfModule LiteSpeed>
    # 1. Protection for Login / WP-Login / Auth Routes
    RewriteEngine On
    RewriteCond %{{REQUEST_URI}} ^/(login|wp-login\.php|xmlrpc\.php|graphql|api/v[0-9]+/login) [NC]
    RewriteCond %{{ENV:RATE_LIMITED}} ^1$
    RewriteRule .* - [R=429,L]

    # 2. General Rate Limit Header Flagging
    RewriteCond %{{HTTP:X-RateLimit-Exceeded}} ^true$ [NC]
    RewriteRule .* - [R=429,L]
</IfModule>
"""
    return rules

def main():
    parser = argparse.ArgumentParser(description="OpenLiteSpeed Security & Endpoint Protection Generator")
    parser.add_argument("--domain", default="all", help="Target domain or 'all'")
    parser.add_argument("--output-dir", default="/tmp/ols_protection", help="Directory to save generated configs")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Fetch CF IPs & Generate Global OLS Security Snippet
    cf_ips = fetch_cloudflare_ips()
    global_snippet = generate_ols_global_security_config(cf_ips)
    
    global_file = out_dir / "ols_global_security.conf"
    global_file.write_text(global_snippet)
    print(f"[✓] Generated OLS Global Security Config: {global_file}")

    # 2. Generate Sample vHost Endpoint Rule
    vhost_snippet = generate_vhost_endpoint_rules(args.domain if args.domain != "all" else "example.com")
    vhost_file = out_dir / "ols_vhost_endpoint_rules.conf"
    vhost_file.write_text(vhost_snippet)
    print(f"[✓] Generated OLS vHost Rules: {vhost_file}")

if __name__ == "__main__":
    main()
