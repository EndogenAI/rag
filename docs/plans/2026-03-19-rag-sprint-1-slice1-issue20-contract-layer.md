# Sprint 1 Slice 1 - Issue #20 Contract Layer (Implementation-Ready Planning)

Parent sequencing artifact: [2026-03-19-rag-sprint-1-execution-sequencing.md](./2026-03-19-rag-sprint-1-execution-sequencing.md)
Dependency slice artifact: [2026-03-19-rag-sprint-1-phase2-dependency-slice.md](./2026-03-19-rag-sprint-1-phase2-dependency-slice.md)
Validation contract artifact: [2026-03-19-rag-sprint-1-phase3-validation-contract.md](./2026-03-19-rag-sprint-1-phase3-validation-contract.md)
Kickoff packet: [2026-03-19-rag-sprint-1-phase4-kickoff-packet.md](./2026-03-19-rag-sprint-1-phase4-kickoff-packet.md)
Issue target: [EndogenAI/rag#20](https://github.com/EndogenAI/rag/issues/20)
Date: 2026-03-19

## Objective

Establish the Issue #20 contract layer as a bounded, implementation-ready planning artifact with deterministic validation and explicit halt/rollback rules.

Scope boundary:
- In scope: planning-level contract design and validation signals.
- Out of scope: implementation coding, rollout, and issue closure actions.

## Dependency Lock and Slice Posture

Dependency order for Sprint 1 remains fixed:
1. #20
2. #19
3. #16
4. #17
5. #18

Governance anchor posture:
- #8 and #15 remain governance anchors only.
- #8 and #15 cannot be used as Slice 1 closure evidence.

## A) Schema Strategy Comparison (Issue #20 AC: at least 3 approaches)

| approach | model | strengths | risks | recommended use posture |
|---|---|---|---|---|
| S1 | Separate DB files (`dogma` index + `client` index) | Strongest hard partition boundary; easiest fail-closed default | Higher operational overhead for synchronization and maintenance | Use for strict mode and high-assurance separation |
| S2 | Single DB with logical namespaces and mandatory scope tags | Lower operational complexity; shared infra and tooling | Leak risk if filters are optional or misapplied | Use only with mandatory filter enforcement and fail-closed rules |
| S3 | Hybrid: separate physical partitions plus optional federated query entrypoint | Balances hard separation with explicit, auditable blending path | Federation entrypoint can drift into permissive default | Use as target posture with strict federation trigger gates |

Recommendation:
- Default posture is S3 with separated-only retrieval as baseline and explicit federation trigger rules.

## B) Metadata and Provenance Contract (Issue #20 AC: metadata contract)

| field | required | allowed values/pattern | rule |
|---|---|---|---|
| `scope` | yes | `dogma` or `client` | Every record must have one scope value. |
| `source_id` | yes | stable source identifier | Must remain stable across refreshes for dedupe and audit. |
| `source_path` | yes | repo-relative path or canonical URL | Enables provenance tracing and rollback targeting. |
| `content_hash` | yes | deterministic hash string | Used for drift detection and idempotent refresh checks. |
| `partition_id` | yes | namespace or physical partition key | Must map one-to-one with scope boundary policy. |
| `retention_policy` | yes | `core-long`, `client-rotating`, `manual` | Policy must be explicit and not inferred from scope. |
| `last_refresh_at` | yes | ISO 8601 UTC timestamp | Required for update-cadence and stale-data checks. |
| `governance_tier` | yes | `core` or `deployment` | Enforces Core-vs-Deployment policy separation in queries. |

Invalid states (must fail validation):
1. Missing `scope` or `partition_id`.
2. `scope=dogma` with `governance_tier=deployment`.
3. Any query mode that omits mandatory scope filters.
4. Any record lacking `source_id` or `content_hash`.

## C) Query Policy Rules and Retrieval Modes (Issue #20 AC: query policy)

Strict mode (default):
1. Require explicit scope input (`dogma` or `client`).
2. Apply mandatory scope + partition filter before retrieval execution.
3. Fail closed when scope is missing, unknown, or filter expansion is ambiguous.

Blended mode (explicit opt-in only):
1. Requires explicit `federation=true` flag and reason code.
2. Executes two scoped retrieval passes and merges results with source attribution preserved.
3. Rejects execution if either scoped pass fails validation.

Policy defaults:
- Default query policy: strict mode.
- Blended mode is disabled by default and requires documented trigger conditions.

## D) Leakage Risk Model and Mitigation (Issue #20 AC: risk model)

| risk | detection signal | threshold | mitigation |
|---|---|---|---|
| Cross-scope contamination in strict mode | Seeded overlap-term boundary tests | Critical leaks must be 0 | Halt, revert to separated-only posture, block federation planning |
| Filter omission or bypass | Contract validation check on query templates | 0 missing mandatory filters | Halt and reject phase progression until corrected |
| Namespace/partition drift | Metadata consistency scan across `scope` and `partition_id` | 0 contradictory mappings | Freeze topology assumptions and re-baseline mappings |
| Undocumented blended retrieval use | Query audit with mode and reason fields | 0 undocumented blended calls | Disable blended mode and require policy correction |

## E) Deterministic Validation Contract (Session objective)

V1 - Schema completeness:
- Pass: all required metadata fields and invalid-state checks are present and explicit.
- Fail: any required field or invalid-state rule is missing.

V2 - Boundary matrix:
- Pass: seeded overlap-term tests show critical cross-scope leaks = 0.
- Fail: any critical leak is observed.

V3 - Leak-rate threshold:
- Pass: aggregate leak rate <= 0.1% across seeded checks.
- Fail: leak rate > 0.1%.

V4 - Dependency and gate consistency:
- Pass: artifact preserves #20 -> #19 -> #16 -> #17 -> #18 ordering and #8/#15 governance-anchor classification.
- Fail: ordering drift or slice-closure misuse of governance anchors.

## F) Halt and Rollback Rules (Session objective)

Immediate halt conditions:
1. V1 fails due to missing metadata or undefined invalid states.
2. V2 fails due to any critical cross-scope leak.
3. V3 fails due to leak rate threshold breach.
4. V4 fails due to dependency-order drift or governance-anchor misuse.

Rollback posture:
1. Revert to separated-only planning posture.
2. Freeze federation and topology expansion inputs.
3. Keep last accepted contract as last-known-good baseline.
4. Re-run only failed validation subset after correction.

Resume rule:
- Progression to #19 is allowed only after all V1-V4 checks pass and Review gate returns APPROVED.

## Readiness Verdict

Verdict: READY FOR ISSUE #20 CONTRACT-LAYER REVIEW GATE.

Authorization boundary:
- This artifact authorizes planning-layer progression only.
- It does not authorize implementation coding, migration, deployment, or issue closure.
