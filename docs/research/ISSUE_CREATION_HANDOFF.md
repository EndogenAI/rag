# Issue Creation Handoff

> **Context:** During the initial repo bootstrap (PR #1), the sandbox agent that authored
> `docs/research/OPEN_RESEARCH.md` could not create GitHub Issues because all outbound HTTP
> calls to `api.github.com` are blocked in the sandboxed CI environment (DNS monitoring proxy
> returns HTTP 403). This document provides a ready-to-paste handoff prompt for a **local
> agent** (or any environment with `gh` CLI access and a valid `GITHUB_TOKEN`) to open the
> 6 research issues.

---

## Handoff Prompt

Paste the following block verbatim into your local agent session:

---

```
You are a GitHub CLI agent with access to the `gh` CLI and a valid GITHUB_TOKEN.

Your task is to open 6 GitHub Issues in the EndogenAI/Workflows repository using the
commands below. Run each command exactly as written. If an issue already exists with the
same title, skip it and note the duplicate.

Repository: EndogenAI/Workflows
Label to apply to every issue: research

---

### Issue 1 — Running VS Code Copilot Locally with Local Models

gh issue create \
  --repo EndogenAI/Workflows \
  --label research \
  --title "[Research] Running VS Code Copilot Locally with Local Models" \
  --body "## Research Question

How do we configure VS Code GitHub Copilot to use local LLM inference (Ollama, LM Studio, llama.cpp) instead of cloud APIs?

## Why This Matters

Cloud inference is expensive in tokens, money, and environmental impact. Running inference locally enables the **local-compute-first** principle from \`MANIFESTO.md\` and can significantly reduce per-session costs.

## Resources / Starting Points

- [ ] https://ollama.ai — local model serving, OpenAI-compatible API
- [ ] https://lmstudio.ai — GUI-based local model management
- [ ] https://www.xda-developers.com/youre-using-local-llm-wrong-if-youre-prompting-it-like-cloud-llm/
- [ ] How I built a Claude Code workflow with LM Studio for offline-first development (see AccessiTech/EndogenAI#32)
- [ ] VS Code Copilot extension GitHub docs for custom model endpoint configuration
- [ ] https://towardsdatascience.com/claude-skills-and-subagents-escaping-the-prompt-engineering-hamster-wheel/

## Suggested Approach

Literature review + hands-on prototype: configure Ollama or LM Studio as a local backend, verify VS Code Copilot can route to it, document the steps.

## Gate Deliverables

- [ ] D1 — Verified step-by-step setup guide in \`docs/guides/local-compute.md\`
- [ ] D2 — Model selection recommendations by task type
- [ ] D3 — Benchmark: token savings vs. quality for common agent tasks

## Agent Guidance

- Delegate to a research-focused agent session
- Do not implement code changes outside \`docs/research/\` during the research phase
- Check for related open issues before beginning to avoid duplicating effort"

---

### Issue 2 — Locally Distributed MCP Frameworks

gh issue create \
  --repo EndogenAI/Workflows \
  --label research \
  --title "[Research] Locally Distributed MCP Frameworks" \
  --body "## Research Question

How do we distribute MCP (Model Context Protocol) server infrastructure across a local network? What are best practices for multi-machine agent coordination without cloud dependency?

## Why This Matters

The endogenic vision includes running agent fleets locally. MCP distribution enables multiple machines (e.g., a powerful GPU machine + a dev workstation) to share inference capacity and context.

## Resources / Starting Points

- [ ] https://opensourceprojects.dev/post/e7415816-a348-4936-b8bd-0c651c4ab2d8
- [ ] https://www.freecodecamp.org/news/build-and-deploy-multi-agent-ai-with-python-and-docker/
- [ ] https://www.kdnuggets.com/docker-ai-for-agent-builders-models-tools-and-cloud-offload
- [ ] AccessiTech/EndogenAI architecture docs and \`docs/architecture.md\`
- [ ] Docker Compose patterns for local MCP server clusters

## Suggested Approach

Survey existing MCP distribution tooling, prototype a two-machine Docker Compose setup, document recommended architecture.

## Gate Deliverables

- [ ] D1 — Survey of MCP distribution patterns and tools
- [ ] D2 — Recommended architecture for local multi-machine MCP deployment
- [ ] D3 — Guide in \`docs/guides/\` for setting up a local MCP cluster

## Agent Guidance

- Delegate to a research-focused agent session
- Do not implement code changes outside \`docs/research/\` during the research phase
- Check for related open issues before beginning to avoid duplicating effort"

---

### Issue 3 — Async Process Handling in Agent Workflows

gh issue create \
  --repo EndogenAI/Workflows \
  --label research \
  --title "[Research] Async Process Handling in Agent Workflows" \
  --body "## Research Question

How should agents and sub-agents handle async/long-running terminal processes (e.g., model downloads, Docker container startup) without hanging or silently failing?

## Why This Matters

Async processes are common in AI development workflows (pulling models, starting containers, running tests). Poor handling leads to silent failures and wasted tokens re-trying failed operations. Inspired by AccessiTech/EndogenAI#33.

## Resources / Starting Points

- [ ] Synchronous wait-with-timeout pattern
- [ ] Interval-based status check pattern
- [ ] Observable status APIs (Docker, Ollama, etc.) — document their check endpoints
- [ ] VS Code task \`problemMatcher\` for background process detection

## Suggested Approach

Enumerate common async operations in the endogenic workflow, document best-practice patterns for each, codify in AGENTS.md.

## Gate Deliverables

- [ ] D1 — Documented patterns for common async operations (Docker, Ollama, npm install, pytest)
- [ ] D2 — Agent guidelines for async handling in \`AGENTS.md\`
- [ ] D3 — (optional) Script or VS Code task wrapper for common long-running operations

## Agent Guidance

- Delegate to a research-focused agent session
- Do not implement code changes outside \`docs/research/\` during the research phase
- Check for related open issues before beginning to avoid duplicating effort"

---

### Issue 4 — Free and Low-Cost LLM Tier Strategy

gh issue create \
  --repo EndogenAI/Workflows \
  --label research \
  --title "[Research] Free and Low-Cost LLM Tier Strategy" \
  --body "## Research Question

What is the optimal strategy for mixing free/low-cost LLM tiers with higher-tier models, maximizing quality while minimizing token cost?

## Why This Matters

From AccessiTech/EndogenAI#35: 'Prepare for free tiered models (we have been using Claude Sonnet exclusively)' and 'Utilize the Auto model in VS Code Copilot chat to get ~10% off token usage.'

## Resources / Starting Points

- [ ] VS Code Copilot Auto model selection behavior — when does it use smaller models?
- [ ] Free tier quotas and rate limits for major providers (Anthropic, OpenAI, GitHub Copilot)
- [ ] Task categorization for model selection: which tasks need Sonnet vs. a local 7B model?
- [ ] GitHub Copilot free tier capabilities

## Suggested Approach

Audit current token usage patterns, map task types to model requirements, produce a decision table and monthly budget strategy.

## Gate Deliverables

- [ ] D1 — Model selection decision table by task type
- [ ] D2 — Monthly token budget strategy document
- [ ] D3 — Update \`docs/guides/local-compute.md\` with tier strategy

## Agent Guidance

- Delegate to a research-focused agent session
- Do not implement code changes outside \`docs/research/\` during the research phase
- Check for related open issues before beginning to avoid duplicating effort"

---

### Issue 5 — Endogenic Methodology — Literature Review and Prior Art

gh issue create \
  --repo EndogenAI/Workflows \
  --label research \
  --title "[Research] Endogenic Methodology — Literature Review and Prior Art" \
  --body "## Research Question

What existing methodologies, frameworks, and research most closely resemble or inform the endogenic approach? What can we learn from them?

## Why This Matters

Endogenic development is inspired by biological endogenesis but should stand on the shoulders of giants — absorbing best practices from software engineering, cognitive science, and AI research rather than reinventing them.

## Resources / Starting Points

- [ ] Morphogenetic computing and self-organizing systems
- [ ] Generative programming and model-driven development
- [ ] Living documentation methodologies (Architecture Decision Records, etc.)
- [ ] Agent-oriented software engineering literature
- [ ] Related GitHub projects: https://github.com/originalankur/GenerateAgents.md
- [ ] AI in science fiction — visionary concepts yet to be realized (AccessiTech/EndogenAI#36)

## Suggested Approach

Broad literature survey across software engineering, cognitive science, and AI research. Identify what to adopt vs. what is genuinely novel about the endogenic approach.

## Gate Deliverables

- [ ] D1 — Literature review in \`docs/research/methodology-review.md\`
- [ ] D2 — What to adopt vs. what is genuinely novel about the endogenic approach
- [ ] D3 — Update \`MANIFESTO.md\` with synthesized insights

## Agent Guidance

- Delegate to a research-focused agent session
- Do not implement code changes outside \`docs/research/\` during the research phase
- Check for related open issues before beginning to avoid duplicating effort"

---

### Issue 6 — Agent Fleet Design Patterns

gh issue create \
  --repo EndogenAI/Workflows \
  --label research \
  --title "[Research] Agent Fleet Design Patterns" \
  --body "## Research Question

What are the best design patterns for hierarchical agent fleets? How should executives, sub-agents, and specialist agents be structured for different project types?

## Why This Matters

The current agent fleet emerged organically from the EndogenAI project. As this repo becomes the authoritative source, we should synthesize and formalize the patterns.

## Resources / Starting Points

- [ ] Hierarchical multi-agent patterns (executive → sub-agent → specialist)
- [ ] Context window management strategies for long agent sessions
- [ ] A2A (Agent-to-Agent) protocol patterns
- [ ] https://arxiv.org/html/2512.05470v1 (referenced in AccessiTech/EndogenAI#32)
- [ ] https://towardsdatascience.com/claude-skills-and-subagents-escaping-the-prompt-engineering-hamster-wheel/

## Suggested Approach

Synthesize patterns from the existing fleet, survey external literature on multi-agent architectures, produce a pattern catalog.

## Gate Deliverables

- [ ] D1 — Agent fleet pattern catalog in \`docs/guides/agents.md\`
- [ ] D2 — Recommendations for when to create new specialist agents vs. extend existing ones
- [ ] D3 — Updated \`.github/agents/README.md\` with pattern documentation

## Agent Guidance

- Delegate to a research-focused agent session
- Do not implement code changes outside \`docs/research/\` during the research phase
- Check for related open issues before beginning to avoid duplicating effort"

---

After running all 6 commands, report back with the issue URLs that were created.
```

---

## Prerequisites for the Local Agent

- `gh` CLI installed and authenticated (`gh auth status` should show a valid token for `EndogenAI`)
- The `research` label must exist in the repo — create it first if it doesn't:

  ```bash
  gh label create research --repo EndogenAI/Workflows --color "#0075ca" --description "Research task to synthesize into the endogenic methodology"
  ```

- No additional dependencies needed
