---
title: "Claude SDK: Subagents"
url: "https://platform.claude.com/docs/en/agent-sdk/subagents"
slug: "claude-sdk-subagents"
type: documentation
cached_at: "2026-03-06"
cache_path: ".cache/sources/claude-sdk-subagents.md"
topics: [subagents, Claude-SDK, context-isolation, parallelization, tool-restrictions, programmatic-agents]
---

# Claude SDK: Subagents

**URL**: https://platform.claude.com/docs/en/agent-sdk/subagents  
**Type**: documentation  
**Cached**: `uv run python scripts/fetch_source.py https://platform.claude.com/docs/en/agent-sdk/subagents --slug claude-sdk-subagents`

## Summary

This is Anthropic's official SDK documentation for programmatic subagent creation in the Claude Agent SDK, covering three definition methods, four benefit categories, invocation mechanics, context inheritance rules, resumable subagents, and tool restriction patterns. The document centres on the programmatic approach using the `agents` parameter in `query()` options, which takes `AgentDefinition` objects specifying each subagent's description, system prompt, allowed tools, and optional model override. It is the primary technical reference for understanding exactly what context a subagent receives from its parent, what it does not, and how the only channel from parent to subagent (the Task prompt string) governs what information transfer is structurally possible. The resumable subagent feature — allowing a subagent to be re-invoked with its full prior conversation history — is introduced here as a first-class SDK capability and has no equivalent in the current EndogenAI fleet design.

## Key Claims

- **Three definition methods**: programmatic (`agents` parameter), filesystem-based (`.claude/agents/` markdown files), and built-in general-purpose subagent invocable without any definition — each with different precedence rules.
- **Context isolation is the primary value**: > "Each subagent runs in its own fresh conversation. Intermediate tool calls and results stay inside the subagent; only its final message returns to the parent."
- **One-way prompt-string channel**: > "The only channel from parent to subagent is the Task prompt string, so include any file paths, error messages, or decisions the subagent needs directly in that prompt."
- **Subagents cannot spawn sub-subagents**: "Subagents cannot spawn their own subagents. Don't include `Task` in a subagent's `tools` array." — depth is capped at two levels.
- **Description field drives automatic routing**: Claude determines whether to invoke a subagent based on the `description` field; explicit name invocation ("Use the code-reviewer agent to...") bypasses automatic matching.
- **Context inheritance table** — a subagent receives: its own system prompt + Task prompt, project CLAUDE.md, and inherited tool definitions. It does NOT receive: parent conversation history, parent system prompt, tool results from the parent.
- **Tool restrictions per subagent** reduce unintended side-effects: a read-only subagent can have `["Read", "Grep", "Glob"]` while a test runner gets `["Bash", "Read", "Grep"]`.
- **Resumable subagents retain full history**: "Resumed subagents retain their full conversation history, including all previous tool calls, results, and reasoning. The subagent picks up exactly where it stopped rather than starting fresh."
- **AgentDefinition required fields**: `description` (string, required) and `prompt` (string, required); optional fields are `tools` (string array) and `model` (`'sonnet'`, `'opus'`, `'haiku'`, or `'inherit'`).
- **Parallelization is native**: multiple subagents can run concurrently; the documentation example shows parallel `style-checker`, `security-scanner`, and `test-coverage` subagents running simultaneously.
- **Windows prompt-length limit**: subagents with very long prompts may fail on Windows due to 8191-char command line limit — keep prompts concise or use filesystem-based agents.
- **Filesystem agents load at startup only**: if a new `.claude/agents/` file is created while Claude Code is running, the session must be restarted to load it.

## Relevance to EndogenAI

This documentation is the canonical technical reference for the VS Code Copilot `runSubagent` delegation pattern used in all EndogenAI `.agent.md` files, and the one-way-prompt-string channel rule directly explains why the EndogenAI Executive Researcher must include all relevant session context (scratchpad path, branch slug, research question) explicitly in every delegation prompt rather than assuming sub-agents inherit it. The filesystem-based subagent definition via `.claude/agents/` markdown files is structurally identical to the `.github/agents/*.agent.md` convention already in use in this repo — this documentation formally validates that convention and clarifies that the `description` frontmatter field is the primary routing signal the parent model reads, meaning weak or vague `description:` values in EndogenAI agent files will silently cause mis-delegation or no delegation at all. The two-level depth cap (subagents cannot spawn sub-subagents) is a hard architectural constraint that the EndogenAI fleet must respect: any future design that imagines a Scout autonomously spawning its own fetch agents would require a different approach at the SDK level, not just prompt-level instructions. The resumable subagent feature has no equivalent in the current EndogenAI workflow — for long multi-day research sessions where a Scout pauses mid-investigation, session continuity is currently lost between VS Code restarts; the SDK resume pattern suggests a future enhancement where session IDs are persisted to the `.tmp/` scratchpad for mid-session recovery. The tool restriction patterns (read-only vs. write-capable subagents) directly map to a current gap: EndogenAI's Scout, Synthesizer, and Archivist are not currently scoped to different tool sets, meaning they all have write access when only the Archivist should.

## Referenced By

<!-- Populated automatically by scripts/link_source_stubs.py — do not edit manually -->
