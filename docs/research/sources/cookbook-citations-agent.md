---
title: "Anthropic Cookbook: Citations Agent Prompt"
url: "https://github.com/anthropics/anthropic-cookbook (multiagent_network/citations_agent.py)"
slug: "cookbook-citations-agent"
type: cookbook
cached_at: "2026-03-06"
cache_path: ".cache/sources/cookbook-citations-agent.md"
topics: [citation, xml-structured-prompts, output-format, post-processing, agent-specialisation]
---

# Anthropic Cookbook: Citations Agent Prompt

**URL**: https://github.com/anthropics/anthropic-cookbook (multiagent_network/citations_agent.py)  
**Type**: cookbook  
**Cached**: `uv run python scripts/fetch_source.py https://github.com/anthropics/anthropic-cookbook --slug cookbook-citations-agent`

## Summary

This source is the full system prompt for the Citations Agent from Anthropic's official multiagent_network cookbook example — a narrowly scoped post-processing agent whose sole task is to insert citation tags into a completed research report without altering any other content. The prompt is notable for its strict output contract: the agent receives a report inside `<synthesized_text>` tags and a set of source documents, and must return the report unchanged except for added citation markers inside `<exact_text_with_citation>` tags, with any preamble or planning appearing before the opening tag to avoid corrupting machine-parsed output. The source exemplifies the principle of radical agent specialisation — one agent, one transformation, one verifiable contract — and its XML tag conventions provide the clearest example in the corpus of using XML delimiters as machine-stable I/O boundaries rather than natural language instructions. Its citation placement rules (semantic units, sentence-boundary preference, no redundancy within a sentence) constitute a concise but complete editorial policy for footnote placement that has direct applicability to documentation-generation agents.

## Key Claims

- **Strict non-modification contract**: > "Do NOT modify the `<synthesized_text>` in any way — keep all content 100% identical, only add citations."
- **XML boundary for I/O**: output must be wrapped in `<exact_text_with_citation>` and `</exact_text_with_citation>` tags — a machine-parseable boundary that downstream consumers can extract without parsing prose.
- **Pre-amble isolation rule**: > "Include any of your preamble, thinking, or planning BEFORE the opening `<exact_text_with_citation>` tag, to avoid breaking the output." This separates reasoning trace from structured output — a pattern applicable to any agent producing machine-consumed XML.
- **Citation only on direct support**: > "ONLY add citations where the source documents directly support claims in the text" — not every sentence needs a citation.
- **Semantic-unit granularity**: > "Citations should span complete thoughts, findings, or claims that make sense as standalone assertions. Avoid citing individual words or small phrase fragments that lose meaning out of context."
- **Sentence-boundary preference**: > "Prefer adding citations at the end of sentences" — mid-sentence citations fragment the reading flow.
- **No same-source redundancy**: > "Do not place multiple citations to the same source in the same sentence... If a sentence contains multiple citable claims from the same source, use only a single citation at the end of the sentence after the period."
- **Verifiable output contract**: > "Text without citations will be collected and compared to the original report from the `<synthesized_text>`. If the text is not identical, your result will be rejected." This implies an automated diff verifier downstream.
- **Selective citation discipline**: > "Avoid citing unnecessarily: Not every statement needs a citation. Focus on citing key facts, conclusions, and substantive claims... Prioritize citing claims that readers would want to verify."

## Relevance to EndogenAI

The Citations Agent exemplifies radical agent specialisation — a design principle that the EndogenAI fleet partly follows (Synthesizer, Reviewer, Archivist are each single-responsibility) but has not yet applied to output post-processing steps like citation insertion or link validation after `scripts/link_source_stubs.py` runs. The XML I/O boundary pattern (`<exact_text_with_citation>` tags) is more parsing-reliable than the current EndogenAI convention of putting structured output inside prose or Markdown code fences; the Archivist agent in particular would benefit from accepting and returning XML-delimited content blocks to prevent accidental prose contamination of committed files. The "preamble before the opening tag" rule directly addresses a recurring failure mode in long-context agents: when reasoning and output are interleaved, downstream parsers break — separating them structurally is a low-cost, high-reliability improvement applicable to all EndogenAI agents that produce machine-read output. The verifiable output contract (automated diff check) maps conceptually to the `get_errors` validation step that should follow all file edits in the EndogenAI Archivist workflow, and suggests the Archivist phase gate should include a structural diff check rather than relying on human review alone. The citation placement rules (semantic units, sentence-boundary, no redundancy) should be adopted verbatim as the citation policy in `docs/guides/session-management.md` when the project begins citing sources in guide documents.

## Referenced By

<!-- Populated automatically by scripts/link_source_stubs.py — do not edit manually -->
