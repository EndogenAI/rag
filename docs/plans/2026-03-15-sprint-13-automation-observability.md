# Workplan: Sprint 13 — Automation & Behavioral Observability

**Branch**: `feat/sprint-13-automation-observability`
**Milestone**: Sprint 13 — Automation & Behavioral Observability (due 2026-03-29)
**Date**: 2026-03-15
**Orchestrator**: Executive Orchestrator
**Capacity**: M (≤20 effort units) | Sprint total: 18 units

---

## Objective

Sprint 13 advances two parallel tracks. The first track hardens behavioral observability
infrastructure: a GitHub Actions caching research sprint (#221, effort xl) establishes
the canonical patterns for token-efficient Orchestrator orientation, and a paired empirical
baseline study (#231, effort m) produces measured A/B data on encode-before-act vs.
reactive reconstruction. The second track converts those findings into shipped code: the
PREEXEC governor gains subshell audit logging (#157, effort s) and token-spinning detection
(#156, effort s), while a capability-aware agent registry (#158, effort m) provides a
queryable index of fleet tool scopes. Research phases (2, 3) gate their respective
implementation phases (4, 5) per the Sprint Phase Ordering Constraints in AGENTS.md.

---

## Phase Plan

### Phase 1 — Workplan Review ⬜
**Agent**: Review
**Deliverables**:
- APPROVED verdict logged under `## Workplan Review Output` in scratchpad

**Depends on**: nothing
**CI**: n/a
**Status**: Not started

---

### Phase 2 — GitHub Actions Caching Research (#221) ⬜
**Agent**: Executive Researcher → Research Scout → Synthesizer
**Deliverables**:
- `docs/research/ci/github-actions-caching-patterns.md` (D4 format, status: Draft)
- Summary of canonical caching patterns for Orchestrator orientation + PM snapshot workflows
- Committed: `docs(research): GitHub Actions marketplace caching patterns (#221)`

**Depends on**: Phase 1 ✅
**CI**: Tests, Auto-validate
**Status**: Not started

**Acceptance criteria**:
- [ ] D4 doc exists with `title`, `status`, Executive Summary, Pattern Catalog, Recommendations
- [ ] At least 3 canonical caching patterns documented with `**Canonical example**:` labels
- [ ] Closes #221 reference in PR body

---

### Phase 3 — Behavioral Observability Baseline (#231) ⬜
**Agent**: Executive Researcher → Research Scout
**Deliverables**:
- `docs/research/methodology/encode-before-act-baseline.md` (D4 format, status: Draft)
- A/B comparison data: encode-before-act vs. reactive reconstruction (H1 hypothesis)
- Committed: `docs(research): H1 empirical baseline encode-before-act (#231)`

**Depends on**: Phase 1 ✅
**CI**: Tests, Auto-validate
**Status**: Not started

**Acceptance criteria**:
- [ ] D4 doc exists with measurable H1 hypothesis validation or falsification
- [ ] At least 1 `**Anti-pattern**:` and 1 `**Canonical example**:` in Pattern Catalog
- [ ] Closes #231 reference in PR body

---

### Phase 4 — PREEXEC Governor Hardening (#156, #157) ⬜
**Agent**: Executive Scripter
**Deliverables**:
- `scripts/` enhancement: subshell audit logging added to PREEXEC governor hooks (#157)
- `scripts/` enhancement: token-spinning detection and rate-limiting script (#156)
- Tests covering happy path, error cases, exit codes (≥80% coverage each)
- Committed: `feat(scripts): PREEXEC subshell audit logging and token-spin detection (#156, #157)`

**Depends on**: Phase 3 ✅ (observability research informs detection thresholds)
**CI**: Tests, Auto-validate
**Status**: Not started

**Acceptance criteria**:
- [ ] `uv run pytest tests/test_token_spin*.py -q` passes
- [ ] `uv run pytest tests/test_preexec*.py -q` passes (or existing governor tests updated)
- [ ] Both scripts have docstrings with purpose, inputs, outputs, usage example
- [ ] Closes #156 and #157 references in PR body

---

### Phase 5 — Capability-Aware Agent Registry (#158) ⬜
**Agent**: Executive Scripter → Executive Fleet
**Deliverables**:
- `scripts/generate_agent_manifest.py` extended (or new `scripts/agent_registry.py`) to produce a capability-indexed registry
- Registry output queryable by tool scope, agent tier, and area
- Tests (≥80% coverage)
- Committed: `feat(agents): capability-aware agent registry design (#158)`

**Depends on**: Phase 1 ✅ (parallel with Phase 4)
**CI**: Tests, Auto-validate
**Status**: Not started

**Acceptance criteria**:
- [ ] Registry script runs without error: `uv run python scripts/agent_registry.py --list`
- [ ] Output includes at minimum: agent name, tier, tools, area for each fleet member
- [ ] Tests pass with ≥80% coverage
- [ ] Closes #158 reference in PR body

---

### Phase 6 — Review, CHANGELOG & Commit ⬜
**Agent**: Review → GitHub Agent
**Deliverables**:
- Review APPROVED verdict for all phase deliverables
- `CHANGELOG.md` updated under `[Unreleased]` with all sprint additions
- All changes committed and PR opened against `main`
- All 5 sprint issues closed via `Closes #NNN` in PR body

**Depends on**: Phases 2–5 ✅
**CI**: Tests, Auto-validate
**Status**: Not started

**Acceptance criteria**:
- [ ] `gh milestone view 13` shows 5/5 issues closed
- [ ] CI green before review request
- [ ] CHANGELOG has entries for #221, #231, #156, #157, #158

---

## Acceptance Criteria (Sprint-Level)

- [ ] All 6 phases complete and committed
- [ ] All 5 sprint milestone issues closed (gh milestone view 13)
- [ ] CI green: `uv run pytest tests/ -x -m "not slow and not integration" -q`
- [ ] CHANGELOG.md updated with all sprint additions
- [ ] PR opened against `main` with all `Closes #NNN` lines

## PR Description Template

<!-- Copy to PR description when opening the PR -->

## Sprint 13 — Automation & Behavioral Observability

Delivers GitHub Actions caching research, behavioral observability baseline,
PREEXEC governor hardening, token-spinning detection, and capability-aware
agent registry.

Closes #221, Closes #157, Closes #156, Closes #158, Closes #231
