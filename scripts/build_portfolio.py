#!/usr/bin/env python3
"""Turn portfolio/sleeves.json into portfolio/holdings.json by fixed rules.

Raw sleeve weight = tier weight (x single_stock_factor for one company). If the sleeves add up to more than
satellites_max, they are scaled down to fit. The regime sleeve (T-bills) comes from the Running Thesis. The core
(the whole market) gets everything left, so it is always the biggest piece. Weights are whole percents.
"""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def build(cfg):
    held = [s for s in cfg["sleeves"] if s.get("vehicle") and cfg["tier_weight"][s["tier"]] > 0]
    raw = {}
    for s in held:
        w = cfg["tier_weight"][s["tier"]]
        if s["type"] == "stock":
            w *= cfg["single_stock_factor"]
        raw[s["id"]] = w
    total = sum(raw.values())
    scale = min(1.0, cfg["satellites_max"] / total) if total else 0
    rows = []
    for s in held:
        rows.append({
            "ticker": s["vehicle"], "type": s["type"], "sector": s["sector"], "name": s["name"],
            "weight": round(raw[s["id"]] * scale) / 100, "market_cap_usd": s.get("market_cap_usd"),
            "tier": s["tier"], "line": s.get("line", ""), "why": s["why"], "risk": s["risk"],
            "theses": [s["source"]],
        })
    reg = cfg["regime_sleeve"]
    rows.append({"ticker": reg["vehicle"], "type": "etf", "sector": reg["sector"], "name": reg["name"],
                 "weight": reg["weight"] / 100, "tier": "regime", "line": reg.get("line", ""), "why": reg["why"],
                 "risk": reg["rule"],
                 "theses": [reg.get("source", "Running Thesis")]})
    core = cfg["core"]
    rest = round(1 - sum(r["weight"] for r in rows), 4)
    rows.insert(0, {"ticker": core["vehicle"], "type": "etf", "sector": core["sector"], "name": core["name"],
                    "weight": rest, "tier": "core", "line": core.get("line", ""), "why": core["why"],
                    "risk": core.get("risk", ""), "theses": [core["source"]] if core.get("source") else []})
    not_held = [{"name": s["name"], "tier": s["tier"], "why": s["why"]} for s in cfg["sleeves"] if s not in held]
    return {"as_of": date.today().isoformat(), "status": "v0, first version",
            "note": "One portfolio, the same for everyone, built from the research. Paper only. Not advice.",
            "holdings": rows, "not_held": not_held}


def main():
    cfg = json.loads((ROOT / "portfolio/sleeves.json").read_text())
    out = build(cfg)
    (ROOT / "portfolio/holdings.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    for r in out["holdings"]:
        print(f"{r['weight']*100:5.1f}%  {r['ticker']:6} {r['name']}")
    print(f"total {sum(r['weight'] for r in out['holdings'])*100:.1f}%")


if __name__ == "__main__":
    main()
