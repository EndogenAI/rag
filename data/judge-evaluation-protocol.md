# RAG Judge Evaluation Protocol

## Overview

**Purpose**: Enable reproducible, calibrated evaluation of RAG system responses across multiple judge models and benchmark runs. This protocol defines standardized tier assignment, preflight signal interpretation, judge prompt templating, and scoring calibration for tier-2 questions requiring LLM-as-judge assessment.

**Scope**: Applies exclusively to tier-2 questions in `data/rag-benchmarks.yml`. Tier-1 questions use deterministic pattern matching and are not subject to this protocol.

**Components**: This protocol integrates three artifacts:
- `data/judge-preflight-checks.yml` — defines preflight signal computation
- `data/judge-prompt-template.md` — standardized judge prompt template
- Tier-2 question rubrics in `data/rag-benchmarks.yml` — explicit scoring criteria per question

---

## Tier Assignment Guidelines

| Question Type | Tier | Evaluation Method | Example |
|---|---|---|---|
| Entity extraction | 1 | Pattern matching | "List all commit types" → match `feat\|fix\|docs\|chore\|test\|refactor\|ci\|perf` |
| Simple pattern rules | 1 | Pattern matching | "What is the heredoc prohibition?" → match `heredoc\|<< 'EOF'\|cat >>` |
| Multi-hop reasoning | 2 | LLM-as-judge | "Which agent handles research, and what tools?" → requires linking agent role → tool list |
| Quantitative reasoning | 2 | LLM-as-judge | "Calculate timeout for 500 tests" → requires reading timeout table + arithmetic |
| Constraint resolution | 2 | LLM-as-judge | "Can subagents commit after Review approval?" → requires checking multiple constraint statements |
| Cross-document synthesis | 2 | LLM-as-judge | "Describe the full orchestration cycle" → requires understanding phase → delegation → review flow |

**Decision Rule**: Assign tier-2 when answer quality depends on reasoning depth, multi-step inference, or cross-source synthesis that cannot be verified with regex patterns alone.

---

## Preflight Signals Reference

Preflight signals are computed before judge invocation and inform scoring decisions:

- **`entity_hit_rate`** (float, 0.0–1.0): Fraction of expected entities (from `expected_entities` list) present in the answer. Entity matches are case-insensitive substring checks. A rate < 0.5 suggests incomplete recall.

- **`pattern_hit_rate`** (float, 0.0–1.0): Fraction of expected patterns (from `expected_patterns` list, regex) matched in the answer. A rate < 0.5 suggests missing expected content.

- **`is_substantive`** (bool): Answer contains ≥20 tokens. False indicates a likely stub or refusal response.

- **`cites_source`** (bool): Answer mentions at least one source file (e.g., `AGENTS.md`, `scripts/fetch_source.py`). True suggests grounding in retrieved context.

- **`has_chunks`** (bool): Retrieval returned non-empty chunks. False indicates retrieval failure; answer is likely hallucinated.

**Interpretation**: Preflight signals are advisory, not deterministic. A low `entity_hit_rate` may still yield a 1.0 score if the answer is semantically complete and rubric-compliant. Conversely, high hit rates do not guarantee quality if reasoning is flawed.

---

## Judge Prompt Template Usage

**Step 1**: Load template from `data/judge-prompt-template.md`:

```python
with open("data/judge-prompt-template.md") as f:
    template = f.read()
```

**Step 2**: Substitute placeholders:

- `{question}` → tier-2 question text
- `{answer}` → RAG system output
- `{rubric}` → question-specific scoring criteria from `data/rag-benchmarks.yml`
- `{preflight_signals}` → YAML-formatted preflight signal dict

**Step 3**: Format preflight signals as YAML:

```python
import yaml
preflight = {
    "entity_hit_rate": 0.75,
    "pattern_hit_rate": 0.5,
    "is_substantive": True,
    "cites_source": True,
    "has_chunks": True
}
signals_yaml = yaml.dump(preflight, default_flow_style=False)
```

**Step 4**: Perform substitution and invoke judge:

```python
prompt = template.format(
    question=q["question"],
    answer=rag_output,
    rubric=q["rubric"],
    preflight_signals=signals_yaml
)
score = judge_model.invoke(prompt)  # returns 0.0, 0.5, or 1.0
```

**Example** (full substitution):

```
Question: Which agent handles research, and what tools does it use?

Answer: The Executive Researcher agent handles research. It uses `search`, `read`, `web`, and `agent` tools.

Rubric: Award 1.0 if answer names Executive Researcher and lists correct tools (search, read, web, agent). Award 0.5 if agent correct but tools incomplete. Award 0.0 if wrong agent.

Preflight Signals:
entity_hit_rate: 1.0
pattern_hit_rate: 0.75
is_substantive: true
cites_source: false
has_chunks: true

Based on the above, assign a score of 0.0, 0.5, or 1.0.
```

---

## Score Interpretation

**1.0 (Full Credit)**:
- Answer fully satisfies all rubric criteria
- All expected elements (entities, patterns, reasoning steps) present
- Preflight signals support quality (high hit rates, substantive, grounded)
- No hallucinations or contradictions detected

**0.5 (Partial Credit)**:
- Answer partially satisfies rubric
- 1–2 expected elements present OR reasoning correct but incomplete
- May have low `entity_hit_rate` but semantically aligned
- Minor omissions or imprecision, but core understanding demonstrated

**0.0 (No Credit)**:
- Answer fails rubric entirely
- No expected elements present OR wrong reasoning
- Hallucination detected (answer contradicts known facts)
- Refusal, stub, or off-topic response

**Edge Cases**:
- If preflight signals conflict with rubric (e.g., high hit rates but wrong reasoning), prioritize rubric alignment over signal values.
- If answer uses synonyms or paraphrases not in `expected_entities`, judge should credit semantic equivalence.

---

## Rubric Authoring Guidelines

When creating tier-2 questions, write explicit 3-level scoring criteria:

1. **Reference expected elements**: Cite specific `expected_entities` or `expected_patterns` where applicable.

2. **Define "complete" vs "partial" vs "failed"**:
   - Complete: All required elements + correct reasoning
   - Partial: Core element(s) present but incomplete or imprecise
   - Failed: Missing core elements OR wrong reasoning

3. **Keep rubric ≤100 tokens**: Brevity ensures judge focus and reduces variance.

4. **Example rubric** (quantitative reasoning):
   ```
   Award 1.0 if answer calculates 600s (500 tests × 120s ceiling from timeout table).
   Award 0.5 if answer cites correct table but wrong arithmetic.
   Award 0.0 if no calculation or wrong source table.
   ```

5. **Example rubric** (constraint resolution):
   ```
   Award 1.0 if answer states "subagents cannot commit; only GitHub agent commits after Review approval."
   Award 0.5 if answer mentions Review gate but unclear on GitHub agent exclusivity.
   Award 0.0 if answer allows subagent commits without Review.
   ```

**Anti-pattern**: Rubrics that restate the question without defining success criteria (e.g., "Award 1.0 if answer is correct").

---

## Calibration Recommendations

**1. Paired Test Set**:
- Assemble 5 known-good and 5 known-bad answer pairs for each tier-2 question
- Run judge on all pairs; verify known-good → 1.0 and known-bad → 0.0
- If any pair misclassifies, revise rubric or preflight thresholds

**2. Variance Check**:
- Run judge 3 independent times on same question-answer pair
- Verify score variance < 0.1 across runs
- High variance indicates rubric ambiguity or judge model instability

**3. Preflight-Rubric Alignment**:
- Document cases where preflight signals conflict with rubric consensus (e.g., high hit rates but wrong reasoning)
- Update rubrics to clarify priority (rubric > signals)
- If conflicts are common, refine `expected_entities` or `expected_patterns`

**4. Human Judgment Audit**:
- Periodically sample 10–20 judge scores and compare to human evaluation
- If judge-human agreement < 80%, investigate systematic bias
- Update rubrics to encode human judgment patterns

**5. Model-Specific Calibration**:
- Test multiple judge models (e.g., GPT-4, Claude, Gemini) on same question set
- Document inter-judge agreement; flag questions with high disagreement
- Prefer judge models with ≥90% intra-judge consistency

---

## Appendix: File References

- **Tier-2 questions**: `data/rag-benchmarks.yml` (questions with `rubric` field)
- **Preflight signal definitions**: `data/judge-preflight-checks.yml`
- **Judge prompt template**: `data/judge-prompt-template.md`
- **Benchmark runner**: `scripts/benchmark_rag.py` (orchestrates evaluation)
- **Evaluation results**: `data/benchmark-results/index.jsonl` (logged scores per run)
