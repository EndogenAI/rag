# Phase 2 Output - Update Strategy and Reliability Research

Parent workplan: [2026-03-19-rag-sprint-planning.md](./2026-03-19-rag-sprint-planning.md)
Phase 1 input: [2026-03-19-rag-sprint-planning-phase1-baseline.md](./2026-03-19-rag-sprint-planning-phase1-baseline.md)
Scope issues: #16, #17
Date: 2026-03-19

## Section A: Update Strategy Matrix

| Strategy option for #16 | Freshness | Stability | Cost (compute + ops) | 2C fit | 3B light checks | 4C separation behavior | Recommended default posture |
|---|---|---|---|---|---|---|---|
| Immediate update on every source change | Very high | Low to medium (high churn risk) | High | Weak (freshness-overfit) | Hard to keep light; check burden rises | Must gate per-scope writes strictly; leak risk increases under high velocity | Not default; reserve for high-volatility client corpora with strict guardrails |
| Fixed periodic full refresh (e.g., daily/weekly) | Medium to low | High | Medium | Weak (stability-overfit if interval long) | Easy (single pre/post refresh checks) | Clean separation by running per-scope jobs | Not default alone; good as baseline safety layer |
| Incremental delta updates + scheduled compaction | High | Medium to high | Medium | Strong | Good (delta integrity + retrieval canary) | Strong if delta pipeline is partition-aware by scope | Candidate, but still needs fallback lane for outages |
| Batched windowed updates (e.g., 2-4/day) + canary validation | Medium to high | High | Medium | Strong | Strong (light canary + rollback check) | Strong with per-scope windows and shared policy contract | Strong candidate for default |
| Manual trigger only | Low to variable | Very high | Low runtime, high human cost | Weak (staleness risk) | Trivially light | Strong separation possible but poor freshness discipline | Fallback mode only, not primary strategy |
| Hybrid recommended model: windowed automatic updates + periodic full refresh + manual override | High enough for drift control | High (bounded blast radius) | Medium, predictable | Best balanced 2C profile | Yes: recommended-by-default + light mandatory checks | Default separate scope lanes; optional federated read path only by policy | Recommended-by-default for pilot and baseline rollout |

Recommended default operating profile:
- Primary: batched windowed incremental updates (2-4/day for client corpora, daily for dogma baseline).
- Safety net: periodic full refresh (weekly or after schema/version changes).
- Guardrails: light checks only (canary retrieval pass rate, metadata scope isolation check, rollback readiness check).
- Manual override: explicit operator trigger to pause/resume or force refresh without changing architecture posture.

## Section B: Reliability and Failure Model

1. Update pipeline execution failure
- Failure injection category: network interruption, dependency timeout, partial ingest completion, malformed source payload.
- Detection signal: non-zero job exit, missing chunk counts, ingest-to-index mismatch.
- Rollback path: revert to last known-good index snapshot and replay queued deltas.
- Manual override behavior: operator sets pipeline to pause mode, runs manual refresh for affected scope only, then resumes scheduled updates.

2. Index corruption or degraded retrieval quality after update
- Failure injection category: corrupt vector segment, embedding version mismatch, index write interruption.
- Detection signal: canary query precision drop, checksum mismatch, index health check failure.
- Rollback path: atomic pointer switch to prior index version; quarantine failed build artifact.
- Manual override behavior: force read-only mode on previous index while rebuilding in background.

3. Metadata boundary failure (dogma/client scope bleed) under 4C
- Failure injection category: missing scope tag, incorrect filter binding, namespace collision.
- Detection signal: cross-scope leak tests return out-of-scope documents above threshold.
- Rollback path: disable federated path, enforce strict per-scope filter mode, reindex contaminated partition.
- Manual override behavior: immediate policy override to separated-only retrieval until leakage is zero in repeated checks.

4. Freshness drift beyond acceptable threshold
- Failure injection category: scheduler disabled, backlog growth, repeated skipped windows.
- Detection signal: p95 document age exceeds freshness SLA by scope.
- Rollback path: run prioritized catch-up windows, then temporary increase cadence until backlog normalizes.
- Manual override behavior: operator triggers one-time forced refresh for lagging scope and can temporarily tighten schedule.

5. High update churn causing instability (2C imbalance to freshness)
- Failure injection category: burst edit storms, repeated retraining, cascading retries.
- Detection signal: rollback frequency spike, canary volatility, repeated degraded query outcomes.
- Rollback path: reduce cadence to stable window profile, cap concurrent update jobs, re-enable only after stable canary pass streak.
- Manual override behavior: set temporary stability mode (longer windows, stricter promotion criteria).

6. Scheduler/orchestrator outage
- Failure injection category: cron/job runner crash, queue service outage, host restart failure.
- Detection signal: missed run alerts, job heartbeat gap, queue depth growth.
- Rollback path: fail over to manual runbook and replay missed windows after service restoration.
- Manual override behavior: operator executes manual scoped updates using runbook sequence; returns control to scheduler after health checks pass.

7. Human/operator error in override or config
- Failure injection category: wrong scope selected, accidental full refresh, bad config toggle.
- Detection signal: config drift detection, unexpected scope-level query regression.
- Rollback path: restore last known-good config + prior index pointer; replay only intended updates.
- Manual override behavior: require two-step confirm for destructive actions and explicit scope declaration before execution.

## Section C: Pilot Metrics

| Major failure mode | Primary metric | Pilot target / threshold | Secondary metric | Pass criterion for pilot |
|---|---|---|---|---|
| Pipeline execution failure | Update job success rate | >= 99% over 14-day pilot | Mean recovery time (MTTR) | MTTR <= 30 min for non-corruption failures |
| Index corruption/degradation | Canary retrieval pass rate | >= 98% per update window | Rollback success rate | 100% successful pointer rollback in drills |
| Metadata boundary leak (4C) | Cross-scope leak rate in seeded tests | <= 0.1% and zero critical leaks | Time to containment | Containment <= 15 min after detection |
| Freshness drift | p95 document age vs SLA | Within SLA + 10% buffer per scope | Backlog size | Backlog cleared within 1 business day after incident |
| Churn-driven instability | Rollbacks per 100 updates | <= 2 per 100 updates | Query quality variance | Variance remains within predefined band for 7-day window |
| Scheduler outage | Missed update windows | <= 1 missed critical window/week | Replay completion time | 95% of missed windows replayed within 4 hours |
| Manual override reliability | Manual run success rate | >= 95% without side effects | Operator error rate | <= 1 recoverable error per 20 overrides |

### Fallback Activation Decision Table

| Failure mode | Trigger threshold | Automatic action | Manual override entry condition | Recovery exit condition |
|---|---|---|---|---|
| Pipeline execution failure | 2 consecutive failed update windows for the same scope OR any single run exceeding 15 minutes timeout | Pause affected scope pipeline and switch reads to last known-good index snapshot | Operator forces scoped manual refresh if backlog exceeds 500 pending docs or SLA breach risk is detected | 3 consecutive successful update windows and backlog under 50 pending docs |
| Index corruption/degradation | Canary pass rate < 98% in a window OR checksum mismatch on promoted artifact | Atomic pointer rollback to previous index and quarantine failed build | Operator triggers rebuild if two consecutive rollbacks occur within 24 hours | 24-hour period with canary >= 98% and no checksum mismatches |
| Metadata boundary leak (4C) | Any critical cross-scope leak OR aggregate leak rate > 0.1% in seeded tests | Disable federated retrieval and enforce separated-only filters | Operator reindexes contaminated scope if leak persists for more than 15 minutes | 3 consecutive leak tests with 0 critical leaks and aggregate leak rate <= 0.1% |
| Freshness drift | p95 document age > SLA + 10% for 2 consecutive windows | Increase cadence one step and run prioritized catch-up for lagging scope | Operator force-runs scoped refresh when p95 age exceeds SLA + 20% | p95 age returns to <= SLA + 10% for 2 consecutive windows |
| Churn-driven instability | Rollbacks > 2 per 100 updates in trailing 7 days OR canary variance beyond threshold | Enter temporary stability mode (longer windows, lower concurrency) | Operator enforces stability mode immediately if rollbacks hit 4 per 100 updates | Rollbacks <= 2 per 100 updates for 7 days and canary variance back in band |
| Scheduler outage | Missed heartbeat >= 10 minutes OR > 1 missed critical window/week | Switch to manual runbook and queue replay | Operator starts manual scoped replay when queue depth exceeds 1,000 items | Scheduler heartbeat stable for 30 minutes and queued replay >= 95% complete |
| Operator/config error | Any detected mis-scoped action OR config drift on protected keys | Revert config to last known-good and rollback index pointer if quality drops | Operator performs two-person confirm before rerunning destructive action | 1 full update cycle completed with no config drift and canary >= 98% |

### Metric Bound Definitions

- Query quality variance band: nDCG@10 change must remain within +/-5% of trailing 7-day baseline.
- Canary pass threshold: at least 98% of seeded canary queries must meet expected relevance and scope constraints.
- Critical cross-scope leak: any result from forbidden scope appearing in top-5 results for a scope-restricted seeded query.

## Section D: Readiness Verdict

- Review Gate 2 criterion 1 (balanced strategy): Satisfied. The hybrid default preserves 2C balance by combining bounded freshness, controlled stability, and predictable cost.
- Review Gate 2 criterion 2 (executable and measurable reliability): Satisfied. Each major failure mode has injection category, detection signal, rollback path, manual override behavior, and pilot metrics.
- Review Gate 2 criterion 3 (research-only scope): Satisfied. Output defines planning contracts and measurable criteria without implementation commitments.
- Phase 2 readiness verdict: Ready for Review Gate 2 with recommended default set to hybrid automatic updates plus light checks and explicit manual fallback.
