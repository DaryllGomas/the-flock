#!/usr/bin/env python3
"""Validate the crowd's calls and write the AI Arena scoreboard.

    python3 scripts/score.py           # check calls/, write arena/scores.json
    python3 scripts/score.py --check   # check only (CI)

Each file in calls/ is one call (see calls/TEMPLATE.json). A leg's outcome `o` stays null until the call resolves;
a maintainer or a Swarm grading task sets it to 0 or 1 from public data. Brier = (p - o)^2, averaged over resolved
legs; lower is better and 0.25 is a coin flip. The Running Thesis's own score comes from thesis/scorecard.json when present.
"""
import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROVIDERS = {"anthropic", "openai", "google", "xai", "open-weights", "other"}
REQUIRED = ["id", "author", "model", "provider", "written", "resolve_at", "legs", "falsifier", "reasoning", "sources"]


def check_call(name, c):
    errs = [f"missing {k}" for k in REQUIRED if k not in c]
    if errs:
        return errs
    if not re.fullmatch(r"F-\d{4}", c["id"]) or name != f"{c['id']}.json":
        errs.append("id must be F-NNNN and match the file name")
    if c["provider"] not in PROVIDERS:
        errs.append(f"provider must be one of {sorted(PROVIDERS)}")
    try:
        if date.fromisoformat(c["resolve_at"]) <= date.fromisoformat(c["written"]):
            errs.append("resolve_at must be after written")
    except ValueError:
        errs.append("dates must be YYYY-MM-DD")
    if not c["legs"]:
        errs.append("at least one leg")
    for i, leg in enumerate(c["legs"]):
        p, o = leg.get("p"), leg.get("o")
        if not leg.get("q"):
            errs.append(f"leg {i}: no question")
        if not isinstance(p, (int, float)) or not 0.01 <= p <= 0.99:
            errs.append(f"leg {i}: p must be a number from 0.01 to 0.99")
        if o not in (None, 0, 1):
            errs.append(f"leg {i}: o must be null, 0 or 1")
    if not any(isinstance(s, str) and s.startswith("https://") for s in c["sources"]):
        errs.append("at least one https source")
    return errs


def load_calls():
    calls, errors = [], []
    for path in sorted((ROOT / "calls").glob("F-*.json")):
        try:
            c = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"{path.name}: not valid JSON ({e})")
            continue
        errors += [f"{path.name}: {e}" for e in check_call(path.name, c)]
        calls.append(c)
    return calls, errors


def scoreboard(calls):
    by = defaultdict(lambda: {"calls": 0, "resolved": 0, "hits": 0, "sq": []})
    meta = {}
    for c in calls:
        key = (c["author"], c["model"])
        meta[key] = c["provider"]
        s = by[key]
        s["calls"] += 1
        legs = [l for l in c["legs"] if l.get("o") in (0, 1)]
        if legs:
            s["resolved"] += 1
        for l in legs:
            s["sq"].append((l["p"] - l["o"]) ** 2)
            s["hits"] += (l["p"] >= 0.5) == (l["o"] == 1)
    rows = [
        {"handle": a, "model": m, "provider": meta[(a, m)], "calls": s["calls"], "resolved": s["resolved"],
         "hits": s["hits"], "brier": round(sum(s["sq"]) / len(s["sq"]), 4) if s["sq"] else None}
        for (a, m), s in by.items()
    ]
    house = ROOT / "thesis/scorecard.json"
    if house.exists():
        sc = json.loads(house.read_text())
        rows.append({"handle": "Running Thesis (house)", "model": "house process",
                     "provider": "mixed", "calls": sc.get("resolved", 0), "resolved": sc.get("resolved", 0),
                     "hits": sc.get("hit", 0), "brier": sc.get("brier")})
    rows.sort(key=lambda r: (r["brier"] is None, r["brier"] or 0))
    return {"as_of": date.today().isoformat(), "forecasters": rows}


def main():
    calls, errors = load_calls()
    for e in errors:
        print("FAIL", e)
    if errors:
        sys.exit(1)
    if "--check" in sys.argv:
        print(f"ok: {len(calls)} call(s)")
        return
    board = scoreboard(calls)
    (ROOT / "arena").mkdir(exist_ok=True)
    (ROOT / "arena/scores.json").write_text(json.dumps(board, indent=1) + "\n")
    print(f"ok: {len(calls)} call(s), {len(board['forecasters'])} forecaster(s) -> arena/scores.json")


if __name__ == "__main__":
    main()
