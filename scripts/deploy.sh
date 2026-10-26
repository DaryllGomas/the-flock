#!/usr/bin/env bash
# Build the site data and deploy the static site to Cloudflare (flock.bigpicsolutions.com).
# Needs CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID in the environment (never commit them).
# Deploys only what is public and reviewed: the git tree must be clean and HEAD must be the same commit as
# origin/main on GitHub. Every integrity check runs first, including "holdings.json is what sleeves.json builds".
set -euo pipefail
cd "$(dirname "$0")/.."
: "${CLOUDFLARE_API_TOKEN:?set CLOUDFLARE_API_TOKEN}"
: "${CLOUDFLARE_ACCOUNT_ID:?set CLOUDFLARE_ACCOUNT_ID}"

# 1. Nothing uncommitted (wrangler's own scratch folder .wrangler/ is ignored here).
dirty="$(git status --porcelain --untracked-files=all -- . ':(exclude).wrangler')"
if [ -n "$dirty" ]; then
  echo "deploy: refusing to deploy, the working tree has changes that are not committed:" >&2
  echo "$dirty" >&2
  echo "Commit and merge them first. Only what is public and reviewed goes live." >&2
  exit 1
fi

# 2. HEAD is exactly the public main branch (asked of GitHub directly, so a stale local copy cannot fool it).
head="$(git rev-parse HEAD)"
remote="$(git ls-remote origin refs/heads/main 2>/dev/null | cut -f1)" || remote=""
if [ -z "$remote" ]; then
  echo "deploy: refusing to deploy, could not read origin/main from GitHub (offline? no 'origin'?)." >&2
  exit 1
fi
if [ "$head" != "$remote" ]; then
  echo "deploy: refusing to deploy, HEAD is not the same commit as origin/main." >&2
  echo "  HEAD        $head" >&2
  echo "  origin/main $remote" >&2
  echo "Merge your change to main on GitHub, pull it, then deploy from a checkout of that commit." >&2
  exit 1
fi
echo "deploy: clean tree at origin/main (${head:0:10})"

# 3. Every check, then build and ship.
python3 scripts/check.py            # the rules, and holdings.json == what sleeves.json builds
python3 scripts/check_theses.py
python3 scripts/score.py --check
bash site/build.sh
# Pinned wrangler (the version already in use) so a new release cannot run with the Cloudflare token.
WRANGLER_SEND_METRICS=false npx --yes wrangler@4.151.1 deploy
