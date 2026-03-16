---
governs: [research]
title: "Competitor Landscape: Agentic Coding Frameworks"
status: Draft
issue: 301
branch: research/301-competitor-landscape-agentic-frameworks
created: 2026-03-16
---

# Competitor Landscape: Agentic Coding Frameworks

> **Status**: Draft — pending review
> **Research Question**: How does EndogenAI's dogma compare to the current agentic coding framework landscape, and where does it hold genuine differentiation versus where is it outcompeted?
> **Date**: 2026-03-16
> **Related**: [Issue #301](https://github.com/EndogenAI/dogma/issues/301) · [`MANIFESTO.md`](../../MANIFESTO.md) · [`AGENTS.md`](../../AGENTS.md) · [`docs/research/platform-agnosticism.md`](platform-agnosticism.md)

---

## Executive Summary

The agentic coding framework landscape in March 2026 comprises approximately 30 distinct tools across four archetypes: spec-first scaffolding frameworks (BMAD Method, Kiro, Taskmaster), full-autonomy execution agents (OpenHands, Devin 2.x, Devika), IDE-coupled agentic tools (Cursor, Windsurf), and multi-agent orchestration platforms (CrewAI, LangGraph, AutoGen). Adoption momentum is concentrated in Cursor (>500 Fortune 500 companies), OpenHands (69.2k★, 484 contributors), BMAD Method (40.9k★, v6.2 shipped March 2026), and CrewAI (46.3k★, 100k+ certified developers).

EndogenAI's dogma occupies a niche that no competitor targets directly: a **values-governance substrate** — a principled, programmatically enforced encoding hierarchy (MANIFESTO.md → AGENTS.md → role files → SKILL.md → session prompts) that governs AI agent behaviour at every contextual layer. The highest-momentum competitors are optimised for code generation throughput and developer experience, not for values fidelity or governance. Their closest analogue to dogma's governance layer is project-scoped rule files (Cursor's `.cursorrules`, Kiro's steering files) with no principled axiom hierarchy, no programmatic enforcement gates, and no fleet audit trail.

The key finding: **dogma is genuinely uncontested in values governance and programmatic enforcement, genuinely outcompeted in code generation throughput and adoption friction, and at real risk of being outpaced in spec-driven development** as BMAD Method, Kiro, and Taskmaster commoditise the spec-first workflow. Per MANIFESTO.md §1 — Endogenous-First: the field is providing the "external giants" that dogma should absorb into its substrate, not compete with on their own terms. The strategic posture is to deepen the uncontested advantages while adopting competitor deployment patterns that reduce onboarding friction without compromising governance integrity.

---

## Hypothesis Validation

### H1 — EndogenAI's values-governance approach is uncontested in the market

**Verdict**: SUPPORTED

**Evidence**: No framework in the surveyed corpus provides an equivalent to the MANIFESTO.md → AGENTS.md → role files encoding chain with programmatic enforcement. Cursor's `.cursorrules` and Kiro's steering files are the closest analogues, but neither implements a principled axiom hierarchy, static-lint enforcement (`validate_agent_files.py`, `no-heredoc-writes` pre-commit hook), or a runtime governor (zsh `accept-line` wrapper + `.envrc`) that intercepts policy violations before they execute. CrewAI's AMP control plane provides RBAC and observability for crew execution, but this is runtime governance of agent interactions — not values encoding into the agent's decision substrate. The T2 (static linting) and T4 (interactive runtime) enforcement layers have no peer in the surveyed field. The closest competitive move is Kiro's background agent hooks on file-save — a reactive automation layer — but this is workflow automation, not values governance. **Dogma's values-governance substrate is uncontested.**

### H2 — Local-compute-first is underserved across the competitive landscape

**Verdict**: SUPPORTED

**Evidence**: Of the 15+ frameworks catalogued, only Taskmaster and CrewAI explicitly provide Ollama-compatible local inference paths. All other major frameworks — Cursor, Devin 2.x, OpenHands, Kiro — are cloud-API-first by design; local model support is either absent or an afterthought. Per MANIFESTO.md §3 — Local Compute-First: "cloud residency transfers enforcement authority, oversight access, or governance guarantees to an external party." No competitor applies this structural test when designing their inference layer; the field treats local compute as a cost-tier option rather than as oversight infrastructure. Even the two LCF-adjacent tools (Taskmaster, CrewAI) position local inference as a cost-saving alternative, not as a governance requirement — dogma's structural framing of LCF is entirely absent from the competitive landscape. **Local-compute-first as a structural governance principle is underserved.**

### H3 — Spec-driven development is the dominant emerging paradigm

**Verdict**: PARTIALLY SUPPORTED

**Evidence**: Spec-first tooling is rapidly commoditising: BMAD Method (40.9k★, v6.2), Taskmaster (26k★, PRD→task hierarchy via MCP), and Kiro (AWS commercial, EARS-notation requirements, steering files) all converge on generating a requirements or specification artifact before invoking code-generation agents. However, full-autonomy execution agents (Cursor, OpenHands, Devin 2.x) remain the adoption-momentum leaders by star count and Fortune 500 entrenchment — these tools treat spec generation as optional or emergent, not as a mandatory gate. Spec-driven development is the dominant methodological trend among deliberate practitioners, but raw execution autonomy is still the dominant mass-market product form. **The paradigm is ascending, not yet dominant — and commoditising rapidly among the tools that do implement it.**

---

## Pattern Catalog

### Archetype 1 — Spec-First Frameworks

**Description**: Frameworks that enforce a requirements or specification phase before any code is generated or executed. The agent persona is constrained to planning tasks until a spec artifact is approved; implementation agents are invoked only after sign-off. This archetype prioritises predictability and human oversight over raw generation throughput. The spec functions as a workflow gate, not merely an optional context document.

**Canonical example**: **BMAD Method** (40.9k★, v6.2 March 2026, 5k forks). BMAD implements 12+ domain agent personas and 34 documented workflows, each operating in strict phase order: Analyst → Architect → Implementation. Users interact with a dedicated SM (Scrum Master) or BA (Business Analyst) persona before any code-generation persona is activated. The spec artifact — a STORY.md or EPIC.md — gates the transition from planning to implementation. This is spec-as-workflow-gate: the constraint is architectural, not advisory. Multi-IDE support (VS Code, Cursor, JetBrains) and npm installability make BMAD the highest-adoption proof point that spec-first tooling can achieve mass adoption without sacrificing rigour.

**Anti-pattern**: A spec-first framework that generates a requirements document and immediately delegates to an autonomous execution agent without a human approval gate. The spec exists on disk but is never reviewed — it becomes a token-burn formality rather than a governance checkpoint. The planning phase adds latency without adding oversight. This pattern collapses spec-first into execute-with-preamble: the structural discipline of spec-first is present in name; its protective function is absent in practice.

---

### Archetype 2 — Full-Autonomy Execution Agents

**Description**: Frameworks optimised for end-to-end code generation, test execution, and PR submission with minimal human intervention between task assignment and delivery. SWE-bench performance is the primary evaluative axis. These systems typically run in sandboxed environments (Docker), instrument CI directly, and surface results as PRs or issue closures rather than as interactive sessions.

**Canonical example**: **OpenHands** (69.2k★, 484 contributors, progressive OSS → Enterprise tier). OpenHands provides SDK + CLI + GUI + Cloud deployment targets, Jira/Linear/Slack integrations, and a documented SWE-bench performance proof point that substantiates its credibility as a code-generation benchmark leader. The progressive OSS → Enterprise tier design — with VPC contracts and RBAC for enterprise customers — demonstrates the archetype's commercial maturity pathway: OpenHands competes on production reliability and enterprise readiness, not merely capability demonstrations. Its 69.2k★ count makes it the second-most-starred framework in the corpus after Cursor.

**Anti-pattern**: An unconstrained autonomy agent that modifies production files without human review gates, commits directly to default branches, and interprets ambiguous task descriptions as permission to refactor unrelated code. Failure mode: scope creep at machine speed. The agent produces technically correct output that violates team conventions, introduces regressions in untouched modules, and requires more human review time than direct implementation would have taken. High throughput without governance is a liability in production codebases — the archetype's commercial risk is that SWE-bench measures isolated task completion, not production reliability or convention fidelity.

---

### Archetype 3 — Values-Governance Substrate (dogma's niche)

**Description**: A principled, programmatically enforced encoding hierarchy that governs agent behaviour through multi-layer axiom inheritance rather than through prompt instructions alone. The governance layer is not an overlay on top of code generation — it is the substrate on which all agent activity runs. Enforcement is mechanised (pre-commit hooks, runtime governors, CI validation) so that adherence is structural, not discretionary. The defining property is that governance cannot be overridden by prompt drift or context window pressure because enforcement operates outside the LLM context.

**Canonical example**: **EndogenAI dogma** — the MANIFESTO.md → AGENTS.md → `.agent.md` role files → `SKILL.md` files → session prompts encoding chain implements values at every contextual layer. The T2 enforcement layer (`scripts/validate_agent_files.py`, `no-heredoc-writes` pre-commit hook) and T4 runtime governor (zsh `accept-line` wrapper via `.envrc`) ensure that constraints are programmatically enforced, not merely documented. The fleet's `data/amplification-table.yml` makes the AGENTS.md Context-Sensitive Amplification table machine-readable so that session-start behaviour is data-driven — a precision implementation of MANIFESTO.md §2 — Algorithms Before Tokens: "prefer deterministic, encoded solutions over interactive token burn; invest in automation early." No competitor in the surveyed corpus reaches even the T2 layer for agent behaviour governance.

**Anti-pattern**: A governance layer that lives entirely in Markdown documentation — AGENTS.md-as-advice rather than AGENTS.md-as-enforced-contract. An agent reads the doc, acknowledges the constraints, and then violates them in the same session because no programmatic gate fires. The documentation is correct; the enforcement is absent. This is the most common failure mode of governance-by-instruction: it degrades proportionally with context window pressure and agent drift. Kiro's steering files and Cursor's `.cursorrules` are both examples of this pattern — well-intentioned convention documents with no enforcement layer and no axiom hierarchy.

---

### Archetype 4 — IDE-Coupled Agentic Tools

**Description**: Agentic AI systems that embed deeply into the IDE workflow — autocomplete, inline edits, chat, and background agents — with tightly integrated codebase understanding. These tools compete on UX responsiveness and codebase comprehension rather than on governance or deployment flexibility. The competitive moat is switching cost: once an engineering org standardises on an IDE-coupled tool, migration carries high friction.

**Canonical example**: **Cursor** (>500 Fortune 500 companies, NVIDIA 40k engineers, Salesforce 20k engineers, JetBrains plugin shipped March 2026). Cursor's Fortune 500 entrenchment reflects the IDE-coupled archetype's primary competitive moat: institutional adoption at the engineering-team level. The March 2026 JetBrains plugin release demonstrates the archetype expanding its coupling surface from one IDE to multiple — trading some depth of integration for broader reach. Brand endorsements from AI field leaders (Karpathy, Jensen Huang, Patrick Collison) accelerate adoption among the developer communities that most directly overlap with dogma's target audience.

**Anti-pattern**: An IDE-coupled agent that provides project rules as a flat, unversioned file with no structured enforcement and no inheritance hierarchy. Conventions are defined once, drift immediately, and are never validated against the agent's actual behaviour. The tooling provides the illusion of governance (a rules file exists) without the substance: no git history of convention changes, no CI validation, no agent tests against the conventions. When the rules file and the agent's behaviour diverge, there is no mechanism to detect or correct the divergence.

---

## Gap & Differentiation Matrix

| Dimension | dogma | Field Leaders | dogma's Position |
|-----------|-------|----------------|-----------------|
| Values governance | Principled axiom hierarchy (MANIFESTO.md → AGENTS.md → role files → skills); five encoding layers | None — Cursor: flat `.cursorrules`; Kiro: steering files; no axiom hierarchy in any peer | **Uncontested** |
| Local-compute-first | Core axiom (MANIFESTO.md §3); framed as oversight infrastructure, not cost tier; Ollama paths documented | Cloud-API-first by design; Taskmaster + CrewAI offer Ollama as cost option only | **Differentiated** — structural framing absent in all peers |
| Programmatic enforcement | Pre-commit hooks (`validate_agent_files.py`, `no-heredoc-writes`); runtime governor (T4 zsh hook); CI validation | None at governance layer — Cursor/OpenHands enforce code style only, not agent behaviour | **Uncontested** |
| Code generation throughput | Not a primary goal; deferred to GitHub Copilot underlying model | Cursor, OpenHands, Devin 2.x optimise for throughput as primary KPI; SWE-bench as benchmark | **Outcompeted** — by design; different goal function |
| Adoption friction | High — requires understanding 5-layer encoding chain before value is realised | Low — Cursor: one-click install; BMAD: `npm install`; Taskmaster: MCP drop-in config | **Outcompeted** — investment cost vs. value clarity gap |
| IDE integration | VS Code only; no Cursor/JetBrains/Zed support | Cursor: VS Code + JetBrains (March 2026); OpenHands: IDE-agnostic CLI + cloud | **Outcompeted** — platform coupling documented in [`platform-agnosticism.md`](platform-agnosticism.md) |
| Fleet governance | Agent files validated by `validate_agent_files.py`; posture enforced at commit boundary; CI gate | No peer offers fleet-level agent governance with CI validation or posture classification | **Uncontested** |

---

## Recommendations

**Adopt**: **Taskmaster's MCP drop-in deployment model as an onboarding path for dogma's Scout + Synthesizer workflow.** Taskmaster demonstrates that a structured, PRD-to-task workflow can achieve mass adoption (26k★, 2.5k forks, 91 releases) by removing the IDE lock-in requirement through MCP compatibility. Dogma's adoption friction is highest at the entry point — the 5-layer encoding chain requires context before it delivers value. Per MANIFESTO.md §1 — Endogenous-First: "Extend or adapt rather than create from zero — prefer existing well-maintained libraries over bespoke implementations." Packaging the Programmatic-First principle (specifically, the Scout + Synthesizer research pipeline) as an MCP-compatible tool would allow developers to experience dogma's governance value on their current IDE before committing to the full substrate.

**Discard**: **Full-autonomy execution as a design goal or competitive axis for dogma.** Cursor, Devin 2.x, and OpenHands optimise for parallel cloud agents running with minimal human checkpoints between task assignment and PR delivery. This directly contradicts the Augmentive Partnership principle in MANIFESTO.md: the system provides deterministic execution and encoding; the human provides direction, judgment, and oversight — neither works without the other. Competing with Cursor or Devin on code-generation throughput would require deprioritising the review gates, programmatic governors, and phase checkpoints that define dogma's actual value proposition. The axioms are non-negotiable; the throughput ambition is a category error.

**Double-Down**: **The T2 + T4 programmatic enforcement stack — extend it and package it.** No competitor in the surveyed corpus provides pre-commit hooks that validate agent-file governance conventions, or a runtime governor that intercepts and blocks policy violations at the shell level before they execute. This is genuine competitive differentiation with zero peer analogues. Per MANIFESTO.md §2 — Algorithms Before Tokens: "invest in automation early." The current stack (`validate_agent_files.py` + `no-heredoc-writes` + zsh governor + `validate_synthesis.py`) should be extended — a `detect_drift.py` runner for session-to-session axiom drift, a packaged pre-commit hook bundle installable via `uv add` or `pip install`, and a `check_governance_coverage.py` script that reports which agent files lack enforcement — and eventually published as a standalone governance toolkit. Deepening an already uncontested advantage compounds faster than closing a competitive gap.

---

## Sources

- https://medium.com/@visrow/spec-driven-development-is-eating-software-engineering-a-map-of-30-agentic-coding-frameworks-6ac0b5e2b484
- https://github.com/bmad-code-org/BMAD-METHOD
- https://github.com/All-Hands-AI/OpenHands
- https://kiro.dev
- https://github.com/crewAIInc/crewAI
- https://github.com/eyaltoledano/claude-task-master
- https://github.com/langchain-ai/langgraph
- https://cognition.ai/blog/devin-2
- https://www.cursor.com/
- https://github.com/microsoft/autogen
- https://tessl.io
- https://sweep.dev
- https://github.com/stitionai/devika
