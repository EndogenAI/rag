# Workplan: Wave 2 Research Sprint — Endogenic Methodology & Values Encoding

**Date**: 2026-03-07
**Branch**: main
**Slug**: wave2-research-sprint
**Status**: In Progress

---

## Objective

Execute Wave 2 and Wave 3 of the pre-flight research sequence for issue #45 (Research: Product Definition). Wave 2 contains two large, independent research items — endogenic methodology prior art (#9) and values encoding (#32) — both `effort:xl` and `priority:critical`. Wave 3 contains a technical chore — repository settings audit (#31, `effort:unknown`, `priority:medium`).

All three phases are required before issue #45 can be unblocked.

---

## Acceptance Criteria

### Wave 2

- [ ] `docs/research/methodology-review.md` — Status: Final, committed to main
- [ ] `MANIFESTO.md` updated with synthesized insights from #9 (D3)
- [ ] Issue #9 closed
- [ ] `docs/research/values-encoding.md` — Status: Final, committed to main
- [ ] New follow-on issues filed per #32 D7
- [ ] Issue #32 closed (or scoped follow-on issues created if full D9 spans multiple sessions)

### Wave 3

- [ ] Repository settings audit report committed (to scratchpad or dedicated issue comment)
- [ ] Prioritised list of recommended changes posted on issue #31
- [ ] Any Critical/High findings addressed as follow-on sub-issues
- [ ] Issue #31 closed or scoped with follow-on items

---

## Phase Plan

### Phase 1 — Research: Endogenic Methodology Prior Art (#9)

**Agent**: Executive Researcher (→ Research Scout → Synthesizer → Reviewer → Archivist)
**Deliverables**:
- `docs/research/methodology-review.md`, Status: Final
- D2: Summary of what to adopt vs. what is genuinely novel
- D3: `MANIFESTO.md` updates with synthesized insights
- Issue #9 closed

**Depends on**: nothing
**Gate**: Phase 2 may start after Phase 1 complete; no dependency between them

---

### Phase 2 — Research: Verbally Encoding Values (#32)

**Agent**: Executive Researcher (→ Research Scout → Synthesizer → Reviewer → Archivist)
**Deliverables**:
- `docs/research/values-encoding.md`, Status: Final
- Cross-sectoral manifest of authoritative literature (D1)
- Synthesis doc per source (D2s)
- Consolidated synthesis targeting the issue (D3)
- Follow-on research manifest for open questions (D4)
- Updated synthesis incorporating D5 sources (D6)
- New GitHub issues for implementation/next steps (D7s)
- Session lessons learned (D8)
- Updated workflow/docs/agents as appropriate (D9)
- Issue #32 closed (or partially closed if full D9 spans sessions)

**Depends on**: nothing (can run after Phase 1 or in a separate session wave)
**Gate**: Wave 2 complete when both Phases 1 and 2 are confirmed and committed

---

### Phase 3 — Chore: Repository Settings Audit (#31)

**Agent**: Orchestrator (direct) or delegated to security/ops specialist
**Deliverables**:
- Audit report: current vs. recommended settings across all areas
- Prioritised remediation list (Critical / High / Medium / Low)
- Any Critical/High items filed as sub-issues or implemented
- Issue #31 closed

**Depends on**: Phases 1 and 2 (Wave 2) complete
**Gate**: Wave 3 complete after #31 closed or scoped

---

### Phase 4 — Update #45 and Session Close

**Agent**: Orchestrator
**Deliverables**:
- Wave 2 + 3 completion comment posted on #45
- All commits pushed
- Session scratchpad archived

**Depends on**: Phases 1–3

---

## Notes

- Issue #9 and #32 are both `effort:xl` — expect full sessions each
- Issue #32 has a complex multi-deliverable structure (D1–D9) including recursive research and follow-on issue creation
- Issue #31 is a technical chore that can be executed directly (no external research needed)
- Run `/compact` between Phase 1 and Phase 2, and between Phase 2 and Phase 3
- After each phase, update this workplan and the scratchpad
