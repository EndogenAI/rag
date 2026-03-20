# Sprint 1 Slice 1 - Issue #17 Reliability and Failure-Injection Contract (Implementation-Ready Planning)

Parent sequencing artifact: [2026-03-19-rag-sprint-1-execution-sequencing.md](./2026-03-19-rag-sprint-1-execution-sequencing.md)
Dependency slice artifact: [2026-03-19-rag-sprint-1-phase2-dependency-slice.md](./2026-03-19-rag-sprint-1-phase2-dependency-slice.md)
Validation contract artifact: [2026-03-19-rag-sprint-1-phase3-validation-contract.md](./2026-03-19-rag-sprint-1-phase3-validation-contract.md)
Issue #16 prerequisite: [2026-03-19-rag-sprint-1-slice1-issue16-update-cadence-contract.md](./2026-03-19-rag-sprint-1-slice1-issue16-update-cadence-contract.md)
Issue target: [EndogenAI/rag#17](https://github.com/EndogenAI/rag/issues/17)
Date: 2026-03-19

## Objective

Define a deterministic local reliability-validation contract and failure-injection playbook structure for issue #17, aligned to Slice 1 dependency ordering.

Scope boundary:
- In scope: planning-level command battery design, failure scenarios, pass/fail gates, and evidence template.
- Out of scope: implementation of new production test frameworks.

## Dependency and Governance Lock

Execution order remains fixed:
1. #20 (approved)
2. #19 (approved)
3. #16 (approved)
4. #17 (this artifact)
5. #18

Governance anchor posture:
- #8 and #15 remain governance anchors only.
- #8 and #15 are excluded from slice closure criteria.

## A) Manual Test Playbook Tiers (Issue #17 deliverable)

| tier | objective | command-level steps | expected output signal |
|---|---|---|---|
| Quick | Fast confidence after small change | 1) run index status check; 2) run targeted reindex command; 3) run one deterministic query check | Status command reports healthy; reindex exits 0; query returns expected scoped source |
| Standard | Pre-push reliability baseline | 1) run full local reindex cycle; 2) run deterministic query set; 3) run drift/status check | All commands exit 0; no stale backlog breach; expected retrieval sources present |
| Stress | Optional resilience test | 1) run repeated edit/reindex loop; 2) run concurrent query during updates; 3) run integrity check | No unrecovered failures; integrity checks pass; latency within defined stress ceiling |

## B) Failure-Injection Checklist (Issue #17 AC: at least 8 scenarios)

| scenario id | injection | expected system response | pass/fail signal |
|---|---|---|---|
| F1 | Delete indexed file before update | Index removes stale entry on next cycle | Pass if stale entry disappears after update window |
| F2 | Rapid sequential edits to same file | Debounce and final-state indexing | Pass if final content is indexed and no duplicate drift remains |
| F3 | Malformed markdown document | Error is logged; index process continues for other files | Pass if malformed file is isolated and process remains healthy |
| F4 | Concurrent writes during indexing | Retry/reconcile path handles transient conflicts | Pass if no corrupted index state and retries converge |
| F5 | Watcher process interruption | Recovery path restarts and catch-up succeeds | Pass if backlog clears after restart window |
| F6 | Corrupted index metadata | Integrity check triggers repair/rebuild policy | Pass if integrity mismatch is detected and remediation path runs |
| F7 | Scope-tag omission in content metadata | Validation blocks or quarantines entry | Pass if missing-scope item is excluded from retrieval |
| F8 | High backlog surge | Throttle and sweep policy engages | Pass if backlog returns below fail threshold in recovery window |
| F9 | Duplicate key collision across namespaces | Collision policy rejects conflicting write | Pass if no silent overwrite and collision event recorded |

## C) Pass/Fail Gates for Freshness, Correctness, Stability

| gate | metric | pass threshold | fail threshold |
|---|---|---|---|
| Freshness gate | p95 age of indexed updates | <= 10 minutes | > 30 minutes |
| Correctness gate | mismatch rate from audit sweep | <= 0.1% | > 0.5% |
| Stability gate | consecutive update failures | 0-1 | >= 5 |
| Recovery gate | restart/catch-up completion | completes within 10 minutes | does not complete within 20 minutes |

Gate policy:
1. Any fail-threshold breach blocks progression.
2. Warning-threshold breaches require explicit note but do not auto-block.

## D) PR Evidence Template (Issue #17 AC)

Required reporting blocks for local runs:
1. Environment snapshot: OS, branch, timestamp.
2. Commands executed: ordered list with exit codes.
3. Scenario coverage: checklist of F1-F9 with pass/fail per scenario.
4. Metrics: freshness, correctness mismatch, stability counters.
5. Verdict: PASS or FAIL with explicit blocker statement.

Minimal template:
- Local test tier: quick|standard|stress
- Commands + exit codes:
- Failure scenarios run:
- Metrics observed:
- Gate verdict:
- Follow-up action (if any):

## E) Pre-push vs Optional Diagnostics Placement

Mandatory pre-push baseline:
1. Quick tier always required.
2. Standard tier required when index-affecting files changed.

Optional diagnostics:
1. Stress tier optional for non-blocking exploratory checks.
2. Stress tier required only when repeated reliability regressions are observed.

## F) Deterministic Validation and Gate Contract

V17-1 Command-level completeness:
- Pass: playbook includes command-level steps and expected outputs for quick/standard/stress tiers.
- Fail: any tier lacks command-level steps or expected output signal.

V17-2 Failure scenario coverage:
- Pass: at least 8 failure scenarios with expected outcomes are documented.
- Fail: fewer than 8 scenarios or missing expected outcomes.

V17-3 Gate threshold coverage:
- Pass: freshness, correctness, and stability pass/fail thresholds are explicit.
- Fail: any gate dimension lacks fail threshold.

V17-4 Evidence template completeness:
- Pass: PR evidence template contains command logs, scenario outcomes, metrics, and final verdict.
- Fail: any required reporting block is missing.

V17-5 Dependency-order and governance posture:
- Pass: artifact preserves #20 -> #19 -> #16 -> #17 -> #18 and #8/#15 governance-anchor status.
- Fail: dependency drift or governance-anchor misuse.

## G) Halt and Rollback Rules

Immediate halt conditions:
1. Any V17-1 to V17-5 check fails.
2. Fewer than 8 failure scenarios are documented.
3. Any freshness/correctness/stability gate lacks explicit fail threshold.

Rollback posture:
1. Freeze progression to #18.
2. Keep last accepted reliability contract as baseline.
3. Re-run only failed validation subset after correction.
4. Preserve #16 update-cadence assumptions unchanged while correcting #17.

Resume rule:
- Progression to #18 is allowed only after V17 checks pass and Review gate returns APPROVED.

## Readiness Verdict

Verdict: READY FOR ISSUE #17 RELIABILITY CONTRACT REVIEW GATE.

Authorization boundary:
- Planning-layer progression only.
- No production test-framework implementation is authorized by this artifact.
