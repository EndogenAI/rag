# Sprint 1 Phase Checklists

## Phase 1 - Research Gates (Pre-Implementation)
**Status**: ✅ Complete

### #9 Competitor-Pattern Memo
- [x] Define 3-5 competitor patterns relevant to local retrieval.
- [x] Assign adopt/defer/reject decision for each pattern and map to #1-#7.
- [x] Convert decisions into concrete implementation constraints.
- [x] Verify no orphan recommendations remain.

### #10 Evaluation Protocol + Quality Gates
- [x] Define Sprint 1 evaluation goals and baseline protocol.
- [x] Define measurable quality gates with thresholds:
  - Recall@5 >= 0.75, Precision@5 >= 0.60
  - Latency p95 <= 700ms, Error rate < 1.0%
  - Median token savings >= 80%, Freshness lag <= 5 min.
- [x] Map gates to #5 #6 #7 and note upstream assumptions on #1 #2 #3.
- [x] Verify run procedure and machine-readable outputs are explicit.

### #11 Threat Model Checklist
- [x] Define threat model scope for ingestion, query tools, storage, and CI.
- [x] Map threats to mitigations and owner issues #1 #2 #3 #6 #7.
- [x] Define minimum preventive/detective controls and deferred controls.
- [x] Verify each threat has mitigation and validation method.

### Phase 1 Done Gate
- [x] #9 #10 #11 each include explicit adopt/defer decisions and issue mapping.
- [x] All recommendations map to #1-#7 with no orphan outputs.
- [x] Deferred items include rationale and revisit trigger.
- [x] Review Gate A packet is ready with actionable mapped constraints.

---

## Phase 2 - Core Retrieval Substrate
**Status**: ✅ Complete (Pending Review Gate B sign-off)

### #2 H2 chunking + metadata schema
- [x] Confirm Phase 2 precondition: H2 fallback rule frozen in #2 AC.
- [x] Define and lock chunk unit: one chunk per H2 section.
- [x] Define deterministic fallback behavior (__FROZEN_H2_FALLBACK__).
- [x] Implement metadata schema: chunk_id, source_file, heading, governs_csv, etc.
- [x] Enforce schema invariants (uniqueness, determinism).
- [x] Add acceptance checks.

### #3 Full/incremental index pipeline
- [x] Build full indexing pipeline.
- [x] Build incremental indexing pipeline (hash-based).
- [x] Enforce version-aware behavior (INDEX_VERSION=phase2-v1).
- [x] Enforce freshness requirements (<= 5 min target).
- [x] Enforce idempotency and integrity.

### #1 MCP tools rag_query / rag_reindex / rag_status
- [x] Implement tool contracts with strict input validation.
- [x] rag_query contract checks (empty query rejection, top_k bounds).
- [x] filter_governs behavior (exact-match against governs_csv).
- [x] rag_reindex contract checks (stats, error classes).
- [x] rag_status contract checks (health, version, freshness).
- [x] Error contract consistency (structured JSON errors).

### Tests (Phase 2 minimum coverage)
- [x] Chunking tests (Happy path, fallback).
- [x] Index pipeline tests (Full, incremental, version mismatch).
- [x] MCP tool tests (Query, reindex, status).
- [x] Coverage threshold: 80% line coverage for core modules.

### Phase 2 Done Gate
- [x] Gate B packet contains evidence for #2, #3, #1 and tests.
- [x] Explicit Phase 2 completion statement recorded.
- [x] Review Gate B start condition: all checkboxes complete.

### Phase 2 Evidence Snapshot (2026-03-19)
- [x] Validation run: `uv run pytest tests/test_rag_index.py tests/test_mcp_retrieval.py tests/test_mcp_server.py --cov=rag_index --cov=mcp_server.tools.retrieval --cov-report=term-missing -q`
- [x] Result: 98 passed in 0.92s
- [x] Coverage result: total 99% (rag_index 98%, retrieval 100%)
- [x] Active pre-delegation provider gate switched to OpenAI profile (`LM_PROVIDER=openai`)

---

## Phase 3 - Quality, Metrics, and Docs
**Status**: ⏳ In Progress

### #5 BEIR-lite harness
- [x] Confirm Review Gate B sign-off is recorded before starting #5 work.
- [x] Define BEIR-lite dataset subset and fixed query set in-repo with explicit version tag.
- [x] Freeze evaluation config inputs: corpus path, query file, top_k, filter_governs behavior, and seed.
- [x] Implement a single reproducible runner command for BEIR-lite baseline generation.
- [x] Ensure runner emits machine-readable results file with per-query and aggregate retrieval metrics.
- [x] Capture mandatory metrics in output: Recall@5 and Precision@5.
- [x] Add deterministic validation check that rerun with unchanged inputs reproduces identical aggregate metrics.
- [x] Add tests for harness happy path, missing input files, and malformed config failure handling.
- [x] Document baseline run procedure and expected output location in project docs.
- [x] Link #5 deliverables to Phase 1 evaluation constraints from #10 (no orphan metrics).

### #6 Latency/token instrumentation
- [x] Confirm instrumentation scope covers full retrieval path: query receive, retrieval start/end, response assembly.
- [x] Define latency measurement contract with p50/p95 and error-rate reporting fields.
- [x] Define token-savings measurement contract and baseline comparator method.
- [x] Implement structured machine-readable metrics output for each run.
- [x] Enforce required fields in output schema: timestamp, run_id, dataset_id, latency_p50_ms, latency_p95_ms, error_rate_pct, token_savings_median_pct.
- [x] Add guard for missing or invalid timing/token inputs with explicit error classification.
- [x] Add tests for normal instrumentation path and failure modes.
- [x] Add a summary view mapping measured outputs to Phase 1 thresholds.
- [x] Document how to run instrumentation and where reports are stored.
- [x] Verify instrumentation can be executed in CI-compatible non-interactive mode.

### #4 Docs/quickstart/architecture
- [x] Author VS Code MCP quickstart with clean-machine setup steps from clone to first successful query.
- [x] Include explicit prerequisites and environment setup sequence.
- [x] Document minimal local index bootstrap and reindex workflow for first use.
- [x] Document how to call rag_query, rag_reindex, and rag_status through the MCP path.
- [x] Add architecture section showing component flow: docs source to index to MCP tools to client.
- [x] Include troubleshooting section for common startup, indexing, and query failures.
- [x] Validate quickstart by dry-running steps against a clean setup checklist.
- [x] Ensure docs reference current Phase 2 contracts and error behaviors only.
- [x] Add verification step proving quickstart produces at least one successful retrieval response.
- [x] Cross-link quickstart and architecture pages so users can navigate setup to internals directly.

### #7 CI guardrails
- [x] Define CI workflow stages for lint, tests, and retrieval smoke checks.
- [x] Ensure lint and test gates run on every PR and fail-fast on errors.
- [x] Add retrieval smoke job that validates index build and at least one rag_query success signal.
- [x] Add smoke assertion for core path health signal via rag_status.
- [x] Add CI artifact upload for smoke outputs and metrics summaries.
- [x] Ensure CI workflow uses deterministic inputs and pinned command paths.
- [x] Add clear failure messages for retrieval smoke regressions.
- [x] Add or update docs describing CI guardrail intent and pass criteria.
- [x] Verify CI covers at minimum one retrieval signal plus basic lint/test gates per Sprint 1 DoD.
- [x] Confirm workflow changes do not weaken existing guardrails from earlier phases.

### Phase 3 Done Gate
- [x] #5 baseline harness runs with one command and produces machine-readable Recall@5 and Precision@5 outputs.
- [x] #6 instrumentation produces machine-readable latency and token-savings report with required schema fields.
- [x] #4 quickstart is validated end-to-end on clean setup checklist and reaches successful retrieval.
- [ ] #7 CI executes lint, tests, and retrieval smoke checks on PRs with failing checks blocking merge.
- [x] Phase 1 threshold check is explicit in evidence: Recall@5 >= 0.75, Precision@5 >= 0.60.
- [x] Phase 1 threshold check is explicit in evidence: latency p95 <= 700ms, error rate < 1.0%.
- [x] Phase 1 threshold check is explicit in evidence: median token savings >= 80%.
- [x] All four Phase 3 issues have mapped artifacts and no orphan acceptance criteria.
- [ ] Review Gate C receives complete evidence packet and returns APPROVED.
- [ ] If any threshold is missed, carry-over note and mitigation plan are recorded before gate closure.

### Review Gate C Evidence Packet
- [ ] E1: BEIR-lite runner command and exact invocation used for baseline.
- [ ] E2: Machine-readable BEIR-lite results artifact with Recall@5 and Precision@5.
- [ ] E3: Instrumentation report artifact with latency, error rate, and token-savings fields.
- [ ] E4: Clean-setup quickstart validation checklist with pass/fail marks.
- [ ] E5: CI run evidence showing lint, tests, and retrieval smoke jobs executed.
- [ ] E6: Retrieval smoke output artifact proving index-to-query success path.
- [ ] E7: Test evidence for new/changed #5/#6/#7 logic (relevant test run summary).
- [ ] E8: Docs diff summary for #4 quickstart and architecture updates.
- [ ] E9: Issue-to-artifact trace table for #5, #6, #4, #7 and related acceptance checks.
- [ ] E10: One-page gate verdict sheet stating pass/fail against each objective criterion above.

### Phase 3 Evidence Snapshot (#5/#6)
- [x] Runner command: `uv run python scripts/beir_lite_eval.py --config scripts/eval_data/beir_lite_config_v1.json --assert-deterministic --output scripts/output/beir_lite_results.json --run-id sprint1-phase3-tuned`
- [x] Artifact: `scripts/output/beir_lite_results.json`
- [x] Metrics: Recall@5=1.0, Precision@5=0.6, latency_p95=0.794ms, error_rate=0.0%, token_savings_median=83.864%
- [x] Harness tests: `uv run pytest tests/test_beir_lite_eval.py -q` => 7 passed

### Phase 3 Evidence Snapshot (#4/#7 local mirror)
- [x] Lint mirror: `uv run ruff check scripts/ tests/` => passed.
- [x] Test mirror: `uv run pytest tests/test_beir_lite_eval.py tests/test_rag_index.py tests/test_mcp_retrieval.py tests/test_mcp_server.py -q` => 105 passed.
- [x] Retrieval smoke mirror: `reindex/query/status` commands returned `ok=true`, query `count=3`, status `is_fresh=true`, `version_ok=true`, `total_chunks=2450`.
- [ ] Pending remote proof: PR CI run must execute lint+tests+retrieval-smoke in GitHub Actions to satisfy E5 and close #7 done-gate line.
