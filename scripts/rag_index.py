"""scripts/rag_index.py — Phase 2 local retrieval index for H2-grounded corpus search.

Purpose:
    Build and query a deterministic local retrieval index over the repository's
    Markdown governance corpus. Chunking is H2-boundary first, with a frozen
    fallback chunk rule when a document has no H2 headings.

Inputs:
    COMMAND (positional):
        reindex — build or refresh index in full or incremental mode
        query   — query indexed chunks via SQLite FTS5
        status  — report index version and freshness metadata

    reindex flags:
        --scope full|incremental  Indexing mode (default: incremental)
        --dry-run                 Preview changes without writing

    query flags:
        --query TEXT              Query text
        --top-k INT               Max chunks to return (1-50, default: 5)
        --filter-governs TEXT     Optional governs slug filter
        --filter-scope TEXT       Optional scope filter (dogma|client)
        --allow-federation        Allow cross-scope retrieval (explicit opt-in)
        --federation-reason TEXT  Required reason when federation is enabled

    status flags:
        --freshness-seconds INT   Staleness threshold (default: 86400)

    health flags:
        --freshness-seconds INT   Staleness threshold (default: 600)
        --pending-backlog INT     Pending update backlog count (default: 0)
        --consecutive-failures INT Consecutive update failures (default: 0)
        --mismatch-rate FLOAT     Audit mismatch rate (default: 0.0)

    local-test flags:
        --test-tier quick|standard|stress  Test battery tier (default: quick)
        --probe-query TEXT                  Probe query text (default: "governance")

    adoption-gate flags:
        --enforcement-level soft|medium|hard  Governance enforcement level (default: medium)

Outputs:
    reindex: Index stats JSON/text (updated/unchanged/removed/chunk counts)
    query:   JSON/text list of chunk matches with metadata
    status:  JSON/text health report (version + freshness)

Usage:
    uv run python scripts/rag_index.py reindex --scope full
    uv run python scripts/rag_index.py reindex --scope incremental --dry-run
    uv run python scripts/rag_index.py query --query "programmatic-first" --top-k 3
    uv run python scripts/rag_index.py query --query "commit" --filter-governs commit-discipline
    uv run python scripts/rag_index.py query --query "values" --filter-scope dogma
    uv run python scripts/rag_index.py query --query "values" --allow-federation --federation-reason "cross-scope audit"
    uv run python scripts/rag_index.py status --freshness-seconds 3600
    uv run python scripts/rag_index.py health --freshness-seconds 600 \
        --pending-backlog 10 --consecutive-failures 0 --mismatch-rate 0.0
    uv run python scripts/rag_index.py local-test --test-tier standard --probe-query "programmatic"
    uv run python scripts/rag_index.py adoption-gate --enforcement-level hard

Exit codes:
    0 — success
    1 — runtime/index error
    2 — validation error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

try:
    import litellm
except ImportError:
    litellm = None

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = REPO_ROOT / "rag-index"
INDEX_DB_PATH = INDEX_DIR / "rag_index.sqlite3"
INDEX_VERSION = "phase2-v2"
FROZEN_H2_FALLBACK_HEADING = "__FROZEN_H2_FALLBACK__"

CORPUS_GLOBS: tuple[str, ...] = (
    "AGENTS.md",
    "MANIFESTO.md",
    "CONTRIBUTING.md",
    "client-values.yml",
    "docs/**/*.md",
    "{{cookiecutter.project_slug}}/**/*.md",
    ".github/agents/*.agent.md",
    ".github/skills/**/*.md",
)

VALID_SCOPE: frozenset[str] = frozenset({"full", "incremental"})
VALID_CONTENT_SCOPE: frozenset[str] = frozenset({"dogma", "client"})
_GOVERNS_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

UPDATE_HEALTH_THRESHOLDS = {
    "freshness": {"warn_sec": 900, "fail_sec": 1800},
    "backlog": {"warn": 100, "fail": 200},
    "failures": {"warn": 2, "fail": 5},
    "mismatch_rate": {"warn": 0.002, "fail": 0.005},
}

VALID_TEST_TIERS: frozenset[str] = frozenset({"quick", "standard", "stress"})
VALID_ENFORCEMENT_LEVELS: frozenset[str] = frozenset({"soft", "medium", "hard"})
FAILURE_SCENARIO_CATALOG: tuple[str, ...] = (
    "F1 delete-indexed-file",
    "F2 rapid-sequential-edits",
    "F3 malformed-markdown",
    "F4 concurrent-writes",
    "F5 watcher-interruption",
    "F6 corrupted-index-metadata",
    "F7 scope-tag-omission",
    "F8 backlog-surge",
    "F9 duplicate-namespace-collision",
)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS files (
    source_file TEXT PRIMARY KEY,
    file_hash TEXT NOT NULL,
    file_mtime REAL NOT NULL,
    chunk_count INTEGER NOT NULL,
    indexed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    source_file TEXT NOT NULL,
    scope TEXT NOT NULL,
    governance_tier TEXT NOT NULL,
    partition_id TEXT NOT NULL,
    retention_policy TEXT NOT NULL,
    heading TEXT NOT NULL,
    governs_csv TEXT NOT NULL,
    fallback_h2 INTEGER NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    indexed_at TEXT NOT NULL,
    FOREIGN KEY (source_file) REFERENCES files(source_file)
);

CREATE INDEX IF NOT EXISTS idx_chunks_source_file ON chunks(source_file);
CREATE INDEX IF NOT EXISTS idx_chunks_governs ON chunks(governs_csv);
CREATE INDEX IF NOT EXISTS idx_chunks_scope ON chunks(scope);

CREATE VIRTUAL TABLE IF NOT EXISTS rag_fts USING fts5(
    chunk_id UNINDEXED,
    content,
    source_file UNINDEXED,
    heading UNINDEXED,
    scope UNINDEXED,
    governs UNINDEXED
);
"""

DROP_SQL = """
DROP TABLE IF EXISTS rag_fts;
DROP TABLE IF EXISTS chunks;
DROP TABLE IF EXISTS files;
DROP TABLE IF EXISTS meta;
"""


class RagIndexError(RuntimeError):
    """Raised for retrieval-index specific runtime failures."""


@dataclass(frozen=True)
class ChunkRecord:
    """Canonical chunk metadata schema for the retrieval index."""

    chunk_id: str
    source_file: str
    scope: str
    governance_tier: str
    partition_id: str
    retention_policy: str
    heading: str
    governs_csv: str
    fallback_h2: int
    start_line: int
    end_line: int
    content: str
    content_hash: str


@dataclass(frozen=True)
class FileState:
    source_file: str
    file_hash: str
    file_mtime: float


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_governs_token(token: str) -> str:
    cleaned = token.strip().lower().replace("_", " ")
    cleaned = re.sub(r"\s+", "-", cleaned)
    cleaned = re.sub(r"[^a-z0-9-]", "", cleaned)
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned


def normalize_governs_values(raw: Any) -> list[str]:
    """Normalize governs or x-governs metadata into canonical slug tokens."""
    values: list[str] = []
    if raw is None:
        return values

    if isinstance(raw, str):
        candidates = [p.strip() for p in raw.split(",") if p.strip()]
    elif isinstance(raw, list):
        candidates = [str(item).strip() for item in raw if str(item).strip()]
    else:
        candidates = [str(raw).strip()] if str(raw).strip() else []

    seen: set[str] = set()
    for candidate in candidates:
        token = _normalize_governs_token(candidate)
        if token and token not in seen:
            values.append(token)
            seen.add(token)
    return values


def parse_frontmatter_governs(text: str) -> list[str]:
    """Extract governs metadata from YAML frontmatter if present."""
    if not text.startswith("---\n"):
        return []

    end = text.find("\n---\n", 4)
    if end == -1:
        return []

    block = text[4:end]
    try:
        data = yaml.safe_load(block) or {}
    except yaml.YAMLError:
        return []

    governs = normalize_governs_values(data.get("governs"))
    x_governs = normalize_governs_values(data.get("x-governs"))

    merged: list[str] = []
    seen: set[str] = set()
    for token in [*x_governs, *governs]:
        if token not in seen:
            merged.append(token)
            seen.add(token)
    return merged


def _governs_csv(governs: list[str]) -> str:
    if not governs:
        return ","
    return "," + ",".join(governs) + ","


def classify_content_scope(source_file: str) -> dict[str, str]:
    """Derive deterministic scope metadata for contract-layer separation.

    Notes:
    - Paths are normalized to POSIX separators to keep behavior stable across OSes.
    - `client-values.yml` and cookiecutter project files are always treated as
      Deployment Layer (client) scope.
    """
    normalized = source_file.replace("\\", "/")
    if normalized == "client-values.yml" or normalized.startswith("{{cookiecutter.project_slug}}/"):
        return {
            "scope": "client",
            "governance_tier": "deployment",
            "partition_id": "client",
            "retention_policy": "client-rotating",
        }

    return {
        "scope": "dogma",
        "governance_tier": "core",
        "partition_id": "dogma",
        "retention_policy": "core-long",
    }


def chunk_markdown_h2(text: str, source_file: str) -> list[ChunkRecord]:
    """Chunk Markdown at H2 boundaries with a deterministic frozen fallback rule.

    Frozen fallback rule:
    - If a file has no H2 headings, index one chunk using heading
      FROZEN_H2_FALLBACK_HEADING and fallback_h2=1.
    """
    if not text.strip():
        return []

    lines = text.splitlines()
    governs = parse_frontmatter_governs(text)
    governs_csv = _governs_csv(governs)
    scope_meta = classify_content_scope(source_file)

    h2_positions: list[int] = []
    for idx, line in enumerate(lines):
        if line.startswith("## "):
            h2_positions.append(idx)

    chunks: list[ChunkRecord] = []
    indexed_at = _now_iso()

    if not h2_positions:
        content = "\n".join(lines).strip()
        if not content:
            return []
        content_hash = _sha256(content)
        chunk_id = _sha256(f"{source_file}\n{FROZEN_H2_FALLBACK_HEADING}\n1\n{len(lines)}\n{content_hash}")[:24]
        chunks.append(
            ChunkRecord(
                chunk_id=chunk_id,
                source_file=source_file,
                scope=scope_meta["scope"],
                governance_tier=scope_meta["governance_tier"],
                partition_id=scope_meta["partition_id"],
                retention_policy=scope_meta["retention_policy"],
                heading=FROZEN_H2_FALLBACK_HEADING,
                governs_csv=governs_csv,
                fallback_h2=1,
                start_line=1,
                end_line=max(1, len(lines)),
                content=content,
                content_hash=content_hash,
            )
        )
        return chunks

    for i, start in enumerate(h2_positions):
        end = h2_positions[i + 1] - 1 if i + 1 < len(h2_positions) else len(lines) - 1
        segment_lines = lines[start : end + 1]
        content = "\n".join(segment_lines).strip()
        if not content:
            continue

        heading_text = lines[start][3:].strip() or FROZEN_H2_FALLBACK_HEADING
        content_hash = _sha256(content)
        chunk_id = _sha256(f"{source_file}\n{heading_text}\n{start + 1}\n{end + 1}\n{content_hash}")[:24]

        chunks.append(
            ChunkRecord(
                chunk_id=chunk_id,
                source_file=source_file,
                scope=scope_meta["scope"],
                governance_tier=scope_meta["governance_tier"],
                partition_id=scope_meta["partition_id"],
                retention_policy=scope_meta["retention_policy"],
                heading=heading_text,
                governs_csv=governs_csv,
                fallback_h2=0,
                start_line=start + 1,
                end_line=end + 1,
                content=content,
                content_hash=content_hash,
            )
        )

    # Keep deterministic timestamp writing for insert rows in the caller.
    _ = indexed_at
    return chunks


def _resolve_corpus_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for pattern in CORPUS_GLOBS:
        for p in sorted(repo_root.glob(pattern)):
            if p.is_dir():
                continue
            if p in seen:
                continue
            seen.add(p)
            files.append(p)
    return files


def _read_file_state(path: Path, repo_root: Path) -> FileState:
    text = path.read_text(encoding="utf-8")
    # Persist POSIX-style repo-relative paths for cross-platform determinism.
    rel = path.relative_to(repo_root).as_posix()
    stat = path.stat()
    return FileState(source_file=rel, file_hash=_sha256(text), file_mtime=stat.st_mtime)


def _count_chunks_for_sources(conn: sqlite3.Connection, sources: list[str]) -> int:
    """Return total chunk count currently stored for the provided source files."""
    if not sources:
        return 0
    placeholders = ",".join("?" for _ in sources)
    row = conn.execute(
        f"SELECT COALESCE(SUM(chunk_count), 0) AS c FROM files WHERE source_file IN ({placeholders})",
        sources,
    ).fetchone()
    return int(row["c"]) if row else 0


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _meta_get(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None


def _meta_set(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute("INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)", (key, value))


def _ensure_schema(conn: sqlite3.Connection, force_rebuild: bool = False) -> None:
    if force_rebuild:
        conn.executescript(DROP_SQL)
    conn.executescript(SCHEMA_SQL)


def _existing_file_map(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    rows = conn.execute("SELECT source_file, file_hash, file_mtime FROM files").fetchall()
    return {r["source_file"]: {"file_hash": r["file_hash"], "file_mtime": r["file_mtime"]} for r in rows}


def _insert_file_and_chunks(
    conn: sqlite3.Connection,
    state: FileState,
    chunks: list[ChunkRecord],
    indexed_at: str,
) -> None:
    conn.execute("DELETE FROM rag_fts WHERE source_file = ?", (state.source_file,))
    conn.execute("DELETE FROM chunks WHERE source_file = ?", (state.source_file,))

    if chunks:
        conn.executemany(
            """
            INSERT INTO chunks(
                chunk_id, source_file, scope, governance_tier, partition_id, retention_policy,
                heading, governs_csv, fallback_h2,
                start_line, end_line, content, content_hash, indexed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    c.chunk_id,
                    c.source_file,
                    c.scope,
                    c.governance_tier,
                    c.partition_id,
                    c.retention_policy,
                    c.heading,
                    c.governs_csv,
                    c.fallback_h2,
                    c.start_line,
                    c.end_line,
                    c.content,
                    c.content_hash,
                    indexed_at,
                )
                for c in chunks
            ],
        )

        conn.executemany(
            "INSERT INTO rag_fts(chunk_id, content, source_file, heading, scope, governs) VALUES (?, ?, ?, ?, ?, ?)",
            [(c.chunk_id, c.content, c.source_file, c.heading, c.scope, c.governs_csv) for c in chunks],
        )

    conn.execute(
        """
        INSERT OR REPLACE INTO files(source_file, file_hash, file_mtime, chunk_count, indexed_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (state.source_file, state.file_hash, state.file_mtime, len(chunks), indexed_at),
    )


def reindex(
    scope: str = "incremental",
    *,
    repo_root: Path = REPO_ROOT,
    db_path: Path = INDEX_DB_PATH,
    dry_run: bool = False,
    file_paths: list[Path] | None = None,
) -> dict[str, Any]:
    """Run full or incremental indexing with version checks and idempotent semantics."""
    if scope not in VALID_SCOPE:
        raise ValueError(f"Invalid scope '{scope}'. Must be one of: {sorted(VALID_SCOPE)}")

    files = file_paths if file_paths is not None else _resolve_corpus_files(repo_root)
    indexed_at = _now_iso()

    conn = _connect(db_path)
    version_before: str | None = None
    force_rebuild = False

    try:
        _ensure_schema(conn)
        version_before = _meta_get(conn, "index_version")

        if version_before and version_before != INDEX_VERSION:
            if scope == "incremental":
                return {
                    "ok": False,
                    "error_code": "INDEX_VERSION_MISMATCH",
                    "message": "Incremental reindex blocked: index version mismatch requires full reindex.",
                    "expected_version": INDEX_VERSION,
                    "actual_version": version_before,
                    "scope": scope,
                    "dry_run": dry_run,
                }
            force_rebuild = True
            if not dry_run:
                _ensure_schema(conn, force_rebuild=True)

        existing = _existing_file_map(conn)
        discovered: dict[str, FileState] = {}

        for path in files:
            try:
                state = _read_file_state(path, repo_root)
            except (OSError, UnicodeDecodeError):
                continue
            discovered[state.source_file] = state

        removed_files = sorted([src for src in existing.keys() if src not in discovered])

        target_states: list[FileState] = []
        unchanged = 0

        if scope == "full" or force_rebuild or not db_path.exists():
            target_states = list(discovered.values())
        else:
            for src, state in discovered.items():
                prev = existing.get(src)
                if prev and prev["file_hash"] == state.file_hash:
                    unchanged += 1
                    continue
                target_states.append(state)

        updated_files = 0
        chunks_indexed = 0

        if not dry_run:
            for src in removed_files:
                conn.execute("DELETE FROM rag_fts WHERE source_file = ?", (src,))
                conn.execute("DELETE FROM chunks WHERE source_file = ?", (src,))
                conn.execute("DELETE FROM files WHERE source_file = ?", (src,))

            for state in target_states:
                source_path = repo_root / state.source_file
                text = source_path.read_text(encoding="utf-8")
                chunks = chunk_markdown_h2(text, state.source_file)
                _insert_file_and_chunks(conn, state, chunks, indexed_at)
                updated_files += 1
                chunks_indexed += len(chunks)

            _meta_set(conn, "index_version", INDEX_VERSION)
            _meta_set(conn, "last_indexed", indexed_at)
            conn.commit()
        else:
            for state in target_states:
                source_path = repo_root / state.source_file
                text = source_path.read_text(encoding="utf-8")
                chunks_indexed += len(chunk_markdown_h2(text, state.source_file))
            updated_files = len(target_states)

        total_chunks_row = conn.execute("SELECT COUNT(*) AS c FROM chunks").fetchone()
        total_chunks = int(total_chunks_row["c"]) if total_chunks_row else 0

        projected_total_chunks: int | None = None
        if dry_run:
            affected_sources = sorted(set(removed_files).union([state.source_file for state in target_states]))
            existing_affected_chunks = _count_chunks_for_sources(conn, affected_sources)
            projected_total_chunks = max(0, total_chunks - existing_affected_chunks + chunks_indexed)

        return {
            "ok": True,
            "scope": scope,
            "dry_run": dry_run,
            "index_path": str(db_path),
            "index_version": INDEX_VERSION,
            "previous_index_version": version_before,
            "rebuilt_schema": force_rebuild,
            "files_total": len(discovered),
            "files_updated": updated_files,
            "files_unchanged": unchanged,
            "files_removed": len(removed_files),
            "chunks_indexed": chunks_indexed,
            "total_chunks": total_chunks,
            "projected_total_chunks": projected_total_chunks,
            "last_indexed": None if dry_run else indexed_at,
        }
    finally:
        conn.close()


def _validate_filter_governs(filter_governs: str | None) -> str | None:
    if filter_governs is None:
        return None
    raw = filter_governs.strip()
    if not raw or not _GOVERNS_RE.fullmatch(raw):
        raise ValueError(
            "Invalid filter_governs. Expected a slug like 'commit-discipline' (lowercase letters, digits, hyphen)."
        )
    return raw


def _validate_filter_scope(filter_scope: str | None) -> str | None:
    if filter_scope is None:
        return None
    normalized = filter_scope.strip().lower()
    if normalized not in VALID_CONTENT_SCOPE:
        raise ValueError("Invalid filter_scope. Expected one of: dogma, client.")
    return normalized


def _normalize_query_for_fts(query: str) -> tuple[str, str]:
    """Convert user query text into tokens and two derived forms.

    Returns:
        (normalized, fts_query) where:
        - normalized: human-readable space-joined form (for API consumers / tests)
        - fts_query: ' OR '-joined form used in the SQLite FTS MATCH clause to
          avoid 0-result 'starvation' for long natural-language questions while
          letting BM25 rank the most relevant overlaps.
    """
    tokens = re.findall(r"[A-Za-z0-9]+", query)
    if not tokens:
        raise ValueError("query must contain at least one alphanumeric token")
    return " ".join(tokens), " OR ".join(tokens)


def query_index(
    query: str,
    *,
    top_k: int = 5,
    filter_governs: str | None = None,
    filter_scope: str | None = None,
    allow_federation: bool = False,
    federation_reason: str | None = None,
    db_path: Path = INDEX_DB_PATH,
) -> dict[str, Any]:
    """Query the index with optional governs filtering."""
    if not query.strip():
        raise ValueError("query must be a non-empty string")
    if top_k < 1 or top_k > 50:
        raise ValueError("top_k must be between 1 and 50")

    normalized_filter = _validate_filter_governs(filter_governs)
    normalized_scope = _validate_filter_scope(filter_scope)

    if allow_federation and not (federation_reason and federation_reason.strip()):
        raise ValueError("federation_reason is required when allow_federation is enabled.")

    if not db_path.exists():
        raise RagIndexError(f"Index not found at {db_path}. Run reindex first.")

    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        version = _meta_get(conn, "index_version")
        if version != INDEX_VERSION:
            raise RagIndexError(
                f"Index version mismatch: found '{version or 'none'}', expected '{INDEX_VERSION}'. Run full reindex."
            )

        normalized_query, fts_query = _normalize_query_for_fts(query)

        sql = (
            "SELECT c.chunk_id, c.source_file, c.scope, c.governance_tier, c.partition_id, c.retention_policy, "
            "c.heading, c.governs_csv, c.fallback_h2, "
            "c.start_line, c.end_line, c.content, "
            "(bm25(rag_fts) + "
            " (CASE WHEN c.source_file IN ('AGENTS.md', 'MANIFESTO.md', 'CONTRIBUTING.md', 'CLAUDE.md') THEN -5.0 ELSE 0.0 END) + "
            " (CASE WHEN c.source_file LIKE 'docs/research/%' THEN 2.0 ELSE 0.0 END)) AS score "
            "FROM rag_fts "
            "JOIN chunks c ON c.chunk_id = rag_fts.chunk_id "
            "WHERE rag_fts MATCH ?"
        )
        params: list[Any] = [fts_query]

        if normalized_filter:
            sql += " AND c.governs_csv LIKE ?"
            params.append(f"%,{normalized_filter},%")

        effective_scope = normalized_scope
        query_mode = "segmented"
        if effective_scope is None and not allow_federation:
            # Fail-closed default posture: do not blend scopes unless explicitly enabled.
            effective_scope = "dogma"

        if effective_scope:
            sql += " AND c.scope = ?"
            params.append(effective_scope)
        elif allow_federation:
            query_mode = "federated"

        sql += " ORDER BY score ASC LIMIT ?"
        params.append(top_k)

        rows = conn.execute(sql, params).fetchall()
        results = []
        for row in rows:
            governs_tokens = [t for t in row["governs_csv"].split(",") if t]
            results.append(
                {
                    "chunk_id": row["chunk_id"],
                    "source_file": row["source_file"],
                    "scope": row["scope"],
                    "governance_tier": row["governance_tier"],
                    "partition_id": row["partition_id"],
                    "retention_policy": row["retention_policy"],
                    "heading": row["heading"],
                    "governs": governs_tokens,
                    "fallback_h2": bool(row["fallback_h2"]),
                    "start_line": row["start_line"],
                    "end_line": row["end_line"],
                    "content": row["content"],
                    "score": row["score"],
                }
            )

        return {
            "ok": True,
            "query": query,
            "normalized_query": normalized_query,
            "top_k": top_k,
            "filter_governs": normalized_filter,
            "filter_scope": effective_scope,
            "query_mode": query_mode,
            "allow_federation": allow_federation,
            "federation_reason": federation_reason.strip() if federation_reason else None,
            "count": len(results),
            "results": results,
        }
    except sqlite3.OperationalError as exc:
        raise RagIndexError(f"Invalid full-text query syntax: {exc}") from exc
    finally:
        conn.close()


def status_report(*, db_path: Path = INDEX_DB_PATH, freshness_seconds: int = 86400) -> dict[str, Any]:
    """Report index existence, version compatibility, and freshness."""
    if freshness_seconds < 1:
        raise ValueError("freshness_seconds must be >= 1")

    if not db_path.exists():
        return {
            "ok": True,
            "exists": False,
            "index_path": str(db_path),
            "index_version": None,
            "version_ok": False,
            "last_indexed": None,
            "seconds_since_last_index": None,
            "is_fresh": False,
            "freshness_seconds": freshness_seconds,
            "total_files": 0,
            "total_chunks": 0,
        }

    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        version = _meta_get(conn, "index_version")
        last_indexed = _meta_get(conn, "last_indexed")
        total_files = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        total_chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]

        seconds_since: float | None = None
        is_fresh = False
        if last_indexed:
            try:
                last_dt = datetime.fromisoformat(last_indexed)
                if last_dt.tzinfo is None:
                    # Normalize naive timestamps to UTC for safe subtraction.
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                seconds_since = (datetime.now(timezone.utc) - last_dt).total_seconds()
                is_fresh = seconds_since <= freshness_seconds
            except (TypeError, ValueError):
                seconds_since = None
                is_fresh = False

        version_ok = version == INDEX_VERSION

        return {
            "ok": True,
            "exists": True,
            "index_path": str(db_path),
            "index_version": version,
            "expected_index_version": INDEX_VERSION,
            "version_ok": version_ok,
            "last_indexed": last_indexed,
            "seconds_since_last_index": seconds_since,
            "is_fresh": bool(is_fresh and version_ok and total_chunks > 0),
            "freshness_seconds": freshness_seconds,
            "total_files": total_files,
            "total_chunks": total_chunks,
        }
    finally:
        conn.close()


def _gate_level(value: float, warn: float, fail: float) -> str:
    if value > fail:
        return "fail"
    if value > warn:
        return "warn"
    return "pass"


def health_report(
    *,
    db_path: Path = INDEX_DB_PATH,
    freshness_seconds: int = 600,
    pending_backlog: int = 0,
    consecutive_failures: int = 0,
    mismatch_rate: float = 0.0,
) -> dict[str, Any]:
    """Evaluate deterministic update-cadence gates for freshness/correctness/stability.

    `freshness_seconds` is the pass threshold for freshness. Values above this
    threshold move into warning/fail bands so CLI overrides change gate behavior
    deterministically.
    """
    if pending_backlog < 0:
        raise ValueError("pending_backlog must be >= 0")
    if consecutive_failures < 0:
        raise ValueError("consecutive_failures must be >= 0")
    if mismatch_rate < 0:
        raise ValueError("mismatch_rate must be >= 0")

    status = status_report(db_path=db_path, freshness_seconds=freshness_seconds)

    # Freshness gate policy: pass <= freshness_seconds, warn up to 3x threshold,
    # fail beyond 3x threshold.
    freshness_warn = float(freshness_seconds)
    freshness_fail = float(freshness_seconds * 3)
    freshness_seconds_since = status.get("seconds_since_last_index")
    if freshness_seconds_since is None:
        freshness_gate = "fail"
    else:
        freshness_gate = _gate_level(
            float(freshness_seconds_since),
            freshness_warn,
            freshness_fail,
        )

    backlog_gate = _gate_level(
        float(pending_backlog),
        float(UPDATE_HEALTH_THRESHOLDS["backlog"]["warn"]),
        float(UPDATE_HEALTH_THRESHOLDS["backlog"]["fail"]),
    )
    failures_gate = _gate_level(
        float(consecutive_failures),
        float(UPDATE_HEALTH_THRESHOLDS["failures"]["warn"]),
        float(UPDATE_HEALTH_THRESHOLDS["failures"]["fail"]),
    )
    mismatch_gate = _gate_level(
        float(mismatch_rate),
        float(UPDATE_HEALTH_THRESHOLDS["mismatch_rate"]["warn"]),
        float(UPDATE_HEALTH_THRESHOLDS["mismatch_rate"]["fail"]),
    )

    gates = {
        "freshness": freshness_gate,
        "backlog": backlog_gate,
        "stability": failures_gate,
        "correctness": mismatch_gate,
    }
    overall = "pass"
    if "fail" in gates.values() or not status.get("version_ok", False):
        overall = "fail"
    elif "warn" in gates.values():
        overall = "warn"

    thresholds = {
        **UPDATE_HEALTH_THRESHOLDS,
        "freshness": {
            "warn_sec": int(freshness_warn),
            "fail_sec": int(freshness_fail),
        },
    }

    return {
        "ok": True,
        "profile": "hybrid-watcher-plus-sweep",
        "overall": overall,
        "gates": gates,
        "inputs": {
            "pending_backlog": pending_backlog,
            "consecutive_failures": consecutive_failures,
            "mismatch_rate": mismatch_rate,
            "freshness_seconds": freshness_seconds,
        },
        "thresholds": thresholds,
        "status": status,
    }


def local_test_report(
    *,
    test_tier: str = "quick",
    probe_query: str = "governance",
    db_path: Path = INDEX_DB_PATH,
) -> dict[str, Any]:
    """Run a deterministic local test battery and return PR-ready evidence payload."""
    tier = test_tier.strip().lower()
    if tier not in VALID_TEST_TIERS:
        raise ValueError("Invalid test_tier. Expected one of: quick, standard, stress.")

    checks: list[dict[str, Any]] = []

    status = status_report(db_path=db_path, freshness_seconds=3600)
    checks.append(
        {
            "name": "status",
            "pass": bool(status.get("exists") and status.get("version_ok")),
            "details": {"exists": status.get("exists"), "version_ok": status.get("version_ok")},
        }
    )

    if status.get("exists") and status.get("version_ok"):
        q = query_index(probe_query, top_k=3, filter_scope="dogma", db_path=db_path)
        checks.append(
            {
                "name": "segmented-query",
                "pass": q.get("count", 0) >= 1,
                "details": {"count": q.get("count", 0), "scope": q.get("filter_scope")},
            }
        )
    else:
        checks.append({"name": "segmented-query", "pass": False, "details": {"reason": "index-unavailable"}})

    if tier in {"standard", "stress"}:
        health = health_report(
            db_path=db_path,
            freshness_seconds=600,
            pending_backlog=0,
            consecutive_failures=0,
            mismatch_rate=0.0,
        )
        checks.append(
            {
                "name": "health-gates",
                "pass": health.get("overall") in {"pass", "warn"},
                "details": {"overall": health.get("overall"), "gates": health.get("gates")},
            }
        )

    if tier == "stress":
        federated = query_index(
            probe_query,
            top_k=5,
            allow_federation=True,
            federation_reason="stress-tier cross-scope probe",
            db_path=db_path,
        )
        checks.append(
            {
                "name": "federated-query",
                "pass": federated.get("query_mode") == "federated",
                "details": {"query_mode": federated.get("query_mode"), "count": federated.get("count", 0)},
            }
        )

    verdict = "PASS" if all(c["pass"] for c in checks) else "FAIL"

    return {
        "ok": True,
        "tier": tier,
        "probe_query": probe_query,
        "verdict": verdict,
        "checks": checks,
        "failure_scenarios": list(FAILURE_SCENARIO_CATALOG),
        "evidence_template": {
            "environment_snapshot": ["os", "branch", "timestamp"],
            "commands_executed": ["status", "segmented-query", "health-gates(optional)", "federated-query(optional)"],
            "scenario_coverage": "F1-F9 checklist",
            "metrics": ["freshness", "correctness", "stability"],
            "gate_verdict": "PASS|FAIL",
        },
    }


def adoption_gate_report(*, enforcement_level: str = "medium", db_path: Path = INDEX_DB_PATH) -> dict[str, Any]:
    """Evaluate installability/adoption governance controls with graded enforcement."""
    level = enforcement_level.strip().lower()
    if level not in VALID_ENFORCEMENT_LEVELS:
        raise ValueError("Invalid enforcement_level. Expected one of: soft, medium, hard.")

    status = status_report(db_path=db_path, freshness_seconds=3600)
    quick = local_test_report(test_tier="quick", db_path=db_path)
    standard = local_test_report(test_tier="standard", db_path=db_path)
    health = health_report(db_path=db_path, freshness_seconds=600)

    reasons: list[str] = []
    passed = True

    if level == "soft":
        passed = True
        reasons.append("soft enforcement: advisory mode")
    elif level == "medium":
        passed = bool(status.get("exists") and status.get("version_ok") and quick.get("verdict") == "PASS")
        if not status.get("exists"):
            reasons.append("index missing")
        if not status.get("version_ok"):
            reasons.append("index version mismatch")
        if quick.get("verdict") != "PASS":
            reasons.append("quick local-test failed")
    else:
        passed = bool(
            status.get("exists")
            and status.get("version_ok")
            and standard.get("verdict") == "PASS"
            and health.get("overall") == "pass"
        )
        if not status.get("exists"):
            reasons.append("index missing")
        if not status.get("version_ok"):
            reasons.append("index version mismatch")
        if standard.get("verdict") != "PASS":
            reasons.append("standard local-test failed")
        if health.get("overall") != "pass":
            reasons.append("health overall is not pass")

    return {
        "ok": True,
        "enforcement_level": level,
        "passed": passed,
        "reasons": reasons,
        "status": status,
        "quick_test": quick,
        "standard_test": standard,
        "health": health,
    }


def answer_query(
    query: str,
    *,
    model: str = "ollama/phi3",
    template_path: Path = REPO_ROOT / "docs/templates/rag_answer.md",
    top_k: int = 5,
    db_path: Path = INDEX_DB_PATH,
) -> dict[str, Any]:
    """Perform retrieval and generate a grounded answer using LiteLLM."""
    if litellm is None:
        raise RagIndexError("litellm is not installed. Install with 'uv pip install litellm'.")

    if not template_path.exists():
        raise RagIndexError(f"Answer template not found at {template_path}")

    retrieval = query_index(query, top_k=top_k, db_path=db_path)
    if not retrieval["ok"]:
        return retrieval

    context_blocks = []
    for res in retrieval["results"]:
        block = (
            f"Source: {res['source_file']}\n"
            f"Range: L{res['start_line']}-L{res['end_line']}\n"
            f"Heading: {res['heading']}\n"
            f"Content:\n{res['content']}"
        )
        context_blocks.append(block)

    context_str = "\n\n---\n\n".join(context_blocks)
    template = template_path.read_text(encoding="utf-8")
    prompt = template.replace("{{context_chunks}}", context_str).replace("{{query}}", query)

    # Note: Using ollama/phi3 as default per Wave 1 Phase 6 constraints.
    # Local-Compute-First: Ollama is preferred over external APIs.
    # Algorithms-Before-Tokens: Prompt is template-driven, not interactive-tweaked.
    try:
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = response.choices[0].message.content
    except Exception as exc:
        if "ServiceUnavailableError" in type(exc).__name__:
            raise RagIndexError(
                "Ollama/Model service is not running. Start it with 'ollama serve' or check 'ollama list'."
            ) from exc
        raise RagIndexError(f"LiteLLM completion failed: {exc}") from exc

    return {
        "ok": True,
        "query": query,
        "model": model,
        "answer": answer,
        "retrieval": {
            "count": retrieval["count"],
            "sources": [res["source_file"] for res in retrieval["results"]],
        },
    }


def _print_output(payload: dict[str, Any], output: str, file: Any = None) -> None:
    if file is None:
        file = sys.stdout
    if output == "json":
        print(json.dumps(payload, indent=2), file=file)
        return

    if "answer" in payload:
        print(f"QUERY: {payload['query']}", file=file)
        print(f"MODEL: {payload['model']}", file=file)
        print("\n" + "=" * 20 + " ANSWER " + "=" * 20 + "\n", file=file)
        print(payload["answer"], file=file)
        print("\n" + "=" * 20 + " SOURCES " + "=" * 20 + "\n", file=file)
        for src in payload["retrieval"]["sources"]:
            print(f"- {src}", file=file)
        return

    if "results" in payload:
        if not payload.get("results"):
            print("No results.", file=file)
            return
        for row in payload["results"]:
            print(f"{row['source_file']}:{row['start_line']}-{row['end_line']} [{row['heading']}]", file=file)
            print(row["content"][:220], file=file)
            print(file=file)
        return

    for key, value in payload.items():
        print(f"{key}: {value}", file=file)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local retrieval index (Phase 2 core substrate).")
    parser.add_argument(
        "command", choices=["reindex", "query", "status", "health", "local-test", "adoption-gate", "answer"]
    )
    parser.add_argument("--output", default="json", choices=["json", "text"])

    parser.add_argument("--scope", default="incremental", choices=sorted(VALID_SCOPE))
    parser.add_argument("--dry-run", action="store_true")

    parser.add_argument("--query")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--filter-governs")
    parser.add_argument("--filter-scope")
    parser.add_argument("--allow-federation", action="store_true")
    parser.add_argument("--federation-reason")

    parser.add_argument("--freshness-seconds", type=int)
    parser.add_argument("--pending-backlog", type=int, default=0)
    parser.add_argument("--consecutive-failures", type=int, default=0)
    parser.add_argument("--mismatch-rate", type=float, default=0.0)
    parser.add_argument("--test-tier", default="quick")
    parser.add_argument("--probe-query", default="governance")
    parser.add_argument("--enforcement-level", default="medium")
    parser.add_argument("--model", default="ollama/phi3")
    parser.add_argument("--template-path", type=Path)

    args = parser.parse_args(argv)

    try:
        if args.command == "reindex":
            payload = reindex(scope=args.scope, dry_run=args.dry_run)
            if not payload.get("ok"):
                _print_output(payload, args.output, file=sys.stderr)
                return 1
            _print_output(payload, args.output)
            return 0

        if args.command == "query":
            if not args.query:
                parser.error("--query is required for query")
            payload = query_index(
                args.query,
                top_k=args.top_k,
                filter_governs=args.filter_governs,
                filter_scope=args.filter_scope,
                allow_federation=args.allow_federation,
                federation_reason=args.federation_reason,
            )
            _print_output(payload, args.output)
            return 0

        if args.command == "answer":
            if not args.query:
                parser.error("--query is required for answer")
            payload = answer_query(
                args.query,
                model=args.model,
                template_path=args.template_path or (REPO_ROOT / "docs/templates/rag_answer.md"),
                top_k=args.top_k,
            )
            if not payload.get("ok"):
                _print_output(payload, args.output, file=sys.stderr)
                return 1
            _print_output(payload, args.output)
            return 0

        if args.command == "status":
            freshness_seconds = args.freshness_seconds if args.freshness_seconds is not None else 86400
            payload = status_report(freshness_seconds=freshness_seconds)
            _print_output(payload, args.output)
            return 0

        if args.command == "health":
            freshness_seconds = args.freshness_seconds if args.freshness_seconds is not None else 600
            payload = health_report(
                freshness_seconds=freshness_seconds,
                pending_backlog=args.pending_backlog,
                consecutive_failures=args.consecutive_failures,
                mismatch_rate=args.mismatch_rate,
            )
            _print_output(payload, args.output)
            return 0

        if args.command == "local-test":
            payload = local_test_report(
                test_tier=args.test_tier,
                probe_query=args.probe_query,
            )
            _print_output(payload, args.output)
            return 0

        if args.command == "adoption-gate":
            payload = adoption_gate_report(enforcement_level=args.enforcement_level)
            _print_output(payload, args.output)
            if payload.get("passed"):
                return 0
            return 1

    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except RagIndexError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
