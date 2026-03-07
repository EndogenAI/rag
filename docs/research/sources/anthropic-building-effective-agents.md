---
title: "Building effective agents"
url: "https://www.anthropic.com/engineering/building-effective-agents"
slug: "anthropic-building-effective-agents"
type: blog
cached_at: "2026-03-06"
cache_path: ".cache/sources/anthropic-building-effective-agents.md"
topics: [agents, workflows, orchestration, tool-design, evaluator-optimizer]
---

# Building Effective Agents

**URL**: https://www.anthropic.com/engineering/building-effective-agents  
**Type**: blog  
**Cached**: `uv run python scripts/fetch_source.py https://www.anthropic.com/engineering/building-effective-agents --slug anthropic-building-effective-agents`

## Summary

Published December 19, 2024 by Erik Schluntz and Barry Zhang of Anthropic Engineering, this post synthesises lessons from working with dozens of teams across industries who are building LLM-powered agentic systems in production. The central thesis is that the most successful implementations favour simple, composable patterns over complex frameworks or specialised libraries. The post draws a hard architectural distinction between *workflows* (LLMs orchestrated through predefined code paths) and *agents* (LLMs that dynamically direct their own processes and tool usage), arguing this distinction should drive architectural choices before any code is written. It surveys five canonical patterns — prompt chaining, routing, parallelization, orchestrator-workers, and evaluator-optimizer — and closes with two appendices covering real-world agent domains and tool prompt-engineering. The evaluator-optimizer loop and the concept of the Agent-Computer Interface (ACI) are the two standout contributions for practitioners building production fleets.

## Key Claims

- > "Consistently, the most successful implementations weren't using complex frameworks or specialized libraries. Instead, they were building with simple, composable patterns."
- **Workflows vs. Agents** is a hard architectural boundary, not a spectrum: workflows use predefined code paths; agents dynamically direct their own processes and tool usage.
- **Simplest solution first**: Anthropic recommends finding the simplest solution and only increasing complexity when it demonstrably improves outcomes — including the option of not building agentic systems at all.
- **Prompt chaining** decomposes tasks into sequential LLM calls with programmatic gate checks between steps to verify progress before proceeding to the next step.
- **Routing** classifies an input and directs it to a specialised downstream prompt; without it, optimising for one input type degrades performance on all other input types.
- **Parallelization** manifests as either sectioning (independent subtasks in parallel) or voting (same task run multiple times for higher-confidence aggregated output).
- **Orchestrator-workers** suits tasks where subtasks cannot be predicted in advance — the orchestrator dynamically breaks down work and delegates to worker LLMs based on the specific input, unlike parallelization where subtasks are pre-defined.
- **Evaluator-optimizer loop** runs one LLM call to generate and another to evaluate and provide feedback in a loop; ideal when iterative refinement produces measurable improvement against clear evaluation criteria.
- **Agent-Computer Interface (ACI)**: tool definitions and specifications deserve the same prompt-engineering attention as overall system prompts — including example usage, edge cases, input format requirements, and Poka-yoke constraints that make model mistakes structurally harder to make.
- > "For the SWE-bench implementation, we actually spent more time optimising our tools than the overall prompt."
- **Stopping conditions are mandatory**: agents operating over many turns must have a maximum iteration count or other explicit terminating condition to maintain control; autonomous nature means higher costs and compounding errors.
- > "We suggest that developers start by using LLM APIs directly: many patterns can be implemented in a few lines of code."
- **Ground-truth at each step**: during execution, agents must obtain observable environmental feedback (tool results, code execution outputs) at each step to assess and steer their own progress.

## Relevance to EndogenAI

The evaluator-optimizer pattern described here is the direct conceptual ancestor of the EndogenAI Reviewer phase gate — `research-reviewer.agent.md` evaluates Synthesizer output and feeds back in a loop exactly as prescribed here, and this source provides precise language to sharpen that agent's mandate in its instructions block. The orchestrator-workers pattern maps precisely onto the Executive Researcher delegating to Scout, Synthesizer, and Archivist sub-agents, validating the current architecture, but also exposing a gap: there is no explicit stopping condition (maximum iteration count or budget ceiling) in `executive-researcher.agent.md`, which this source says is mandatory for agent control. The ACI appendix indicts the current state of tool documentation in EndogenAI scripts — `scripts/fetch_source.py` and `scripts/link_source_stubs.py` lack parameter-level docstrings and usage examples of the kind Anthropic recommends, and adopting that practice would reduce agent tool-use errors in live sessions. The routing workflow is notably absent from the EndogenAI research pipeline: the Scout currently receives all research queries without a classification gate that would route narrow factual queries to a simpler path and reserve full multi-source research for broad synthesis questions. The workflows-vs-agents distinction has direct import for `docs/guides/agents.md`, which currently conflates the two; this source provides precise, Anthropic-endorsed language to sharpen that guide.

## Referenced By

<!-- Populated automatically by scripts/link_source_stubs.py — do not edit manually -->
