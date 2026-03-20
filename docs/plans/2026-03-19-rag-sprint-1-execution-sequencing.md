# Workplan: RAG Sprint 1 Execution Sequencing

**Branch**: `sprint/rag-sprint-1-execution-planning`
**Date**: 2026-03-19
**Orchestrator**: Executive Orchestrator

---

## Objective

Convert the merged sprint-planning packet into an executable Sprint 1 delivery sequence for issues #8 and #15-#20, preserving RG4 conditional-release guardrails and explicit gate discipline. This workplan defines the first implementation-planning execution track, aligns issue acceptance criteria to current post-merge evidence state, and prepares a deterministic phase order that avoids re-discovery and cross-artifact drift.

---

## Phase Plan

### Phase 1 — Post-Merge Issue State Alignment ✅
**Agent**: Executive PM
**Deliverables**:
- Verify post-merge state for #8 and #15-#20 against merged planning artifacts.
- Update issue bodies where acceptance criteria or blocker wording drift from post-RG4 re-entry status.
- Add explicit link-outs from each issue to the authoritative planning artifacts for execution kickoff.

**Depends on**: nothing
**CI**: Tests, Auto-validate, Lint
**Status**: Complete

Phase 1 output:
- Issue body alignment completed for #8 and #15-#20 with controlling artifact links.
- Verification command used: `gh issue view <num> --json body`.

### Phase 2 — Execution Dependency and Slice Design ✅
**Agent**: Executive Planner + RAG Specialist
**Deliverables**:
- Define Sprint 1 execution sequence across #16/#17/#18/#19/#20 with explicit dependency graph and gate boundaries.
- Produce a first implementation-planning slice recommendation that respects RG4 conditional-release scope.
- Specify per-phase evidence expectations and rollback checkpoints.
- Explicitly classify #8 and #15 as governance-tracking issues for this pass (not implementation-slice items), with link-outs to controlling planning artifacts.

**Depends on**: Phase 1
**CI**: Tests, Auto-validate, Lint
**Status**: Complete

Phase 2 output:
- [2026-03-19-rag-sprint-1-phase2-dependency-slice.md](./2026-03-19-rag-sprint-1-phase2-dependency-slice.md)

### Phase 3 — Execution Validation Contract ✅
**Agent**: Executive Scripter + Test Coordinator
**Deliverables**:
- Map each execution phase to required validation commands (tests, lint, substrate checks).
- Define pass/fail criteria for boundary safety, drift detection, and fallback readiness during Sprint 1 execution.
- Document CI gating posture for each planned phase.

**Depends on**: Phase 2
**CI**: Tests, Auto-validate, Lint
**Status**: Complete

Phase 3 output:
- [2026-03-19-rag-sprint-1-phase3-validation-contract.md](./2026-03-19-rag-sprint-1-phase3-validation-contract.md)

### Phase 4 — Sprint 1 Kickoff Packet ✅
**Agent**: Executive Docs
**Deliverables**:
- Publish an execution kickoff packet under docs/plans linking sequencing, validation contract, and gate criteria.
- Add supersession note if any prior planning artifact is operationally replaced.
- Ensure cross-artifact state synchronization notes are present where blocker status changed.

**Depends on**: Phase 3
**CI**: Tests, Auto-validate, Lint
**Status**: Complete

Phase 4 draft output:
- [2026-03-19-rag-sprint-1-phase4-kickoff-packet.md](./2026-03-19-rag-sprint-1-phase4-kickoff-packet.md)

### Phase 5 — Commit and Handoff ⬜
**Agent**: Executive Orchestrator + Review
**Deliverables**:
- Fleet integration (if adding new agents/skills: run `uv run python scripts/check_fleet_integration.py --dry-run`)
- Session close (archive session, update scratchpad summary, push branch)
- Confirm final Review verdict is APPROVED for changed planning/governance files.
- Commit and push Sprint 1 execution-sequencing outputs.
- Publish session-end issue progress comments and next-session orientation prompt.

**Depends on**: Phase 4
**CI**: Tests, Auto-validate, Lint
**Status**: Not started

---

## Acceptance Criteria

- [x] Post-merge issue states are synchronized and verifiable by `gh issue view <num> --json body` for #8 and #15-#20, and each body includes link-outs to the controlling artifacts: `docs/plans/2026-03-19-rag-sprint-planning-rg4-reentry-update.md` and `docs/plans/2026-03-19-rag-sprint-1-execution-sequencing.md`.
- [x] Sprint 1 execution sequence is documented with explicit dependencies and phase gates in this file with no placeholder phase names.
- [x] Validation contract includes concrete command-level checks and binary pass/fail signals for each planned phase.
- [x] Kickoff packet is published in `docs/plans/` and linked from all active Sprint 1 issues (#8, #15-#20).
- [ ] Branch is pushed, PR exists, and latest CI checks are green (`gh run list --limit 3`).

## PR Description Template

<!-- Copy to PR description when opening the PR -->

Refs #8
Refs #15
Refs #16
Refs #17
Refs #18
Refs #19
Refs #20
