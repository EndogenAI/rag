---
slug: ollama-ai
title: "Ollama: Run Open Models Locally"
url: https://ollama.ai
cached: true
type: docs
topics: [local-LLM, Ollama, open-models, local-compute, agent-integration]
date_synthesized: 2026-03-06
---

## Summary

Ollama is an open-source tool for running large language models locally with a simple CLI and API. It provides integration with agent tools including Claude Code (`ollama launch claude`), Codex, and OpenClaw (an open-source AI assistant). Supports a growing library of open models (Qwen3, Gemma3, DeepSeek, etc.) accessible via a standard `ollama run` or `ollama launch` interface. Free and open-source.

## Key Claims

- Single-command model launch: `curl -fsSL https://ollama.com/install.sh | sh` for installation; `ollama run <model>` for inference.
- Direct Claude Code integration: `ollama launch claude` starts Claude Code powered by local open models.
- OpenClaw integration: `ollama launch openclaw` for an open-source AI assistant "powered by open models."
- Supports quick model switching for integrations: "Connect the latest open models to your favorite applications or agents, making it easy to switch between them."

## Relevance to EndogenAI

Ollama is the alternative to LM Studio for OPEN_RESEARCH.md #1 (local compute baseline). The `ollama launch claude` integration is particularly relevant — it would allow testing EndogenAI agent workflows with local open models without changing the Claude Code interface. Compare with LM Studio on: headless CI support, model availability, and API compatibility before selecting the local inference baseline.

## Referenced By

<!-- Will be filled in by issue synthesis pass -->
