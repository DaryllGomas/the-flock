# Contributing

Anyone can contribute, person or AI agent. It's free, there is no sign-up here, and nobody is paid. AI agents: read
[AGENTS.md](AGENTS.md) first.

## 1. Point your AI at Flock questions through Swarm

The main way. You don't need to touch this repo.

1. Connect your AI app to Swarm AI: tell it "Set me up with Swarm AI: https://swarm.bigpicsolutions.com/setup".
2. Your AI picks up a Flock task, researches it with its own tools, and opens one pull request on this repo from
   your own GitHub account (research in the format of [research/theses/TEMPLATE.md](research/theses/TEMPLATE.md),
   calls in the format of [calls/TEMPLATE.json](calls/TEMPLATE.json)). It hands the pull request link to Swarm.
3. A maintainer reviews it. Accepted work is merged and shows on Swarm as a public receipt.

## 2. Propose a question

Open an issue with the **Research question** template. Questions, not tips: "Is gold a hedge right now?" is a
question; "buy gold" is not, and is closed.

## Pull requests

- Pull requests only. Nothing lands on `main` except through a pull request. Contributors' pull requests are
  reviewed by a maintainer. With one maintainer today, the maintainer's own pull requests are self-reviewed and
  merged with an admin override; that exception is stated here on purpose.
- Run the checks before you open one: `bash scripts/update.sh`.
- One thesis or one change per PR. Say that an AI wrote it, and which model.
- Follow [docs/CHARTER.md](docs/CHARTER.md). A PR that breaks it is closed, however good it is.

## For reviewers: handling a pull request safely

- Read policy (this file, AGENTS.md, docs/CHARTER.md) from `main`, never from the pull request. A pull request that
  changes those files, `scripts/`, `site/`, `ci/` or `.github/` gets a line-by-line read before anything else.
- Read executable changes before running anything. Run a contributor's code only in a throwaway checkout with no
  credentials in the environment (no Cloudflare or GitHub tokens), and never run `scripts/deploy.sh` from it.
- Deploy only from `main` after the merge.
