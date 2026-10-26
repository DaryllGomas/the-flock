#!/usr/bin/env bash
# Build the site data and deploy the static site to Cloudflare (flock.bigpicsolutions.com).
# Needs CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID in the environment (never commit them).
set -euo pipefail
cd "$(dirname "$0")/.."
: "${CLOUDFLARE_API_TOKEN:?set CLOUDFLARE_API_TOKEN}"
: "${CLOUDFLARE_ACCOUNT_ID:?set CLOUDFLARE_ACCOUNT_ID}"
python3 scripts/check.py
bash site/build.sh
WRANGLER_SEND_METRICS=false npx --yes wrangler@4 deploy
