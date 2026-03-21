---
title: "Study 2b: Token Savings from RAG Component Localization"
status: Draft
created: 2026-03-20
depends_on: 2026-03-20-research-2a-model-landscape.md
---

# Study 2b: Token Savings from RAG Component Localization

## Sprint Objective

Quantify token savings from localizing RAG pipeline components (Retrieval, Augmentation, Generation) using the model subset recommended by Study 2a.

**Dependency**: Study 2b uses a subset of models recommended from Study 2a's results. Execution cannot begin until Study 2a completes and identifies which models meet the reasoning floor and performance thresholds.

## Hypotheses

**2bH0 (Null Hypothesis)**: Localizing RAG components produces no significant token savings compared to fully remote RAG.

**2bH1**: Local Retrieval (R) reduces external API token burn by ≥20% compared to remote Retrieval.

**2bH2**: Local Retrieval + Augmentation (RA) reduces external API token burn by ≥40% compared to remote RA.

**2bH3**: Fully local RAG (R+A+G all local) reduces external API token burn by ≥60% compared to fully remote RAG.

## Test Dimensions

| Dimension | Values | Notes |
|-----------|--------|-------|
| **Localization Configuration** | 4 variants | Fully Remote, R-Local, RA-Local, Fully Local |
| **Model** | Subset from Study 2a | Only models passing Study 2a acceptance criteria |
| **Query Set** | Governance questions | Same query set as Study 2a for consistency |
| **Retrieval Engine** | `scripts/rag_index.py` | Governance Boosting enabled (top-k 3) |

### Localization Configuration Definitions

1. **Fully Remote RAG**: All components use external API (e.g., Claude)
   - Retrieval: Claude API receives query + full corpus
   - Augmentation: Claude constructs context
   - Generation: Claude synthesizes answer

2. **R-Local**: Retrieval local, Augmentation + Generation remote
   - Retrieval: Local SQLite BM25 search
   - Augmentation: Claude receives query + retrieved chunks
   - Generation: Claude synthesizes answer

3. **RA-Local**: Retrieval + Augmentation local, Generation remote
   - Retrieval: Local SQLite BM25 search
   - Augmentation: Local model constructs context
   - Generation: Claude synthesizes final answer

4. **Fully Local RAG**: All components use local models
   - Retrieval: Local SQLite BM25 search
   - Augmentation: Local model constructs context
   - Generation: Local model synthesizes answer

## Token Measurement Methodology

### Instrumentation Approach

**Session-Level Tracking**: Track cumulative token usage per configuration across all queries in a session.

**Component-Level Attribution**:
- **Retrieval tokens**: Count input tokens sent to R component (query + corpus subset)
- **Augmentation tokens**: Count input + output tokens for A component (chunks → context)
- **Generation tokens**: Count input + output tokens for G component (context → answer)

### Token Counting Implementation

1. **For Remote Components** (Claude API):
   - Read token counts from Claude API response headers (`anthropic-token-input`, `anthropic-token-output`)
   - Log per-query and aggregate per session

2. **For Local Components** (Ollama):
   - Use tokenizer API or estimate via character count (1 token ≈ 4 chars)
   - Local token count does NOT contribute to "external API token burn" metric (2bH1-H3 measure external burn only)

3. **Baseline Comparison**:
   - Fully Remote configuration is the 100% baseline
   - Token savings = `(baseline_tokens - variant_tokens) / baseline_tokens × 100%`

### Governance Boosting Note

Study 2b builds on the **Governance Boosting** finding from the scratchpad: applying SQL-level rank multipliers to core dogma files (`AGENTS.md`, `MANIFESTO.md`) ensures they consistently occupy `top-k 1`, preventing displacement by high-volume research noise. This mechanism is enabled in all localization configurations.

### Reasoning Floor Note

Study 2b builds on the **Reasoning Floor** finding: small models (<8B parameters) require explicit BDI tags and verbose scaffolding to avoid catastrophic accuracy drops (observed: 0.25 → 0.08 for Phi-3-mini when scaffolds removed). Study 2a will validate which models pass the reasoning floor threshold; only those models proceed to Study 2b testing.

## Dependencies

### Study 2a Results (Blocking Dependency)

Study 2b **cannot begin** until Study 2a completes and identifies:
- Which models meet the reasoning floor threshold (accuracy ≥0.25 on governance queries with BDI tags)
- Which models meet the latency ceiling (≤60s per synthesis on MacBook Air 16GB)
- Recommended model subset for production RAG use

### Infrastructure

- `scripts/benchmark_rag.py`: Modified to support `--localization` flag with values: `remote`, `r-local`, `ra-local`, `local`
- `scripts/rag_index.py`: Governance Boosting SQL multiplier enabled
- Token-counting instrumentation: New module to track component-level token usage
- Ollama API: For local model token estimation

### Scratchpad Findings

Study 2b integrates two key findings from `.tmp/research-rag-stress-test-quantization/2026-03-20.md`:
- **Governance Boosting**: SQL rank multipliers ensure core dogma files hit top-k 1
- **Reasoning Floor**: Small models require BDI scaffolding to preserve accuracy

## Acceptance Criteria

Each hypothesis has a measurable acceptance criterion tied to token burn reduction:

| Hypothesis | Acceptance Criterion | Measurement |
|------------|---------------------|-------------|
| **2bH1** | Local R reduces external token burn by ≥20% | Compare Fully Remote vs R-Local token counts |
| **2bH2** | Local RA reduces external token burn by ≥40% | Compare Fully Remote vs RA-Local token counts |
| **2bH3** | Fully Local reduces external token burn by ≥60% | Compare Fully Remote vs Fully Local token counts |
| **Dry-Run** | Dry-Run Validation Gate | Successful completion of `--dry-run` across all 4 configurations is a hard gate for Phase 2. |

**Pass Threshold**: A hypothesis passes if the measured token savings meet or exceed the stated percentage threshold across ≥5 governance queries.

**Fail Threshold**: A hypothesis fails if the measured token savings are <50% of the stated threshold (e.g., 2bH1 fails if savings are <10%).

## Phase Structure

### Phase 0: Planning & Dependencies (This Document)

**Deliverables**:
- Workplan document committed to `docs/plans/`
- Review agent approval

**Gate Conditions**: 
- All hypotheses numbered and testable
- Dependency on Study 2a explicit
- Token measurement methodology defined

### Phase 1: Token Instrumentation & Dry-Run Validation

**Agent**: Executive Scripter

**Deliverables**:
- `scripts/count_tokens.py`: Token counting module for Claude API + Ollama estimation
- `scripts/benchmark_rag.py`: Modified to accept `--localization` and `--dry-run` flags; implements dry-run loop over all configurations without inference burn.
- Unit tests for token counting accuracy

**Gate Conditions**:
- Token counter returns accurate counts for Claude API responses
- Ollama token estimation validated against known prompts
- `uv run pytest tests/test_count_tokens.py` passes
- Successful `--dry-run` execution over all 4 localization configurations.

### Phase 2: Localization Comparison Runs

**Agent**: RAG Specialist

**Deliverables**:
- Benchmark results for all 4 localization configurations × model subset from Study 2a
- Token usage logs per configuration per query
- Aggregated token savings table

**Gate Conditions**:
- All configurations run without errors
- Token counts logged for every query
- Savings calculations verified (baseline = Fully Remote)

### Phase 3: Synthesis & Recommendations

**Agent**: Executive Researcher (Scout → Synthesizer → Reviewer → Archivist)

**Deliverables**:
- `docs/research/rag-token-savings-localization.md` (D4 synthesis doc)
- Pattern Catalog entry: "Token Burn Reduction via Component Localization"
- Recommendations section: Which localization strategy to adopt for production RAG

**Gate Conditions**:
- All 4 hypotheses evaluated (pass/fail verdict per hypothesis)
- Token savings table included with raw data
- Recommendations cite specific savings percentages
- Review agent approves synthesis doc

## Notes

- **Top-k ceiling**: All tests use `top-k 3` to maintain MacBook Air stability (established finding from prior session)
- **Prompt consistency**: Use same BDI-tagged prompts across all configurations to isolate localization as the only variable
- **Disk space management**: If disk space <10 GB, remove unused models before pulling new ones (`ollama rm <model>`)

## Cross-References

- **Study 2a**: [docs/plans/2026-03-20-research-2a-model-landscape.md](2026-03-20-research-2a-model-landscape.md)
- **Session scratchpad**: `.tmp/research-rag-stress-test-quantization/2026-03-20.md`
- **Benchmark script**: `scripts/benchmark_rag.py`
- **Retrieval engine**: `scripts/rag_index.py`
