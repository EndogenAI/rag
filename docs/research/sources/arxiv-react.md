---
slug: arxiv-react
title: "ReAct: Synergizing Reasoning and Acting in Language Models"
url: https://arxiv.org/abs/2210.03629
cached: true
type: paper
topics: [agent-reasoning, ReAct, thought-action-observation, hallucination-reduction]
date_synthesized: 2026-03-06
---

## Summary

Yao et al. (arXiv:2210.03629, ICLR 2023) introduce ReAct — a framework that interleaves reasoning traces (Thought) with task-specific actions (Action) and observations (Observation) in language model inference. On question answering and fact verification benchmarks, ReAct outperforms chain-of-thought-only methods by grounding reasoning in external API results, significantly reducing hallucination. On interactive decision-making benchmarks, ReAct outperforms imitation and reinforcement learning methods by 34% and 10% absolute success rate respectively.

## Key Claims

- "ReAct overcomes issues of hallucination and error propagation prevalent in chain-of-thought reasoning by interacting with a simple Wikipedia API."
- The Thought→Action→Observation trace structure is the canonical interleaved reasoning pattern — each thought updates the agent's plan; each observation refines it.
- ReAct generates "human-like task-solving trajectories that are more interpretable than baselines without reasoning traces."
- ICLR camera-ready version; project site with code: https://react-lm.github.io

## Relevance to EndogenAI

ReAct's Thought→Action→Observation trace is the theoretical grounding for the explicit reasoning step recommendation in agent files. The Anthropic cookbook's OODA loop (Observe/Orient/Decide/Act) is the production equivalent of ReAct's trace structure. EndogenAI agent files do not currently enforce this trace for research-phase tasks — encoding it as a prompt principle in research agent files would reduce hallucination risk during scouting phases.

## Referenced By

<!-- Will be filled in by issue synthesis pass -->
