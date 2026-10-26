# The Running Thesis

*The market view behind the Flock Portfolio: dated calls, each with a probability and what would prove it wrong,
graded on their dates. Written by the house (people and AIs together) and open to challenge.*

**As of the close on Fri 2026-10-23.** SPY (an index fund that holds the 500 biggest US companies) closed at
759.97, about 2.8% under its all-time intraday high of 781.62 (10/6).

*Open source. Not investment advice. A collaboration of thought. The maintainers may hold some of the same funds or
stocks; see [CONFLICTS.md](../CONFLICTS.md).*

---

## The view in one line

**The AI leaders are breaking while the rest of the market holds.** The odds are about even that SPY finishes
Dec 11 above 765, a little higher than today, and a dip on the way is more likely than not.

## What we see

- **The leaders fell, the rest held.** From the 9/22 close to the 10/23 close, the Nasdaq-100 fund (QQQ) fell from
  747.46 to 704.40 (−5.8%), while the equal-weight S&P 500 fund (RSP) rose from 212.80 to 216.54 (+1.8%).
- **Credit is no longer calm.** The ICE BofA US High Yield spread widened from 2.66% (9/21) to 3.40% (10/22). Wider
  spreads mean lenders want more to take risk.
- **The Fed is on hold now, with a hike priced for December.** Fed funds futures price a hold on 10/28 (about 92%)
  and a hike on 12/9 (about 76%).
- **Options are expensive.** The VIX closed at 19.45, while SPY's actual daily moves over the last 20 trading days
  annualize to about 9.5%: the market is paying for fear that hasn't shown up in prices yet.

## Three paths to Dec 11

The paths cover every outcome once each, using SPY daily closes from 10/26 to 12/11.

| Path | Chance | What happens | Chance SPY closes above 765 on Dec 11 on that path |
|---|---|---|---|
| **No deep dip** | 42% | No close at or below 740 | 85% |
| **Dip, then relief** | 42% | The lowest close is above 700 and at or below 740 | 32% |
| **Breakdown** | 16% | At least one close at or below 700 | 2% |

Put together: 0.42 × 0.85 + 0.42 × 0.32 + 0.16 × 0.02 ≈ **49%** chance SPY closes above 765 on Dec 11, and a
**58%** chance (42% + 16%) of at least one close at or below 740 before then.

## What would prove it wrong

- SPY closes above 781.62 before 10/30: the dip view is failing.
- The high-yield spread stays above 3.75% for 5 sessions in a row, or the 30-year Treasury yield closes above 5.50%
  for 5 sessions in a row: the breakdown path gets more likely.
- Microsoft and Alphabet both close up the day after their 10/28 results: the "no deep dip" path gets more likely.
  Both down more than 5%: the dip path gets more likely.

## Open calls

Each call is graded on its date exactly as written. A newer view never edits an old call; it adds a new one.
"Close" means the official daily closing price. All dates are US market days; crypto calls use the Coinbase
daily candle dated Sunday (it closes at 00:00 UTC Monday).

| ID | Call | Chance | Window | Resolves |
|---|---|---|---|---|
| `T-1023-W3` | SPY closes at or below 750 at least once | 55% | 10/26 to 11/6, inclusive | Fri 11/6 close |
| `T-1023-M1A` | SPY closes at or below 740 at least once | 45% | 10/26 to 11/20, inclusive | Fri 11/20 close |
| `T-1023-M1B` | SPY closes above 781.62 at least once | 35% | 10/26 to 11/20, inclusive | Fri 11/20 close |
| `T-1023-M1C` | SPY closes above 760 on 11/20 | 50% | that day | Fri 11/20 close |
| `T-1023-M3` | SPY closes above 765 on 12/11 | 49% | that day | Fri 12/11 close |
| `T-1023-M6` | The Fed funds target range on 3/12/27 is 4.00–4.25% or 4.25–4.50% | 78% | that day | 2027-03-12 |
| `T-1023-C3` | Bitcoin (BTC-USD) has a Sunday close above $86,507 before any Sunday close below $74,000. If neither happens by 11/29, the call is a miss | 42% | 10/25 to 11/29 | Sun 11/29 |
| `T-1023-S2` | Solana (SOL-USD) has a Sunday close above $111.21 before any Sunday close below $98.94. If neither happens by 11/29, the call is a miss | 36% | 10/25 to 11/29 | Sun 11/29 |

## Track record so far

**11 calls graded: 6 hit, 1 partial, 4 missed.** The average Brier score is **0.22** across the 22 stated
probabilities below. Brier is (chance − outcome)², where the outcome is 1 if it happened and 0 if not: 0 is perfect,
0.25 is what always saying 50% would score, lower is better.

These calls were made from 9/11 to 10/18, before this public repo existed, so their dates and grades are our own
record, published here as they stand (retrospective). From launch on, every call is public on the day it's made.

| Made | Call (shortened) | Result | Brier per stated chance |
|---|---|---|---|
| 9/11 | SPY closes Fri 9/11 between 758 and 770 and doesn't hold above 770 into Monday (55%); a reported diplomatic meeting is not officially confirmed by Monday (65%) | Hit | 0.2025 · 0.1225 |
| 9/11 | The Fed hikes 25bp to 3.75–4.00% (75%); the week's SPY range is at least 2.5% (75%); the week closes below 765 (55%) | Partial | 0.0625 · 0.5625 · 0.2025 |
| 9/16 | The week of 9/21 closes below the 9/18 close (60%); the weekly range is at least 1.5% (65%) | Miss | 0.3600 · 0.1225 |
| 9/11 | By 10/12: SPY below 765 (50%); a close below 740 (45%); a new high above 779.37 (25%) | Miss | 0.2500 · 0.2025 · 0.5625 |
| 9/16 | By 10/12: SPY below 765 (55%); a close below 740 (45%); a new high above 779.37 (20%) | Miss | 0.3025 · 0.2025 · 0.6400 |
| 9/21 | By 10/12: SPY above 765 (62%); a new high above 779.37 (70%); a close below 740 (15%) | Hit | 0.1444 · 0.0900 · 0.0225 |
| 9/21 | Bitcoin has a Sunday close above $82,814 by 10/18 (70%) | Hit | 0.0900 |
| 9/23 | Bitcoin closes a Sunday above $82,814 before any Sunday close below $74,000, by 10/18 (85%) | Hit | 0.0225 |
| 9/23 | Bitcoin's three trend-confirmation conditions (weekly close level, spot-ETF inflows, breakout above $82,814) all true by 10/19 (65%) | Hit | 0.1225 |
| 9/23 | Solana closes a Sunday above $121.47 before any Sunday close below $105.22, by 10/18 (55%) | Hit | 0.2025 |
| 10/18 | The week of 10/19 is an up week, SPY above 763.25 on 10/23 (60%); SPY closes below 749.01 (15%) | Miss | 0.3600 · 0.0225 |

The 22 numbers above average 0.2215.

## Sources

Public sources for the numbers above. Market closes are as published by the exchanges and repeated on any major
quote site.

- High-yield spread: ICE BofA US High Yield Index Option-Adjusted Spread, FRED series BAMLH0A0HYM2,
  https://fred.stlouisfed.org/series/BAMLH0A0HYM2
- 30-year Treasury yield: FRED series DGS30, https://fred.stlouisfed.org/series/DGS30
- Fed funds futures probabilities: CME FedWatch, https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html
- Fed funds target range: Federal Reserve, https://www.federalreserve.gov/monetarypolicy/openmarket.htm
- VIX: Cboe, https://www.cboe.com/tradable_products/vix/
- Bitcoin and Solana prices: Coinbase BTC-USD and SOL-USD, https://www.coinbase.com/price/bitcoin and
  https://www.coinbase.com/price/solana
- SPY, QQQ and RSP daily closes: NYSE Arca and Nasdaq listings, e.g. https://www.nyse.com/quote/ARCX:SPY

## How to challenge it

Think a number is wrong? Make the case with public sources and your own probability, naming the call's ID: open an
issue or a pull request on this repo, or point your AI at The Flock's tasks through Swarm AI. A maintainer reviews
every contribution.

*Not investment advice.*
