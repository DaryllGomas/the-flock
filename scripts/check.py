#!/usr/bin/env python3
"""Check portfolio/holdings.json against portfolio/rules.json. Exits 1 on any broken rule."""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check(rules, holdings):
    errors = []
    rows = holdings["holdings"]
    total = sum(h["weight"] for h in rows)
    if abs(total - 1.0) > 1e-6:
        errors.append(f"weights add up to {total:.4f}, not 1")
    sectors = defaultdict(float)
    for h in rows:
        t = h["ticker"]
        if h["type"] not in rules["allowed_types"]:
            errors.append(f"{t}: type {h['type']} is not allowed")
        if h["weight"] < 0:
            errors.append(f"{t}: negative weight (shorting is banned)")
        if t == rules["remainder_to"]:
            continue
        if h.get("sector") == "gold":
            if h["weight"] > rules["max_weight_gold"]:
                errors.append(f"{t}: gold weight {h['weight']:.2%} over the cap")
            continue
        sectors[h["sector"]] += h["weight"]
        if h["type"] == "stock":
            if h["weight"] > rules["max_weight_stock"]:
                errors.append(f"{t}: weight {h['weight']:.2%} over the per-stock cap")
            if (h.get("market_cap_usd") or 0) < rules["min_market_cap_usd"]:
                errors.append(f"{t}: market cap under the minimum or missing")
        if len(h.get("theses", [])) == 0:
            errors.append(f"{t}: no thesis linked")
    for s, w in sectors.items():
        if w > rules["max_weight_sector"]:
            errors.append(f"sector {s}: {w:.2%} over the sector cap")
    return errors


def main():
    rules = json.loads((ROOT / "portfolio/rules.json").read_text())
    holdings = json.loads((ROOT / "portfolio/holdings.json").read_text())
    errors = check(rules, holdings)
    for e in errors:
        print("FAIL", e)
    if errors:
        sys.exit(1)
    print(f"ok: {len(holdings['holdings'])} holding(s) within the rules")


if __name__ == "__main__":
    main()
