---
name: rag-rapid-research
description: |
  Factorial RAG sweep workflow: tier-0–3 stressor progression, model benchmarking,
  adaptive k-selection, and reasoning density diagnostics for local compute-first evaluation.
effort: L
languages: [python, bash]
related-docs:
  - docs/research/2026-03-22-rag-study-2a-synthesis.md
  - AGENTS.md
---

# SKILL: RAG Rapid Research (Factorial Sweeps)

**Governing Constraints**:
- **Endogenous-First** ([AGENTS.md](../../AGENTS.md)) — scaffold from existing system knowledge and local compute before reaching outward.
- **Algorithms-Before-Tokens** ([AGENTS.md](../../AGENTS.md#programmatic-first-principle)) — prefer deterministic, encoded solutions (like `scripts/adaptive_k_selector.py`) over interactive token burn for parameter selection.
- **Local Compute-First** ([MANIFESTO.md](../../MANIFESTO.md#3-local-compute-first)) — all primary research runs on local hardware; cloud API is a last resort.

---

## 1. Overview

This skill encodes the factorial sweep workflow used in **RAG Study 2a** (Model Stratification and Retrieval Volatility). It provides a repeatable protocol for executing tiered RAG benchmarks, interpreting results, and encoding findings into the substrate.

**Primary deliverable**: A D4 synthesis doc in `docs/research/` with validated performance tables, pattern catalog, and actionable recommendations.

**Key insight from Study 2a**: Raw token volume (k=20) is not a universal performance driver. Model response to context volume is stratified by parameter density and **family alignment** with the embedding space. See [docs/research/2026-03-22-rag-study-2a-synthesis.md](../../docs/research/2026-03-22-rag-study-2a-synthesis.md).

---

## 2. RAG Stressor Progression (Tier 0–3)

| Tier | Focus | Diagnostic | Success Metric |
|------|-------|------------|----------------|
| **Tier 0** | Baseline Retrieval | Hits@K | NDCG@10 > 0.8 |
| **Tier 1** | Distraction Tolerance | Noise Filtering | Zero hallucination in irrelevant context |
| **Tier 2** | Reasoning Density | **Reasoning Density Threshold (RDT)** | ≥ 3 distinct inferential leaps per answer |
| **Tier 3** | Multi-hop Synthesis | Cross-Document Join | Verified synthesis of ≥ 2 non-adjacent facts |

**Reasoning Density Threshold (RDT)**: A key diagnostic measuring the ratio of inferential logic steps to total token count. Low density indicates "trendslop" or paraphrasing; high density indicates active synthesis.

**Factorial design pattern**: Each study runs a baseline (e.g., top-k=10, standard template) before applying single-variable variants (e.g., top-k=20, enhanced prompt). This isolates each variable's contribution to performance delta.

---

## 3. Study 2a Benchmark Results (Reference Baseline)

Study 2a established the current performance frontier across 17 models on 9 task types using `nomic-embed-text` embeddings. These numbers are the canonical baselines for future sweep comparisons.

### Option C (k=20, Reasoning-First prompt) — Final Results

| Model | Score | Avg Latency | RAM | Viability |
|-------|-------|-------------|-----|-----------|
| SmollM-360M | 0.333 | 8.86s | <1 GB | High Efficiency |
| TinyLlama-1.1B | 0.611 | 9.75s | ~1.5 GB | Optimal Entry |
| Qwen2.5-1.5B | 0.733 | 22.04s | ~2.5 GB | Balanced |
| **Granite-3.3-2B** | **0.867** | **43.20s** | ~3.5 GB | **Deployment Baseline** |
| **Qwen2.5-7B** | **0.956** | 85.18s | ~8 GB | **SOTA (High-Res)** |
| Llama3.1-8B | 0.611 | 95.37s | ~9 GB | Sub-optimal |
| Gemma2-9B | 0.311 | 525.00s | ~10 GB+ | **Non-Viable** |

**60s Interactivity Threshold**: Models exceeding 60s latency require ≥16 GB RAM to reach interactive speeds. Granite-3.3-2B is the primary deployment baseline (90%+ quality-to-latency ratio).

### The 1.5B Reasoning Density Threshold

| Parameter Range | Response to k=20 | Evidence |
|----------------|------------------|----------|
| **< 1.5B (Stabilization)** | Volume compensates for reasoning gaps | SmollM-360M: **+92.1%** gain (0.278 → 0.533) |
| **~1.5B (Equilibrium)** | Diminishing returns | Qwen2.5-1.5B: **+11.1%** gain (0.700 → 0.778) |
| **1.5B–8B (Degradation risk)** | Increased context introduces noise (family-dependent) | Granite-3.3-2B: **-3.6%** drop (0.922 → 0.889) |
| **7B–9B (Affinity dominates)** | Family alignment overrides parameter count | Qwen2.5-7B: **0.956** SOTA |

**Anti-pattern**: Assuming larger parameters always produce better retrieval. Gemma2-9B (9 B params) returned zero sources on 5/9 queries; Qwen2.5-7B (7 B params) achieved 100% citation accuracy on all 9 tasks — same hardware, same k.

---

## 4. Adaptive K-Selection

Use `scripts/adaptive_k_selector.py` to determine optimal retrieval depth. Do not use a global `top_k` setting across all models.

| Tier | Parameter Range | Recommended k | Rationale |
|------|----------------|---------------|-----------|
| **Tier 1** | < 1.5B | k = 20 | Maximise evidence redundancy |
| **Tier 2** | 1.5B – 8B | k = 10 | Prioritise signal precision |
| **Tier 3** | > 8B | k = 5–8 | Highly focused precision |
| **Exception** | Validated mid-tier families (e.g., Qwen2.5-7B) | k = 20 | Family-aligned models benefit from volume |

```bash
# Get adaptive k for a model
uv run python scripts/adaptive_k_selector.py --model qwen2.5:7b
```

---

## 5. Sweep Execution Workflow

### 5.1 Pre-sweep Checklist

```bash
# 1. Verify no model is pinned in RAM
ollama ps   # must show empty table before starting

# 2. Check available disk space (need ≥ model_size + 2 GB headroom)
df -h /

# 3. Pull required models (do NOT use `ollama run` — it pins RAM)
ollama pull <model-name>

# 4. Verify index is current
uv run python scripts/afs_index.py --check
```

**RAM filter rule**: Exclude models requiring > 60% of available system RAM. On 16 GB systems this means excluding models > 9 GB. On 8 GB systems, models > 4.5 GB cause disk swap and false-negative timeouts (hardware-constrained, not model-limited).

### 5.2 Running a Sweep

```bash
# Baseline (top-k=10, standard template)
bash scripts/run_model_sweep.sh --variant baseline --models qwen2.5:1.5b,granite3.3:2b

# Option A: Top-k=20 ablation (isolates retrieval volume effect)
bash scripts/run_model_sweep.sh --variant optiona --models qwen2.5:1.5b,granite3.3:2b

# Option B: Enhanced prompt engineering (isolates prompt framing effect)
bash scripts/run_model_sweep.sh --variant optionb --models qwen2.5:1.5b,granite3.3:2b

# Option C: k=20 + Reasoning-First prompt (full factorial)
bash scripts/run_model_sweep.sh --variant optionc --models qwen2.5:7b,gemma2:9b

# Dry run (validate config without executing)
bash scripts/run_model_sweep.sh --variant optionc --dry-run
```

**Variant reference**:

| Variant | top-k | Template | Study ID | Purpose |
|---------|-------|----------|----------|---------|
| `baseline` | 10 | `rag_answer.md` | `study-2a` | Control group |
| `optiona` | 20 | `rag_answer.md` | `study-2a-topk20` | Isolate retrieval volume |
| `optionb` | 10 | `rag_answer_optionb.md` | `study-2a-optionb` | Isolate prompt framing |
| `optionc` | 20 | `rag_answer_optionc.md` | `study-2a-optionc` | Full factorial (k=20 + Reasoning-First) |

### 5.3 Rescoring with LLM-as-Judge

Pattern-match scoring underestimates complex reasoning. Always rescore Tier-2 results with the LLM judge:

```bash
# Rescore a study with phi3:mini judge (fast, low-RAM)
uv run python scripts/batch_rescore_judge.py --study study-2a --judge-model ollama/phi3:mini

# Dry run (count queries without rescoring)
uv run python scripts/batch_rescore_judge.py --study study-2a --dry-run

# In-place overwrite (default writes *-rescored.jsonl)
uv run python scripts/batch_rescore_judge.py --study study-2a --in-place
```

**Calibration note**: `phi3:mini` is the validated judge model for this corpus — produces stable scores in < 2s per query on 8 GB systems. Do not switch judge models mid-study; it recalibrates the scoring baseline.

### 5.4 Backfilling Machine Metadata

After each sweep, backfill hardware context into result artifacts:

```bash
uv run python scripts/backfill_machine_metadata.py --study study-2a
```

This adds `machine_metadata` (CPU, RAM, OS, Python version) to every JSONL entry — essential for reproducing results across different hardware environments.

---

## 6. Lessons Learned (Study 2a)

These encoded findings inform how to run future sweeps:

**L1 — Non-quant can outperform quant**: `llama3:8b` (non-quant) was faster than `llama3.1:8b-q4` on 16 GB Apple Silicon. Do not assume "smaller quantized = faster" without benchmarking.

**L2 — Timeout ≠ capability**: Models causing disk swap (> 60% RAM) produce > 420s inference times. This is a hardware failure, not a quality signal. Filter by RAM ceiling first.

**L3 — Family alignment dominates at 7B+**: Embedding-space alignment predicts retrieval quality better than parameter count at the 7–9B tier. Validate family alignment before investing GPU time in a new model.

**L4 — RAM floor vs RAM ceiling**: Ollama RAM management uses a *floor* (`initial_ram - 1.5 GB`) to detect post-inference cleanup, not a ceiling. This prevents premature model-unload calls when RAM readings fluctuate during inference.

**L5 — Small N inflates variance**: 9 queries (N=1 per task type) produces high variance (σ = 0.73 in Study 2a Option C). Individual model scores are unreliable at N=1. Use Study 2b to expand to ≥ 3 queries per task type.

**L6 — LLM judge calibration**: Study 2a showed 10–40× score improvement over pattern-match (e.g., `qwen:0.5b`: 0.28 LLM-judge vs 0.007–0.026 pattern-match). The LLM judge is the authoritative score source for Tier-2 queries.

---

## 7. Guardrails

- **Unload before sweep**: Always `ollama ps` before starting. Use `ollama stop <model>` if anything is pinned.
- **Disk headroom**: Ensure ≥ 2 GB free disk headroom beyond the model size before pulling.
- **Never `ollama run`**: This pins the model in RAM. Use `ollama pull` to fetch; let the API load on demand.
- **No manual lock-files**: Never edit `rag-index/manifest.json` or `rag-index/rag_index.sqlite3` directly.
- **Cite the judge**: Always record `judge_model` in result artifacts — scores are not comparable across judge models.
- **Archive with metadata**: Always run `backfill_machine_metadata.py` before archiving results. Bare JSONL without hardware context cannot be reproduced.

---

**Closes Issue**: #342 (Rapid Research Workflow)
**Governance**: L2 Specialized Skill
**Evidence base**: [Study 2a Synthesis](../../docs/research/2026-03-22-rag-study-2a-synthesis.md) · [Session notes 2026-03-21/22](../../.tmp/research-rag-stress-test-quantization/)
