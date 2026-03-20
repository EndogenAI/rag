# Sprint 1 Slice 1 - Issue #18 Installability and Adoption Contract (Implementation-Ready Planning)

Parent sequencing artifact: [2026-03-19-rag-sprint-1-execution-sequencing.md](./2026-03-19-rag-sprint-1-execution-sequencing.md)
Dependency slice artifact: [2026-03-19-rag-sprint-1-phase2-dependency-slice.md](./2026-03-19-rag-sprint-1-phase2-dependency-slice.md)
Validation contract artifact: [2026-03-19-rag-sprint-1-phase3-validation-contract.md](./2026-03-19-rag-sprint-1-phase3-validation-contract.md)
Issue #17 prerequisite: [2026-03-19-rag-sprint-1-slice1-issue17-reliability-failure-contract.md](./2026-03-19-rag-sprint-1-slice1-issue17-reliability-failure-contract.md)
Issue target: [EndogenAI/rag#18](https://github.com/EndogenAI/rag/issues/18)
Date: 2026-03-19

## Objective

Define a deterministic installability and adoption contract for dogma-first, downstream-second rollout that preserves governance controls and minimizes operator burden.

Scope boundary:
- In scope: installation model comparison, compatibility contract, upgrade strategy, and usage-enforcement controls.
- Out of scope: building full installer automation.

## Dependency and Governance Lock

Execution order remains fixed:
1. #20 (approved)
2. #19 (approved)
3. #16 (approved)
4. #17 (approved)
5. #18 (this artifact)

Governance anchor posture:
- #8 and #15 remain governance anchors only.
- #8 and #15 are excluded from slice closure criteria.

## A) Install Model Comparison (Issue #18 AC: at least 3 models)

| model | operator burden | failure modes | strengths | recommendation signal |
|---|---|---|---|---|
| I1: script bootstrap | Medium | script/env drift, shell portability issues | Fast onboarding in one command | Good for initial dogma-first bootstrap |
| I2: package install | Low-Medium | package version mismatch, dependency conflicts | Standard versioned distribution path | Strong for downstream reuse once stable |
| I3: template include | Medium-High | template divergence and manual sync overhead | Explicit repo-level control and visibility | Useful for strongly customized repos |
| I4: hybrid (bootstrap -> package, template fallback) | Medium | complexity of multi-path guidance | Balances speed, stability, and customization | Recommended canonical rollout posture |

Default recommendation:
- Adopt I4 hybrid posture: bootstrap for initial dogma enablement, package for standardized downstream adoption, template include only as controlled fallback.

## B) Compatibility Matrix (Issue #18 AC)

| repo variant | install path | config discovery expectation | compatibility risk |
|---|---|---|---|
| Dogma-core layout | bootstrap then package | root-level config discovery | Low |
| Dogma-like downstream with docs/plans/scripts | package-first with bootstrap fallback | root plus known subpath search | Low-Medium |
| Minimal downstream repo | bootstrap + template fallback | explicit config path required | Medium |
| Customized enterprise fork | template-guided install with package pinning | explicit discovery map in repo settings | Medium-High |

Compatibility rule:
1. Installation must declare required path conventions and fallback behavior.
2. Missing config discovery path is a blocking condition, not a warning.

## C) Upgrade and Versioning Strategy (Issue #18 AC)

Versioning policy:
1. Semantic version tags for installable package path.
2. Bootstrap script pins to compatible package minor line.
3. Template fallback includes explicit version marker and upgrade notes.

Upgrade flow:
1. Dry-run compatibility check.
2. Apply upgrade in dogma reference repo first.
3. Promote to downstream repos in staged batches.
4. Roll back to last-known-good version on failed compatibility gate.

Drift prevention controls:
1. Version marker required in config contract.
2. Upgrade notes required for every minor/major change.
3. Repository health check must confirm expected version marker before enabling new features.

## D) Governance Controls for Actual Agent Usage (Issue #18 AC)

| enforcement level | mechanism | posture | failure action |
|---|---|---|---|
| Soft | onboarding prompts and docs nudges | advisory only | record warning |
| Medium | pre-phase checklist requiring RAG checks | gate-assisted | block phase progression until checklist complete |
| Hard | pre-commit or pre-push enforcement for required RAG validation step | deterministic gate | block commit/push until satisfied |

Recommended enforcement posture:
1. Dogma-first: medium enforcement during initial adoption.
2. Downstream rollout: medium by default, hard enforcement for repos with repeated bypass patterns.
3. Any hard-enforcement rollout must include explicit rollback toggle.

## E) Rollout Sequence (dogma first, then downstream)

1. Stage 1: dogma reference rollout with hybrid install path and compatibility checks.
2. Stage 2: pilot downstream repos with package-first path and bootstrap fallback.
3. Stage 3: broader downstream rollout with version-pinned upgrades and enforcement posture calibration.

Progression rule:
- Do not advance stages unless prior stage validation and rollback readiness are both documented as passing.

## F) Deterministic Validation and Gate Contract

V18-1 Install-model comparison coverage:
- Pass: at least three install models compared with operator burden and failure modes.
- Fail: fewer than three models or missing burden/failure analysis.

V18-2 Compatibility matrix completeness:
- Pass: matrix includes dogma-like variants and explicit discovery expectations.
- Fail: missing variant coverage or missing discovery expectations.

V18-3 Upgrade strategy completeness:
- Pass: includes versioning policy, staged upgrade flow, and rollback path.
- Fail: missing rollback path or missing version marker policy.

V18-4 Governance control completeness:
- Pass: soft/medium/hard usage-enforcement options and recommended posture are explicit.
- Fail: no enforcement-level distinction or no fail action.

V18-5 Dependency-order and governance posture:
- Pass: artifact preserves #20 -> #19 -> #16 -> #17 -> #18 and #8/#15 governance-anchor status.
- Fail: dependency drift or governance-anchor misuse.

## G) Halt and Rollback Rules

Immediate halt conditions:
1. Any V18-1 to V18-5 check fails.
2. Upgrade strategy lacks deterministic rollback path.
3. Governance enforcement posture lacks explicit failure action.

Rollback posture:
1. Freeze installability progression at current validated stage.
2. Revert to last-known-good install/version contract.
3. Re-run only failed validation subset after correction.

Resume rule:
- Slice progression beyond #18 is allowed only after V18 checks pass and Review gate returns APPROVED.

## Readiness Verdict

Verdict: READY FOR ISSUE #18 INSTALLABILITY/ADOPTION REVIEW GATE.

Authorization boundary:
- Planning-layer progression only.
- No full installer automation or production rollout is authorized by this artifact.
