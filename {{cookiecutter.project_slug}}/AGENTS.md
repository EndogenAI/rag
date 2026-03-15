# AGENTS.md — Deployment Layer Governance Notice

This repository is a fork of [EndogenAI/dogma](https://github.com/EndogenAI/dogma).

See the upstream [AGENTS.md](https://github.com/EndogenAI/dogma/blob/main/AGENTS.md) for full
operational constraints and guiding axioms. When you run the adoption wizard it copies a
full `AGENTS.md` into this directory — replace this notice once that step is complete.

## Deployment Layer

This fork specializes dogma's Core Layer axioms for `{{ cookiecutter.project_name }}`.
Before any first action, agents **must** read `client-values.yml` — the Deployment Layer
file that encodes this project's mission, priorities, and axiom emphasis.

Deployment Layer constraints may **not** override MANIFESTO.md Core Layer constraints
(Endogenous-First, Algorithms Before Tokens, Local Compute-First). They may only
specialize or add priorities.

## Quickstart

```bash
# Install dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install
uv run pre-commit install --hook-type pre-push

# Run validation
uv run pre-commit run --all-files
uv run pytest tests/ -m "not slow and not integration" -q
```

## Upstream governance

To pull in upstream dogma governance improvements:

```bash
git remote add dogma https://github.com/EndogenAI/dogma.git
git fetch dogma
```

Refer to the upstream [Product Fork Initialization Guide](https://github.com/EndogenAI/dogma/blob/main/docs/guides/product-fork-initialization.md)
for the full initialization and sync workflow.
