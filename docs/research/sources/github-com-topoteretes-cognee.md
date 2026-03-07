---
slug: github-com-topoteretes-cognee
title: "Cognee: Knowledge Engine for AI Agent Memory"
url: https://github.com/topoteretes/cognee
cached: true
type: repo
topics: [knowledge-graph, memory, knowledge-engine, vector-search, agent-memory]
date_synthesized: 2026-03-06
---

## Summary

Cognee (topoteretes/cognee, 13k stars) is an open-source knowledge engine that transforms raw data into persistent, dynamic AI memory by combining vector search, graph databases, and self-improvement. It interconnects heterogeneous data (conversations, files, images, audio) into a unified knowledge graph searchable by both semantic meaning and relationship structure. Offers a Python API, MCP server, and frontend, supporting 30+ data source integrations.

## Key Claims

- "Cognee is an open-source knowledge engine that transforms your raw data into persistent and dynamic AI memory for Agents."
- Replaces traditional database lookups with a unified knowledge engine built with graphs and vectors.
- "Reduces developer effort and infrastructure cost while improving quality and precision."
- Provides Pythonic data pipelines for ingestion from 30+ data sources; high customisability through user-defined tasks and modular pipelines.
- Available as `uv pip install cognee`; requires Python 3.10–3.13.

## Relevance to EndogenAI

Cognee is the lighter knowledge-graph alternative to Graphiti/Zep, with similar episodic memory capabilities but more emphasis on knowledge ingestion from diverse sources. Its uv-based installation aligns with the EndogenAI Python tooling convention (`uv run`). The MCP server enables Claude Code integration. Deferred to D4 evaluation alongside mem0/Letta — no clear advantage over simpler scratchpad approach at current session volume, but worth revisiting when the episodic memory bottleneck is confirmed.

## Referenced By

<!-- Will be filled in by issue synthesis pass -->
