# Agent Fleet Catalog

VS Code Copilot custom agents for the EndogenAI Workflows project.
Each `.agent.md` file appears in the Copilot chat agents dropdown automatically.

For authoring rules — frontmatter schema, posture table, handoff patterns — see [`.github/agents/AGENTS.md`](./AGENTS.md).

Typical workflow: **Plan → (approve) → Implement → (complete) → Review → GitHub (commit)**

---

## Research Agents

Orchestrate research sessions from question to committed synthesis. The Executive Researcher drives the fleet using the expansion→contraction pattern.

| Agent | File | Posture | Trigger | Handoffs |
|-------|------|---------|---------|----------|
| **Executive Researcher** | `executive-researcher.agent.md` | full | Start a research session; orchestrate Scout→Synthesizer→Reviewer→Archivist; spawn new area agents | Research Scout, Research Synthesizer, Research Reviewer, Research Archivist, Executive Docs, Review |
| **Research Scout** | `research-scout.agent.md` | read + web | Gather and catalogue raw sources for a topic — no synthesis | Executive Researcher |
| **Research Synthesizer** | `research-synthesizer.agent.md` | read + create | Transform Scout findings into a structured synthesis draft in `docs/research/` | Executive Researcher |
| **Research Reviewer** | `research-reviewer.agent.md` | read-only | Validate synthesis drafts against methodology standards; flag gaps and unsupported claims | Executive Researcher |
| **Research Archivist** | `research-archivist.agent.md` | read + create | Finalise approved drafts, commit to `docs/research/`, update issue | Review, Executive Researcher |

---

## Documentation Agents

Maintain and evolve all project documentation — encoding dogmatic values and methodology across every documentation layer.

| Agent | File | Posture | Trigger | Handoffs |
|-------|------|---------|---------|----------|
| **Executive Docs** | `executive-docs.agent.md` | read + create | Update guides, top-level docs, AGENTS.md, MANIFESTO.md; codify values across all documentation layers | Review, GitHub, Executive Researcher |

---

## Scripting & Automation Agents

Enforce the programmatic-first principle — encode repeated tasks as scripts and non-agent automation before performing them a third time interactively.

| Agent | File | Posture | Trigger | Handoffs |
|-------|------|---------|---------|----------|
| **Executive Scripter** | `executive-scripter.agent.md` | full | Identify tasks done >2 times interactively; audit `scripts/` for gaps; write or extend scripts | Review, GitHub, Executive Automator |
| **Executive Automator** | `executive-automator.agent.md` | full | Design file watchers, pre-commit hooks, CI tasks, VS Code background tasks; first escalation for event-driven automation | Review, GitHub, Executive Scripter |

---

## Planning & Coordination Agents

Decompose and sequence complex multi-domain work before execution begins. Invoke these when a request spans multiple executive agents or requires explicit dependency ordering.

| Agent | File | Posture | Trigger | Handoffs |
|-------|------|---------|---------|----------|
| **Executive Orchestrator** | `executive-orchestrator.agent.md` | full | Coordinate multi-workflow sessions spanning research, docs, scripting, and fleet changes — sequence executive agents and maintain session coherence | All executive agents, Review, GitHub |
| **Executive Planner** | `executive-planner.agent.md` | read-only | Decompose complex multi-step requests into structured plans with phases, gates, agent assignments, and dependency ordering — before any execution | Executive Orchestrator |

---

## Fleet Management Agents

Maintain the health and standards compliance of the agent fleet itself.

| Agent | File | Posture | Trigger | Handoffs |
|-------|------|---------|---------|----------|
| **Executive Fleet** | `executive-fleet.agent.md` | full | Manage the agent fleet — create, audit, update, and deprecate `.agent.md` files and fleet documentation | Review, GitHub, Executive Docs |

---

## Project Management Agents

Maintain the health of the repository as an open-source resource.

| Agent | File | Posture | Trigger | Handoffs |
|-------|------|---------|---------|----------|
| **Executive PM** | `executive-pm.agent.md` | full | Maintain issues, labels, milestones, changelog, contributing docs, and community health files following open-source best practices | Review, GitHub, Executive Docs, Executive Orchestrator |

---

## Workflow Agents

Cross-cutting agents used at the end of every workflow for quality gating and committing.

| Agent | File | Posture | Trigger | Handoffs |
|-------|------|---------|---------|----------|
| **Review** | `review.agent.md` | read-only | Validate any changed files against AGENTS.md constraints before committing | GitHub, originating agent |
| **GitHub** | `github.agent.md` | terminal | Commit approved changes to the current branch following Conventional Commits | Review |

---

## Adding a New Agent

1. Read [`.github/agents/AGENTS.md`](./AGENTS.md) for the frontmatter schema and naming conventions.
2. Run the scaffold script: `uv run python scripts/scaffold_agent.py --name "<Name>" --description "<desc>" --posture <posture>`.
3. Fill in the generated stub's TODO sections.
4. Add the agent to the correct table above.
5. Commit: `feat(agents): add <name> agent`.

---

## Supporting Scripts

Scripts that back agents in this fleet. All scripts support `--dry-run`.

| Script | Purpose |
|--------|---------|
| `scripts/scaffold_agent.py` | Scaffold a new `.agent.md` stub from a validated template |
| `scripts/prune_scratchpad.py` | Manage cross-agent scratchpad session files in `.tmp/` |
| `scripts/watch_scratchpad.py` | File watcher — auto-annotates `.tmp/*.md` on change |
