---
slug: a2a-announcement
title: "Announcing the Agent2Agent Protocol (A2A)"
url: https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-agent2agent-protocol-a2a
cached: true
type: blog
topics: [multi-agent, interoperability, protocol, A2A, MCP]
date_synthesized: 2026-03-06
---

## Summary

Google's April 2025 announcement of the Agent2Agent (A2A) open protocol, backed by 50+ technology partners, introduces a standards-based way for AI agents to communicate regardless of underlying framework or vendor. A2A uses HTTP, SSE, and JSON-RPC and introduces "Agent Cards" — JSON documents advertising agent capabilities for discovery. The protocol explicitly complements (not competes with) Anthropic's Model Context Protocol (MCP): MCP handles agent↔tool interactions; A2A handles agent↔agent coordination.

## Key Claims

- "A2A is an open protocol that complements Anthropic's Model Context Protocol (MCP), which provides helpful tools and context to agents."
- Agents advertise capabilities via **Agent Cards** in JSON format, enabling dynamic capability discovery by client agents.
- Protocol stack is HTTP + SSE + JSON-RPC — standards already present in enterprise IT stacks.
- Supports long-running tasks with real-time feedback and state updates, including human-in-the-loop scenarios.
- Designed for enterprise-grade authentication with parity to OpenAPI authentication schemes; air-gapped/local deployment explicitly supported.
- A task "artifact" is the named output of a completed task; the task object has a defined lifecycle managed by the protocol.

## Relevance to EndogenAI

A2A's Agent Card format is structurally analogous to the output of `generate_agent_manifest.py`, but with a different purpose: Agent Cards are live service-discovery documents for networked agents, while the manifest is a static CI artifact for context loading. The MCP/A2A separation clarifies the EndogenAI tool vs. agent-coordination boundary. If the fleet ever expands to cross-provider coordination, A2A is the correct protocol layer to evaluate — the existing `generate_agent_manifest.py` would need an A2A-compatible card schema extension.

## Referenced By

- [agentic-research-flows](../agentic-research-flows.md)
