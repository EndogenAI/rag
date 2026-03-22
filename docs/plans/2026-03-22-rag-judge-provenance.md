# Workplan: Rag Judge Provenance

**Branch**: `research/rag-stress-test-quantization`
**Date**: 2026-03-22
**Orchestrator**: Executive Orchestrator

---

## Objective

This session addresses the provenance failure for `rag-judge.agent.md`. It involves triaging the missing `x-governs:` metadata, fixing the agent file, and verifying the fix via the provenance reporting script and a formal Review gate.

---

## Phase Plan

### Phase 1 — Triage & Fix ⬜
**Agent**: Executive Fleet
**Deliverables**:
- `.github/agents/rag-judge.agent.md` updated with `x-governs:` metadata

**Depends on**: nothing
**CI**: Tests, Auto-validate
**Status**: Not started

### Phase 2 — Review Gate ⬜
**Agent**: Review
**Deliverables**:
- `## Phase 2 Review Output` in scratchpad (Verdict: APPROVED)

**Depends on**: Phase 1
**CI**: Tests, Auto-validate
**Status**: Not started

### Phase 3 — Commit & Verify ⬜
**Agent**: GitHub
**Deliverables**:
- Commit: `fix(agents): add x-governs provenance to rag-judge`
- Provenance report verified green (no "Would annotate" for rag-judge)

**Depends on**: Phase 2
**CI**: Tests, Auto-validate
**Status**: Not started

### Phase 4 — Session close ⬜
**Agent**: Executive Orchestrator
**Deliverables**:
- Fleet integration check (`scripts/check_fleet_integration.py`)
- Session archive and summary
- PR comment update

**Depends on**: Phase 3
**CI**: Tests, Auto-validate
**Status**: Not started

---

## Acceptance Criteria

- [ ] `rag-judge.agent.md` contains a valid `x-governs:` field in its frontmatter.
- [ ] `scripts/annotate_provenance.py --dry-run` returns 0 files to nominate for `rag-judge.agent.md`.
- [ ] Review agent provides an APPROVED verdict.
- [ ] Changes are committed and pushed to the branch.
