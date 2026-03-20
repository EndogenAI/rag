# Sprint 2 Pilot Results - Issue #8

Parent plan: [2026-03-19-rag-sprint-2-execution-sequencing.md](./2026-03-19-rag-sprint-2-execution-sequencing.md)
Integration packet: [2026-03-19-rag-sprint-2-integration-packet.md](./2026-03-19-rag-sprint-2-integration-packet.md)
Issue target: #8
Date: 2026-03-19
Status: Draft Template

## Phase Gate Context

- Phase dependency: Phase 2 Review APPROVED is required before pilot execution starts.
- This artifact is the Phase 3 primary evidence package and must be review-ready before Phase 3 Review begins.

### Gate Entry Checklist

- [ ] Phase 2 Review verdict recorded as APPROVED
- [ ] Baseline profile source links captured
- [ ] Scenario owners assigned (S1-S3)
- [ ] Evidence storage locations prepared

### Gate Exit Checklist

- [ ] All scenarios (S1-S3) have complete execution logs
- [ ] Metrics table has measured values and evidence links
- [ ] Verdict and decision memo are filled and non-TODO
- [ ] Issue #8 closure text is fully populated

## Objective

Capture measured baseline-vs-pilot effectiveness evidence for the Sprint 2 issue #8 pilot phase, then produce an explicit adopt/iterate/reject decision suitable for Review Gate approval and issue-close readiness checks.

## Pilot Scope

- In scope: RAG Specialist-guided execution paths for retrieval, indexing, and evaluation workflows.
- In scope: measurable comparison against pre-specialist baseline behavior for the same scenario set.
- Out of scope: broad architecture changes not required to evaluate pilot effectiveness.

## Scenario Set

| Scenario ID | Scenario name | Purpose | Owner | Status |
|---|---|---|---|---|
| S1 | Clean environment run | Establish baseline and pilot behavior under expected conditions | RAG Specialist | ⬜ Not started |
| S2 | Partial configuration run | Validate operator workflow quality and recovery guidance | RAG Specialist | ⬜ Not started |
| S3 | Drift/failure injection run | Validate fail signal clarity and deterministic recovery path | RAG Specialist | ⬜ Not started |

## Baseline vs Pilot Profile

| Dimension | Baseline (pre-specialist/default) | Pilot (RAG specialist-guided) | Evidence source |
|---|---|---|---|
| Decision clarity | TODO | TODO | TODO |
| Operator burden | TODO | TODO | TODO |
| Failure handling | TODO | TODO | TODO |
| Boundary safety posture | TODO | TODO | TODO |
| Repeatability | TODO | TODO | TODO |

## Metrics Table

| Metric | Baseline value | Pilot value | Unit | Measurement method | Evidence artifact |
|---|---|---|---|---|---|
| Scenario pass rate | TODO | TODO | % | S1-S3 pass count / total | TODO |
| Time-to-diagnosis | TODO | TODO | minutes | start of failure to root-cause confirmation | TODO |
| Time-to-recovery | TODO | TODO | minutes | first fail signal to successful rerun | TODO |
| Scope-leak incidents | TODO | TODO | count | canary + scoped query audit | TODO |
| Command-path length | TODO | TODO | commands | count from runbook to success | TODO |

## Metric Thresholds and Pass Rules

| Metric | Target threshold | Pass rule |
|---|---|---|
| Scenario pass rate | 100% in S1-S3 | Pass when all 3 scenarios are marked PASS |
| Time-to-diagnosis | <= baseline or <= 10 minutes | Pass when pilot is not slower than baseline and below cap |
| Time-to-recovery | <= baseline or <= 15 minutes | Pass when pilot recovers faster or equal vs baseline and below cap |
| Scope-leak incidents | 0 critical, <= 1 non-critical | Pass when critical leaks are zero and non-critical leaks are within cap |
| Command-path length | <= baseline + 1 command | Pass when pilot does not materially increase operator burden |

Decision aggregation rule:

- Adopt requires all Gate Exit checklist items plus at least 4/5 metric pass rules.
- Iterate is selected when 3/5 metric pass rules are met with no critical leak.
- Reject is mandatory when any critical leak occurs or fewer than 3/5 rules pass.

## Required Evidence Artifacts

| Artifact ID | Required content | Location |
|---|---|---|
| E1 | Baseline run log and commands | docs/plans/evidence/rag-sprint-2/e1-baseline-run.json |
| E2 | Pilot run logs for S1-S3 | docs/plans/evidence/rag-sprint-2/e2-scenario-runs.json |
| E3 | Scoped query and canary leak audit output | docs/plans/evidence/rag-sprint-2/e3-scope-audit.json |
| E4 | Failure injection and recovery evidence | docs/plans/evidence/rag-sprint-2/e4-drift-recovery.json |
| E5 | Final metric worksheet and decision worksheet | docs/plans/evidence/rag-sprint-2/e5-metrics-and-decision.md |

## Execution Log

### S1 - Clean environment run

- Run context:
  - Commit SHA: TODO
  - Index snapshot/version: TODO
  - Environment (OS/Python/tool versions): TODO
- Start timestamp: TODO
- Commands executed:
  - `uv run python scripts/rag_index.py reindex --scope full --output json`
  - `uv run python scripts/rag_index.py status --output json`
  - `uv run python scripts/rag_index.py query --query "programmatic first" --top-k 5 --filter-scope dogma --output json`
  - `uv run python scripts/rag_index.py local-test --test-tier quick --probe-query "programmatic first" --output json`
- Outcome: TODO
- Observations: TODO
- Evidence links: E1, E2 (S1 section), E3

### S2 - Partial configuration run

- Run context:
  - Commit SHA: TODO
  - Index snapshot/version: TODO
  - Environment (OS/Python/tool versions): TODO
- Start timestamp: TODO
- Commands executed:
  - `uv run python scripts/rag_index.py status --output json`
  - `uv run python scripts/rag_index.py health --freshness-seconds 600 --pending-backlog 150 --consecutive-failures 3 --mismatch-rate 0.003 --output json`
  - `uv run python scripts/rag_index.py local-test --test-tier standard --probe-query "programmatic first" --output json`
  - `uv run python scripts/rag_index.py adoption-gate --enforcement-level medium --output json`
- Outcome: TODO
- Observations: TODO
- Evidence links: E2 (S2 section), E3, E5

### S3 - Drift/failure injection run

- Run context:
  - Commit SHA: TODO
  - Index snapshot/version: TODO
  - Environment (OS/Python/tool versions): TODO
- Start timestamp: TODO
- Failure injected: index version mismatch (forced downgrade in local sqlite meta table)
- Commands executed:
  - `uv run python -c "import sqlite3; conn=sqlite3.connect('rag-index/rag_index.sqlite3'); conn.execute(\"UPDATE meta SET value='old-version' WHERE key='index_version'\"); conn.commit(); conn.close()"`
  - `uv run python scripts/rag_index.py query --query "programmatic first" --output json`
  - `uv run python scripts/rag_index.py reindex --scope full --output json`
  - `uv run python scripts/rag_index.py query --query "programmatic first" --output json`
  - `uv run python scripts/rag_index.py adoption-gate --enforcement-level hard --output json`
- Fail signal: query command exits non-zero and reports index version mismatch before recovery reindex
- Recovery signal: full reindex exits zero, subsequent query returns non-empty result set, adoption-gate hard returns passed=true
- Observations: TODO
- Evidence links: E2 (S3 section), E4, E5

Failure verification checklist (must all pass):

- [ ] Pre-recovery query command produced non-zero exit code
- [ ] Pre-recovery output/stderr includes version mismatch indicator
- [ ] Post-recovery full reindex succeeded with exit code 0
- [ ] Post-recovery query succeeded with exit code 0 and count >= 1

## Effectiveness Verdict

- Verdict: TODO (Adopt | Iterate | Reject)
- Confidence: TODO (High | Medium | Low)
- Why this verdict: TODO
- Caveat 1: TODO
- Caveat 2: TODO

## Decision Memo

### Adopt criteria (all must pass)

- [ ] Pilot outperforms baseline on at least 4 of 5 core metrics
- [ ] No critical scope-leak events
- [ ] Drift scenario has deterministic fail and deterministic recovery evidence
- [ ] Operator burden decreases or remains neutral with stronger reliability

### Iterate triggers

- [ ] Pilot improves reliability but evidence volume is insufficient
- [ ] Non-critical leaks or ambiguity remain and require remediation
- [ ] One scenario requires manual intervention not encoded in runbook

### Reject triggers

- [ ] Pilot materially degrades reliability or operator burden
- [ ] Critical scope-leak event observed
- [ ] Failure handling is non-deterministic or non-recoverable

Decision selected: TODO

## Issue #8 Closure Text (Copy-Ready)

Issue #8 pilot criterion closure update:

- Sprint 2 pilot-effectiveness evidence is documented in this file with measured baseline-vs-pilot comparison across clean, partial, and drift scenarios.
- Decision outcome: TODO.
- Residual risks and follow-ups: TODO.

## Review Gate Notes

- Review verdict: TODO
- Reviewer: TODO
- Review timestamp: TODO
- Gate entry criteria satisfied: TODO (Yes/No)
- Gate exit criteria satisfied: TODO (Yes/No)
- Required follow-up actions (if any): TODO
