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

    status flags:
        --freshness-seconds INT   Staleness threshold (default: 86400)

Outputs:
    reindex: Index stats JSON/text (updated/unchanged/removed/chunk counts)
    query:   JSON/text list of chunk matches with metadata
    status:  JSON/text health report (version + freshness)

Usage:
    uv run python scripts/rag_index.py reindex --scope full
    uv run python scripts/rag_index.py reindex --scope incremental --dry-run
    uv run python scripts/rag_index.py query --query "programmatic-first" --top-k 3
    uv run python scripts/rag_index.py query --query "commit" --filter-governs commit-discipline
    uv run python scripts/rag_index.py status --freshness-seconds 3600

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

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = REPO_ROOT / "rag-index"
INDEX_DB_PATH = INDEX_DIR / "rag_index.sqlite3"
INDEX_VERSION = "phase2-v1"
FROZEN_H2_FALLBACK_HEADING = "__FROZEN_H2_FALLBACK__"

CORPUS_GLOBS: tuple[str, ...] = (
    "AGENTS.md",
    "MANIFESTO.md",
    "docs/**/*.md",
    ".github/agents/*.agent.md",
    ".github/skills/**/*.md",
)

VALID_SCOPE: frozenset[str] = frozenset({"full", "incremental"})
_GOVERNS_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

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

CREATE VIRTUAL TABLE IF NOT EXISTS rag_fts USING fts5(
    chunk_id UNINDEXED,
    content,
    source_file UNINDEXED,
    heading UNINDEXED,
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
    rel = str(path.relative_to(repo_root))
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
                chunk_id, source_file, heading, governs_csv, fallback_h2,
                start_line, end_line, content, content_hash, indexed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    c.chunk_id,
                    c.source_file,
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
            "INSERT INTO rag_fts(chunk_id, content, source_file, heading, governs) VALUES (?, ?, ?, ?, ?)",
            [(c.chunk_id, c.content, c.source_file, c.heading, c.governs_csv) for c in chunks],
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


def query_index(
    query: str,
    *,
    top_k: int = 5,
    filter_governs: str | None = None,
    db_path: Path = INDEX_DB_PATH,
) -> dict[str, Any]:
    """Query the index with optional governs filtering."""
    if not query.strip():
        raise ValueError("query must be a non-empty string")
    if top_k < 1 or top_k > 50:
        raise ValueError("top_k must be between 1 and 50")

    normalized_filter = _validate_filter_governs(filter_governs)

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

        sql = (
            "SELECT c.chunk_id, c.source_file, c.heading, c.governs_csv, c.fallback_h2, "
            "c.start_line, c.end_line, c.content, bm25(rag_fts) AS score "
            "FROM rag_fts "
            "JOIN chunks c ON c.chunk_id = rag_fts.chunk_id "
            "WHERE rag_fts MATCH ?"
        )
        params: list[Any] = [query]

        if normalized_filter:
            sql += " AND c.governs_csv LIKE ?"
            params.append(f"%,{normalized_filter},%")

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
            "top_k": top_k,
            "filter_governs": normalized_filter,
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


def _print_output(payload: dict[str, Any], output: str) -> None:
    if output == "json":
        print(json.dumps(payload, indent=2))
        return

    if "results" in payload:
        if not payload.get("results"):
            print("No results.")
            return
        for row in payload["results"]:
            print(f"{row['source_file']}:{row['start_line']}-{row['end_line']} [{row['heading']}]")
            print(row["content"][:220])
            print()
        return

    for key, value in payload.items():
        print(f"{key}: {value}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local retrieval index (Phase 2 core substrate).")
    parser.add_argument("command", choices=["reindex", "query", "status"])
    parser.add_argument("--output", default="json", choices=["json", "text"])

    parser.add_argument("--scope", default="incremental", choices=sorted(VALID_SCOPE))
    parser.add_argument("--dry-run", action="store_true")

    parser.add_argument("--query")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--filter-governs")

    parser.add_argument("--freshness-seconds", type=int, default=86400)

    args = parser.parse_args(argv)

    try:
        if args.command == "reindex":
            payload = reindex(scope=args.scope, dry_run=args.dry_run)
            if not payload.get("ok"):
                print(json.dumps(payload, indent=2), file=sys.stderr)
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
            )
            _print_output(payload, args.output)
            return 0

        if args.command == "status":
            payload = status_report(freshness_seconds=args.freshness_seconds)
            _print_output(payload, args.output)
            return 0

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
