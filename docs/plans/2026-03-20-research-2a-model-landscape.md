---
title: "Study 2a: Local Model Landscape for RAG Synthesis"
status: Draft
created: 2026-03-20
---

# Study 2a: Local Model Landscape for RAG Synthesis

## Sprint Objective

Establish which local models (size, quantization, family) are optimal for RAG synthesis on resource-constrained hardware (MacBook Air 16GB). This study identifies the "reasoning floor" threshold, quantifies the trade-offs between model size and quantization, and determines whether model family architecture differences materially affect synthesis accuracy in the 0.5B–8B parameter range.

## Hypotheses

**2aH1: Reasoning Floor (Parameter Threshold)**
Small models (<4B parameters) require explicit reasoning scaffolds (BDI tags, verbose logic chains) to maintain synthesis accuracy above 0.25. Below this threshold, models revert to general-purpose training data over retrieved local dogma.

**2aH2: Size vs. Quantization Trade-Off**
Model size (parameter count) correlates with synthesis accuracy more strongly than quantization level in the 3.8B–8B parameter range. A 4-bit quantized 8B model will outperform an 8-bit quantized 4B model.

**2aH3: Model Family Architecture Effects**
Qwen model family will demonstrate measurably different efficiency characteristics (latency, memory footprint, accuracy) compared to Llama/Phi families at equivalent parameter counts, due to architectural differences in attention mechanisms and tokenization.

**2aH4: Governance Boosting Robustness**
Governance Boosting (SQL rank multiplication for `AGENTS.md` and `MANIFESTO.md`) effectiveness is model-agnostic for models ≥3B parameters. Core dogma files will consistently occupy top-k 1 slot regardless of model selection.

## Model Matrix

| Name | Tag | Size (GB) | Quantization | Role |
|------|-----|-----------|--------------|------|
| Qwen | `qwen:0.5b` | 0.4 | 4-bit | Speed baseline (reasoning floor test) |
| Qwen | `qwen:1.8b` | 1.1 | 4-bit | Efficiency sweep |
| Qwen | `qwen:4b` | 2.3 | 4-bit | Phi-3 competitor (BDI tag testing) |
| Qwen | `qwen:7b` | 4.5 | 4-bit | Safety ceiling for 16GB RAM |
| Phi-3 | `phi3:mini` | 2.3 | 4-bit | Baseline (prior Reasoning Floor discovery) |
| Llama 3 | `llama3:8b-instruct-q4_K_M` | 4.9 | 4-bit | Quantization reference |
| Llama 3 | `llama3:latest` | ~8 | 8-bit | High-fidelity reference |

**Exclusions**: `qwen:14b`, `qwen:72b` (will cause machine lockup on 16GB hardware).

## Test Dimensions

This study varies the following dimensions:

1. **Model Size** — 0.5B to 8B parameters
2. **Quantization Level** — 4-bit vs 8-bit (Llama 3 pair only)
3. **Model Family** — Qwen, Phi-3, Llama 3
4. **Prompt Scaffolding** — Minimalist vs BDI-tagged (reasoning scaffold test)
5. **Governance Boosting** — SQL rank multiplication on/off (robustness test)

## Acceptance Criteria

Each hypothesis has one measurable acceptance criterion:

1. **2aH1 (Reasoning Floor)**: Models <4B show accuracy drop ≥0.15 when BDI tags removed; models ≥4B show drop <0.10
2. **2aH2 (Size vs Quantization)**: Llama 3 4-bit (4.9GB) accuracy > Phi-3 8-bit (hypothetical) by ≥0.05
3. **2aH3 (Model Family)**: Qwen 4B vs Phi-3 Mini latency differs by ≥15% OR accuracy differs by ≥0.08
4. **2aH4 (Governance Boosting)**: `AGENTS.md` and `MANIFESTO.md` occupy top-k 1 slot in ≥95% of queries across all models ≥3B

## Phase Structure

### Phase 0: Planning (Current)
- **Deliverables**: This workplan document; hypothesis definition; model matrix; acceptance criteria
- **Gate**: Review agent validation

### Phase 1: Script Hardening
- **Deliverables**: 
  - Update `scripts/benchmark_rag.py` to support `--governance-boost-off` flag
  - Add `--template-path` support for BDI-tagged vs minimalist prompts
  - Verify `ollama ps` clean state before each run
- **Dependencies**: Existing `scripts/benchmark_rag.py`
- **Gate**: Test run on single model (e.g., `phi3:mini`) produces valid JSON output

### Phase 2: Benchmark Sweep
- **Deliverables**: 
  - Pull all models in matrix: `ollama pull <tag>` for each
  - Execute benchmark runs (7 models × 2 prompt variants × 2 governance states = 28 runs)
  - Capture results in `data/rag-benchmarks.yml`
- **Dependencies**: Phase 1 (script ready); disk space ≥14GB free
- **Gate**: All 28 runs complete; no OOM crashes; results parseable

### Phase 3: Synthesis & Archival
- **Deliverables**: 
  - D4 research document: `docs/research/rag-model-landscape-2a.md`
  - Recommendation: Which model(s) to carry forward to Study 2b
  - Pattern catalog: Reasoning floor, size-quantization trade-offs, family differences
- **Dependencies**: Phase 2 (benchmark data); scratchpad findings
- **Gate**: Review agent APPROVED; synthesis follows D4 schema

## Dependencies

**Existing Infrastructure**:
- `scripts/benchmark_rag.py` — primary benchmark harness
- `scripts/rag_index.py` — retrieval engine with Governance Boosting implemented
- `.tmp/research-rag-stress-test-quantization/2026-03-20.md` — scratchpad with baseline findings

**Prior Findings** (from scratchpad):
- **Governance Boosting**: Confirmed to work (top-k 1 consistency for `AGENTS.md`/`MANIFESTO.md`)
- **Reasoning Floor**: Phi-3 accuracy drop 0.25 → 0.08 when BDI tags removed
- **top-k 3 ceiling**: Established for MacBook Air (16GB RAM) to avoid system lag
- **Baseline latency**: ~50s per synthesis (Llama 3 8-bit)

**Hardware Constraints**:
- MacBook Air 16GB RAM
- Current disk: 14 GB free (52% usage)
- Models on disk: phi3:mini, phi3:latest, llama3:latest, llama3:8b-instruct-q4_K_M

## Sequencing

**Study 2a MUST complete before Study 2b begins.**

Study 2b's token-savings comparison requires Study 2a's model recommendations to narrow the sweep. Running them in parallel would waste benchmark time on models that Study 2a reveals as non-viable.
