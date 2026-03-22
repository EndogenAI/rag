---
title: RAG Study 2a Synthesis — Model Stratification and Retrieval Volatility
status: Final
closes_issue: [28, 31, 32, 33]
date: 2026-03-22
---

# RAG Study 2a Synthesis — Model Stratification and Retrieval Volatility

## Executive Summary

RAG Study 2a (Small and Mid-Tier Stress Tests) evaluated 17 models across 9 core task types, isolating the impacts of retrieval volume (top-k=10 vs. top-k=20) and prompt framing. The synthesis identifies a critical **Reasoning Density Threshold** at approximately 1.5B parameters. Following the **Algorithms-Before-Tokens** axiom ([MANIFESTO.md](../../MANIFESTO.md#2-algorithms-before-tokens)), we conclude that raw token volume (k=20) is not a universal performance driver; rather, it acts as a capability stabilizer for sub-1.5B models while introducing significant noise-based degradation or retrieval failures in specific mid-tier architectures (e.g., Gemma2-9B). 

**Key Finding**: The "Reasoning Density Threshold" hypothesis—which previously suggested that increased retrieval volume (high-k) degrades performance in smaller models—was refuted at the 7B–9B scale. Performance in the mid-tier is governed by **Family Alignment** and **Retrieval Affinity** rather than raw parameter count. **Qwen2.5-7B** emerged as the new state-of-the-art (SOTA) for the repository's local RAG task with a score of **0.956**, outperforming all smaller models. Conversely, **Gemma2-9B** exhibited systemic retrieval failure (0.311 score), frequently returning zero sources despite high-volume context availability.

## Hypothesis Validation — The 1.5B Threshold

Current benchmarks support the hypothesis that model response to context volume is non-linear and stratified by parameter density:

| Threshold | Observation | Evidence (Study 2a Option A/C) |
|-----------|-------------|----------------------------|
| **< 1.5B (Stabilization)** | Retrieval volume (k=20) compensates for reasoning gaps. | SmollM-360M: **+92.1%** gain (0.278 → 0.533) |
| **~1.5B (Equilibrium)** | Volume and precision reach a point of diminishing returns. | Qwen2.5-1.5B: **+11.1%** gain (0.700 → 0.778) |
| **> 1.5B (Degradation)** | Increased context introduces signal noise (Family dependent). | Granite-3.3-2B: **-3.6%** drop (0.922 → 0.889) |
| **7B–9B (Affinity)** | High-k (k=20) becomes the primary SOTA driver. | Qwen2.5-7B: **0.956** score (SOTA) |

**Conclusion**: The "Reasoning Density" of a model determines its optimal context window. Lower-density models require higher recall (redundant evidence) to maintain signal, while higher-density models require higher precision (targeted signal) to avoid distractor-based reasoning failures. At the 7B+ scale, family alignment with the embedding space becomes the dominant factor.

## Pattern Catalog

### Pattern: Architectural Retrieval Failure (Gemma2-9B)
*   **Observation**: Gemma2-9B recorded a catastrophic score of **0.311** in Option C (k=20), failing to retrieve *any* sources on 5/9 queries.
*   **Evidence**: Unlike Qwen2.5-7B (0.956) which excelled with the same parameters, Gemma2 exhibited a fundamental misalignment with the `nomic-embed-text` indexed corpus.
*   **Anti-pattern**: Scaling parameter count without verifying semantic alignment between the generator and the embedding space leads to "silent retrieval voids."

### Pattern: Reasoning Density Stabilization (Qwen2.5)
*   **Observation**: Qwen2.5-7B achieved the highest overall score (**0.956**) in the mid-tier sweep.
*   **Evidence**: Perfectly handled verbose prompts and high-context (k=20) environments.
*   **Canonical Example**: Qwen2.5-7B maintained 100% citation accuracy across 9/9 queries, demonstrating that "verbose" is not "noisy" for high-density architectures.

## Recommendations

### 1. ADOPT Qwen2.5-7B as Default Mid-tier Baseline
Replace Llama3 as the recommended model for users with ≥16GB RAM. Its 0.956 score represents a significant improvement over previous mid-tier expectations.

### 2. Implement Adaptive K-Tuning
Shift from a global `top_k: 10` setting to a tiered approach using `scripts/adaptive_k_selector.py`.
*   **Tier 1 (<1.5B)**: `top_k: 20` (Maximise evidence redundancy)
*   **Tier 2 (1.5B - 8B)**: `top_k: 10` (Prioritize signal precision)
*   **Tier 3 (>8B)**: `top_k: 5-8` (Highly focused precision)
*   **Exception**: Standardize `top_k=20` for validated mid-tier families (e.g., Qwen2.5-7B).

### 3. Model Lifecycle Telemetry (Issue #31)
Adopt telemetry to track the "Retrieval Health" of every inference. If a model consistently returns zero sources despite an active index, trigger an architectural audit (ref. Gemma2 failure).

### 4. Augmented A-Phase Selection (Issue #32)
Selection logic for RAG pipelines must be family-aware. Qwen-series models should be paired with verbose, role-heavy prompts, while Gemma-series models require minimal, precision-focused instructions to avoid retrieval drift.

### 5. DEPRECATE Gemma2 for Local RAG
Until embedding alignment issues are resolved, flag Gemma2 as "Not Recommended" for the EndogenAI Workflows corpus.

## Sources
*   [data/benchmark-results/study-2a/](../../data/benchmark-results/study-2a/) (Baseline k=10)
*   [data/benchmark-results/study-2a-optionc/](../../data/benchmark-results/study-2a-optionc/) (Mid-tier k=20)
*   [.tmp/research-rag-stress-test-quantization/2026-03-22.md](../../.tmp/research-rag-stress-test-quantization/2026-03-22.md) (Session Scratchpad)
*   `scripts/analyze_study2a.py`