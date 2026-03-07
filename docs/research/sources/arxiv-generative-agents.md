---
slug: arxiv-generative-agents
title: "Generative Agents: Interactive Simulacra of Human Behavior"
url: https://arxiv.org/abs/2304.03442
cached: true
type: paper
topics: [memory-architecture, agent-design, episodic-memory, reflection, planning]
date_synthesized: 2026-03-06
---

## Summary

Park et al. (arXiv:2304.03442, Stanford, 2023) introduce generative agents — computational agents that simulate believable human behaviour in an interactive sandbox. The architecture extends an LLM with a complete natural-language experience record, synthesises memories into higher-level reflections over time, and retrieves them dynamically for planning. The paper demonstrates that observation, planning, and reflection each independently contribute to believable behaviour.

## Key Claims

- Agent architecture has three components: observation (recording experiences), planning (generating behavioural plans), and reflection (synthesising memories into higher-level insights).
- "A complete record of the agent's experiences using natural language" is stored and retrieved dynamically — episodic memory as first-class architecture.
- Ablation confirms that removing any single component (observation, planning, or reflection) meaningfully degrades emergent social behaviour.
- Memory retrieval is time-decayed, relevance-weighted, and recency-boosted — not pure semantic similarity.

## Relevance to EndogenAI

This paper provides the theoretical grounding for episodic memory as a distinct architectural concern, supporting the memory gap analysis in the agentic-research-flows synthesis. The reflection mechanism (synthesising episodic memories into higher-level heuristics) maps conceptually to the `_index.md` stub archive and the Copilot memory tool, though neither implements the dynamic retrieval or weighting described here. The observation→planning→reflection loop is a structural analogue to the EndogenAI Scout→Synthesizer→Archivist flow.

## Referenced By

<!-- Will be filled in by issue synthesis pass -->
