# Session Synthesis — Inter-Phase Review Gate (2026-03-08)

**Branch**: `feat/review-gate-inter-phase` → merged to `main` as PR #66  
**Scratchpad**: `.tmp/feat-review-gate-inter-phase/2026-03-08.md` (full session record)  
**Sessions**: 4 (2 prior + 2 this date)  
**Issues closed**: #41, #42, #43, #44, #67, #68

---

## What shipped

| Deliverable | Commit |
|---|---|
| Inter-phase Review gate formalised in AGENTS.md, orchestrator, AGENTS (agents dir), workflows.md | `e5d92b5` |
| First Copilot review: 9 comments addressed (heading standardisation, per-phase sequence ordering, YAML scalar, gate table, title casing) | `71d0593` |
| 4 new agent files: A5 Context Architect, B5 Dependency Auditor, D4 Methodology Enforcer, D5 Knowledge Base | `d416bf9` |
| Second Copilot review: 5 comments addressed (gate enforcement wording, Fetch→Check label×2, CI truncation, orchestrator guardrail) | `4444ecf` |

---

## Patterns Identified

### 1. Guardrail label name must match verb order
`Fetch-before-check` shipped in two agent files; the behaviour described was *check first, then optionally fetch*. Correct label: `Check-before-fetch`. Caught only in second review pass.

**Signal for `validate_agent_files.py`**: flag any label where `fetch` precedes `check` in the name but the body says "check cache first."

### 2. Contract heading stated independently → drifts
`## Review Output` is defined in `review.agent.md` but was restated (incorrectly, as `## Phase N Review Output`) in three other files across two review rounds.

**Signal**: headings that enforce a cross-file contract must be defined once and cited by reference. A grep assertion in CI — `! grep -r "Phase N Review Output" .github/` — would catch this cheaply.

### 3. Committed workplan CI field was free text, got truncated
`Auto-...` made it into a committed plan. Workplan's CI field should use a fixed vocabulary templated by `scaffold_workplan.py`.

### 4. Issues not auto-closed on merge
`Closes #N` keywords were absent from PR body and commit messages for #67/#68. Required manual close after merge.

**Signal**: `scaffold_workplan.py` should prompt for linked issue numbers and insert `Closes #N` into the PR description template.

### 5. Two review passes required for one PR
Both rounds caught different instances of the same underlying issue (heading contract drift). A pre-review local grep sweep — e.g. `grep -r "Phase N Review Output\|Fetch-before-check" .github/` — would have caught residual instances before requesting the second review.

---

## Recommended Follow-ups

- [ ] `validate_agent_files.py`: add assertion — no `Fetch-before-check` label anywhere in `.github/`
- [ ] `validate_agent_files.py`: add assertion — no literal `## Phase N Review Output` string
- [ ] `scaffold_workplan.py`: template CI field with fixed vocab (`Tests`, `Auto-validate`, `Lint`)
- [ ] `scaffold_workplan.py`: prompt for linked issue numbers, insert `Closes #N` into PR description template
- [ ] Consider adding a "pre-review sweep" step to the per-phase sequence in `executive-orchestrator.agent.md`
