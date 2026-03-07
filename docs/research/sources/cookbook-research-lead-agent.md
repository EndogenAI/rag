---
title: "Anthropic Cookbook: Research Lead Agent Prompt"
url: "https://github.com/anthropics/anthropic-cookbook (multiagent_network/research_lead_agent.py)"
slug: "cookbook-research-lead-agent"
type: cookbook
cached_at: "2026-03-06"
cache_path: ".cache/sources/cookbook-research-lead-agent.md"
topics: [research-orchestration, subagent-delegation, query-classification, prompt-template, xml-structured-prompts]
---

# Anthropic Cookbook: Research Lead Agent Prompt

**URL**: https://github.com/anthropics/anthropic-cookbook (multiagent_network/research_lead_agent.py)  
**Type**: cookbook  
**Cached**: `uv run python scripts/fetch_source.py https://github.com/anthropics/anthropic-cookbook --slug cookbook-research-lead-agent`

## Summary

This source is the full system prompt for the Research Lead Agent from Anthropic's official multiagent_network cookbook example — a production-grade prompt template for an orchestrating LLM that plans, delegates, and synthesises multi-source research. The prompt is structured with XML-tagged operational sections (`<research_process>`, `<delegation_instructions>`, `<subagent_count_guidelines>`, `<answer_formatting>`, `<use_available_internal_tools>`, `<use_parallel_tool_calls>`, `<important_guidelines>`) that the lead agent reads and follows at runtime. The core contribution is a four-step research process — query assessment, query-type classification, research plan development, and methodical plan execution — with explicit subagent count heuristics calibrated to query complexity. The prompt explicitly mandates the query-type gate (depth-first / breadth-first / straightforward) as the primary branching decision before any delegation occurs, making it the canonical external reference for a classification-before-research architecture.

## Key Claims

- **Three query types** are defined as a hard gate before delegation: *Depth-first* (multiple perspectives on one issue), *Breadth-first* (distinct independent sub-questions), and *Straightforward* (single focused investigation) — each triggering a different subagent count and delegation strategy.
- > "Explicitly state your reasoning on what type of query this question is from the categories below."
- **Subagent budget ladder**: simple → 1 subagent; standard complexity → 2–3; medium complexity → 3–5; high complexity → 5–10, maximum 20.
- > "Default to using 3 subagents for most queries."
- **Budget termination rule**: > "Adjust research depth based on time constraints and efficiency — if you are running out of time or a research process has already taken a very long time, avoid deploying further subagents and instead just start composing the output report immediately."
- **XML-tagged sections** carry all role-level instructions to the lead — not Markdown headings — providing structural delimiters the model can reliably parse at runtime.
- **Delegation via `run_blocking_subagent` tool**: the only channel from the lead to a subagent is the `prompt` parameter of this tool call; no shared state is passed.
- **Synthesis responsibility boundary**: the lead agent synthesises; lead agents NEVER delegate report writing to a subagent: > "NEVER create a subagent to generate the final report — YOU write and craft this final research report yourself."
- **Subagent instructions must be complete**: > "Make sure that IF all the subagents followed their instructions very well, the results in aggregate would allow you to give an EXCELLENT answer to the user's question."
- **Overlap prevention** is an explicit principle: "Avoid overlap between subagents — every subagent should have distinct, clearly separate tasks, to avoid replicating work unnecessarily and wasting resources."
- **Bayesian updating** is specified during execution: "Adapt to new information well — analyse the results, use Bayesian reasoning to update your priors, and then think carefully about what to do next."
- **Parallel tool calls are mandatory** for launching multiple subagents: > "You MUST use parallel tool calls for creating multiple subagents (typically running 3 subagents at the same time) at the start of the research."

## Relevance to EndogenAI

This is the single most directly applicable external model for the `executive-researcher.agent.md` prompt design. The three-query-type classification gate (depth-first / breadth-first / straightforward) is entirely absent from the current EndogenAI Executive Researcher instructions, which dispatch the Research Scout regardless of query type — adopting this gate would prevent over-engineering trivial queries and under-resourcing complex ones. The XML-tagged section convention (`<research_process>`, `<delegation_instructions>`) is more machine-stable than the current `.agent.md` Markdown-heading convention, which relies on model interpretation of heading hierarchy; a future refactor of agent files should evaluate XML-delimited blocks for role-critical instruction sections. The explicit subagent budget ladder (capped at 20) provides the quantitative stopping condition that is currently missing from the Executive Researcher — adding a `maxSubagents` or `maxRounds` field to the agent's instruction block is a low-effort, high-value improvement. The synthesis-responsibility boundary (lead writes the report, never delegates it) directly validates the current EndogenAI pattern of Synthesizer being an independent agent rather than a sub-task of the Scout — but also implies the Synthesizer should be given the full aggregate Scout output in a single delegation prompt rather than being called piecemeal. The `run_blocking_subagent` tool pattern maps to the VS Code Copilot `runSubagent` call in `.agent.md` files, confirming the one-way prompt-string delegation model in use.

## Referenced By

<!-- Populated automatically by scripts/link_source_stubs.py — do not edit manually -->
