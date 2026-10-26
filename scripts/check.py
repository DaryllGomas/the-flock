#!/usr/bin/env python3
"""Check the Flock Portfolio against portfolio/rules.json and the reviewed registry portfolio/instruments.json.

    python3 scripts/check.py                  # the rules, then: holdings.json is exactly what sleeves.json builds
    python3 scripts/check.py --rules-only     # the rules only (skip the sleeves comparison)
    python3 scripts/check.py --json FILE...   # only prove each file is strict JSON (used by site/build.sh)

Exits 1 on any broken rule. Everything that decides a rule (type, issuer, sector, bucket, leverage, market cap) comes
from the REGISTRY, never from labels in holdings.json, so a contributor cannot dodge a cap by relabelling a row.
This module also holds the strict JSON loader and the URL check that the other scripts share.
"""
import ipaddress
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
EPS = 1e-9
TICKER = re.compile(r"[A-Z][A-Z0-9.\-]{0,9}")
LEVERAGE_WORDS = re.compile(r"leverag|inverse|\b[23]x\b|-[123]x\b|ultrapro|ultrashort|\bbear\b", re.I)
REGISTRY_KEYS = {"name", "type", "issuer", "sector", "bucket", "gold", "leveraged", "inverse", "market_cap_usd_min", "notes"}
BUCKETS = ("core", "cash", "tilt")
TIER_FOR_BUCKET = {"core": "core", "cash": "regime"}


# ---------- strict JSON: no NaN/Infinity (browsers cannot parse them), no out-of-range numbers, no duplicate keys

def _reject_constant(name):
    raise ValueError(f"{name} is not valid JSON (browsers cannot parse it)")


def _finite_float(text):
    value = float(text)
    if not math.isfinite(value):
        raise ValueError(f"number out of range: {text}")
    return value


def _no_duplicate_keys(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate key {key!r}")
        out[key] = value
    return out


def loads(text):
    return json.loads(text, parse_constant=_reject_constant, parse_float=_finite_float,
                      object_pairs_hook=_no_duplicate_keys)


def load_json(path):
    path = Path(path)
    try:
        return loads(path.read_text(encoding="utf-8"))
    except ValueError as e:  # includes JSONDecodeError and UnicodeDecodeError
        raise ValueError(f"{path.name}: {e}") from None


def is_num(x):
    """A real, finite JSON number (not a bool)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return False
    try:
        return math.isfinite(x)
    except OverflowError:
        return False


def real_https_url(s):
    """True only for a plausible public https link: a real dotted host, no credentials, no placeholder like https://..."""
    if not isinstance(s, str) or re.search(r"\s", s):
        return False
    try:
        u = urlsplit(s)
        u.port  # raises ValueError on a bad port
    except ValueError:
        return False
    if u.scheme != "https" or u.username is not None or u.password is not None:
        return False
    host = (u.hostname or "").lower()
    labels = host.split(".")
    if len(labels) < 2 or not all(re.fullmatch(r"[a-z0-9]([a-z0-9-]*[a-z0-9])?", x) for x in labels):
        return False
    if not re.fullmatch(r"[a-z]{2,}|xn--[a-z0-9-]+", labels[-1]):
        return False
    if labels[-1] in {"local", "localhost", "internal", "invalid", "example", "test"}:
        return False
    if labels[-2:] in (["example", "com"], ["example", "org"], ["example", "net"]):
        return False
    try:
        ipaddress.ip_address(host)
        return False
    except ValueError:
        return True


# ---------- the rules and the registry themselves

def check_rules(rules):
    errors = []
    if not isinstance(rules, dict):
        return ["rules.json must be an object"]
    for k in ("max_weight_stock", "max_weight_sector", "max_weight_gold", "max_tilts"):
        if not is_num(rules.get(k)) or not 0 < rules[k] <= 1:
            errors.append(f"rules.json: {k} must be a number above 0 and at most 1")
    if not is_num(rules.get("min_market_cap_usd")) or rules["min_market_cap_usd"] <= 0:
        errors.append("rules.json: min_market_cap_usd must be a positive number")
    for k in ("allowed_types", "allowed_sectors"):
        v = rules.get(k)
        if not isinstance(v, list) or not v or not all(isinstance(x, str) and x for x in v):
            errors.append(f"rules.json: {k} must be a non-empty list of text")
    if not isinstance(rules.get("remainder_to"), str) or not rules.get("remainder_to"):
        errors.append("rules.json: remainder_to must name the core ticker")
    return errors


def instruments(registry):
    """The registry's rows (everything except the underscore notes)."""
    return {k: v for k, v in registry.items() if not k.startswith("_")} if isinstance(registry, dict) else {}


def registry_entry_errors(t, e, rules):
    p = f"registry {t}"
    if not isinstance(t, str) or not TICKER.fullmatch(t):
        return [f"{p}: not a valid ticker"]
    if not isinstance(e, dict):
        return [f"{p}: must be an object"]
    errors = []
    if set(e) != REGISTRY_KEYS:
        errors.append(f"{p}: fields must be exactly {sorted(REGISTRY_KEYS)}")
        return errors
    for k in ("name", "issuer", "notes"):
        if not isinstance(e[k], str) or not e[k].strip():
            errors.append(f"{p}: {k} must be non-empty text")
    if e["type"] not in rules["allowed_types"]:
        errors.append(f"{p}: type {e['type']!r} is not an allowed type")
    if e["sector"] not in rules["allowed_sectors"]:
        errors.append(f"{p}: sector {e['sector']!r} is not on the fixed sector list")
    if e["bucket"] not in BUCKETS:
        errors.append(f"{p}: bucket must be one of {BUCKETS}")
    for k in ("gold", "leveraged", "inverse"):
        if not isinstance(e[k], bool):
            errors.append(f"{p}: {k} must be true or false")
    if errors:
        return errors
    if e["type"] == "stock":
        if not is_num(e["market_cap_usd_min"]) or e["market_cap_usd_min"] <= 0:
            errors.append(f"{p}: a stock needs market_cap_usd_min, a positive lower bound")
    elif e["market_cap_usd_min"] is not None:
        errors.append(f"{p}: only stocks have market_cap_usd_min (use null)")
    if e["gold"] != (e["sector"] == "gold"):
        errors.append(f"{p}: gold must be true exactly when the sector is gold")
    wanted = {"core": "broad", "cash": "cash"}.get(e["bucket"])
    if wanted and e["sector"] != wanted:
        errors.append(f"{p}: a {e['bucket']} instrument must have sector {wanted!r}")
    if not wanted and e["sector"] in ("broad", "cash"):
        errors.append(f"{p}: sector {e['sector']!r} is only for the core and cash buckets")
    if e["bucket"] in ("core", "cash") and e["type"] != "etf":
        errors.append(f"{p}: the core and cash instruments must be ETFs")
    if LEVERAGE_WORDS.search(e["name"]) and not (e["leveraged"] or e["inverse"]):
        errors.append(f"{p}: the name describes a leveraged or inverse fund but the flags say no")
    return errors


def check_registry(rules, registry):
    if not isinstance(registry, dict):
        return ["instruments.json must be an object keyed by ticker"]
    errors = []
    for t, e in instruments(registry).items():
        errors += registry_entry_errors(t, e, rules)
    return errors


# ---------- the holdings against the rules

def check(rules, registry, holdings):
    errors = check_rules(rules)
    if errors:
        return errors
    errors = check_registry(rules, registry)
    reg = {t: e for t, e in instruments(registry).items() if not registry_entry_errors(t, e, rules)}
    rows = holdings.get("holdings") if isinstance(holdings, dict) else None
    if not isinstance(rows, list) or not rows:
        return errors + ["holdings.json has no holdings"]

    total = 0.0
    seen = set()
    placed = []  # (ticker, weight, bucket)
    sector_w, issuer_w = defaultdict(float), defaultdict(float)
    gold_w, gold_names, tilts = 0.0, [], 0.0
    for i, h in enumerate(rows):
        if not isinstance(h, dict) or not isinstance(h.get("ticker"), str):
            errors.append(f"holding #{i + 1}: needs a ticker")
            continue
        t, w = h["ticker"], h.get("weight")
        if not is_num(w) or not 0 <= w <= 1:
            errors.append(f"{t}: weight must be a finite number from 0 to 1 (got {w!r}; negative would be shorting)")
            continue
        total += w
        if t in seen:
            errors.append(f"{t}: listed more than once (one row per ticker)")
        seen.add(t)
        e = reg.get(t)
        if e is None:
            errors.append(f"{t}: not in portfolio/instruments.json, the reviewed registry (unknown or invalid entry)")
            continue
        placed.append((t, w, e["bucket"]))
        if e["leveraged"] or e["inverse"]:
            errors.append(f"{t}: leveraged and inverse funds are banned")
        if e["type"] not in rules["allowed_types"]:
            errors.append(f"{t}: type {e['type']} is not allowed")
        for label in ("type", "sector"):
            if h.get(label) != e[label]:
                errors.append(f"{t}: holdings.json says {label} {h.get(label)!r} but the registry says {e[label]!r}")
        want_tier = TIER_FOR_BUCKET.get(e["bucket"])
        if (want_tier and h.get("tier") != want_tier) or (not want_tier and h.get("tier") in TIER_FOR_BUCKET.values()):
            errors.append(f"{t}: tier {h.get('tier')!r} does not fit its registry bucket {e['bucket']!r}")
        if e["bucket"] != "core" and not (isinstance(h.get("theses"), list) and h["theses"]
                                          and all(isinstance(x, str) and x.strip() for x in h["theses"])):
            errors.append(f"{t}: no thesis linked")
        if e["bucket"] == "tilt":
            tilts += w
            sector_w[e["sector"]] += w
        if e["type"] == "stock":
            issuer_w[e["issuer"]] += w
            if not is_num(e["market_cap_usd_min"]) or e["market_cap_usd_min"] < rules["min_market_cap_usd"]:
                errors.append(f"{t}: market cap under the minimum or missing in the registry")
        if e["gold"]:
            gold_w += w
            gold_names.append(t)

    if abs(total - 1.0) > 1e-6:
        errors.append(f"weights add up to {total:.4f}, not 1")
    core = [(t, w) for t, w, b in placed if b == "core"]
    cash = [t for t, _, b in placed if b == "cash"]
    if len(core) != 1:
        errors.append(f"need exactly one core holding (the registry's core instrument), found {len(core)}")
    else:
        ct, cw = core[0]
        if ct != rules["remainder_to"]:
            errors.append(f"the core must be {rules['remainder_to']}, not {ct}")
        biggest = max(((w, t) for t, w, b in placed if b != "core"), default=None)
        if biggest and biggest[0] >= cw - EPS:
            errors.append(f"the core {ct} ({cw:.2%}) must be the biggest piece, but {biggest[1]} is {biggest[0]:.2%}")
    if len(cash) > 1:
        errors.append(f"at most one waiting-cash holding, found {cash}")
    if tilts > rules["max_tilts"] + EPS:
        errors.append(f"focused bets add up to {tilts:.2%}, over the {rules['max_tilts']:.0%} cap")
    for s, w in sector_w.items():
        if w > rules["max_weight_sector"] + EPS:
            errors.append(f"sector {s}: {w:.2%} over the {rules['max_weight_sector']:.0%} sector cap")
    for who, w in issuer_w.items():
        if w > rules["max_weight_stock"] + EPS:
            errors.append(f"{who}: {w:.2%} in one company, over the {rules['max_weight_stock']:.0%} per-company cap")
    if gold_w > rules["max_weight_gold"] + EPS:
        errors.append(f"gold ({', '.join(gold_names)}): {gold_w:.2%} over the {rules['max_weight_gold']:.0%} gold cap")
    return errors


# ---------- holdings.json must be exactly what sleeves.json builds

def _canon(x):
    return json.dumps(x, sort_keys=True)


def check_consistency(rules, registry, sleeves, holdings):
    import build_portfolio  # here, not at the top: build_portfolio imports this module
    try:
        expected = build_portfolio.build(sleeves, registry, rules)
    except Exception as e:  # a malformed sleeves.json is a failed check, not a traceback
        return [f"sleeves.json does not build: {e.__class__.__name__}: {e}"]
    if not isinstance(holdings, dict) or not isinstance(holdings.get("holdings"), list):
        return ["holdings.json has no holdings to compare"]
    expected["as_of"] = holdings.get("as_of")  # the date is the one thing allowed to differ
    errors = []
    want = {r["ticker"]: r for r in expected["holdings"]}
    got = {r.get("ticker"): r for r in holdings["holdings"] if isinstance(r, dict)}
    for t in want.keys() - got.keys():
        errors.append(f"{t}: sleeves.json builds this holding but holdings.json lacks it")
    for t in got.keys() - want.keys():
        errors.append(f"{t}: holdings.json has this holding but sleeves.json does not build it")
    for t in want.keys() & got.keys():
        if want[t]["weight"] != got[t].get("weight"):
            errors.append(f"{t}: holdings.json has weight {got[t].get('weight')!r}, sleeves.json builds {want[t]['weight']!r}")
    if not errors and _canon(expected) != _canon(holdings):
        errors.append("holdings.json differs from what sleeves.json builds (text, order or other fields)")
    if errors:
        errors.append("holdings.json is generated: run python3 scripts/build_portfolio.py, review and commit it")
    return errors


def main(argv):
    if argv[:1] == ["--json"]:
        bad = 0
        for f in argv[1:]:
            try:
                load_json(f)
            except (OSError, ValueError) as e:
                print("FAIL", e)
                bad += 1
        if not argv[1:]:
            print("FAIL --json needs at least one file")
            return 1
        return 1 if bad else 0
    try:
        rules = load_json(ROOT / "portfolio/rules.json")
        registry = load_json(ROOT / "portfolio/instruments.json")
        holdings = load_json(ROOT / "portfolio/holdings.json")
        sleeves = None if "--rules-only" in argv else load_json(ROOT / "portfolio/sleeves.json")
    except (OSError, ValueError) as e:
        print("FAIL", e)
        return 1
    errors = check(rules, registry, holdings)
    if sleeves is not None:
        errors += check_consistency(rules, registry, sleeves, holdings)
    for e in errors:
        print("FAIL", e)
    if errors:
        return 1
    n = len(holdings["holdings"])
    print(f"ok: {n} holding(s) within the rules" + ("" if sleeves is None else ", and holdings.json matches sleeves.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
