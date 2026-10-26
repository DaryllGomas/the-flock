#!/usr/bin/env python3
"""Tests for the integrity checks (stdlib only): python3 scripts/test_checks.py

Builds bad portfolios, calls and theses in memory and asserts each is rejected, and that the committed portfolio passes.
"""
import copy
import sys
import unittest
from datetime import date
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_portfolio  # noqa: E402
import check  # noqa: E402
import check_theses  # noqa: E402
import score  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RULES = check.load_json(ROOT / "portfolio/rules.json")
REG = check.load_json(ROOT / "portfolio/instruments.json")
SLEEVES = check.load_json(ROOT / "portfolio/sleeves.json")
HOLDINGS = check.load_json(ROOT / "portfolio/holdings.json")
TIER = {"core": "core", "cash": "regime", "tilt": "high"}


def entry(name, sector, kind="etf", bucket="tilt", **kw):
    e = {"name": name, "type": kind, "issuer": name, "sector": sector, "bucket": bucket, "gold": sector == "gold",
         "leveraged": False, "inverse": False, "market_cap_usd_min": 5e11 if kind == "stock" else None, "notes": "test"}
    e.update(kw)
    return e


def registry(**extra):
    r = copy.deepcopy(REG)
    r.update(extra)
    return r


def portfolio(reg, weights, **label_overrides):
    """holdings.json in memory: labels are copied from the registry, so only the weights are under test."""
    rows = []
    for t, w in weights:
        e = reg[t]
        row = {"ticker": t, "type": e["type"], "sector": e["sector"], "name": e["name"], "weight": w,
               "tier": TIER[e["bucket"]], "theses": ["test"]}
        row.update(label_overrides.get(t, {}))
        rows.append(row)
    return {"as_of": "2026-10-25", "holdings": rows}


def errors(weights, reg=None, **kw):
    reg = reg or REG
    return check.check(RULES, reg, portfolio(reg, weights, **kw))


def mentions(errs, *words):
    return any(all(w.lower() in e.lower() for w in words) for e in errs)


GOOD = [("VTI", 0.51), ("SMH", 0.07), ("GOOGL", 0.03), ("IAU", 0.07), ("ITA", 0.05), ("NLR", 0.03), ("XLV", 0.03),
        ("BOTZ", 0.03), ("IBIT", 0.03), ("SGOV", 0.15)]


class PortfolioRules(unittest.TestCase):
    def test_harness_baseline_passes(self):
        self.assertEqual(errors(GOOD), [])

    def test_committed_portfolio_passes(self):
        self.assertEqual(check.check(RULES, REG, HOLDINGS), [])
        self.assertEqual(check.check_consistency(RULES, REG, SLEEVES, HOLDINGS), [])

    def test_40_core_and_three_20_tilts(self):
        e = errors([("VTI", 0.40), ("SMH", 0.20), ("ITA", 0.20), ("XLV", 0.20)])
        self.assertTrue(mentions(e, "focused bets", "cap"), e)

    def test_duplicate_googl_rows(self):
        e = errors([("VTI", 0.69), ("GOOGL", 0.04), ("GOOGL", 0.04), ("SGOV", 0.15), ("IAU", 0.08)])
        self.assertTrue(mentions(e, "GOOGL", "more than once"), e)
        self.assertTrue(mentions(e, "Alphabet", "per-company cap"), e)

    def test_two_classes_of_one_company(self):
        reg = registry(GOOG=entry("Alphabet Inc. Class C", "tech", "stock", issuer="Alphabet Inc."))
        e = errors([("VTI", 0.78), ("GOOGL", 0.04), ("GOOG", 0.04), ("SGOV", 0.14)], reg)
        self.assertTrue(mentions(e, "Alphabet", "per-company cap"), e)

    def test_two_gold_funds_10_each(self):
        reg = registry(GLD=entry("Gold fund B", "gold"))
        e = errors([("VTI", 0.60), ("IAU", 0.10), ("GLD", 0.10), ("SGOV", 0.20)], reg)
        self.assertTrue(mentions(e, "gold", "cap"), e)

    def test_unknown_ticker_tqqq_labelled_etf(self):
        labelled = portfolio(registry(TQQQ=entry("ProShares UltraPro QQQ", "tech", leveraged=True)),
                             [("VTI", 0.58), ("SGOV", 0.15), ("IAU", 0.07), ("TQQQ", 0.20)])
        self.assertEqual(labelled["holdings"][3]["type"], "etf")  # the row says etf; the real registry has no TQQQ
        e = check.check(RULES, REG, labelled)
        self.assertTrue(mentions(e, "TQQQ", "not in", "registry"), e)

    def test_leveraged_registry_entry_is_rejected(self):
        reg = registry(TQQQ=entry("ProShares UltraPro QQQ", "tech", leveraged=True))
        e = errors([("VTI", 0.60), ("SGOV", 0.15), ("TQQQ", 0.20), ("IAU", 0.05)], reg)
        self.assertTrue(mentions(e, "TQQQ", "leveraged"), e)

    def test_inverse_registry_entry_is_rejected(self):
        reg = registry(SH=entry("Short fund", "financials", inverse=True))
        e = errors([("VTI", 0.70), ("SGOV", 0.15), ("SH", 0.15)], reg)
        self.assertTrue(mentions(e, "SH", "inverse"), e)

    def test_registry_cannot_hide_a_leveraged_fund_by_flags(self):
        reg = registry(TQQQ=entry("ProShares UltraPro QQQ 3x", "tech"))
        self.assertTrue(mentions(check.check_registry(RULES, reg), "TQQQ", "leveraged"))

    def test_nan_and_infinite_weights(self):
        for bad in (float("nan"), float("inf"), float("-inf"), -0.01, 1.5, True, "0.5", None):
            e = errors([("VTI", bad), ("SGOV", 0.15)])
            self.assertTrue(mentions(e, "VTI", "weight must be"), (bad, e))

    def test_weights_not_summing_to_one(self):
        e = errors([("VTI", 0.50), ("SMH", 0.07), ("SGOV", 0.15)])
        self.assertTrue(mentions(e, "add up to"), e)

    def test_core_smaller_than_a_tilt(self):
        e = errors([("VTI", 0.20), ("SMH", 0.25), ("ITA", 0.10), ("SGOV", 0.45)])
        self.assertTrue(mentions(e, "biggest piece"), e)

    def test_core_smaller_than_the_cash(self):
        e = errors([("VTI", 0.30), ("SGOV", 0.70)])
        self.assertTrue(mentions(e, "biggest piece", "SGOV"), e)

    def test_label_cannot_dodge_the_stock_checks(self):
        # a stock whose row says sector "gold" and type "etf": the registry still treats it as a tech stock
        e = errors([("VTI", 0.77), ("GOOGL", 0.08), ("SGOV", 0.15)],
                   GOOGL={"sector": "gold", "type": "etf"})
        self.assertTrue(mentions(e, "Alphabet", "per-company cap"), e)
        self.assertTrue(mentions(e, "GOOGL", "registry says"), e)

    def test_stock_market_cap_comes_from_the_registry(self):
        reg = registry(TINY=entry("Tiny Inc.", "tech", "stock", market_cap_usd_min=1e8))
        e = errors([("VTI", 0.82), ("TINY", 0.03), ("SGOV", 0.15)], reg)
        self.assertTrue(mentions(e, "TINY", "market cap"), e)

    def test_sector_cap_uses_registry_sectors(self):
        reg = registry(AAA=entry("A", "tech"), BBB=entry("B", "tech"))
        e = errors([("VTI", 0.50), ("SMH", 0.10), ("AAA", 0.10), ("BBB", 0.10), ("SGOV", 0.20)], reg)
        self.assertTrue(mentions(e, "sector tech", "cap"), e)

    def test_wrong_tier_label(self):
        e = errors(GOOD, SMH={"tier": "core"})
        self.assertTrue(mentions(e, "SMH", "tier"), e)

    def test_two_cores_and_missing_thesis(self):
        reg = registry(VOO=entry("S&P 500 fund", "broad", bucket="core"))
        e = errors([("VTI", 0.45), ("VOO", 0.30), ("SGOV", 0.25)], reg)
        self.assertTrue(mentions(e, "exactly one core"), e)
        e = errors(GOOD, SMH={"theses": []})
        self.assertTrue(mentions(e, "SMH", "no thesis"), e)

    def test_bad_registry_rows(self):
        for patch, word in (({"sector": "made-up"}, "sector"), ({"gold": True}, "gold"), ({"bucket": "core"}, "sector"),
                            ({"type": "option"}, "type"), ({"market_cap_usd_min": 1}, "market_cap")):
            bad = entry("Z", "tech")
            bad.update(patch)
            self.assertTrue(check.check_registry(RULES, registry(ZZZ=bad)), patch)


class StrictJson(unittest.TestCase):
    def test_non_finite_and_repeated_keys(self):
        for text in ('{"w": NaN}', '{"w": Infinity}', '{"w": -Infinity}', '{"w": 1e999}', '{"a": 1, "a": 2}'):
            with self.assertRaises(ValueError, msg=text):
                check.loads(text)
        self.assertEqual(check.loads('{"w": 0.5}'), {"w": 0.5})


class Rounding(unittest.TestCase):
    def six_equal(self):
        cfg = {"tier_weight": {"high": 10, "medium": 5}, "single_stock_factor": 0.5, "satellites_max": 35,
               "regime_sleeve": copy.deepcopy(SLEEVES["regime_sleeve"]), "core": copy.deepcopy(SLEEVES["core"]),
               "sleeves": []}
        reg = copy.deepcopy(REG)
        sectors = ["tech", "industrials", "energy-power", "healthcare", "crypto", "materials"]
        for i, sec in enumerate(sectors):
            t = "T" + "ABCDEF"[i]
            reg[t] = entry(f"Fund {t}", sec)
            cfg["sleeves"].append({"id": t, "name": t, "vehicle": t, "type": "etf", "sector": sec, "tier": "high",
                                   "source": "test", "why": "x", "risk": "y"})
        return cfg, reg

    def test_six_equal_high_sleeves_stay_within_35(self):
        raw = {i: Fraction(10) for i in range(6)}
        pts = build_portfolio.allocate_points(raw, 35)
        self.assertLessEqual(sum(pts.values()), 35)
        self.assertEqual(sorted(pts.values()), [5, 6, 6, 6, 6, 6])
        self.assertEqual(sum(round(10 * 35 / 60) for _ in range(6)), 36)  # what plain rounding did

    def test_built_portfolio_passes(self):
        cfg, reg = self.six_equal()
        out = build_portfolio.build(cfg, reg, RULES)
        tilts = round(sum(r["weight"] for r in out["holdings"] if r["tier"] == "high") * 100)
        self.assertLessEqual(tilts, 35)
        self.assertEqual(check.check(RULES, reg, out), [])

    def test_current_weights_are_unchanged(self):
        out = build_portfolio.build(SLEEVES, REG, RULES)
        self.assertEqual([round(r["weight"] * 100) for r in out["holdings"]], [51, 7, 3, 7, 5, 3, 3, 3, 3, 15])

    def test_build_refuses_unregistered_or_mislabelled_vehicle(self):
        for patch in ({"vehicle": "TQQQ"}, {"vehicle": "VTI"}, {"sector": "gold"}, {"type": "stock"}):
            cfg = copy.deepcopy(SLEEVES)
            cfg["sleeves"][0].update(patch)
            with self.assertRaises(build_portfolio.BuildError, msg=str(patch)):
                build_portfolio.build(cfg, REG, RULES)


class Consistency(unittest.TestCase):
    def test_edited_weight_is_caught(self):
        h = copy.deepcopy(HOLDINGS)
        h["holdings"][0]["weight"] = 0.50
        h["holdings"][1]["weight"] = 0.08  # still sums to 1 and passes every rule on its own
        self.assertEqual(check.check(RULES, REG, h), [])
        e = check.check_consistency(RULES, REG, SLEEVES, h)
        self.assertTrue(mentions(e, "VTI", "weight"), e)
        self.assertTrue(mentions(e, "SMH", "weight"), e)

    def test_swapped_ticker_prose_and_extra_rows_are_caught(self):
        h = copy.deepcopy(HOLDINGS)
        h["holdings"][1]["why"] = "edited text"
        self.assertTrue(check.check_consistency(RULES, REG, SLEEVES, h))
        h = copy.deepcopy(HOLDINGS)
        h["holdings"].pop(2)
        self.assertTrue(mentions(check.check_consistency(RULES, REG, SLEEVES, h), "lacks it"))

    def test_date_alone_may_differ(self):
        h = copy.deepcopy(HOLDINGS)
        h["as_of"] = "2030-01-01"
        self.assertEqual(check.check_consistency(RULES, REG, SLEEVES, h), [])

    def test_broken_sleeves_fail_not_crash(self):
        self.assertTrue(check.check_consistency(RULES, REG, {"sleeves": []}, HOLDINGS))


def good_call(**kw):
    c = {"id": "F-0001", "author": "someone", "model": "Claude Sonnet 5.5", "provider": "anthropic",
         "written": "2026-10-26", "resolve_at": "2026-11-06",
         "legs": [{"q": "SPY closes at or below 750 between 10/26 and 11/6", "p": 0.5, "o": None}],
         "falsifier": "SPY closes above 781.62 with broad breadth before 10/30",
         "reasoning": "Credit spreads are widening and the leaders are breaking, but breadth held up, so a dip is "
                      "about as likely as not.",
         "sources": ["https://fred.stlouisfed.org/series/BAMLH0A0HYM2"]}
    c.update(kw)
    return c


class Calls(unittest.TestCase):
    TODAY = date(2026, 10, 27)

    def errs(self, **kw):
        return score.check_call("F-0001.json", good_call(**kw), today=self.TODAY, placeholders=score.template_text())

    def test_good_call_passes(self):
        self.assertEqual(self.errs(), [])

    def test_template_itself_is_rejected(self):
        t = check.load_json(ROOT / "calls/TEMPLATE.json")
        t["written"], t["resolve_at"] = "2026-10-26", "2026-11-06"
        self.assertTrue(score.check_call("F-0000.json", t, today=self.TODAY))

    def test_backdated_future_and_order(self):
        self.assertTrue(mentions(self.errs(written="2026-10-24"), "backdated"))
        self.assertTrue(mentions(self.errs(written="2026-10-28"), "future"))
        self.assertTrue(mentions(self.errs(resolve_at="2026-10-26"), "after written"))
        self.assertTrue(self.errs(written="20261026"))

    def test_empty_fields(self):
        for k in ("model", "reasoning", "falsifier", "author"):
            self.assertTrue(self.errs(**{k: ""}), k)
            self.assertTrue(self.errs(**{k: "  x "}), k)

    def test_bad_sources(self):
        for s in ("https://...", "https://localhost/x", "https://nodot/x", "http://fred.stlouisfed.org/x",
                  "https://user:pw@fred.stlouisfed.org/x", "https://10.0.0.1/x", "https://example.com/x", "not a link"):
            self.assertTrue(mentions(self.errs(sources=[s]), "source"), s)
        self.assertTrue(self.errs(sources=[]))
        self.assertTrue(self.errs(sources=["https://fred.stlouisfed.org/x", "https://..."]))

    def test_outcome_only_after_resolve_date(self):
        early = [{"q": "SPY closes at or below 750 between 10/26 and 11/6", "p": 0.5, "o": 1}]
        self.assertTrue(mentions(self.errs(legs=early), "not arrived"))
        done = score.check_call("F-0001.json", good_call(legs=early), today=date(2026, 11, 7), placeholders=set())
        self.assertEqual(done, [])
        for o in (True, 1.0, 2, "1"):
            early[0]["o"] = o
            self.assertTrue(self.errs(legs=early), o)

    def test_bad_probabilities(self):
        for p in (0, 1, float("nan"), True, "0.5", None):
            leg = [{"q": "SPY closes at or below 750 between 10/26 and 11/6", "p": p, "o": None}]
            self.assertTrue(self.errs(legs=leg), p)


GOOD_THESIS = """# T
*Open source. Not investment advice.*
## Open calls
| ID | Call | Chance |
|---|---|---|
| `T-1023-W3` | SPY at or below 750 | 55% |
| F-2026-10-25-2 | SPY above 760 | 50% |
## Sources
- FRED, https://fred.stlouisfed.org/series/DGS30
## How to challenge it
"""


class Theses(unittest.TestCase):
    def test_good_thesis(self):
        self.assertEqual(check_theses.check_thesis(GOOD_THESIS), [])

    def test_committed_thesis_passes(self):
        self.assertEqual(check_theses.check_thesis((ROOT / "thesis/THESIS.md").read_text(encoding="utf-8")), [])

    def test_missing_pieces(self):
        no_sources = GOOD_THESIS.replace("## Sources", "## Notes")
        self.assertTrue(mentions(check_theses.check_thesis(no_sources), "Sources"))
        no_link = GOOD_THESIS.replace("https://fred.stlouisfed.org/series/DGS30", "see FRED")
        self.assertTrue(mentions(check_theses.check_thesis(no_link), "source link"))
        fake_link = GOOD_THESIS.replace("https://fred.stlouisfed.org/series/DGS30", "https://...")
        self.assertTrue(check_theses.check_thesis(fake_link))
        no_advice = GOOD_THESIS.replace("Not investment advice", "Just a thesis")
        self.assertTrue(mentions(check_theses.check_thesis(no_advice), "advice"))

    def test_open_calls_need_ids(self):
        no_id = GOOD_THESIS.replace("`T-1023-W3`", "SPY dips")
        self.assertTrue(mentions(check_theses.check_thesis(no_id), "call ID"))
        bad_form = GOOD_THESIS.replace("`T-1023-W3`", "`t-1023-w3`")
        self.assertTrue(mentions(check_theses.check_thesis(bad_form), "call ID"))
        bad_date = GOOD_THESIS.replace("F-2026-10-25-2", "F-2026-13-45-2")
        self.assertTrue(mentions(check_theses.check_thesis(bad_date), "call ID"))
        dup = GOOD_THESIS.replace("F-2026-10-25-2", "T-1023-W3")
        self.assertTrue(mentions(check_theses.check_thesis(dup), "twice"))
        no_rows = GOOD_THESIS.split("| `T-1023")[0] + "## Sources\n- https://fred.stlouisfed.org/x\n"
        self.assertTrue(mentions(check_theses.check_thesis(no_rows), "no rows"))
        no_table = GOOD_THESIS.replace("## Open calls", "## Other")
        self.assertTrue(mentions(check_theses.check_thesis(no_table), "Open calls"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
