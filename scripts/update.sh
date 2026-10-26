#!/usr/bin/env bash
# Update (whenever we get to it): after editing the research or the sleeves, rebuild the portfolio and the site
# and run every check. It never commits, pushes or deploys; review the diff, commit, then run scripts/deploy.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/build_portfolio.py     # sleeves.json + instruments.json -> holdings.json (refuses a rule-breaking result)
python3 scripts/check.py               # the rules, and holdings.json == what sleeves.json builds
python3 scripts/check_theses.py
python3 scripts/score.py --check
python3 scripts/test_checks.py         # the checks themselves still reject bad input
bash site/build.sh
git status --short
echo "Review the diff (git diff), then commit."
