# dogma-governance

Standalone governance validators extracted from the [dogma](https://github.com/EndogenAI/dogma) template repository. Zero dogma-internal imports — install anywhere.

## Install

```bash
pip install dogma-governance
# or
uv add dogma-governance --dev
```

## Pre-commit Integration

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/EndogenAI/dogma-governance
    rev: v0.1.0
    hooks:
      - id: validate-agent-files
      - id: validate-synthesis
      - id: detect-drift
      - id: no-heredoc-writes
      - id: no-terminal-file-io-redirect
```

## CLI Usage

### Validate agent files

```bash
# Validate one or more .agent.md files
dogma-validate-agent .github/agents/my-agent.agent.md

# Validate all agents + skills in current repo
dogma-validate-agent --all
```

### Validate synthesis documents

```bash
# Validate a D4 issue synthesis
dogma-validate-synthesis docs/research/my-topic.md

# Validate a D3 per-source synthesis
dogma-validate-synthesis docs/research/sources/my-source.md
```

### Check value-encoding drift

```bash
# JSON report (default)
dogma-detect-drift

# Human-readable summary, fail if any agent scores below 0.5
dogma-detect-drift --format summary --fail-below 0.5
```

### Full health check

```bash
# Scan current directory for agent + synthesis files
dogma-check-health

# JSON output, specific directory
dogma-check-health --directory /path/to/repo --format json
```

## Security Model

- **Zero dogma-internal dependencies** — no imports from the dogma repo's `scripts/` directory.
- **No network calls** — all checks are purely file-based and regex-based; no HTTP requests.
- **Standalone validation** — can be installed into any Python project without depending on the dogma repo being present.
- **git usage** — `dogma-validate-synthesis` uses `git diff` to detect Final-status doc modifications; this is the only subprocess call and requires git to be installed (gracefully skipped if absent).
