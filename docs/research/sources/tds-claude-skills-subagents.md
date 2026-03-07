---
slug: tds-claude-skills-subagents
title: "Claude Skills and Subagents: Escaping the Prompt Engineering Hamster Wheel"
url: https://towardsdatascience.com/claude-skills-and-subagents
cached: true
type: article
topics: [Claude-Skills, lazy-loading, token-economics, subagents, progressive-disclosure]
date_synthesized: 2026-03-06
---

## Summary

Ruben Broekx (Towards Data Science, February 2026) explains Claude Skills — Anthropic's reusable, lazy-loaded instruction sets that solve context bloat through three-level progressive disclosure: metadata stub (~100 tokens, loaded at startup), skill body (~5,000 tokens, loaded on invocation), and referenced files (loaded on demand). Compares Skills with MCP tools and subagents, and articulates the token economics of each. Note: this slug appears to be a cached duplicate of `towardsdatascience-com-claude-skills-and-subagents` — both point to the same article.

## Key Claims

- "Skills are reusable, lazy-loaded, and auto-invoked instruction sets that use progressive disclosure across three levels: metadata, body, and referenced files."
- Level 1 (metadata): ~100 tokens per skill, always loaded. Level 2 (body): up to ~5,000 tokens, loaded on invocation. Level 3 (referenced files): no practical limit, loaded on demand.
- "The main strength of skills lies in the auto-invocation. When starting a new conversation, the agent only reads each skill's name and description, to save on tokens."
- The `prompt engineering hamster wheel` is the anti-pattern Skills solves: repeatedly re-writing prompts from scratch because there's no reuse mechanism.

## Relevance to EndogenAI

This is the primary source for the skills manifest generator recommendation (D5 #1 in the synthesis). The three-level disclosure model is directly applicable: `generate_agent_manifest.py` implements level 1 (metadata stubs); full `.agent.md` bodies are level 2 (loaded on invocation). This pattern justifies the lazy loading approach currently recommended in AGENTS.md for context management.

## Referenced By

- [agentic-research-flows](../agentic-research-flows.md)
