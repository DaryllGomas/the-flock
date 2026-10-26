# The Flock

**A portfolio for everybody.** One public paper portfolio, built from open research. See what the Flock holds, why,
and what could go wrong.

**Open source. Not investment advice. A collaboration of thought.**

**Live:** https://flock.bigpicsolutions.com

## Why it exists

Closed "investment groups" recruit people with no financial education through DMs, then sell them signals, a
platform or a "teacher". The Flock is the opposite, built on purpose:

| A DM "investment group" | The Flock |
|---|---|
| Invite only, private chat | Public site and repo; anyone can read without an account |
| A guru you can't check | Every holding says why it's held and what could go wrong, with its research |
| Wins shown, losses hidden | Every change is dated and logged in public, losses included |
| Ends with "deposit here" | Never takes money, never links to a broker, never sells anything |
| "Insider tips" | Only public information, including what insiders must file publicly |

## How it works

1. **The Flock Portfolio** is one paper model portfolio, the same for everyone. Most of it is the whole US stock
   market; smaller tilts follow the research; some cash can wait in T-bills when the research expects a dip. Fixed
   rules turn research into weights ([`portfolio/sleeves.json`](portfolio/sleeves.json),
   `scripts/build_portfolio.py`), and `scripts/check.py` refuses a portfolio that breaks a rule.
2. **The Running Thesis** is the market view behind it: dated calls, each with a probability and a falsifier,
   graded on its date ([`thesis/THESIS.md`](thesis/THESIS.md)).
3. **It changes when the research changes**, and every change is logged with the date and the reason. We update it
   in the open whenever we get to it.
4. **Anyone can make it better.** Point your spare AI at The Flock's tasks through
   [Swarm AI](https://swarm.bigpicsolutions.com): challenge a call, test a claim, research a question. Or open an
   issue or a pull request here. Full detail: [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

## What's in this repo

| Path | What |
|---|---|
| [`site/`](site/) | The public page (Portfolio, Research, Changes, Help): plain files, no outside requests, no trackers |
| [`portfolio/`](portfolio/) | `sleeves.json` (research to holdings), `holdings.json` (built), `rules.json`, `changes.json`, `LEDGER.md` |
| [`thesis/`](thesis/) | The Running Thesis: the market view, open calls and the track record |
| [`docs/CHARTER.md`](docs/CHARTER.md) | The hard lines: no money, no advice, public information only, built so it can't be pumped |
| [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) | How research becomes weights, step by step |
| [`docs/SWARM.md`](docs/SWARM.md), [`docs/SEED-ISSUES.md`](docs/SEED-ISSUES.md) | How this plugs into Swarm AI, and the first tasks |
| [`docs/SCAM-SIGNS.md`](docs/SCAM-SIGNS.md) | How the DM "investment group" scam works, for newcomers |
| [`calls/`](calls/), [`research/theses/`](research/theses/) | Contributed calls and research, with templates |
| [`scripts/`](scripts/) | `update.sh` (rebuild and check everything), `deploy.sh`, `build_portfolio.py`, `check.py`, `check_theses.py`, `score.py` |
| [`CONTRIBUTING.md`](CONTRIBUTING.md), [`AGENTS.md`](AGENTS.md) | How people and AI agents take part |

## Run it locally

```bash
bash site/build.sh                      # copy the data into site/data/
python3 -m http.server -d site 8000     # then open http://127.0.0.1:8000
```

## Where it runs

A static site on Cloudflare Workers (assets only: no server code, no database, no cookies), at
flock.bigpicsolutions.com. Deploy: `scripts/deploy.sh` with a Cloudflare token in the environment.

## Licence

Code: MIT ([LICENSE](LICENSE)). Research and docs: CC BY 4.0 ([LICENSE-CONTENT](LICENSE-CONTENT)).

**Not investment advice.** The Flock Portfolio is a paper model, the same for every reader. It knows nothing about
your situation, and nothing here tells you what to buy or sell. Real investments can lose money.
