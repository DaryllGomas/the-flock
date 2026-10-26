# The Running Thesis

*The market view behind the Flock Portfolio: dated calls, each with a probability and what would prove it wrong,
graded on their dates. Written by the house (people and AIs together) and open to challenge.*

**As of the close on Fri 2026-10-23.** SPY (an index fund of the 500 biggest US companies) closed at 759.97, about
2.8% under its high of 781.62 on 10/6.

*Open source. Not investment advice. A collaboration of thought.*

---

## The view in one line

**The AI leaders are breaking while the rest of the market holds.** The odds are about even that SPY finishes
Dec 11 above 765, a little higher than today, and a dip on the way is more likely than not.

## What we see

- **The leaders fell, the rest held.** From 9/22 to 10/23 the Nasdaq-100 fund (QQQ) fell 5.8% and some of the
  biggest AI names fell 12% to 20%, while the equal-weight S&P 500 fund (RSP) rose 1.8%. About 59% of a 103-stock
  basket sits above its 50-day average, up from 35%.
- **Credit is no longer calm.** The high-yield bond spread (FRED series BAMLH0A0HYM2) widened from 2.66% to 3.40% in
  a month. Wider spreads mean lenders want more to take risk.
- **The Fed is on hold now, with a hike priced for December.** Fed funds futures price a hold on 10/28 (about 92%)
  and a hike on 12/9 (about 76%).
- **Options are expensive.** The VIX is 19.45 while SPY has actually moved about 9.5% a year over the last 20 days:
  the market is paying for fear that hasn't shown up in prices yet.

## Three paths to Dec 11

| Path | Chance | What happens | Chance SPY is above 765 on Dec 11 on that path |
|---|---|---|---|
| **Dip, then relief** | 42% | The lowest close lands between 700 and 740, then it recovers | 32% |
| **No deep dip** | 42% | No close at or below 740 | 85% |
| **Breakdown** | 16% | A close at or below 700 | 2% |

Put together: about a **49%** chance SPY is above 765 on Dec 11, and a **58%** chance of at least one close at or
below 740 before then.

## What would prove it wrong

- SPY closes above its high (781.62) with broad breadth (60% or more of the basket above its 50-day average) before
  10/30: the dip view is failing.
- The high-yield spread stays above 3.75% for 5 sessions, or the 30-year Treasury yield stays above 5.50% for 5
  closes: the breakdown path gets more likely.
- Microsoft and Alphabet both close up the day after their 10/28 results: the "no deep dip" path gets more likely.

## Open calls

Each call is graded on its date as written. A newer version never edits an old call; it adds a new one.

| Call | Chance | Resolves |
|---|---|---|
| SPY closes at or below 750 at least once between 10/26 and 11/6 | 55% | Fri 11/6 |
| SPY closes at or below 740 at least once before 11/20 | 45% | Fri 11/20 |
| SPY closes above 781.62 (a new high) at least once before 11/20 | 35% | Fri 11/20 |
| SPY is above 760 on 11/20 | 50% | Fri 11/20 |
| SPY is above 765 on 12/11 | 49% | Fri 12/11 |
| The Fed funds target range is within 4.00%–4.50% on 3/12/27 | 78% | 2027-03-12 |
| Bitcoin has a Sunday close above $86,507 before any Sunday close below $74,000, by 11/29 (Coinbase BTC-USD) | 42% | Sun 11/29 |
| Solana has a Sunday close above $111.21 before any Sunday close below $98.94, by 11/29 (Coinbase SOL-USD) | 36% | Sun 11/29 |

## Track record so far

**11 calls graded: 6 hit, 1 partial, 4 missed.** The average Brier score is **0.22** across 22 stated
probabilities. Brier is the squared gap between the stated chance and what happened: 0 is perfect, 0.25 is what
always saying 50% would score, lower is better.

These calls were made from 9/11 to 10/18, before this public repo existed, so their timestamps are our own record.
From launch on, every call is public on the day it's made.

## How to challenge it

Think a number is wrong? Make the case with public sources and your own probability: open an issue or a pull
request on this repo, or point your AI at The Flock's tasks through Swarm AI. A person reviews every contribution.
