# docs/research/sources/

Per-source synthesis stubs — one file per research source surveyed by the research fleet.

Each file is a structured distillation of a single external source: its key claims, methodology
notes, and relevance to the EndogenAI project. These stubs are the **atomic unit** that issue
synthesis documents (`docs/research/*.md`) reference and build upon.

---

## Why This Exists

When the same source is relevant to multiple research questions — which happens as the project
matures — having a dedicated stub prevents duplication and keeps issue syntheses lean. Instead
of re-summarising `arXiv:2512.05470` in every synthesis that cites it, you write the summary
once here and link to it.

This also produces a **cumulative source knowledge base**: every source ever surveyed by the
research fleet is catalogued here. Over time this becomes the project's annotated bibliography.

---

## File Naming

Files are named by **slug** — the same slug used in `.cache/sources/manifest.json`:

```
docs/research/sources/<slug>.md
```

The slug is derived from the URL by `fetch_source.py`. To find a source's slug:

```bash
uv run python scripts/fetch_source.py --list
```

---

## File Structure

Each stub is a **substantive synthesis document**, not a placeholder. It is generated in isolation from the full `.cache/sources/<slug>.md` distillation.

```markdown
---
title: "<source title>"
url: "<source url>"
slug: "<slug>"
type: paper | documentation | blog | cookbook | repo
cached_at: "<YYYY-MM-DD>"
cache_path: ".cache/sources/<slug>.md"
topics: [<tag1>, <tag2>]
---

# <Source Title>

**URL**: <url>
**Type**: paper | documentation | blog | cookbook | repo
**Cached**: `uv run python scripts/fetch_source.py <url> --slug <slug>`

## Summary

<!--
  4–6 sentences covering:
  - What the source is (type, author/org, publication date if known)
  - Its structure or scope (e.g. "166-page survey of 1400+ papers")
  - Its primary contribution or argument
  - Any notable methodology or standout finding
-->

## Key Claims

<!--
  8–15 bullet points. Each bullet should:
  - State a specific, falsifiable claim from the source
  - Include a direct quote where available (use > blockquote format)
  - Note if the claim is from the abstract only vs. body
-->

## Relevance to EndogenAI

<!--
  5–8 sentences as editorial opinion:
  - Which EndogenAI agent files, scripts, or guides does this source bear on?
  - What gap in the EndogenAI methodology does this source address or expose?
  - What should be adopted, adapted, or rejected — and why?
-->

## Referenced By

<!-- Populated automatically by scripts/link_source_stubs.py — do not edit manually -->
```

### Depth requirements

A stub is considered complete when:
- `## Summary` has ≥ 4 sentences
- `## Key Claims` has ≥ 6 bullets with direct quotes where available
- `## Relevance to EndogenAI` has ≥ 3 substantive sentences with concrete project references
- Total length ≥ 60 lines

Stubs below these thresholds are treated as **placeholder stubs** and should be regenerated before any issue synthesis that cites them.

---

## Git Tracking

| Artifact | Git status |
|----------|-----------|
| `docs/research/sources/*.md` (these stubs) | **tracked** — committed to the repo |
| `.cache/sources/<slug>.md` (raw distillations) | **gitignored** — regenerable via `fetch_source.py` |
| `.cache/sources/manifest.json` (fetch index) | **tracked** — committed to the repo |

The raw distillations are excluded because they are large, regenerable, and contain noise.
The stubs are the curated, committed record of what each source says and why it matters.

---

## Relationship to Issue Syntheses

```
docs/research/
  sources/
    arxiv-org-abs-2512-05470.md    ← per-source stub
    anthropic-building-effective-agents.md
    ...
  agentic-research-flows.md        ← issue synthesis (references stubs above)
  OPEN_RESEARCH.md
```

Issue syntheses own the cross-source conclusions. Per-source stubs own the source summaries.
Never duplicate a source summary inside an issue synthesis — link to the stub instead.
