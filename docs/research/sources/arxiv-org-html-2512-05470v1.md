---
slug: arxiv-org-html-2512-05470v1
title: "Everything is Context: Agentic File System Abstraction for Context Engineering (AIGNE)"
url: https://arxiv.org/abs/2512.05470
cached: true
type: paper
topics: [context-engineering, agentic-file-system, AIGNE, memory-taxonomy, context-pipeline]
date_synthesized: 2026-03-06
---

## Summary

Xu et al. propose the Agentic File System (AFS) — a Unix-inspired file-system abstraction for context engineering in GenAI systems, implemented in the AIGNE framework (`https://github.com/AIGNE-io/aigne-framework`). The paper formalises a three-component Context Engineering Pipeline (Constructor, Updater, Evaluator) and a seven-type memory taxonomy. It explicitly cites LangChain's write/select/compress/isolate four-stage pattern as prior industrial work, distinguishing it from AIGNE's own contribution.

## Key Claims

- AIGNE's contribution is the **Context Engineering Pipeline**: Context Constructor (selects + compresses context from AFS; produces JSON manifest with selected files, compressed representations, relevance scores) → Context Updater (three modes: Static Snapshot, Incremental Streaming, Adaptive Refresh) → Context Evaluator (validates outputs before committing to AFS; writes back with lineage metadata including `createdAt`, `sourceId`, `confidence`, `revisionId`; triggers human review when confidence falls below threshold).
- **Seven memory types**: Scratchpad, Episodic, Fact, Experiential, Procedural, User, Historical Record — each with distinct persistence scopes.
- **LangChain attribution** (critical): "Agents first write contextual information into a shared memory or store, select the most relevant elements for a given task, compress the selected context to fit model constraints, and isolate the final subset across agents for reasoning" is cited as `[LangChainContextEngineering2024]` — this four-stage pattern is LangChain's industrial practice, not AIGNE's invention.
- The AFS uses SQLite + vector backend + MCP integration; context artefacts carry provenance metadata (lineage) for traceability and human-in-the-loop evaluation.

## Relevance to EndogenAI

The seven-type memory taxonomy is the source for the memory audit table in the agentic-research-flows synthesis. The AIGNE Context Engineering Pipeline (Constructor→Updater→Evaluator) is the most architecturally aligned external framework for the EndogenAI context governance gap. Note the correct GitHub URL is `https://github.com/AIGNE-io/aigne-framework` — earlier references in the synthesis used an incorrect `AIGNE-Project` organisation name.

## Referenced By

- [agentic-research-flows](../agentic-research-flows.md)
