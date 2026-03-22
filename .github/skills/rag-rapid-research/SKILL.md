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

## 1. Overview
This skill encodes the "Rapid Prototyping Research" workflow for executing factorial RAG sweeps. It optimizes for local compute-first evaluation using tiered stressors and reasoning density diagnostics.

## 2. RAG Stressor Progression (Tier 0-3)

| Tier | Focus | Diagnostic | Success Metric |
|------|-------|------------|----------------|
| **Tier 0** | Baseline Retrieval | Hits@K | NDCG@10 > 0.8 |
| **Tier 1** | Distraction Tolerance | Noise Filtering | Zero Hallucination in irrelevant context |
| **Tier 2** | Reasoning Density | **Reasoning Density Threshold** (RDT) | ≥ 3 distinct inferential leaps per answer |
| **Tier 3** | Multi-hop Synthesis | Cross-Document Join | Verified synthesis of ≥ 2 non-adjacent facts |

**Reasoning Density Threshold (RDT)**: A key diagnostic measuring the ratio of inferential logic steps to total token count. Low density indicates "trendslop" or paraphrasing; high density indicates active synthesis.

## 3. Workflow
1. **Source Warming**: Run `uv run python scripts/fetch_source.py <url> --check` for all sweep targets.
2. **Index Mutation**: Use `scripts/afs_index.py` with experimental chunking variants.
3. **Execution**: Run `bash scripts/run_model_sweep.sh --variant <name> --models <list>`.
4. **Distillation**: Archive results in `data/benchmark-results/` with machine metadata.

## 4. Guardrails
- **Unload Models**: Always run `ollama ps` before a sweep. Use `ollama stop <model>` to clear RAM.
- **Disk Headroom**: Ensure ≥ 10GB free disk before pulling new quantization variants.
- **No Manual Lock-files**: Never edit `rag-index/manifest.json` by hand.

---
**Closes Issue**: #342 (Rapid Research Workflow)  
**Governance**: L2 Specialized Skill
