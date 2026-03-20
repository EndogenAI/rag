# Sprint 1 Slice 1 - Issue #16 Update-Cadence Contract (Implementation-Ready Planning)

Parent sequencing artifact: [2026-03-19-rag-sprint-1-execution-sequencing.md](./2026-03-19-rag-sprint-1-execution-sequencing.md)
Dependency slice artifact: [2026-03-19-rag-sprint-1-phase2-dependency-slice.md](./2026-03-19-rag-sprint-1-phase2-dependency-slice.md)
Validation contract artifact: [2026-03-19-rag-sprint-1-phase3-validation-contract.md](./2026-03-19-rag-sprint-1-phase3-validation-contract.md)
Issue #20 prerequisite: [2026-03-19-rag-sprint-1-slice1-issue20-contract-layer.md](./2026-03-19-rag-sprint-1-slice1-issue20-contract-layer.md)
Issue #19 prerequisite: [2026-03-19-rag-sprint-1-slice1-issue19-topology-trigger-contract.md](./2026-03-19-rag-sprint-1-slice1-issue19-topology-trigger-contract.md)
Issue target: [EndogenAI/rag#16](https://github.com/EndogenAI/rag/issues/16)
Date: 2026-03-19

## Objective

Define a deterministic update-cadence policy contract for local index refresh behavior that remains low-cost, robust to partial failures, and auditable.

Scope boundary:
- In scope: planning-level architecture comparison, failure recovery posture, health checks, and readiness statement.
- Out of scope: watcher implementation, scheduler rollout, production execution.

## Dependency and Governance Lock

Execution order remains fixed:
1. #20 (approved)
2. #19 (approved)
3. #16 (this artifact)
4. #17
5. #18

Governance anchor posture:
- #8 and #15 remain governance anchors only.
- #8 and #15 are excluded from slice closure criteria.

## A) Architecture Comparison Matrix (Issue #16 AC)

| option | reliability | complexity | local resource cost | strengths | risks |
|---|---|---|---|---|---|
| U1: event-driven watcher + debounce + incremental reindex | Medium-High | Medium | Low-Medium | Fast feedback and low steady-state churn | Missed file events and watcher process crashes |
| U2: scheduled incremental sweeps + periodic full rebuild fallback | High | Low-Medium | Medium | Deterministic schedule and simpler recovery baseline | Higher latency for freshness and more redundant scans |
| U3: hybrid watcher fast-path + scheduled audit sweep | High | Medium-High | Medium | Combines freshness with deterministic correctness backstop | Coordination complexity between fast and audit paths |

Default recommendation:
- Use U3 hybrid posture as default, with watcher for low-latency updates and scheduled audit sweeps for correctness repair.

## B) Trigger and Granularity Policy Decisions

Trigger model decision:
1. Primary trigger: watcher events with debounce window.
2. Correctness backstop: scheduled audit sweep at fixed interval.
3. Manual override: explicit command-hooked rebuild available at all times.

Granularity decision:
1. Fast path: file-level incremental update.
2. Audit path: batch-window verification and targeted reindex.
3. Full rebuild path: only on explicit corruption or repeated drift threshold breach.

## C) Failure-Mode Catalog and Recovery Strategy (Issue #16 AC)

| failure mode | detection signal | threshold | recovery action | manual override |
|---|---|---|---|---|
| Dropped watcher events | Audit sweep detects changed file hash not reflected in index | Any missed change in audited window | Reindex affected files and mark missed-event incident | Operator forces immediate targeted reindex |
| Watcher process crash | Heartbeat absent and queue inactivity while file churn exists | > 2 minutes absent heartbeat | Restart watcher and run catch-up batch reindex | Operator runs full rebuild if restart fails |
| Corrupted index state | Integrity check mismatch between metadata and vector entries | Any integrity mismatch | Freeze fast path, run integrity repair pass | Operator triggers full rebuild and validation sweep |
| Stale drift accumulation | Age/backlog metrics exceed threshold for sustained period | Backlog > 200 pending or age > 30 minutes for 15 minutes | Prioritize sweep lane and throttle new indexing jobs | Operator enters maintenance mode until stable |

Recovery principle:
- Fail toward deterministic correctness, not toward silent freshness claims.

## D) Health Checks and SLO-style Thresholds (Issue #16 AC)

| signal | target | warning threshold | fail threshold |
|---|---|---|---|
| Index freshness age (p95) | <= 10 minutes | > 15 minutes | > 30 minutes |
| Update latency (p95) | <= 90 seconds | > 180 seconds | > 300 seconds |
| Pending backlog | <= 50 items | > 100 items | > 200 items |
| Consecutive update failures | 0 | >= 2 | >= 5 |
| Sweep mismatch rate | <= 0.1% | > 0.2% | > 0.5% |

Required telemetry posture:
1. Emit age, backlog, latency, and failure count as mandatory local signals.
2. Record mismatch incidents with source path and recovery action.
3. Keep last successful sweep timestamp for deterministic health auditing.

## E) Readiness Level and Open Risks (Issue #16 AC)

Implementation readiness level:
- IRL-2 (contract complete, implementation not started).

Open risks:
1. OS-specific watcher semantics can vary and may increase false negatives.
2. Resource-constrained environments may require relaxed sweep cadence.
3. Overlapping update and sweep windows can increase contention unless serialized.

Risk controls:
1. Keep sweep backstop mandatory.
2. Keep deterministic thresholds and explicit maintenance-mode entry.
3. Require rollback to last-known-good index profile on repeated failures.

## F) Deterministic Validation and Gate Contract

V16-1 Architecture coverage:
- Pass: at least three update architecture options with explicit tradeoffs are documented.
- Fail: fewer than three options or missing tradeoffs.

V16-2 Recovery completeness:
- Pass: dropped events and corrupted-index recovery design is explicit with detection and actions.
- Fail: either failure class lacks deterministic recovery path.

V16-3 Health checks coverage:
- Pass: required telemetry signals and SLO-style thresholds are explicit.
- Fail: missing required signal or missing fail threshold.

V16-4 Dependency-order and governance posture:
- Pass: artifact preserves #20 -> #19 -> #16 -> #17 -> #18 and #8/#15 governance-anchor status.
- Fail: ordering drift or governance-anchor misuse.

## G) Halt and Rollback Rules

Immediate halt conditions:
1. Any V16-1 to V16-4 check fails.
2. Any SLO metric lacks a fail threshold.
3. Recovery action is undefined for dropped events or corrupted index.

Rollback posture:
1. Freeze progression to #17.
2. Retain last accepted update-cadence contract as baseline.
3. Re-run only failed validation subset after correction.
4. Keep planned topology and boundary assumptions unchanged while correcting #16.

Resume rule:
- Progression to #17 is allowed only after V16 checks pass and Review gate returns APPROVED.

## Readiness Verdict

Verdict: READY FOR ISSUE #16 UPDATE-CADENCE REVIEW GATE.

Authorization boundary:
- Planning-layer progression only.
- No implementation rollout is authorized by this artifact.
