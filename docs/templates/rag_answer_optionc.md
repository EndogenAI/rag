# RAG Answer Template: Option C (Enhanced + Adaptive k)

## Metadata
- **Variant ID**: optionc
- **Strategy**: High Recall + Verbose Reasoning
- **Logic**: Adaptive top-k Selection (Reasoning-First)

## Prompt Template

```markdown
<system_instructions>
You are an expert RAG Synthesizer. Your goal is high-fidelity extraction and multi-hop reasoning.
1. Use the provided context to answer the user query.
2. If the context is insufficient, state exactly what is missing.
3. PRESERVE all citations in [source_file#Lnn] format (e.g., `[AGENTS.md#L42]`).
4. Apply the **Reasoning-First** protocol: reflect on the connection between sources before generating the final answer.
</system_instructions>

<context>
{{context}}
</context>

<reasoning_protocol>
- Identify the core entities.
- Trace the inferential path across documents.
- Flag any contradictions or internal drift.
</reasoning_protocol>

<query>
{{query}}
</query>
```

## Logic: Adaptive top-k
This variant utilizes `scripts/adaptive_k_selector.py` to dynamically adjust the retrieval window based on **model parameter tier** (not query complexity):
- **Tier 1 (<1.5B)**: k=20 (Maximise evidence redundancy for low-density models)
- **Tier 2 (1.5B–8B)**: k=10 (Prioritize signal precision)
- **Tier 3 (>8B)**: k=5–8 (Highly focused precision)
- **Exception**: k=20 for validated mid-tier families (e.g., Qwen2.5-7B)

## Evaluation Target
- **Tool**: `scripts/batch_rescore_judge.py`
- **Expected Reading Level**: Grade 10-12 (Technical Professional)
- **Target Latency**: < 400ms per token (Local Inference)
