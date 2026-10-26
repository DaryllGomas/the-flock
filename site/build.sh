#!/usr/bin/env bash
# Copies the public data into site/data/ so site/index.html can fetch it with relative paths.
# Nothing is fetched from outside: the page, its fonts and its data are all local files.
#
#   portfolio/holdings.json   -> data/holdings.json   (the holdings, tiers, why, risk, not_held)
#   portfolio/changes.json    -> data/changes.json    (What changed)
#   portfolio/this-week.json  -> data/this-week.json  (This week: the market)
#   portfolio/rules.json      -> data/rules.json      (paper notional)
#   portfolio/LEDGER.md       -> data/ledger.md       (paper trade ledger note, Changes tab)
#   thesis/THESIS.md          -> data/THESIS.md       (Research tab)
#   docs/SCAM-SIGNS.md        -> data/scam-signs.md   (Help tab)
set -euo pipefail
cd "$(dirname "$0")"
root=".."

copy() { # copy <source relative to repo root> <name in data/>
  if [ ! -f "$root/$1" ]; then
    echo "build: missing $1" >&2
    exit 1
  fi
  cp "$root/$1" "data/$2"
}

rm -rf data
mkdir -p data
copy portfolio/holdings.json   holdings.json
copy portfolio/changes.json    changes.json
copy portfolio/this-week.json  this-week.json
copy portfolio/rules.json      rules.json
copy portfolio/LEDGER.md       ledger.md
copy thesis/THESIS.md          THESIS.md
copy docs/SCAM-SIGNS.md        scam-signs.md

# Sanity: the JSON files must parse strictly, or the page would show an error. Plain Python json accepts NaN and
# Infinity (and a repeated key) that browsers reject or misread, so the check lives in scripts/check.py --json.
for f in holdings changes this-week rules; do
  python3 ../scripts/check.py --json "data/$f.json" || { echo "build: data/$f.json is not strict JSON" >&2; exit 1; }
done

echo "built: $(ls data | tr '\n' ' ')"
