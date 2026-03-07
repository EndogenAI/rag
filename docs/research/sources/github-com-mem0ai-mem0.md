---
slug: github-com-mem0ai-mem0
title: "mem0: Universal Memory Layer for AI Agents"
url: https://github.com/mem0ai/mem0
cached: true
type: repo
topics: [memory, agent-memory, long-term-memory, personalization, RAG]
date_synthesized: 2026-03-06
---

## Summary

mem0 (mem0ai/mem0, 48.9k stars) is an open-source intelligent memory layer for AI assistants and agents, enabling personalised interactions by remembering user preferences, adapting over time, and retrieving relevant memories on demand. Published benchmarks claim +26% accuracy over OpenAI Memory on the LOCOMO benchmark, 91% faster responses, and 90% fewer tokens versus full-context approaches. Available as hosted platform or self-hosted open-source package.

## Key Claims

- "+26% Accuracy over OpenAI Memory on the LOCOMO benchmark; 91% Faster Responses than full-context; 90% Lower Token Usage than full-context."
- Multi-level memory: retains User, Session, and Agent state with adaptive personalisation across levels.
- API: `memory.add(messages, user_id=...)` to store; `memory.search(query, user_id=...)` to retrieve relevant memories before generation.
- Available via `pip install mem0ai` (self-hosted) or managed platform at app.mem0.ai.
- Integrations: LangGraph, CrewAI, browser extension (works across ChatGPT, Perplexity, Claude).

## Relevance to EndogenAI

mem0 addresses the episodic memory gap — specifically the inability to query "what did we learn about X in prior sessions?" The 90% token reduction versus full-context is directly relevant to local-compute-first constraints. However, it is an embedding-based solution requiring an LLM to function and adds an external service dependency. Deferred to D4 evaluation alongside Letta, pending confirmation that the episodic memory bottleneck is confirmed at scale.

## Referenced By

<!-- Will be filled in by issue synthesis pass -->
