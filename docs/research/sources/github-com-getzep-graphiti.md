---
slug: github-com-getzep-graphiti
title: "Graphiti: Real-Time Knowledge Graph Framework for AI Agents"
url: https://github.com/getzep/graphiti
cached: true
type: repo
topics: [knowledge-graph, memory, temporal-reasoning, RAG, agent-memory]
date_synthesized: 2026-03-06
---

## Summary

Graphiti (getzep/graphiti, 23.4k stars) is an open-source Python framework for building and querying temporally-aware knowledge graphs for AI agents. Unlike static RAG, Graphiti continuously integrates new data episodes without batch recomputation, using a bi-temporal data model that tracks both event occurrence time and ingestion time. It powers Zep's commercial context engineering platform and has an MCP server for Claude/Cursor integration.

## Key Claims

- "Unlike traditional retrieval-augmented generation (RAG) methods, Graphiti continuously integrates user interactions, structured and unstructured enterprise data, and external information into a coherent, queryable graph."
- Bi-temporal data model: explicit tracking of both event occurrence time and data ingestion time, enabling accurate point-in-time historical queries.
- Hybrid retrieval: combines semantic embeddings, keyword (BM25), and graph traversal — does not rely solely on LLM summarisation.
- Incremental updates: new data episodes are integrated immediately without requiring complete graph recomputation.
- Graphiti → open-source flexible core; Zep → fully managed production platform built on Graphiti. Choose Zep for turnkey; Graphiti for custom control.

## Relevance to EndogenAI

Graphiti/Zep is the leading candidate for closing the episodic and experiential memory gaps identified in the agentic-research-flows synthesis. The bi-temporal model is particularly relevant for a project that values immutable git history (historical record) alongside evolving session context. Deferred to D3 pending confirmation of episodic memory bottleneck at scale. The MCP server enables integration with Claude Code without custom tooling.

## Referenced By

<!-- Will be filled in by issue synthesis pass -->
