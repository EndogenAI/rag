# RAG Judge Prompt Template (v1.0.0)

## Template Body

```
Score this RAG answer on a 0-1 scale:

Question: {query}
Answer: {answer}

Rubric: {rubric}

Preflight Signals:
{preflight_signals}

Return only a score (0.0, 0.5, or 1.0) and brief reasoning.
```

## Rationale

This template externalizes the judge prompt to enable:
1. **Versioning** — judge prompt changes are tracked via git, not buried in code
2. **Auditing** — research sessions can cite a specific template version (e.g., "v1.0.0")
3. **Iteration** — preflight signal integration happens at template level, not scattered across function calls
4. **Reproducibility** — same template version + same inputs = deterministic judge behavior across runs

Preflight signals are computed programmatically before the LLM judge call; they inform the judge's evaluation by surfacing patterns (entity presence, citation discipline, substantiveness) that can be checked deterministically.

## Placeholders

- `{query}` — User's original question from test case
- `{answer}` — RAG system's generated response
- `{rubric}` — Tier-specific evaluation rubric from test case
- `{preflight_signals}` — YAML-formatted preflight check results (entity_hit_rate, pattern_hit_rate, is_substantive, cites_source, has_chunks)

## Example Usage

```python
template = load_judge_template()
preflight = run_preflight_checks(answer, test_case, retrieved_chunks)
signals_yaml = yaml.dump(preflight, default_flow_style=False)

prompt = template.format(
    query=test_case["query"],
    answer=answer,
    rubric=test_case.get("judge_rubric", ""),
    preflight_signals=signals_yaml
)
```

## Version History

- **v1.0.0** (2026-03-21): Initial extraction from inline judge_prompt in benchmark_rag.py; added preflight_signals placeholder
