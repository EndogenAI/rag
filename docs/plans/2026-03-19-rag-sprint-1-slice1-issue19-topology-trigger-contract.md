# Sprint 1 Slice 1 - Issue #19 Topology Trigger Contract (Implementation-Ready Planning)

Parent sequencing artifact: [2026-03-19-rag-sprint-1-execution-sequencing.md](./2026-03-19-rag-sprint-1-execution-sequencing.md)
Dependency slice artifact: [2026-03-19-rag-sprint-1-phase2-dependency-slice.md](./2026-03-19-rag-sprint-1-phase2-dependency-slice.md)
Validation contract artifact: [2026-03-19-rag-sprint-1-phase3-validation-contract.md](./2026-03-19-rag-sprint-1-phase3-validation-contract.md)
Issue #20 contract-layer prerequisite: [2026-03-19-rag-sprint-1-slice1-issue20-contract-layer.md](./2026-03-19-rag-sprint-1-slice1-issue20-contract-layer.md)
Issue target: [EndogenAI/rag#19](https://github.com/EndogenAI/rag/issues/19)
Date: 2026-03-19

## Objective

Define the bounded topology decision and migration-trigger contract for issue #19, strictly downstream of issue #20 boundary controls.

Scope boundary:
- In scope: planning-level topology contract, exception conditions, migration triggers, and rollback rules.
- Out of scope: implementing federation code, runtime migration, or issue closure actions.

## Dependency and Governance Lock

Execution order remains fixed:
1. #20 (completed and review-approved prerequisite)
2. #19 (this artifact)
3. #16
4. #17
5. #18

Governance anchor posture:
- #8 and #15 remain governance anchors only.
- #8 and #15 are excluded from slice closure criteria.

## A) Decision Matrix (Issue #19 deliverable)

| topology option | correctness and blast radius | relevance/collision risk | maintenance and overhead | recovery posture |
|---|---|---|---|---|
| T1: single shared DB | Weakest isolation; highest blast radius | Highest namespace collision risk without strict partitioning | Lowest infra count, highest governance burden | Recovery requires broad remediation across all repos |
| T2: per-repo DB default | Strongest isolation and smallest blast radius | Lowest collision risk; highest retrieval precision by default | More DB artifacts and maintenance steps | Recovery is localized to one repo context |
| T3: hybrid (per-repo default + controlled federation) | Strong baseline isolation with bounded blending path | Low default collision risk; controlled blended retrieval when allowed | Moderate overhead with explicit governance gates | Recovery can disable federation and retain per-repo integrity |

Default recommendation:
- Use T3 posture with per-repo DB as default and federation disabled unless explicit trigger criteria pass.

## B) Default Topology and Exception Policy (Issue #19 AC)

Default topology decision:
1. Default is per-repo DB boundary posture.
2. All retrieval requests run in repo-scoped mode unless federation is explicitly enabled.
3. Federation is never the default startup posture.

Exception policy (all conditions required):
1. Boundary contract from issue #20 remains passing (no critical cross-scope leaks).
2. Federation business value is documented (cross-repo use case and expected retrieval gain).
3. Trigger owner is assigned and rollback owner is assigned.
4. Exit condition is defined before federation is enabled.

## C) Namespace and Collision Policy Decision

Namespace policy:
1. Every record key is prefixed with repo identifier and partition_id.
2. Shared identifiers without repo prefix are invalid.
3. Scope and partition keys are mandatory and must match issue #20 contract fields.

Collision policy:
1. On key collision across repos, reject write and log collision event.
2. No silent overwrite is allowed.
3. Collision events above threshold trigger automatic federation disable.

## D) Migration Trigger Criteria and Strategy (Issue #19 AC)

| trigger id | condition | threshold | owner | activation action | rollback condition |
|---|---|---|---|---|---|
| M1 | Cross-repo query demand sustained | >= 15% of total queries for 14 days | topology owner | Propose limited federation pilot for defined repos only | Query demand drops below 10% for 14 days |
| M2 | Duplicate indexing overhead sustained | >= 25% duplicated storage footprint for 14 days | platform owner | Enable shared index metadata layer with strict partition keys | Duplicate footprint returns below 15% |
| M3 | Retrieval uplift from federation pilot | >= 10% precision gain without leak-threshold breach | retrieval owner | Keep federation enabled for pilot scope | Precision gain < 5% or leak threshold breach |
| M4 | Security/privacy concern signal | Any local privacy incident or policy violation | security owner | Immediate federation disable and segmented mode lock | Incident closed and controls re-verified |

Migration strategy:
1. Start from per-repo default posture.
2. Enable federation only for bounded pilot scope.
3. Keep fallback path to per-repo-only mode always available.
4. Do not expand federation until all trigger exit and rollback conditions are documented and tested.

## E) Security and Privacy Implications (Issue #19 AC)

| concern | risk | control |
|---|---|---|
| Cross-repo data visibility | Accidental exposure of client/deployment context between repos | Per-repo default + mandatory scope filters + federation disabled by default |
| Namespace collisions | Retrieval contamination and provenance ambiguity | Repo-prefixed keys + collision rejection policy |
| Broad blast radius in shared topology | One policy error affects all repos | Fail-closed default + owner-assigned trigger controls + immediate disable path |
| Audit trace loss in blended paths | Inability to explain retrieval origin | Require reason code, mode log, and per-result source attribution |

## F) Deterministic Validation and Gate Contract

V19-1 Default posture check:
- Pass: default topology is per-repo boundary mode and federation is opt-in only.
- Fail: any statement allows shared/federated default mode.

V19-2 Exception completeness check:
- Pass: exception policy contains boundary precondition, value rationale, owner assignment, and exit condition.
- Fail: any exception criterion missing.

V19-3 Trigger table completeness check:
- Pass: every trigger has threshold, owner, activation action, and rollback condition.
- Fail: any trigger row lacks one required element.

V19-4 Dependency-order check:
- Pass: artifact preserves sequence #20 -> #19 -> #16 -> #17 -> #18 and governance-anchor status for #8/#15.
- Fail: any ordering drift or governance-anchor misuse.

## G) Halt and Rollback Rules

Immediate halt conditions:
1. Any V19-1 to V19-4 check fails.
2. Trigger table contains undefined threshold or owner.
3. Any policy implies federation-by-default behavior.

Rollback posture:
1. Freeze topology at per-repo segmented mode.
2. Disable federation path in planning posture.
3. Preserve last accepted trigger table as last-known-good baseline.
4. Re-run only failed validation subset after correction.

Resume rule:
- Progression to #16 is allowed only after V19 checks pass and Review gate returns APPROVED.

## Readiness Verdict

Verdict: READY FOR ISSUE #19 TOPOLOGY CONTRACT REVIEW GATE.

Authorization boundary:
- Planning-layer progression only.
- No implementation or migration execution is authorized by this artifact.
