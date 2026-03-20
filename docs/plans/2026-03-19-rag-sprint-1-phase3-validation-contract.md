# Sprint 1 Phase 3 - Execution Validation Contract

Parent sequencing artifact: [2026-03-19-rag-sprint-1-execution-sequencing.md](./2026-03-19-rag-sprint-1-execution-sequencing.md)
Phase 2 dependency slice: [2026-03-19-rag-sprint-1-phase2-dependency-slice.md](./2026-03-19-rag-sprint-1-phase2-dependency-slice.md)
Phase 2 reliability output: [2026-03-19-rag-sprint-planning-phase2-update-reliability.md](./2026-03-19-rag-sprint-planning-phase2-update-reliability.md)
Date: 2026-03-19

## A) Objective

Define a deterministic, planning-layer validation contract for Sprint 1 phases so every phase transition is gated by explicit pass/fail signals before downstream work is authorized.

Planning-layer scope statement:
- This artifact defines validation expectations only.
- It does not authorize implementation execution, production rollout, or issue closure.

## B) Phase-to-Validation Command Matrix

| phase | command | purpose | pass signal |
|---|---|---|---|
| Phase 1 - Post-Merge Issue State Alignment | `gh issue view 8 --json body` and `gh issue view 15 --json body` and `gh issue view 16 --json body` and `gh issue view 17 --json body` and `gh issue view 18 --json body` and `gh issue view 19 --json body` and `gh issue view 20 --json body` | Verify issue bodies exist and remain synchronized with controlling planning artifacts. | Every command exits 0 and each JSON body includes links to sequencing and RG4 planning artifacts. |
| Phase 1 - Post-Merge Issue State Alignment | `uv run python scripts/check_problems_panel.py` | Confirm no unresolved workspace diagnostics are silently carried into dependency design. | Exit code 0 and result contains zero error-severity diagnostics. |
| Phase 2 - Execution Dependency and Slice Design | `uv run python scripts/check_doc_links.py docs/plans/2026-03-19-rag-sprint-1-phase2-dependency-slice.md` | Validate links in the dependency slice artifact resolve and prevent planning drift from broken references. | Exit code 0 with no broken-link findings. |
| Phase 2 - Execution Dependency and Slice Design | `uv run python scripts/query_docs.py "Sprint 1 phase dependency gate"` | Confirm dependency/gate terminology is discoverable in local docs corpus for later review consistency. | Exit code 0 and output returns at least one match from docs/plans Sprint 1 artifacts. |
| Phase 3 - Execution Validation Contract | `uv run python scripts/check_doc_links.py docs/plans/2026-03-19-rag-sprint-1-phase3-validation-contract.md` | Validate internal links in this contract before it is used as a gate source. | Exit code 0 with no broken-link findings. |
| Phase 3 - Execution Validation Contract | `uv run python scripts/check_substrate_health.py` | Ensure substrate state is healthy before declaring validation framework ready. | Exit code 0 and summary has no blocking errors. |
| Phase 4 - Sprint 1 Kickoff Packet | `uv run python scripts/check_doc_links.py docs/plans/` | Verify kickoff packet and cross-linked plan files are navigable and consistent. | Exit code 0 with no broken links under docs/plans. |
| Phase 4 - Sprint 1 Kickoff Packet | `gh issue view 8 --json body` and `gh issue view 15 --json body` and `gh issue view 16 --json body` and `gh issue view 17 --json body` and `gh issue view 18 --json body` and `gh issue view 19 --json body` and `gh issue view 20 --json body` | Confirm Sprint 1 execution docs are linked from active issues before handoff. | Every command exits 0 and each issue body references the kickoff packet path. |
| Phase 5 - Review, Commit, and Handoff | `uv run ruff check scripts/ tests/` | Enforce repository lint gate before commit/push. | Exit code 0. |
| Phase 5 - Review, Commit, and Handoff | `uv run ruff format --check scripts/ tests/` | Enforce formatting gate before commit/push. | Exit code 0. |
| Phase 5 - Review, Commit, and Handoff | `uv run pytest tests/ -x -m "not slow and not integration" -q` | Enforce fast-test gate before commit/push. | Exit code 0 and no failed tests. |
| Phase 5 - Review, Commit, and Handoff | `gh run list --limit 3` | Verify latest CI runs are green after push and before review request. | Most recent run for the branch shows completed success for Tests, Docs Build, and Auto-label by area workflows. |

## C) Boundary/Drift/Fallback Pass-Fail Contract

| contract dimension | check method | fail trigger | pass condition | fallback/halt action |
|---|---|---|---|---|
| Boundary safety (4C scope separation) | Verify planned gate alignment against Phase 2 G-20 policy and issue-linked artifacts. | Any contradictory boundary rule, missing scope-filter requirement, or explicit cross-scope leak allowance. | All planning artifacts preserve fail-closed separation and do not relax G-20 leak thresholds. | Halt next phase; revert to separated-only planning posture; require contract correction and re-review. |
| Dependency drift | Compare phase dependencies and gate names across sequencing, dependency slice, and validation contract docs. | Any mismatch in dependency order, gate name, or issue dependency mapping. | One consistent acyclic dependency chain is present in all three artifacts. | Halt progression; reconcile docs first; rerun dependency validation commands. |
| Reliability/fallback readiness | Validate that each failure mode in Phase 2 reliability output has trigger, automatic action, manual override entry, and recovery exit. | Any failure mode missing trigger threshold, rollback action, or exit condition. | Every listed failure mode has complete trigger-action-recovery semantics. | Halt authorization for downstream phase planning; require reliability table correction before proceeding. |
| CI gate consistency | Compare local gate outputs with expected CI gates (Tests, Docs Build, Auto-label by area). | Local checks pass but CI gate mapping is absent or contradictory. | Local and CI gate definitions are explicitly mapped and non-conflicting. | Freeze handoff and require CI gate mapping update in this contract. |
| Artifact-link integrity | Run doc-link validation for all Sprint 1 plan artifacts used for gating. | Any broken relative link in the three controlling docs or this contract. | Zero broken links reported by command checks. | Halt and fix links before readiness verdict can remain valid. |

## D) CI Gate Mapping for Sprint 1 phases

| sprint phase | required local pre-gate checks | required CI gate(s) | deterministic phase pass rule |
|---|---|---|---|
| Phase 1 - Post-Merge Issue State Alignment | Issue body reads for #8 and #15-#20, plus problems panel check. | Tests, Docs Build, Auto-label by area (branch baseline gate posture). | Phase passes only if all issue-body reads succeed, no diagnostics breach, and CI posture remains unchanged. |
| Phase 2 - Execution Dependency and Slice Design | Link check on dependency slice and docs query reproducibility check. | Tests, Docs Build, Auto-label by area. | Phase passes only if dependency artifact checks exit 0 and CI gate triad remains green. |
| Phase 3 - Execution Validation Contract | Link check on this file and substrate health check. | Tests, Docs Build, Auto-label by area. | Phase passes only if contract checks exit 0 and no blocking substrate health finding exists. |
| Phase 4 - Sprint 1 Kickoff Packet | docs/plans link sweep and issue body verification for execution links. | Tests, Docs Build, Auto-label by area. | Phase passes only if packet links are valid, issue references are present, and CI triad is green. |
| Phase 5 - Review, Commit, and Handoff | Ruff check, Ruff format check, fast pytest subset, CI status readback. | Tests, Docs Build, Auto-label by area must be success on latest branch run. | Phase passes only if all local checks and latest CI gates are success with no failing workflow in the latest run set. |

## E) Rollback and Halt Rules

1. Immediate halt conditions
- Any command in Section B exits non-zero.
- Any drift contradiction is detected in Section C checks.
- Any missing deterministic threshold in reliability/fallback semantics.

2. Rollback posture
- Revert planning progression to the last phase with a fully satisfied pass signal.
- Mark current phase status as Blocked and record the exact failing command and trigger.
- Re-run only the failed validation subset after correction; do not advance phases in parallel.

3. Non-authority clause
- Passing this contract does not authorize implementation coding, deployment, or release.
- It authorizes planning-layer progression only, per Sprint 1 sequencing scope.

4. CI-specific halt rule
- If local checks pass but latest CI run is not success for Tests, Docs Build, and Auto-label by area, phase progression remains halted.

## F) Phase 3 Readiness Verdict

Verdict: READY FOR PHASE 4 PLANNING KICKOFF, WITH STRICT GATE ENFORCEMENT.

Readiness basis:
1. Validation commands are realistic for this repository and mapped to deterministic pass signals.
2. Boundary, drift, and fallback checks include explicit fail triggers and halt/rollback actions.
3. CI gate mapping is consistent with Sprint 1 sequencing posture (Tests, Docs Build, Auto-label by area).
4. Scope is explicitly planning-layer only and does not authorize implementation execution.
