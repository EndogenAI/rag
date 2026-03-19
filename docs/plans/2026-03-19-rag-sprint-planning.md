# RAG Sprint Planning Workplan (Issues #15-#20 with #8 pilot hold)

## Sprint Objective
Produce an evidence-backed planning contract for the next RAG architecture sprint, resolving open research questions in #15-#20 while preserving a strict implementation hold until #8 pilot evidence is reviewed and approved.

## Scope Snapshot
- Research epic: #15
- Sub-issues: #16, #17, #18, #19, #20
- Pilot hold issue: #8
- Decision constraints fixed at sprint start:
  - 1C: neutral architecture baseline
  - 2C: balanced freshness/stability
  - 3B: recommended-by-default with light checks
  - 4C: hybrid separation (default separate, optional federation)
- Sprint cadence rule: every domain phase is followed by a Review gate with APPROVED verdict before the next domain phase begins.

## Source-of-Truth Backlog Snapshot (session start)
- #15: research epic for RAG architecture decisions and execution framing
- #16: auto-update architecture model
- #17: manual and failure-injection testing model
- #18: installability and adoption model
- #19: shared single DB vs per-repo DB topology
- #20: dogma baseline vs client-specific corpus separation
- #8: RAG specialist role remains open pending pilot evidence artifact

## Phase Plan

### Phase 1 - Baseline Consolidation and Unknowns Map
Issues: #15, #19, #20
Owner recommendation: Executive Researcher + Executive Planner
Depends on: none
Deliverables:
- One architecture decision matrix mapping 1C/2C/3B/4C to each issue question
- One explicit unknowns-and-risks map (testable questions only)
- One dependency map for downstream phases
Exit criteria:
- Every question in #15/#19/#20 is classified as either already-decided or evidence-required
- No conflicts exist between baseline decisions and planned research posture
- Unknowns are phrased as testable hypotheses, not generic discussion points

### Review Gate 1 - Baseline Fidelity
Owner recommendation: Review
Depends on: Phase 1
Goal: verify decision-fidelity and dependency completeness before update/testing planning
Hard gate: Phase 2 cannot begin until APPROVED.
Gate acceptance criteria:
1. Decision constraints 1C/2C/3B/4C are represented faithfully without reinterpretation drift.
2. Phase dependencies are explicit and non-circular.
3. Unknowns are testable and mapped to later phases.

### Phase 2 - Update Strategy and Reliability Research
Issues: #16, #17
Owner recommendation: Executive Researcher + Executive Scripter
Depends on: Review Gate 1 APPROVED
Deliverables:
- Update strategy matrix across freshness, cost, and stability tradeoffs
- Failure-mode and manual-fallback test model
- Pilot-measurable criteria for major failure categories
Exit criteria:
- Update strategy explicitly demonstrates 2C compliance
- Reliability model includes failure injection, recovery path, and manual override behavior
- At least one measurable criterion exists for each major failure mode

### Review Gate 2 - Update and Reliability Integrity
Owner recommendation: Review
Depends on: Phase 2
Goal: verify the update and reliability model is testable, bounded, and governance-aligned
Hard gate: Phase 3 cannot begin until APPROVED.
Gate acceptance criteria:
1. Proposed update strategy remains balanced (freshness/stability) and does not overfit one dimension.
2. Failure and fallback criteria are executable and measurable.
3. Scope remains research-first and does not drift into implementation.

### Phase 3 - Installability and Adoption Research
Issues: #18
Owner recommendation: Executive PM + Executive Researcher
Depends on: Review Gate 2 APPROVED
Deliverables:
- Installability scenarios (clean machine, partially configured machine, drifted environment)
- Adoption-friction map and light-check policy recommendations
- Pass/fail signals and remediation outline per scenario
Exit criteria:
- Recommendations comply with 3B (recommended default + light checks)
- Scenarios include explicit pass/fail criteria
- Top adoption risks are prioritized with mitigation candidates

### Review Gate 3 - Adoption Evidence Quality
Owner recommendation: Review
Depends on: Phase 3
Goal: verify adoption/installability claims are evidence-anchored and actionable
Hard gate: Phase 4 cannot begin until APPROVED.
Gate acceptance criteria:
1. Installability scenarios are reproducible and complete.
2. Adoption recommendations are grounded in evidence rather than preference.
3. Risk mitigation proposals are concrete and prioritized.

### Phase 4 - Pilot Evidence Integration and Hold/Release Decision
Issues: #8 and cross-reference to #15-#20
Owner recommendation: Executive Orchestrator + Executive Docs
Depends on: Review Gate 3 APPROVED
Deliverables:
- Evidence summary mapping pilot data to Phase 1-3 hypotheses
- Binary hold/release recommendation for implementation start
- Blocking-gap ledger (blocking vs non-blocking)
Exit criteria:
- #8 pilot evidence is explicitly mapped to prior research claims
- Any remaining gap is classified with owner and next action
- Decision is explicit: hold implementation or permit implementation planning

### Review Gate 4 - Implementation Hold Gate
Owner recommendation: Review
Depends on: Phase 4
Goal: verify hold/release decision quality and evidence sufficiency
Hard gate: Phase 5 cannot begin until APPROVED.
Gate acceptance criteria:
1. Hold/release verdict is explicit and evidence-backed.
2. Gap classification is complete and non-ambiguous.
3. #8 remains open unless release criteria are fully satisfied.

### Phase 5 - Sprint Contract Synthesis and Next-Step Sequencing
Issues: #15-#20 and #8
Owner recommendation: Executive Planner + Executive Docs
Depends on: Review Gate 4 APPROVED
Deliverables:
- Final sprint planning contract with ordered execution tracks
- Ready-now vs defer-later issue classification
- Recommended first implementation slice (only if hold is released)
Exit criteria:
- Every issue is classified as ready, needs evidence, or deferred
- Dependencies are explicit and non-circular
- Next sprint handoff is executable without re-discovery

### Review Gate 5 - Planning Completeness and Coherence
Owner recommendation: Review
Depends on: Phase 5
Goal: confirm planning package is complete, coherent, and safe to operationalize
Hard gate: no implementation planning begins until APPROVED.
Gate acceptance criteria:
1. Full issue-to-phase traceability exists for #15-#20 and #8.
2. Implementation hold constraints are explicit and enforceable.
3. Final contract is coherent across objective, dependencies, and acceptance criteria.

## Review Gates Summary
- RG1 after Phase 1: decision-fidelity gate
- RG2 after Phase 2: update/reliability gate
- RG3 after Phase 3: adoption/installability gate
- RG4 after Phase 4: implementation hold/release gate
- RG5 after Phase 5: final sprint-contract gate

## Implementation Hold Constraint (Mandatory)
- Default state: HOLD.
- No implementation phase may start before Review Gate 4 and Review Gate 5 are APPROVED.
- Release requires an explicit approved verdict and #8 pilot evidence sufficiency.

## Definition of Done
- Planning contract covers #15-#20 and #8 with explicit dependencies and acceptance criteria.
- Every domain phase has a paired Review gate.
- Implementation hold is encoded as a hard gate, not a recommendation.
- Final output cleanly separates ready-now work from defer-later work.

## First Actions
1. Reconfirm backlog snapshot and decision constraints in the scratchpad.
2. Execute Phase 1 baseline consolidation and unknowns mapping.
3. Run Review Gate 1 and log verdict before starting Phase 2.
