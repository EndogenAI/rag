---
slug: claude-code-agent-teams
title: "Claude Code: Run Agent Teams"
url: https://code.claude.com/docs/en/agent-teams
cached: true
type: docs
topics: [agent-teams, multi-agent, Claude-Code, orchestration, parallel-execution]
date_synthesized: 2026-03-06
---

## Summary

Anthropic's official documentation for the experimental Claude Code Agent Teams feature, which allows multiple Claude Code instances to coordinate work with one acting as team lead and others as independent teammates each with their own context window. Unlike subagents (which report back to a single parent), teammates can communicate directly with each other and can be addressed by the user without going through the lead. The feature is disabled by default and has known limitations around session resumption and task coordination.

## Key Claims

- "Agent teams let you coordinate multiple Claude Code instances working together. One session acts as the team lead, coordinating work, assigning tasks, and synthesizing results."
- Unlike subagents, teammates each have their own context window and can communicate directly with each other without routing through the lead agent.
- Best use cases: research and review (parallel investigation of different aspects), competing hypotheses (parallel exploration of different approaches), and code review (parallel style/security/coverage checks).
- "Give teammates enough context" is the first best practice — team lead must explicitly pass sufficient context when assigning tasks since teammates start with fresh context windows.
- Teams are experimental; known limitations include session resumption, task coordination, and shutdown behaviour.

## Relevance to EndogenAI

The agent teams model clarifies the difference between the EndogenAI fleet's subagent delegation pattern (runSubagent → returns to parent) and a true multi-agent team (direct peer communication). The current EndogenAI design uses the subagent model exclusively. Agent Teams would be relevant if the Executive Researcher needed to run truly parallel scouts with inter-scout coordination, but this requires the experimental feature to be enabled and has known limitations.

## Referenced By

<!-- Will be filled in by issue synthesis pass -->
