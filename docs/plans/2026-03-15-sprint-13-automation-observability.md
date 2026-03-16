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
the canonical patterns for token-efficient Orchestrator orientation and PM workflows, and
is cross-cutting — it informs both Phase 4 (token-spinning detection thresholds and
PREEXEC audit logging concepts) and Phase 5 (capability-aware agent registry design). A
paired empirical baseline study (#231, effort m) produces measured A/B data on
encode-before-act vs. reactive reconstruction and gates Phase 4 specifically. The second
track converts those findings into shipped code: the PREEXEC governor gains subshell audit
logging (#157) and token-spinning detection (#156), while a capability-aware agent registry
(#158) provides a queryable index of fleet tool scopes. Phase 2 (cross-cutting) and Phase
3 (phase-specific, gates Phase 4) both gate implementation, per Sprint Phase Ordering
Constraints in AGENTS.md.

---

## Phase Plan

### Phase 1 — Workplan Review ⬜
**Agent**: Review
**Deliverables**:
- APPROVED verdict logged under `## Workplan Review Output` in scratchpad

**Depends on**: nothing
**CI**: n/a
**Status**: Complete

---

### Phase 2 — GitHub Actions Caching Research (#221) ⬜
**Agent**: Executive Researcher → Research Scout → Synthesizer
**Deliverables**:
- `docs/research/ci/github-actions-caching-patterns.md` (D4 format, status: Draft)
- Summary of canonical caching patterns for Orchestrator orientation + PM snapshot workflows
- Committed: `docs(research): GitHub Actions marketplace caching patterns (#221)`

**Depends on**: Phase 1 ✅
**CI**: Tests, Auto-validate
**Status**: Complete

**Acceptance criteria**:
- [x] D4 doc exists with `title`, `status`, Executive Summary, Pattern Catalog, Recommendations
- [x] At least 3 canonical caching patterns documented with `**Canonical example**:` labels
- [x] Closes #221 reference in PR body

---

### Phase 3 — Behavioral Observability Baseline (#231) ⬜
**Agent**: Executive Researcher → Research Scout
**Deliverables**:
- `docs/research/methodology/encode-before-act-baseline.md` (D4 format, status: Draft)
- A/B comparison data: encode-before-act vs. reactive reconstruction (H1 hypothesis)
- Committed: `docs(research): H1 empirical baseline encode-before-act (#231)`

**Depends on**: Phase 1 ✅
**CI**: Tests, Auto-validate
**Status**: Complete

**Acceptance criteria**:
- [x] D4 doc exists with measurable H1 hypothesis validation or falsification
- [x] At least 1 `**Anti-pattern**:` and 1 `**Canonical example**:` in Pattern Catalog
- [x] Closes #231 reference in PR body

---

### Phase 4 — PREEXEC Governor Hardening (#156, #157) ⬜
**Agent**: Executive Scripter
**Deliverables**:
- `scripts/` enhancement: subshell audit logging added to PREEXEC governor hooks (#157)
- `scripts/` enhancement: token-spinning detection and rate-limiting script (#156)
- Tests covering happy path, error cases, exit codes (≥80% coverage each)
- Committed: `feat(scripts): PREEXEC subshell audit logging and token-spin detection (#156, #157)`

**Depends on**: Phase 2 ✅ (caching/orientation patterns inform detection concepts), Phase 3 ✅ (observability baseline informs detection thresholds)
**CI**: Tests, Auto-validate
**Status**: Complete

**Acceptance criteria**:
- [x] `uv run pytest tests/test_token_spin*.py -q` passes
- [x] `uv run pytest tests/test_preexec*.py -q` passes (or existing governor tests updated)
- [x] Both scripts have docstrings with purpose, inputs, outputs, usage example
- [x] Closes #156 and #157 references in PR body

---

### Phase 5 — Capability-Aware Agent Registry (#158) ⬜
**Agent**: Executive Scripter → Executive Fleet
**Deliverables**:
- `scripts/generate_agent_manifest.py` extended (or new `scripts/agent_registry.py`) to produce a capability-indexed registry
- Registry output queryable by tool scope, agent tier, and area
- Tests (≥80% coverage)
- Committed: `feat(agents): capability-aware agent registry design (#158)`

**Depends on**: Phase 1 ✅, Phase 2 ✅ (GH Actions caching patterns inform registry capability model)
**CI**: Tests, Auto-validate
**Status**: Complete

**Acceptance criteria**:
- [x] Registry script runs without error: `uv run python scripts/agent_registry.py --list`
- [x] Output includes at minimum: agent name, tier, tools, area for each fleet member
- [x] Tests pass with ≥80% coverage
- [x] Closes #158 reference in PR body

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
**Status**: Complete

**Acceptance criteria**:
- [x] `gh milestone view 13` shows 5/5 issues closed
- [x] CI green before review request
- [x] CHANGELOG has entries for #221, #231, #156, #157, #158

---

## Acceptance Criteria (Sprint-Level)

- [x] All 6 phases complete and committed
- [x] All 5 sprint milestone issues closed (gh milestone view 13)
- [x] CI green: `uv run pytest tests/ -x -m "not slow and not integration" -q`
- [x] CHANGELOG.md updated with all sprint additions
- [x] PR opened against `main` with all `Closes #NNN` lines

## PR Description Template

<!-- Copy to PR description when opening the PR -->

## Sprint 13 — Automation & Behavioral Observability

Delivers GitHub Actions caching research, behavioral observability baseline,
PREEXEC governor hardening, token-spinning detection, and capability-aware
agent registry.

Closes #221, Closes #157, Closes #156, Closes #158, Closes #231
