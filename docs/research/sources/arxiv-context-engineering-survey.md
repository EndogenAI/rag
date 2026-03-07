---
slug: arxiv-context-engineering-survey
title: "A Survey of Context Engineering for Large Language Models"
url: https://arxiv.org/abs/2507.13334
cached: true
type: paper
topics: [context-engineering, RAG, memory, multi-agent, comprehension-generation-gap]
date_synthesized: 2026-03-06
---

## Summary

A comprehensive 166-page survey by Lingrui Mei et al. (arXiv:2507.13334, July 2025) covering over 1,400 research papers on context engineering for LLMs. The paper formally defines context engineering as a discipline transcending prompt design, covering context retrieval, generation, processing, and management, as well as system-level integrations including RAG, memory systems, tool-integrated reasoning, and multi-agent architectures. Key finding: a fundamental comprehension-generation asymmetry exists in current LLMs.

## Key Claims

- "A fundamental asymmetry exists between model capabilities. While current models, augmented by advanced context engineering, demonstrate remarkable proficiency in understanding complex contexts, they exhibit pronounced limitations in generating equally sophisticated, long-form outputs. Addressing this gap is a defining priority for future research."
- Context engineering is a formal discipline "that transcends simple prompt design to encompass the systematic optimization of information payloads for LLMs."
- The survey cites LangChain's industrial four-stage context engineering practice (write/select/compress/isolate) as `[LangChainContextEngineering2024]` — confirming this is LangChain's contribution, not AIGNE's.
- The paper is an ongoing work (166 pages, 1,411 citations) serving as a technical roadmap for the field.

## Relevance to EndogenAI

The comprehension-generation gap finding directly informs the evaluator-optimizer loop design: context engineering can partially close this gap by structuring output generation as iterative evaluation. The survey's formal taxonomy is the academic foundation for the context engineering vocabulary used across the EndogenAI research docs. The attribution of write/select/compress/isolate to LangChain (not AIGNE) is critical for correcting an error in the original agentic-research-flows synthesis.

## Referenced By

- [agentic-research-flows](../agentic-research-flows.md)
