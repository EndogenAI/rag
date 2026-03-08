---
name: agent-file-authoring
description: |
  Encodes the conventions for authoring .agent.md files in .github/agents/: YAML frontmatter requirements, required section headings, relative path rules, cross-reference density, and CI validation. USE FOR: creating or modifying .agent.md custom agent files; diagnosing validate_agent_files.py CI failures; verifying a draft agent file before committing; scaffolding a new agent from template. DO NOT USE FOR: skill authoring (SKILL.md files use a different format — see the agent-customization skill); general VS Code settings questions; MCP server configuration.
argument-hint: "role slug for the agent (e.g. executive-docs)"
---

# Agent File Authoring

This skill enacts the *Endogenous-First* axiom from [`MANIFESTO.md`](../../MANIFESTO.md): agent files are re-encodings of [`AGENTS.md`](../../AGENTS.md), not independent inventions. Every `.agent.md` file derives its structure, posture, and governing constraints from `AGENTS.md` and `MANIFESTO.md`. Agents re-encode; they do not re-derive. Full authoring guidance is in [`docs/guides/agents.md`](../../docs/guides/agents.md) and the fleet catalog in [`.github/agents/README.md`](../README.md).

---

## 1. File Naming and Location

- **Location**: `.github/agents/<role-slug>.agent.md`
- **Slug format**: kebab-case, lowercase, e.g. `executive-docs`, `research-scout`
- **One file per agent role** — do not combine multiple personas into a single file

Use the scaffold helper to generate a compliant template:

```bash
uv run python scripts/scaffold_agent.py <role-slug>
# Creates: .github/agents/<role-slug>.agent.md
```

---

## 2. YAML Frontmatter

Every agent file must open with YAML frontmatter:

```yaml
---
name: <role name in title case>
description: |
  <≥25 character description — CI enforces minimum length>
---
```

**Field requirements** (enforced by `validate_agent_files.py`):

| Field | Required | Constraint |
|-------|---------|------------|
| `name` | Yes | Non-empty string |
| `description` | Yes | ≥ 25 characters |

The `description` field should be a `|` block for multi-line content. It is consumed by VS Code and GitHub Copilot as the agent's self-description in selection menus.

---

## 3. Required Sections

CI fuzzy-matches for three required section types. Every agent file must contain at least one of each:

| Category | Accepted heading variants |
|----------|--------------------------|
| Endogenous Sources | `Endogenous Sources`, `Sources`, `Reference`, `Context` |
| Action | `Action`, `Workflow`, `Checklist`, `Conventions`, `Instructions`, `Steps` |
| Quality-gate | `Quality-gate`, `Completion Criteria`, `Guardrails`, `Done When`, `Acceptance` |

Use `## Endogenous Sources`, `## Workflow`, and `## Completion Criteria` as the canonical heading names unless you have a specific reason to deviate.

---

## 4. Relative Path Rule

**All references to repo-root files must use `../../` as the prefix** — never `../`.

Agent files live at `.github/agents/<file>.agent.md`. The repo root is two levels up:

```
.github/agents/<file>.agent.md
           │
           ├─ ../   → .github/       ← WRONG
           └─ ../../ → (repo root)   ← CORRECT
```

**Correct**:
```markdown
[`AGENTS.md`](../../AGENTS.md)
[`MANIFESTO.md`](../../MANIFESTO.md)
[`docs/guides/agents.md`](../../docs/guides/agents.md)
```

**Incorrect** (will fail link checks and encoding fidelity audit):
```markdown
[`AGENTS.md`](../AGENTS.md)       ← resolves to .github/AGENTS.md — does not exist
```

---

## 5. Cross-Reference Density

Every agent file must contain at least one back-reference to `../../MANIFESTO.md` **or** `../../AGENTS.md` in the body. CI checks this as a proxy for encoding fidelity.

**Minimum pattern** (place in the first substantive section):

```markdown
This agent is governed by [`AGENTS.md`](../../AGENTS.md) and the foundational axioms
in [`MANIFESTO.md`](../../MANIFESTO.md).
```

Low cross-reference density is a signal of encoding drift — the agent has been authored without grounding in the inheritance chain.

---

## 6. Encoding Inheritance Declaration

The first substantive section of every agent file must name the governing axiom and cite the primary endogenous source. This mirrors the session-start encoding checkpoint pattern:

```markdown
## Endogenous Sources

This agent enacts the *<Axiom Name>* axiom from [`MANIFESTO.md`](../../MANIFESTO.md).
Read [`AGENTS.md`](../../AGENTS.md) before modifying any procedure in this file.
```

Governing axioms by agent type:

| Agent type | Governing axiom |
|------------|----------------|
| Research agents | *Endogenous-First* |
| Scripting / automation agents | *Algorithms Before Tokens* |
| Docs / archival agents | *Endogenous-First* |
| Validation / CI agents | *Algorithms Before Tokens* |
| Executive / orchestration | *Endogenous-First* + *Algorithms Before Tokens* |

---

## 7. No Heredoc Writes

Agent files must not contain `cat >> file << 'EOF'` patterns or inline Python heredoc writes in their workflow steps. CI flags these as failures.

**Why**: Heredocs silently corrupt Markdown content containing backticks or triple-backtick fences when executed through the VS Code terminal tool.

**Instead**: instruct the agent to use `create_file` (new files) or `replace_string_in_file` (edits) — both are safe for Markdown content.

---

## 8. Validate Before Committing

Run the compliance check before every `git commit` that touches agent files:

```bash
# Check a single file
uv run python scripts/validate_agent_files.py .github/agents/<file>.agent.md

# Check all agent files
uv run python scripts/validate_agent_files.py --all
```

The validator enforces:
1. Valid YAML frontmatter (`name`, `description` ≥ 25 chars)
2. Required sections present (fuzzy-matched)
3. At least one cross-reference to `../../MANIFESTO.md` or `../../AGENTS.md`
4. No heredoc patterns

A file that fails validation will also fail CI. Fix all violations before committing.

---

## Guardrails

- **Never use `../` for repo-root references** in agent files — always `../../`.
- **Never omit the cross-reference density check** — at least one `../../MANIFESTO.md` or `../../AGENTS.md` link is required.
- **Never embed heredoc write patterns** in workflow steps.
- Do not add an agent without running `validate_agent_files.py --all` and passing.
- Do not introduce a new governing axiom that is not grounded in an existing `MANIFESTO.md` principle.
