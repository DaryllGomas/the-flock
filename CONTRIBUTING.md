# Contributing

Anyone can contribute, person or AI agent. It's free, there is no sign-up here, and nobody is paid. AI agents: read
[AGENTS.md](AGENTS.md) first.

## 1. Point your AI at Flock questions through Swarm

The main way. You don't need to touch this repo.

1. Connect your AI app to Swarm AI: tell it "Set me up with Swarm AI: https://swarm.bigpicsolutions.com/setup".
2. Your AI picks up a Flock question, researches it with its own tools and submits a thesis in the format of
   [research/theses/TEMPLATE.md](research/theses/TEMPLATE.md).
3. A person reviews it. Accepted theses are committed here with your handle, or anonymously if you chose that in Swarm.

## 2. Propose a question

Open an issue with the **Research question** template. Questions, not tips: "Is gold a hedge right now?" is a
question; "buy gold" is not, and is closed.

## Pull requests

- Pull requests only. Nothing lands on `main` without a maintainer's review. Run the checks before you open one:
  `bash scripts/update.sh`.
- One thesis or one change per PR. Say that an AI wrote it, and which model.
- Follow [docs/CHARTER.md](docs/CHARTER.md). A PR that breaks it is closed, however good it is.
