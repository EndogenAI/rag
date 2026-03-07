---
title: "Anthropic Cookbook: Research Subagent Prompt"
url: "https://github.com/anthropics/anthropic-cookbook (multiagent_network/research_subagent.py)"
slug: "cookbook-research-subagent"
type: cookbook
cached_at: "2026-03-06"
cache_path: ".cache/sources/cookbook-research-subagent.md"
topics: [subagent, OODA-loop, tool-budget, source-quality, research-execution]
---

# Anthropic Cookbook: Research Subagent Prompt

**URL**: https://github.com/anthropics/anthropic-cookbook (multiagent_network/research_subagent.py)  
**Type**: cookbook  
**Cached**: `uv run python scripts/fetch_source.py https://github.com/anthropics/anthropic-cookbook --slug cookbook-research-subagent`

## Summary

This source is the full system prompt for the Research Subagent from Anthropic's official multiagent_network cookbook example — the worker agent that executes individual research tasks delegated by the Research Lead. The prompt is structured with XML-tagged sections covering the research process, research guidelines, source quality evaluation, parallel tool usage, and absolute resource limits. Its central contribution is the operationalisation of the OODA loop (Observe-Orient-Decide-Act) as the step-level reasoning cycle that drives every tool call, combined with a quantitative tool-call budget that scales to task difficulty. The source also provides the most detailed source-quality red-flag taxonomy in the corpus, explicitly naming speculative language patterns, false authority, passive-voice anonymous sourcing, and cherry-picked data as failure modes that must be flagged — not silently presented — in reports to the lead agent.

## Key Claims

- **OODA loop is the prescribed reasoning cycle**: > "Execute an excellent OODA (observe, orient, decide, act) loop by (a) observing what information has been gathered so far... (b) orienting toward what tools and queries would be best... (c) making an informed, well-reasoned decision... (d) acting to use this tool."
- **Quantitative tool-call budget by difficulty**: simple tasks → under 5 tool calls; medium → ~5; hard → ~10; very difficult/multi-part → up to 15. > "Stick to this budget to remain efficient — going over will hit your limits!"
- **Internal tools take strict priority**: > "ALWAYS use internal tools (google drive, gmail, calendar, or similar other tools) for tasks that might require the user's personal data, work, or internal context... Internal tools strictly take priority."
- **Core search loop is search-then-fetch**: > "The core loop is to use web search to run queries, then use web_fetch to get complete information using the URLs of the most promising sources."
- **Absolute hard cap**: 20 tool calls and 100 sources maximum per subagent invocation before forced `complete_task` call.
- **Source quality red-flag list**: speculation with future tense, passive voice with nameless sources, false authority, general qualifiers without specifics, unconfirmed reports, marketing language, spin language, misleading/cherry-picked data — all must be flagged explicitly rather than accepted as fact.
- **Never repeat identical queries**: > "NEVER repeatedly use the exact same queries for the same tools, as this wastes resources and will not return new results."
- **Parallel tool calls are preferred**: > "Invoke 2 relevant tools simultaneously rather than sequentially."
- **Query width calibration**: use moderately broad queries under 5 words; hyper-specific queries have poor hit rates; narrow only when results are abundant.
- **Diminishing-returns termination**: > "Avoid continuing to use tools when you see diminishing returns — when you are no longer finding new relevant information and results are not getting better, STOP using tools and instead compose your final report."
- **Conflict escalation**: when conflicting facts cannot be reconciled, include the conflict in the final report for the lead researcher to resolve — do not silently drop one version.

## Relevance to EndogenAI

This is the canonical reference implementation for `research-scout.agent.md` in the EndogenAI fleet. The OODA loop maps directly to the step-by-step observation pattern the Scout is meant to follow, but the current `research-scout.agent.md` does not name OODA explicitly — adopting the OODA framing would tighten the loop description and give the agent clearer step terminology during self-reflection. The tool-call budget ladder (5–15 calls by difficulty) is entirely absent from the current Scout instructions, and adding it as a `## Research Budget` section would prevent both under-research (returning too early) and runaway thrashing (exceeding context limits). The source-quality red-flag taxonomy is the most directly actionable finding for the `research-synthesizer.agent.md` — the Synthesizer's `## Discard freely` principle needs a concrete list of red flags to act on, and this source provides exactly that vocabulary (speculation cues, false authority, marketing language). The "never repeat identical queries" principle reinforces the `fetch-before-act` posture in AGENTS.md — checking `.cache/sources/` before fetching is the structural analogue of not re-running duplicate tool calls. The conflict-escalation pattern (flag conflicts, don't silently drop) should be adopted as an explicit instruction in the Scout's output format, since the current scratchpad format does not distinguish confirmed facts from contested ones.

## Referenced By

<!-- Populated automatically by scripts/link_source_stubs.py — do not edit manually -->
