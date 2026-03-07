---
slug: github-com-letta-ai-letta
title: "Letta (formerly MemGPT): Platform for Stateful Agents"
url: https://github.com/letta-ai/letta
cached: true
type: repo
topics: [stateful-agents, memory, MemGPT, agent-platform, self-improvement]
date_synthesized: 2026-03-06
---

## Summary

Letta (letta-ai/letta, formerly MemGPT, 21.4k stars) is an open-source platform and API for building stateful agents — AI systems with persistent memory that can learn and self-improve over time. Provides both a CLI tool (Letta Code) and a full-featured agents API with Python/TypeScript SDKs. Agents are built around persistent memory blocks (human, persona) that survive across conversations, enabling genuine long-term personalisation.

## Key Claims

- "Letta is the platform for building stateful agents: AI with advanced memory that can learn and self-improve over time."
- Memory blocks (`human`, `persona`) are persistent across sessions — agents genuinely remember prior interactions rather than relying on injected context.
- Supports skills and subagents via `.skills` directory convention — structurally parallel to EndogenAI's `.github/agents/` convention.
- Model-agnostic; officially supports Opus 4.5 and GPT-5.2 with a public model leaderboard.
- `alembic` database migrations and `init.sql` confirm SQLite/PostgreSQL persistent storage backend.

## Relevance to EndogenAI

Letta addresses the experiential memory gap (persistent cross-session learning) that the Copilot memory tool partially fills. Its skills + subagents architecture is structurally the closest external analogue to the EndogenAI agent fleet design. Deferred to D4 evaluation alongside mem0, pending confirmation that cross-session memory is a bottleneck at current scale. The model-agnostic design supports local-compute-first constraints.

## Referenced By

<!-- Will be filled in by issue synthesis pass -->
