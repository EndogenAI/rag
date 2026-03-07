---
slug: lmstudio-ai
title: "LM Studio: Run AI Models Locally and Privately"
url: https://lmstudio.ai
cached: true
type: docs
topics: [local-LLM, LM-Studio, local-compute, OpenAI-compatible-API, headless-deployment]
date_synthesized: 2026-03-06
---

## Summary

LM Studio is a desktop application and server for running LLMs locally and privately on personal hardware. It provides an OpenAI-compatible API, JavaScript and Python SDKs, MCP client support, and a headless deployment option (`llmster`) for server/CI environments without a GUI. Supports models including GPT-OSS, Qwen3, Gemma3, and DeepSeek. Free for home and work use.

## Key Claims

- "Run AI models, locally and privately" — no cloud dependency, data stays on device.
- Headless deployment via `llmster` (install with `curl -fsSL https://lmstudio.ai/install.sh | bash`) for Linux servers, cloud instances, and CI pipelines.
- OpenAI-compatible API enables drop-in local replacement for cloud inference without code changes.
- JavaScript and Python SDKs (`npm install @lmstudio/sdk`, `pip install lmstudio`) for programmatic integration.
- Supports Apple MLX models, MCP client mode, and CLI management via `lms`.

## Relevance to EndogenAI

LM Studio is the primary candidate for OPEN_RESEARCH.md #1 (local compute baseline) alongside Ollama. The headless `llmster` deployment mode is significant: it enables local inference in CI and scripted workflows without a GUI dependency, which aligns with the EndogenAI programmatic-first principle. The OpenAI-compatible API removes vendor lock-in and enables testing with different local models without agent code changes.

## Referenced By

<!-- Will be filled in by issue synthesis pass -->
