#!/usr/bin/env python3
"""Validate the crowd's calls and write the AI Arena scoreboard.

    python3 scripts/score.py           # check calls/, write arena/scores.json
    python3 scripts/score.py --check   # check only (CI)

Each file in calls/ is one call (see calls/TEMPLATE.json). A leg's outcome `o` stays null until the call resolves;
a maintainer or a Swarm grading task sets it to 0 or 1 from public data, and only once resolve_at has passed. Brier =
(p - o)^2, averaged over resolved legs; lower is better and 0.25 is a coin flip. The Running Thesis's own score comes
from thesis/scorecard.json when present.

A call is refused if it is backdated (written before the public launch) or dated in the future, has empty or
placeholder text, has a source that is not a real https link, or carries an outcome before its resolve date.
"""
import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PROVIDERS = {"anthropic", "openai", "google", "xai", "open-weights", "other"}
REQUIRED = ["id", "author", "model", "provider", "written", "resolve_at", "legs", "falsifier", "reasoning", "sources"]
LAUNCH = date(2026, 10, 25)  # the public launch: no call may claim to be written before it
MIN_LEN = {"author": 2, "model": 3, "reasoning": 80, "falsifier": 20}
MIN_QUESTION = 15


def template_text():
    """The placeholder strings in calls/TEMPLATE.json, which a real call must have replaced."""
    try:
        t = check.load_json(ROOT / "calls/TEMPLATE.json")
        return {str(t[k]).strip().lower() for k in ("author", "model", "reasoning", "falsifier")} | {
            str(l.get("q", "")).strip().lower() for l in t.get("legs", []) if isinstance(l, dict)}
    except (OSError, ValueError, KeyError, AttributeError):
        return set()


def day(text):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        raise ValueError(text)
    return date.fromisoformat(text)


def check_call(name, c, today=None, placeholders=None):
    today = today or date.today()
    placeholders = template_text() if placeholders is None else placeholders
    if not isinstance(c, dict):
        return ["a call must be a JSON object"]
    errs = [f"missing {k}" for k in REQUIRED if k not in c]
    if errs:
        return errs
    for k in ("id", "author", "model", "provider", "written", "resolve_at", "falsifier", "reasoning"):
        if not isinstance(c[k], str):
            errs.append(f"{k} must be text")
    if errs:
        return errs
    if not re.fullmatch(r"F-\d{4}", c["id"]) or name != f"{c['id']}.json":
        errs.append("id must be F-NNNN and match the file name")
    if c["provider"] not in PROVIDERS:
        errs.append(f"provider must be one of {sorted(PROVIDERS)}")
    for k, n in MIN_LEN.items():
        v = c[k].strip()
        if len(v) < n:
            errs.append(f"{k} must be at least {n} characters (it is {len(v)})")
        elif v.lower() in placeholders:
            errs.append(f"{k} is still the template text")
    try:
        written, resolve = day(c["written"]), day(c["resolve_at"])
    except ValueError:
        errs.append("dates must be YYYY-MM-DD")
        written = resolve = None
    if written:
        if written > today:
            errs.append(f"written ({written}) is in the future")
        if written < LAUNCH:
            errs.append(f"written ({written}) is before the public launch ({LAUNCH}); backdated calls are not accepted")
        if resolve <= written:
            errs.append("resolve_at must be after written")
    legs = c["legs"]
    if not isinstance(legs, list) or not legs:
        errs.append("at least one leg")
        legs = []
    for i, leg in enumerate(legs):
        if not isinstance(leg, dict):
            errs.append(f"leg {i}: must be an object")
            continue
        p, o, q = leg.get("p"), leg.get("o"), leg.get("q")
        if not isinstance(q, str) or len(q.strip()) < MIN_QUESTION:
            errs.append(f"leg {i}: the question must be at least {MIN_QUESTION} characters")
        elif q.strip().lower() in placeholders:
            errs.append(f"leg {i}: the question is still the template text")
        if not check.is_num(p) or not 0.01 <= p <= 0.99:
            errs.append(f"leg {i}: p must be a number from 0.01 to 0.99")
        if o is not None and not (type(o) is int and o in (0, 1)):
            errs.append(f"leg {i}: o must be null, 0 or 1")
        elif o is not None and resolve and resolve > today:
            errs.append(f"leg {i}: has an outcome but resolve_at ({resolve}) has not arrived yet")
    sources = c["sources"]
    if not isinstance(sources, list) or not sources:
        errs.append("at least one https source")
    else:
        for s in sources:
            if not check.real_https_url(s):
                errs.append(f"source {s!r} is not a real https link (a host with a dot, no placeholder)")
    return errs


def load_calls():
    calls, errors = [], []
    placeholders = template_text()
    for path in sorted((ROOT / "calls").glob("*.json")):
        if path.name == "TEMPLATE.json":
            continue
        try:
            c = check.load_json(path)
        except (OSError, ValueError) as e:
            errors.append(f"{path.name}: not valid JSON ({e})")
            continue
        errors += [f"{path.name}: {e}" for e in check_call(path.name, c, placeholders=placeholders)]
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
        sc = check.load_json(house)
        for k in ("resolved", "hit"):
            if not (type(sc.get(k, 0)) is int and sc.get(k, 0) >= 0):
                raise ValueError(f"scorecard.json: {k} must be a whole number of 0 or more")
        if sc.get("brier") is not None and not (check.is_num(sc["brier"]) and 0 <= sc["brier"] <= 1):
            raise ValueError("scorecard.json: brier must be a number from 0 to 1")
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
    try:
        board = scoreboard(calls)
    except (OSError, ValueError) as e:
        print("FAIL", e)
        sys.exit(1)
    (ROOT / "arena").mkdir(exist_ok=True)
    (ROOT / "arena/scores.json").write_text(json.dumps(board, indent=1, allow_nan=False) + "\n")
    print(f"ok: {len(calls)} call(s), {len(board['forecasters'])} forecaster(s) -> arena/scores.json")


if __name__ == "__main__":
    main()
