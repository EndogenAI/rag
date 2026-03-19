# G1 Evidence - Pilot vs Baseline Effectiveness (Issue #8)

Parent contract: [2026-03-19-rag-sprint-planning-phase5-closure-contract.md](./2026-03-19-rag-sprint-planning-phase5-closure-contract.md)
Issue target: #8
Date: 2026-03-19

## Section A: Baseline vs Pilot Profile

| Profile | Baseline operating profile (pre-specialist/default) | Pilot profile (RAG specialist-guided) |
|---|---|---|
| Definition | Decision anchors existed, but effectiveness evidence was still hypothesis-driven and not yet closed for issue 8. | Specialist-guided evidence packet executed across clean, partial, and drifted scenarios with explicit pass criteria and recorded outcomes. |
| Validation model | Unknowns map and planned hypotheses; no completed pilot-vs-baseline effectiveness closure artifact. | Reproducibility spec with concrete commands, thresholds, and evidence artifacts, including canary and drift drills. |
| Boundary safety posture | Intended hybrid separation policy, but pilot-repeatability evidence not yet integrated as closure. | Scope-filter canary run passed; filtered results remained in-scope; leak thresholds and fail-closed behavior defined and exercised at planning gate. |
| Drift handling | Drift strategy defined conceptually as evidence-needed. | Controlled fail then recover drill completed with explicit failure signal and successful recovery signal. |
| Operator workflow | Higher interpretation burden: policy intent present, but no single consolidated operational effectiveness closure. | Lower burden through lightweight scripted checks: single-command health check in partial scenario, short explicit command sequences in clean and drift scenarios. |
| Evidence maturity | Planning-complete, pilot-closure-incomplete. | Pilot evidence strong but still limited in runtime breadth and repeat-window depth. |

## Section B: Metric Comparison

| Dimension | Baseline (pre-specialist/default) | Pilot (specialist-guided) | Value type | Evidence source |
|---|---|---|---|---|
| Success rate | Not instrumented as measured runtime effectiveness; baseline remained evidence-required in Phase 1 and unresolved for issue 8 in Phase 4. | 3/3 scenario packets marked PASS (clean proxy, partially configured, drifted recovery drill). | Baseline: unknown; Pilot: observed sample result | [2026-03-19-rag-sprint-planning-phase1-baseline.md](./2026-03-19-rag-sprint-planning-phase1-baseline.md), [2026-03-19-rag-sprint-planning-phase3-installability-adoption.md](./2026-03-19-rag-sprint-planning-phase3-installability-adoption.md), [2026-03-19-rag-sprint-planning-phase4-hold-release.md](./2026-03-19-rag-sprint-planning-phase4-hold-release.md) |
| Boundary safety and leak behavior | Policy-level intent for hybrid separation and strict metadata filtering; no closed pilot-repeatability proof artifact yet. | Filtered canary returned in-scope results (3 results carrying endogenous-first governs), with no critical-leak evidence in packet; thresholds defined as <= 0.1% leak and zero critical leaks. | Pilot: observed canary pass + bounded threshold target | [2026-03-19-rag-sprint-planning-phase2-update-reliability.md](./2026-03-19-rag-sprint-planning-phase2-update-reliability.md), [2026-03-19-rag-sprint-planning-phase3-installability-adoption.md](./2026-03-19-rag-sprint-planning-phase3-installability-adoption.md), [2026-03-19-rag-sprint-planning-phase4-hold-release.md](./2026-03-19-rag-sprint-planning-phase4-hold-release.md) |
| Drift detection and recovery | Drift concerns identified as hypothesis/evidence-needed; no closed operational drill in baseline profile. | Controlled drift injection produced fail_exit=1 (file not found) followed by recover_exit=0 PASS after remediation command. | Pilot: observed fail-to-recover drill | [2026-03-19-rag-sprint-planning-phase1-baseline.md](./2026-03-19-rag-sprint-planning-phase1-baseline.md), [2026-03-19-rag-sprint-planning-phase3-installability-adoption.md](./2026-03-19-rag-sprint-planning-phase3-installability-adoption.md) |
| Operator burden | Higher cognitive/coordination burden because baseline was planning-anchor-heavy and not yet closed into a single accepted effectiveness packet. | Lower burden with light checks and scripted flow: partial scenario uses one health command; drift scenario uses two commands; clean scenario uses explicit short sequence with deterministic pass criteria. | Bounded estimate from command-path complexity and closure state | [2026-03-19-rag-sprint-planning-phase1-baseline.md](./2026-03-19-rag-sprint-planning-phase1-baseline.md), [2026-03-19-rag-sprint-planning-phase3-installability-adoption.md](./2026-03-19-rag-sprint-planning-phase3-installability-adoption.md), [2026-03-19-rag-sprint-planning-phase4-hold-release.md](./2026-03-19-rag-sprint-planning-phase4-hold-release.md) |

## Section C: Effectiveness Verdict

- Outcome judgment: Partially effective.
- Why: Pilot evidence demonstrates clear improvement over baseline in operationalization quality, with observed passes in scenario execution, scope-filter canary behavior, and drift fail-to-recover handling.
- Why not fully effective yet: Phase 4 still records issue 8 closure as blocked due to missing integrated pilot-vs-baseline closure artifact and insufficient repeated pilot-window evidence for boundary safety repeatability.
- Caveat 1: Current pilot evidence is strong but sample-limited and partly planning-proxy-based.
- Caveat 2: Full effectiveness should require repeat-window confirmation against leak thresholds and inclusion in a single accepted Gate 4 decision packet.

## Section D: Acceptance Closure Text (Issue #8)

- Pilot run completed in one sprint phase using RAG specialist-guided protocol, with documented comparison against pre-specialist baseline profile.
- Effectiveness is demonstrated as partially effective: pilot showed 3/3 scenario PASS outcomes, in-scope filtered canary results, and successful drift fail-to-recover drill, while baseline remained uninstrumented for equivalent runtime evidence.
- Remaining caveat is explicitly documented: repeat-window boundary-safety evidence and final integrated Gate 4 packet are required to elevate judgment from partially effective to fully effective.
- Acceptance criterion is satisfied for documented pilot-vs-baseline comparison, with follow-on work tracked as repeatability hardening rather than criterion absence.
