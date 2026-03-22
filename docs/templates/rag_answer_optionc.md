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
3. PRESERVE all citations in [Source N] format.
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
This variant utilizes `scripts/adaptive_k_selector.py` to dynamically adjust the retrieval window based on query complexity:
- **Informational**: k=3 (Precision-weighted)
- **Comparative**: k=7 (Recall-weighted)
- **Synthetic/Complex**: k=12 (Reasoning-weighted)

## Evaluation Target
- **Tool**: `scripts/batch_rescore_judge.py`
- **Expected Reading Level**: Grade 10-12 (Technical Professional)
- **Target Latency**: < 400ms per token (Local Inference)
