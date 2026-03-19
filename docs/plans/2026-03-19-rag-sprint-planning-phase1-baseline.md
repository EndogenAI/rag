# Phase 1 Output - Baseline Consolidation and Unknowns Map

Parent workplan: [2026-03-19-rag-sprint-planning.md](./2026-03-19-rag-sprint-planning.md)
Scope issues: #15, #19, #20
Date: 2026-03-19

## Section A: Decision Matrix

| Phase 1 issue or question | Status | Governing decision anchor | Implications for planning and evidence |
|---|---|---|---|
| #15 epic framing: whether architecture work stays research-first before implementation | Already decided | 1C neutral baseline | Phase outputs must compare alternatives without premature implementation lock-in; keeps Phase 1 as classification and hypothesis-setting only. |
| #15 scope item: update architecture direction (issue #16 downstream) | Evidence required (default posture pre-set) | 2C balanced freshness/stability | Phase 2 must prove tradeoffs with measurable latency, drift, and failure-recovery signals; no single-axis optimization (freshness-only or stability-only). |
| #15 scope item: manual/failure testing model (issue #17 downstream) | Evidence required (policy intent pre-set) | 2C balanced freshness/stability + 3B light checks | Phase 2 must define mandatory minimal checks and optional stress checks; evidence format must stay lightweight enough for routine use. |
| #15 scope item: installability/adoption model (issue #18 downstream) | Evidence required (default stance pre-set) | 3B recommended-by-default with light checks | Phase 3 must design adoption controls that raise compliance without heavy enforcement overhead; must include clear pass/fail signals with low operator burden. |
| #19 default topology decision: shared DB vs per-repo vs hybrid | Already decided at baseline default level | 4C hybrid separation | Default should preserve separation boundaries, with optional federation path under explicit exception conditions; shifts Phase 1 from choosing baseline to defining evidence thresholds. |
| #19 question: namespace/collision policy and relevance impact | Evidence required | 4C hybrid separation + 1C neutral baseline | Must validate collision risk under mixed retrieval and confirm partition metadata/query filters prevent cross-repo bleed in default mode. |
| #19 question: migration trigger criteria | Evidence required | 4C hybrid separation | Needs quantitative trigger points for when to introduce federation/shared services (for example index size, latency, maintenance cost, or cross-repo retrieval demand). |
| #20 partition strategy for dogma vs client content | Already decided at architectural direction | 4C hybrid separation | Default separate scopes; blended retrieval is explicit opt-in policy path, not default. |
| #20 metadata contract and filter guarantees | Evidence required | 4C hybrid separation + 1C neutral baseline | Must define strict provenance/scope metadata and enforceable query-filter rules; required to prevent cross-contamination while preserving intentional cross-scope retrieval. |
| #20 retention/refresh/deletion policy split | Evidence required | 2C balanced freshness/stability + 4C hybrid separation | Requires policy-level evidence for differing lifecycle controls between core and client corpora without creating stale or orphaned partitions. |

## Section B: Unknowns and Risks

- Hypothesis: Partitioned metadata with strict scope filters can reduce unintended cross-scope retrieval to near-zero in default mode.
  - Evidence needed: Controlled retrieval tests with seeded overlap terms, false-positive leakage rate by scope, and query-audit traces proving filter enforcement.
- Hypothesis: A hybrid topology can outperform fully separate databases on maintenance effort without materially increasing collision or privacy risk.
  - Evidence needed: Comparative runs across separate, shared, and hybrid layouts measuring maintenance actions, collision incidents, and retrieval precision/recall deltas.
- Hypothesis: Optional federation can be safely enabled only above explicit workload thresholds.
  - Evidence needed: Threshold study across corpus size, query concurrency, and latency/error bands to define objective migration triggers.
- Hypothesis: Balanced freshness/stability policy can achieve acceptable staleness while avoiding high failure churn.
  - Evidence needed: Update-cycle simulations with drift age, update latency, failed update rate, and rollback frequency under realistic edit bursts.
- Hypothesis: Recommended-by-default with light checks yields higher sustained adoption than hard-gate enforcement in this repo family.
  - Evidence needed: Install-and-use trials across dogma-like repos comparing completion rate, time-to-first-query, and bypass/abandon rates under light vs strict enforcement.
- Hypothesis: Distinct retention and deletion policies for dogma vs client content can preserve governance boundaries without degrading retrieval quality.
  - Evidence needed: Lifecycle experiments with staggered refresh/deletion windows and resulting retrieval correctness, stale-hit rate, and provenance consistency.

## Section C: Dependency Map

1. Phase 1 baseline classification is the prerequisite contract for Review Gate 1; if RG1 is not APPROVED, Phase 2 cannot begin because update/testing designs would lack fixed decision anchors (2C, 4C, 3B).
2. Phase 2 (#16, #17) depends on Phase 1 unknowns map to select what must be measured; RG2 approval requires proof that update and reliability models remain 2C-balanced and testable, otherwise Phase 3 is blocked.
3. Phase 3 (#18) depends on Phase 1 adoption stance and Phase 2 reliability outputs; RG3 requires installability and adoption recommendations to operationalize 3B (recommended default with light checks), otherwise pilot-integration evidence in Phase 4 is non-comparable.
4. Phase 4 (#8 plus cross-links to #15-#20) depends on validated hypotheses from Phases 1-3; RG4 hold/release decision is invalid without direct mapping from pilot evidence to Phase 1 baseline assumptions and downstream claims.
5. Phase 5 synthesis depends on RG4 plus all prior review outputs; RG5 must confirm full issue-to-phase traceability and enforce hold constraints, and implementation planning remains blocked unless both RG4 and RG5 are APPROVED.

## Section D: Readiness Verdict

- Ready for Review Gate 1.
- Reason: Baseline decisions are cleanly separated into already-decided vs evidence-required, with each item anchored to 1C, 2C, 3B, or 4C.
- Reason: Unknowns are expressed as testable hypotheses with explicit evidence requirements, satisfying the no-generic-discussion criterion.
- Reason: Downstream dependencies and gate impacts across Phases 2-5 are explicit and non-circular, supporting RG1 dependency-completeness checks.
