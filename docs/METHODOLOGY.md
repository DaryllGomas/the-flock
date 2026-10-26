# Methodology

How research becomes the Flock Portfolio. Everything here is public, and none of it is investment advice.

## 1. The Running Thesis (the market view)
[thesis/THESIS.md](../thesis/THESIS.md): dated calls, each with a probability and what would prove it wrong, graded
on its date. Written by the house (people and AIs together), updated whenever we get to it.

- **Grading:** HIT (right, and the "proven wrong" line never fired), PARTIAL (direction right, level wrong), MISS
  (the "proven wrong" line fired), VOID (the premise changed). Every stated probability also gets a Brier score:
  (probability − outcome)², where the outcome is 1 or 0. Lower is better; 0.25 is a coin flip.
- **No editing the past:** a call is never changed after it's written. A newer view adds new calls, and the old ones
  are still graded as written.

## 2. The Flock Portfolio
One model portfolio, the same for everyone. Defined in [sleeves.json](../portfolio/sleeves.json) and built by
`scripts/build_portfolio.py`:

- **Core:** the whole US market (VTI) gets whatever is left, so it is always the biggest piece.
- **Focused bets:** each research view maps to one plain, liquid vehicle. Weight by conviction: high 10, medium-high
  7, medium 5, watch or avoid 0; a single company counts half. If they add up to more than 35%, they are scaled
  down to fit.
- **Waiting cash:** short-term T-bills (SGOV), set by the Running Thesis: 15% while it gives 55% or better odds of a
  dip before its next horizon, otherwise 0%.
- **Not held, and why:** themes the research avoids, and a watch list, are published too.
- **Caps:** at most 5% in one company, 25% in one sector, 35% in focused bets together, and the core always the
  biggest piece. Rounding to whole percents never breaks the 35% cap.
- **Only reviewed instruments:** every fund or stock must be in [instruments.json](../portfolio/instruments.json),
  which records its type, company, sector, and whether it is leveraged or inverse (those are refused). The checks take
  these facts from the registry, never from labels in the portfolio file.
- **Checked every time:** `scripts/check.py` refuses a portfolio that breaks a rule, and fails if `holdings.json`
  doesn't match a fresh build from `sleeves.json`. `scripts/test_checks.py` tests the checks themselves.
- **Changes:** the portfolio changes only when the research changes. Each change gets a dated line and the reason in
  [changes.json](../portfolio/changes.json) and, once paper trades start, in [LEDGER.md](../portfolio/LEDGER.md).
- **Track record:** starts with the first logged paper trade, shown next to the whole-market fund (VTI) from the
  same day, gains and losses alike.

## 3. Contributions
Anyone can help, person or AI, through GitHub or through Swarm AI ([SWARM.md](SWARM.md)):

| Kind | What it is |
|---|---|
| **Challenge** | A sourced case that a call's probability is wrong, with your own number |
| **Call** | A new dated call with a probability, what would prove it wrong, and sources ([template](../calls/TEMPLATE.json)) |
| **Grade** | Resolving a call on its date from public data, with the closing prices linked |
| **Research** | A write-up on a holding or theme, both sides ([template](../research/theses/TEMPLATE.md)) |

A maintainer reviews every contribution before it is merged. With one maintainer today, the maintainer's own
changes also go through pull requests but are self-reviewed (see CONTRIBUTING.md). Research that holds up can change a view, and
a changed view can change the portfolio, through the same rules.

## Updates
Whenever we get to it: edit the research or the sleeves, run `bash scripts/update.sh` (rebuilds the portfolio and
the site and runs every check), commit, then `scripts/deploy.sh`.
