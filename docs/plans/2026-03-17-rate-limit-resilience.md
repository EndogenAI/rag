# Workplan: Rate-Limit Resilience — Detection & Proactive Mitigation

**Branch**: Main (cross-cutting infrastructure)  
**Date**: 2026-03-17  
**Milestone**: N/A (critical cross-session infrastructure)  
**Orchestrator**: Executive Orchestrator  
**Urgency**: Blocking (active rate-limit failures in multi-phase sessions)

---

## Problem Statement

Rate limiting from external LLM APIs is catastrophic for multi-phase sessions:

1. **Session interruption mid-phase** — agent delegations fail silently or timeout
2. **Expensive re-orientation** — scratchpad rebuild costs tokens; by re-entry, rate limits are re-triggered
3. **Cascading failure** — sessions become unrecoverable; work from earlier phases is lost or must be rediscovered
4. **No visibility** — orchestrators have no way to predict when rate limits will hit, so they cannot plan mitigation

**Today's state**: Zero rate-limit detection, zero proactive throttling. Sessions fail reactively.

**Desired state**: 
- Detect approaching rate limits **before** they trigger failures
- Implement smart mitigation: sleep injection, model switching, work compression
- Provide operators insight into remaining budget and session feasibility
- Enable sessions to continue gracefully instead of failing hard

---

## Solution Architecture

### Core Components

1. **Rate-Limit Header Parser** (`scripts/detect_rate_limit.py`)
   - Parse Claude API response headers: `anthropic-ratelimit-*` headers
   - Extract: requests remaining, tokens remaining, window size, retry-after
   - Compute: estimated time to limit, tokens per unit time

2. **Session Budget Tracker** (Session State extension)
   - Track cumulative tokens in current session
   - Estimate per-agent delegation cost (based on prior delegations)
   - Compute: remaining budget before window close

3. **Orchestrator Pre-Delegation Gate** (Orchestrator Agent enhancement)
   - Before delegating each phase: check budget vs. remaining work estimate
   - If approaching limit: inject sleep, compress work, or signal model-switch
   - Provide visibility: "Remaining budget: 45K tokens, next phase costs ~30K, margin: 15K"

4. **Model Switching Logic** (Claude Code integration point)
   - Detect when Claude 3.5 Sonnet is rate-limited
   - Offer Claude 3 Opus (slower, different rate limit window) as fallback
   - Coordinate: don't context-switch mid-phase, but signal at phase boundary

5. **Documentation & Runbooks**
   - Session operator guide: interpreting budget alerts
   - When to accept sleep injection vs. switch models vs. defer phase
   - Architecture decision record: why this approach, limitations

---

## Phase Plan

### Phase 0 — Research: Rate-Limiting Detection Patterns ⬜

**Agent**: Research Scout (or inline quick research for speed)
**Research questions**:
1. What rate-limit headers does Claude API return? What metadata is available?
2. What is the structure of `anthropic-ratelimit-*` headers (requests_limit, requests_remaining, requests_reset, tokens_limit, tokens_remaining, tokens_reset)?
3. How are rate limits scoped (per-org? per-user? per-API-key? per-model)?
4. What is the retry-after window typical duration?
5. Can we detect approaching limits before hitting them (e.g., at 80% of window)?
6. What are the known patterns for model switching (Sonnet ↔ Opus) and do they have separate rate-limit windows?
7. Are there existing tools/libraries in the Python ecosystem for rate-limit budgeting/scheduling?

**Deliverables**: 
- `docs/research/rate-limit-detection-api.md` (Status: Working)
- List of API response headers, typical values, window sizes
- Model switching strategy document

**Depends on**: None  
**Gate**: Research complete before Phase 1 implementation begins  
**Status**: Not started

---

### Phase 0 Review — Review Gate ⬜

**Agent**: Review  
**Deliverables**: `## Phase 0 Review Output` in scratchpad, verdict: APPROVED  
**Depends on**: Phase 0 committed  
**Status**: Not started

---

### Phase 1 — Implementation: Rate-Limit Detector & Budget Tracker ⬜

**Agent**: Executive Scripter  
**Issues**: None (infrastructure, not tied to a specific issue yet)  
**Deliverables**:
- `scripts/detect_rate_limit.py` — parses Claude API headers, computes budget
  - `detect_rate_limit.py --check <remaining_tokens> <estimated_next_phase_cost>` → returns "OK", "WARN", "CRITICAL", "SLEEP_REQUIRED N_SECONDS"
  - Constructor: log file or environment variable to read rate-limit state
  - Tests: mock API responses, edge cases (zero remaining, negative window)
- `mcp_server/tools/session_budget_query.py` — MCP tool callable from internal MCP server
  - Returns: `{remaining_tokens, remaining_requests, time_to_reset, session_total_consumed, recommendation}`
- Integration point: store headers in session state (`.tmp/<branch>/<date>.md` under `## Session Budget State`)
- Tests in `tests/test_detect_rate_limit.py` (80%+ coverage)
- `scripts/README.md` updated with new detector usage

**Depends on**: Phase 0 APPROVED  
**Gate**: Phase 1 Review APPROVED before Phase 2 begins  
**CI**: Tests, validate-synthesis on research doc  
**Status**: Not started

---

### Phase 1 Review — Review Gate ⬜

**Agent**: Review  
**Deliverables**: `## Phase 1 Review Output` in scratchpad, verdict: APPROVED  
**Depends on**: Phase 1 committed  
**Status**: Not started

---

### Phase 2 — Integration: Orchestrator Agent Enhancement ⬜

**Agent**: Executive Orchestrator (or Executive Fleet + Executive Docs for agent file changes)  
**Deliverables**:
- Update [`.github/agents/executive-orchestrator.agent.md`](../../.github/agents/executive-orchestrator.agent.md) with pre-delegation budget check
  - New section: `## Pre-Delegation Rate-Limit Check`
  - Pseudo-code: `if (session_state.remaining_tokens < next_phase_estimate + 8000_safety_margin): trigger mitigation`
  - Three paths: (a) inject sleep, (b) compress work, (c) offer model switch
- Update [`.github/skills/phase-gate-sequence/SKILL.md`](../../.github/skills/phase-gate-sequence/SKILL.md) with budget alert logic
  - New checkpoints in pre-phase gate sequence
- Session State schema update (YAML block under `## Session Budget State`)
  - Fields: `last_rate_limit_check: {timestamp, remaining_tokens, remaining_requests, recommendation}`
- Documentation: `docs/guides/rate-limit-resilience.md`
  - How to read rate-limit alerts
  - When to accept sleep vs. switch models
  - Runbook: recovering from rate-limit

**Depends on**: Phase 1 APPROVED  
**Gate**: Phase 2 Review APPROVED before Phase 3 begins  
**CI**: validate-agent-files, validate-skill-files  
**Status**: Not started

---

### Phase 2 Review — Review Gate ⬜

**Agent**: Review  
**Deliverables**: `## Phase 2 Review Output` in scratchpad, verdict: APPROVED  
**Depends on**: Phase 2 committed  
**Status**: Not started

---

### Phase 3 — Documentation & Operator Runbooks ⬜

**Agent**: Executive Docs  
**Deliverables**:
- `docs/guides/session-rate-limit-resilience.md` — operator guide
  - Interpreting budget alerts
  - Sleep injection: acceptable overhead, calculation
  - Model switching: when/why/how
  - Example: "Budget alert: 42K remaining, Phase 3 costs 30K, Phase 4 costs 25K. Total: 55K. Recommendation: SLEEP 400s after Phase 3 completes, or defer Phase 4 to next session."
- Update `docs/guides/session-management.md` with rate-limit section
- Update `AGENTS.md` → `## Async Process Handling` with rate-limit timeout patterns
  - Add rate-limit retry semantics alongside network timeout handling

**Depends on**: Phase 2 APPROVED  
**Gate**: Phase 3 Review APPROVED before Phase 4 begins  
**Status**: Not started

---

### Phase 3 Review — Review Gate ⬜

**Agent**: Review  
**Deliverables**: `## Phase 3 Review Output` in scratchpad, verdict: APPROVED  
**Depends on**: Phase 3 committed  
**Status**: Not started

---

### Phase 4 — Deployment & Validation ⬜

**Agent**: GitHub + Executive Orchestrator  
**Deliverables**:
- Commit all changes with `feat(rate-limit): add resilience detection & mitigation`
- PR: link to this workplan, reference issue #xxx (TBD: open issue for rate-limit resilience)
- CI passes: all tests green, agents validate, docs link-check passes
- Post-deployment: run next multi-phase session with rate-limit monitoring enabled, capture data

**Depends on**: Phase 3 APPROVED  
**Gate**: CI green, one successful tracked session completes with rate-limit visibility  
**Status**: Not started

---

## Acceptance Criteria

- [ ] Rate-limit headers are parsed and available to orchestrator
- [ ] Budget is computed per-session, updated after each delegation
- [ ] Orchestrator checks budget before delegating each phase (gate enforced in agent.md)
- [ ] At-risk sessions receive recommendation: sleep, defer, or model-switch
- [ ] Operators can query current budget any time via session state
- [ ] Documentation is clear, examples included
- [ ] One full multi-phase session completes with rate-limit tracking and zero interruptions due to limit
- [ ] Runbook is tested: sleep injection stops a cascading failure scenario

---

## Risk Mitigations

| Risk | Mitigation |
|------|-----------|
| Rate-limit headers are undocumented or change | Research phase validates API contract; add defensive parsing |
| Model switching has different latency/cost | Document trade-offs; provide clear decision points |
| Sleep overhead breaks critical-path sessions | Calculate acceptable sleep window as % of phase duration; allow skip if margin is large |
| Operator overrides detection and causes failure | Provide clear "force continue" option but log warning; education in runbook |

