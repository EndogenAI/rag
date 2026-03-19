# Phase 3 Output - Installability and Adoption Research

Parent workplan: [2026-03-19-rag-sprint-planning.md](./2026-03-19-rag-sprint-planning.md)
Phase 1 input: [2026-03-19-rag-sprint-planning-phase1-baseline.md](./2026-03-19-rag-sprint-planning-phase1-baseline.md)
Phase 2 input: [2026-03-19-rag-sprint-planning-phase2-update-reliability.md](./2026-03-19-rag-sprint-planning-phase2-update-reliability.md)
Scope issue: #18
Date: 2026-03-19

## Section A: Installability Scenarios

| Scenario | Context Definition | Pass Criteria | Fail Criteria | Remediation Path |
|---|---|---|---|---|
| Clean machine | Fresh environment with no prior RAG assets, no cached index, standard toolchain only | 1. Bootstrap completes without manual patching. 2. First scoped retrieval succeeds for both dogma and client partitions. 3. Light checks pass: environment health check, scope-isolation canary, baseline retrieval canary. 4. Time-to-first-success stays within target onboarding window. | 1. Bootstrap requires undocumented manual fixes. 2. First retrieval fails or returns empty unexpectedly. 3. Scope leak appears in canary query. 4. Setup duration exceeds adoption threshold. | 1. Run guided preflight that identifies missing dependencies and proposes one-command fixes. 2. Auto-generate minimal config from defaults. 3. Re-run light checks only (not full test suite) after fixes. 4. Escalate to fallback manual path only if two consecutive preflight cycles fail. |
| Partially configured machine | Existing environment with some prerequisites installed and prior local settings present; mixed old/new state possible | 1. Installer detects existing state and performs safe reconciliation without destructive overwrite. 2. Incremental update path succeeds. 3. Light checks pass with no critical warnings. 4. Existing user workflow remains uninterrupted after adoption. | 1. Configuration collisions block install or silently override user settings. 2. Update path enters unstable retry loop. 3. Partition routing is ambiguous after merge. 4. User must perform repeated manual edits for normal operation. | 1. Run drift-aware config merge with explicit preview and accept/reject options. 2. Apply safe defaults under recommended mode, preserve local overrides unless incompatible. 3. If conflict persists, switch to stability-first profile and retry incremental sync. 4. Produce targeted remediation report listing only blocking conflicts. |
| Drifted environment | Previously working setup with version skew, stale artifacts, schema mismatch, or policy drift from recommended defaults | 1. Drift detection classifies mismatches by severity and scope. 2. Recovery restores operational state without full rebuild in most cases. 3. Light checks pass after remediation. 4. Scope boundaries remain intact throughout repair flow. | 1. Drift cannot be classified deterministically. 2. Recovery requires frequent destructive resets. 3. Post-repair canaries still fail or leak across scopes. 4. Recurrent drift appears within short cycle after repair. | 1. Use three-tier recovery: metadata repair, targeted reindex, full partition rebuild only as last resort. 2. Enforce separated retrieval mode during repair to honor hybrid separation constraints. 3. Pin to stable update window profile until two healthy cycles complete. 4. Open drift ledger entry with root-cause category and recurrence guard. |

### Reproducibility Spec (RG3)

| Scenario | Preconditions | Command sequence | Numeric pass thresholds | Required evidence artifacts |
|---|---|---|---|---|
| Clean machine (proxy via fresh CI runner + scoped retrieval canary) | GitHub-hosted fresh runner on current branch commit plus local index available for retrieval-canary verification | 1. `gh run list --branch sprint/rag-sprint-planning-2026-03-19 --limit 10 --json databaseId,workflowName,conclusion,createdAt,updatedAt,displayTitle` 2. Select latest row where `workflowName == "Tests"` and `conclusion == "success"` 3. `uv run python scripts/rag_index.py status --output json` 4. `uv run python scripts/rag_index.py query --query "endogenous first" --top-k 3 --output json` 5. `uv run python scripts/rag_index.py query --query "endogenous first" --top-k 3 --filter-governs endogenous-first --output json` | CI check: latest Tests row must be `success`; retrieval check: `status.ok=true`, `status.version_ok=true`, `query.count>=1`; scope canary check: filtered query `count>=1` and every returned result includes `endogenous-first` in `governs` | 1. Run id + timestamp 2. Workflow conclusion 3. Status JSON snapshot 4. Unfiltered/filtered query JSON snapshots |
| Partially configured machine (local) | Existing local repo with active virtual environment and prior state | 1. `uv run python scripts/check_substrate_health.py` 2. Capture exit code + elapsed time + status table | Exit code = 0; all checked files PASS; elapsed time <= 60 sec | 1. Command transcript summary 2. Exit code/elapsed time 3. Tail output |
| Drifted environment (controlled injection) | Local repo; injected missing-file condition through explicit `--files` check list | 1. `uv run python scripts/check_substrate_health.py --files AGENTS.md does/not/exist.md` 2. Confirm fail exit 3. `uv run python scripts/check_substrate_health.py --files AGENTS.md .github/agents/executive-orchestrator.agent.md` 4. Confirm recovery pass | Failure step exit code = 1 with `file not found`; recovery step exit code = 0 with PASS status | 1. Failure transcript summary 2. Recovery transcript summary 3. Fail/recover exit codes |

## Section B: Adoption Friction Map

| Priority | Adoption Friction Risk | Why It Blocks Adoption | 3B-Aligned Mitigation | Success Signal | Residual Risk |
|---|---|---|---|---|---|
| P1 | Setup ambiguity across environments | Users abandon when setup path branches early and guidance is unclear | Recommended-by-default install profile with three light checks only; show optional advanced paths after first success | First-run completion rate increases and median setup time decreases | Advanced users may still request stricter controls |
| P1 | Fear of breakage in existing repos | Teams avoid enabling when they expect config overwrite or index instability | Non-destructive reconciliation default, explicit preview of changes, one-step rollback | Drop in rollback-triggered abandonments and support asks | Legacy edge cases may require manual intervention |
| P1 | Scope-boundary trust gap under hybrid model | Adoption stalls if users doubt separation between dogma and client corpora | Mandatory scope-isolation canary in light checks; fail closed to separated mode when uncertain | Zero critical cross-scope leaks in onboarding and early use | False positives can create short-term friction |
| P2 | Perceived maintenance burden | If cadence and upkeep feel heavy, recommended mode is ignored | Balanced default cadence with low-touch health prompts; avoid hard enforcement loops | Higher weekly active usage under default mode | Some teams may under-monitor drift signals |
| P2 | Drift recovery uncertainty | Users resist adoption if drift remediation seems opaque or risky | Drift classification report with prioritized, reversible repair steps | Faster mean-time-to-recovery and fewer full rebuilds | Complex multi-cause drift remains hard to auto-resolve |
| P3 | Over-checking fatigue | Too many gates reduce adherence to recommended defaults | Keep baseline checks light and deterministic; defer deep diagnostics to opt-in troubleshooting mode | Sustained check completion without rising bypass rate | Rare failures may escape early detection |
| P3 | Documentation-to-action gap | Even good guidance fails if not mapped to concrete operator actions | Action-oriented runbooks tied to each fail signal with minimal decision branching | Reduced time from failure detection to successful remediation | Runbooks can lag behind new failure patterns |

## Section C: Recommendations for Phase 4

- Build an evidence packet per scenario with three required artifacts: install transcript summary, light-check outcomes, and remediation outcome log.
- Use a single RG3 evidence scorecard with weighted dimensions: reproducibility, operator burden, and boundary safety; require pass on all P1 risks before hold/release discussion.
- Carry forward 2C explicitly by reporting both freshness impact and stability impact for every remediation path; reject any proposal that improves one while materially degrading the other without justification.
- Validate 4C posture during evidence integration by proving default separated behavior and documenting exact conditions for optional federated access.
- Include an adoption delta view versus Phase 2 assumptions: completion rate, rollback frequency, drift recurrence, and bypass behavior under light checks.
- Prepare a binary pre-read for Phase 4: ready-to-integrate evidence complete versus evidence gaps that keep implementation hold active.

### Completed Evidence Packets (RG3)

| Scenario | Evidence summary | Result | Scorecard dimension outcome |
|---|---|---|---|
| Clean machine (proxy) | Fresh-run CI evidence captured from branch `sprint/rag-sprint-planning-2026-03-19`: `Tests` workflow run `23319010212` concluded `success` at `2026-03-19T22:02:40Z` for display title `docs(plan): add phase 2 update and reliability outputs`; retrieval canary evidence: `rag_index status` returned `ok=true`, `version_ok=true`; filtered query with `--filter-governs endogenous-first` returned 3 results and each result carried `governs` containing `endogenous-first`. | PASS | Reproducibility: PASS; Operator burden: PASS (scripted checks); Boundary safety: PASS (scope-filter canary satisfied) |
| Partially configured machine | Local health run output: `uv run python scripts/check_substrate_health.py` returned `exit=0 elapsed_sec=0` with PASS statuses and final line `RESULT: PASS — all files meet the health threshold.` | PASS | Reproducibility: PASS; Operator burden: PASS (single command); Boundary safety: PASS for substrate integrity checks |
| Drifted environment (controlled) | Failure and remediation drill: failure command with missing file returned `fail_exit=1` and `ERROR (file not found)`; recovery command returned `recover_exit=0` and `RESULT: PASS — all files meet the health threshold.` | PASS | Reproducibility: PASS; Operator burden: PASS (two-step recovery); Boundary safety: PASS (recovery restores baseline checks) |

### P1 Closure Table (Phase 3 Exit)

| P1 risk | Evidence reference | Status | Owner | Notes |
|---|---|---|---|---|
| Setup ambiguity across environments | Reproducibility Spec + Completed Evidence Packets (clean proxy + partial local) | Closed for planning gate | Executive Researcher | Remaining work is operational rollout docs in later phase, not planning blocker |
| Fear of breakage in existing repos | Partial local pass + drift recovery drill with explicit fail/recover signals | Closed for planning gate | Executive Researcher | Recovery and rollback path validated at planning-contract level |
| Scope-boundary trust gap under hybrid model | Phase 2 leak thresholds and fail-closed separation posture + Phase 3 boundary checks | Closed for planning gate | Executive Researcher | Boundary safety remains a hold criterion for Phase 4 integration packet |

## Section D: Readiness Verdict

- Review Gate 3 criterion 1, reproducible and complete scenarios: Satisfied with explicit preconditions, command sequence, thresholds, and evidence artifacts per scenario.
- Review Gate 3 criterion 2, evidence-anchored recommendations: Satisfied with completed evidence packets for clean proxy, partially configured local, and controlled drift recovery scenarios.
- Review Gate 3 criterion 3, concrete prioritized mitigations: Satisfied with prioritized P1 to P3 friction risks and actionable mitigations aligned to recommended-by-default plus light checks.
- Overall Phase 3 readiness verdict: Ready for Review Gate 3 with no unresolved P1 blocker for planning-gate progression to Phase 4, based on completed clean-scenario boundary-safety checks and reproduced scenario evidence packets.
