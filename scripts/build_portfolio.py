#!/usr/bin/env python3
"""Turn portfolio/sleeves.json into portfolio/holdings.json by fixed rules, then refuse to write it if it breaks one.

Raw sleeve weight = tier weight (x single_stock_factor for one company). If the sleeves add up to more than
satellites_max, they are scaled down to fit. Weights are whole percentage points, shared out by a largest-remainder
method that can never go over satellites_max: every sleeve gets the whole points of its scaled weight, then the spare
points go to the sleeves with the largest leftover fraction, but only to a fraction of a half or more (so it still
rounds like rounding does) and only while room is left under the cap. The regime sleeve (T-bills) comes from the
Running Thesis. The core (the whole market) gets everything left, so it is always the biggest piece.

A vehicle must exist in portfolio/instruments.json (the reviewed registry), and its type and sector are taken from
there. The sleeves' own type and sector labels must agree with the registry, or the build stops.
"""
import json
import math
import sys
from datetime import date
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


class BuildError(Exception):
    pass


def num(value, what, lo=0, hi=None):
    """A finite number in range, as an exact Fraction (so no float rounding can creep into the shares)."""
    if not check.is_num(value) or value < lo or (hi is not None and value > hi):
        raise BuildError(f"{what} must be a number from {lo} to {hi if hi is not None else 'any'} (got {value!r})")
    return Fraction(str(value))


def allocate_points(raw, cap):
    """raw: {key: weight in points (Fraction)}; cap: points available. Returns {key: whole points}, sum <= cap."""
    total = sum(raw.values())
    scale = min(Fraction(1), Fraction(cap) / total) if total else Fraction(0)
    scaled = {k: v * scale for k, v in raw.items()}
    points = {k: math.floor(v) for k, v in scaled.items()}
    room = math.floor(cap) - sum(points.values())
    # largest fraction first; ties keep the order of the sleeves file
    for k in sorted(scaled, key=lambda k: scaled[k] - points[k], reverse=True):
        if room <= 0:
            break
        if scaled[k] - points[k] >= Fraction(1, 2):
            points[k] += 1
            room -= 1
    return points


def build(cfg, registry, rules, today=None):
    problems = check.check_rules(rules) + check.check_registry(rules, registry)
    if problems:
        raise BuildError("; ".join(problems))
    reg = check.instruments(registry)

    def instrument(ticker, what, bucket):
        e = reg.get(ticker) if isinstance(ticker, str) else None
        if e is None:
            raise BuildError(f"{what} {ticker!r} is not in portfolio/instruments.json (the reviewed registry)")
        if e["bucket"] != bucket:
            raise BuildError(f"{what} {ticker} is a {e['bucket']} instrument in the registry, not a {bucket} one")
        return e

    tier_weight = {k: num(v, f"tier_weight.{k}") for k, v in cfg["tier_weight"].items()}
    factor = num(cfg["single_stock_factor"], "single_stock_factor", 0, 1)
    cap = num(cfg["satellites_max"], "satellites_max", 0, 100)
    if cap > Fraction(str(rules["max_tilts"])) * 100:
        raise BuildError(f"satellites_max {cap} is over rules.json max_tilts {rules['max_tilts']}")

    held, raw, seen = [], {}, set()
    for s in cfg["sleeves"]:
        if s.get("vehicle") is None:
            continue
        if s["tier"] not in tier_weight:
            raise BuildError(f"sleeve {s['id']}: unknown tier {s['tier']!r}")
        if tier_weight[s["tier"]] <= 0:
            continue
        e = instrument(s["vehicle"], f"sleeve {s['id']} vehicle", "tilt")
        if s["vehicle"] in seen:
            raise BuildError(f"{s['vehicle']} is the vehicle of more than one sleeve")
        seen.add(s["vehicle"])
        for label in ("type", "sector"):
            if s.get(label) != e[label]:
                raise BuildError(f"sleeve {s['id']}: says {label} {s.get(label)!r} but the registry says {e[label]!r} for {s['vehicle']}")
        held.append((s, e))
        raw[s["id"]] = tier_weight[s["tier"]] * (factor if e["type"] == "stock" else 1)
    if len(raw) != len(held):
        raise BuildError("sleeve ids must be unique")

    pts = allocate_points(raw, cap)
    reg_sleeve = cfg["regime_sleeve"]
    reg_e = instrument(reg_sleeve["vehicle"], "regime vehicle", "cash")
    cash_pts = num(reg_sleeve["weight"], "regime_sleeve.weight", 0, 100)
    if cash_pts.denominator != 1:
        raise BuildError("regime_sleeve.weight must be a whole percent")
    core = cfg["core"]
    core_e = instrument(core["vehicle"], "core vehicle", "core")
    core_pts = 100 - sum(pts.values()) - int(cash_pts)
    if core_pts <= 0:
        raise BuildError("nothing is left for the core")

    rows = [{"ticker": core["vehicle"], "type": core_e["type"], "sector": core_e["sector"], "name": core["name"],
             "weight": core_pts / 100, "tier": "core", "line": core.get("line", ""), "why": core["why"],
             "risk": core.get("risk", ""), "theses": [core["source"]] if core.get("source") else []}]
    for s, e in held:
        if pts[s["id"]] <= 0:
            raise BuildError(f"sleeve {s['id']} rounds to 0%: raise its tier or take it out")
        rows.append({
            "ticker": s["vehicle"], "type": e["type"], "sector": e["sector"], "name": s["name"],
            "weight": pts[s["id"]] / 100, "market_cap_usd": s.get("market_cap_usd"),
            "tier": s["tier"], "line": s.get("line", ""), "why": s["why"], "risk": s["risk"],
            "theses": [s["source"]],
        })
    rows.append({"ticker": reg_sleeve["vehicle"], "type": reg_e["type"], "sector": reg_e["sector"],
                 "name": reg_sleeve["name"], "weight": int(cash_pts) / 100, "tier": "regime",
                 "line": reg_sleeve.get("line", ""), "why": reg_sleeve["why"], "risk": reg_sleeve["rule"],
                 "theses": [reg_sleeve.get("source", "Running Thesis")]})
    held_ids = {s["id"] for s, _ in held}
    not_held = [{"name": s["name"], "tier": s["tier"], "why": s["why"]} for s in cfg["sleeves"] if s["id"] not in held_ids]
    return {"as_of": (today or date.today()).isoformat(), "status": "v0, first version",
            "note": "One portfolio, the same for everyone, built from the research. Paper only. Not advice.",
            "holdings": rows, "not_held": not_held}


def main():
    try:
        cfg = check.load_json(ROOT / "portfolio/sleeves.json")
        registry = check.load_json(ROOT / "portfolio/instruments.json")
        rules = check.load_json(ROOT / "portfolio/rules.json")
        out = build(cfg, registry, rules)
    except (OSError, ValueError, BuildError) as e:
        print("FAIL", e)
        sys.exit(1)
    except (KeyError, TypeError, AttributeError) as e:
        print(f"FAIL sleeves.json is incomplete or malformed: {e.__class__.__name__}: {e}")
        sys.exit(1)
    errors = check.check(rules, registry, out)
    for e in errors:
        print("FAIL", e)
    if errors:
        print("holdings.json was NOT written")
        sys.exit(1)
    (ROOT / "portfolio/holdings.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    for r in out["holdings"]:
        print(f"{r['weight']*100:5.1f}%  {r['ticker']:6} {r['name']}")
    print(f"total {sum(r['weight'] for r in out['holdings'])*100:.1f}%")


if __name__ == "__main__":
    main()
