# Sprint 1 Phase 2 - Execution Dependency and First Slice Design

Parent sequencing artifact: [2026-03-19-rag-sprint-1-execution-sequencing.md](./2026-03-19-rag-sprint-1-execution-sequencing.md)
RG4 re-entry posture: [2026-03-19-rag-sprint-planning-rg4-reentry-update.md](./2026-03-19-rag-sprint-planning-rg4-reentry-update.md)
Phase 2 reliability research: [2026-03-19-rag-sprint-planning-phase2-update-reliability.md](./2026-03-19-rag-sprint-planning-phase2-update-reliability.md)
Phase 3 installability/adoption research: [2026-03-19-rag-sprint-planning-phase3-installability-adoption.md](./2026-03-19-rag-sprint-planning-phase3-installability-adoption.md)
Date: 2026-03-19

## A) Objective

Define a deterministic execution dependency map and bounded first implementation-planning slice for Sprint 1 issues #16, #17, #18, #19, and #20 under RG4 conditional-release posture.
This artifact authorizes planning kickoff only and does not authorize broad implementation expansion.

## B) Dependency Graph

| issue | depends_on | rationale | gate |
|---|---|---|---|
| #20 | none | Partition metadata contract and scope-filter guarantees are foundational boundary controls for all downstream planning. | G-20: Metadata boundary contract accepted with explicit scope fields, filter rules, and leak-threshold checks. |
| #19 | #20 | Topology and migration-trigger planning requires stable partition semantics to avoid namespace and collision ambiguity. | G-19: Topology trigger table accepted with explicit federation-entry conditions and fail-closed default separation. |
| #16 | #19, #20 | Update strategy selection must operate on finalized topology assumptions and partition boundaries to keep 2C balanced and 4C safe. | G-16: Update-cadence profile accepted with measurable freshness/stability thresholds and fallback triggers. |
| #17 | #16 | Reliability and manual-failure planning is valid only after update-path behavior is fixed and measurable. | G-17: Failure model accepted with detection signals, rollback actions, and manual override entry/exit criteria. |
| #18 | #16, #17, #19, #20 | Installability/adoption planning depends on update, reliability, and boundary topology constraints to keep checks light and reproducible. | G-18: Installability scorecard accepted with reproducibility thresholds and P1 friction closure evidence. |

Dependency interpretation:
1. #20 and #19 establish boundary and topology contracts.
2. #16 and #17 establish update and reliability contracts within those boundaries.
3. #18 is validated after upstream contracts are fixed so adoption evidence is comparable and reproducible.

## C) First Implementation-Planning Slice Recommendation

1. Slice name: Boundary-safe update promotion contract.
2. Included issues: #20 plus planning subsets of #19 and #16.
3. Excluded issues in this slice: #17 and #18 execution details (kept for next slice after slice acceptance).
4. Bounded scope:
- Define final metadata field contract for scope separation and retrieval filtering from #20.
- Define topology posture from #19 as default-separated with explicit optional federation trigger thresholds.
- Define one default update promotion lane from #16 using batched windows plus canary validation and rollback trigger.
5. Required output artifacts for this slice:
- Deterministic contract table: scope fields, mandatory filters, invalid states, fail-closed behavior.
- Topology trigger table: threshold, trigger owner, activation condition, rollback condition.
- Update promotion table: cadence, canary threshold, promotion rule, rollback rule.
6. Explicit non-goals for this slice:
- No implementation code changes.
- No scheduler rollout.
- No installability playbook execution.
- No broad cross-issue closure claims.
7. Slice completion condition:
- All three contract tables are accepted under review with binary pass/fail criteria and mapped gates G-20, G-19, and G-16.

## D) Evidence Expectations and Rollback Checkpoints

| gate | evidence expectation | pass threshold | rollback checkpoint | rollback action |
|---|---|---|---|---|
| G-20 | Scope-filter contract test matrix with seeded overlap terms and scope-tag validation | Zero critical cross-scope leaks in seeded boundary checks; aggregate leak rate <= 0.1% | Any critical leak or missing mandatory scope tag | Force separated-only retrieval posture and reject federation planning paths until retest passes |
| G-19 | Topology trigger matrix with explicit threshold values and owner accountability | Every migration trigger has numeric threshold, owner, and exit condition | Any trigger without numeric threshold or owner | Freeze topology at default-separated posture and defer migration-trigger adoption |
| G-16 | Update promotion contract with cadence, canary pass rate, and rollback threshold | Canary pass rate >= 98%; fallback trigger and recovery exit rules fully specified | Canary threshold undefined or fallback entry/exit missing | Hold promotion to last known-good profile and require contract correction before progression |
| Pre-next-slice checkpoint | Cross-artifact consistency check between sequencing and slice contract | No contradiction across dependencies, gates, and non-goals | Any dependency mismatch or gate naming drift | Reconcile artifacts and repeat consistency check before authorizing next slice |

## E) Governance Tracking Classification for #8 and #15 (Explicitly Non-Slice)

| issue | classification | role in this pass | non-slice statement |
|---|---|---|---|
| #8 | Governance-tracking anchor | Tracks pilot-vs-baseline and RG4 evidence continuity across planning artifacts | #8 is not part of the first implementation-planning slice and is used only for governance traceability. |
| #15 | Governance-tracking epic anchor | Tracks sprint-level framing, issue linkage, and gate coherence across #16-#20 | #15 is not part of the first implementation-planning slice and remains an orchestration-level tracking issue. |

Governance rule for this pass: #8 and #15 provide traceability and gate coherence only; no slice completion is declared by closing governance-tracking anchors.

## F) Phase 2 Readiness Verdict

Verdict: READY FOR PLANNING KICKOFF WITH CONSTRAINTS.

Readiness basis:
1. Dependency ordering is explicit and acyclic across #20 -> #19 -> #16 -> #17 -> #18.
2. First slice is bounded to planning contracts only, consistent with RG4 conditional-release posture.
3. Evidence expectations and rollback checkpoints are binary and measurable.
4. Governance-tracking separation for #8 and #15 is explicit and prevents false slice-closure signaling.

Constraint statement:
- Authorization is limited to implementation-planning kickoff artifacts and gate design.
- Broad implementation execution remains out of scope until this slice is accepted and subsequent slice gates are approved.
