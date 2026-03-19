"""mcp_server/tools/retrieval.py — MCP wrappers for Phase 2 retrieval substrate tools.

Tools:
    rag_query   — query the local retrieval index with optional governs filter
    rag_reindex — run full/incremental reindex
    rag_status  — report index version + freshness status

All tool responses use a strict envelope:
    success: {"ok": true, ...}
    error:   {"ok": false, "error": {"code", "message", "details"}}
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from typing import Any

from mcp_server._security import REPO_ROOT

_VALID_SCOPE: frozenset[str] = frozenset({"full", "incremental"})
_GOVERNS_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def _run_script(args: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=timeout,
    )


def _error(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
    }


def _parse_json(text: str) -> dict[str, Any]:
    return json.loads(text) if text.strip() else {}


def rag_query(query: str, top_k: int = 5, filter_governs: str | None = None) -> dict[str, Any]:
    """Query local retrieval index chunks.

    Args:
        query: Free-text query.
        top_k: Number of chunks to return (1-50).
        filter_governs: Optional governs slug filter.

    Returns:
        Success envelope containing query metadata and `results`.
        Error envelope with structured `error` payload.
    """
    if not isinstance(query, str) or not query.strip():
        return _error("INVALID_ARGUMENT", "query must be a non-empty string")

    if not isinstance(top_k, int) or top_k < 1 or top_k > 50:
        return _error("INVALID_ARGUMENT", "top_k must be an integer between 1 and 50", {"top_k": top_k})

    if filter_governs is not None:
        if not isinstance(filter_governs, str):
            return _error(
                "INVALID_ARGUMENT",
                "filter_governs must be a string slug when provided",
                {"filter_governs": filter_governs},
            )
        if not _GOVERNS_RE.fullmatch(filter_governs):
            return _error(
                "INVALID_ARGUMENT",
                "filter_governs must match ^[a-z0-9][a-z0-9-]*$",
                {"filter_governs": filter_governs},
            )

    args = [
        str(REPO_ROOT / "scripts" / "rag_index.py"),
        "query",
        "--query",
        query,
        "--top-k",
        str(top_k),
        "--output",
        "json",
    ]
    if filter_governs:
        args.extend(["--filter-governs", filter_governs])

    result = _run_script(args)
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        code = "INDEX_QUERY_FAILED"
        if "Index not found" in stderr:
            code = "INDEX_NOT_FOUND"
        elif "version mismatch" in stderr.lower():
            code = "INDEX_VERSION_MISMATCH"
        elif "Invalid" in stderr:
            code = "INVALID_ARGUMENT"
        return _error(code, "rag_query failed", {"stderr": stderr})

    try:
        payload = _parse_json(result.stdout)
    except json.JSONDecodeError:
        return _error("MALFORMED_SCRIPT_OUTPUT", "rag_query returned non-JSON output", {"stdout": result.stdout})

    return {
        "ok": True,
        "query": payload.get("query", query),
        "top_k": payload.get("top_k", top_k),
        "filter_governs": payload.get("filter_governs"),
        "count": payload.get("count", 0),
        "results": payload.get("results", []),
    }


def rag_reindex(scope: str = "incremental", dry_run: bool = False) -> dict[str, Any]:
    """Build or refresh the retrieval index.

    Args:
        scope: `full` or `incremental`.
        dry_run: If True, preview reindex behavior without writes.

    Returns:
        Success envelope with reindex stats or structured error payload.
    """
    if scope not in _VALID_SCOPE:
        return _error("INVALID_ARGUMENT", f"scope must be one of: {sorted(_VALID_SCOPE)}", {"scope": scope})

    if not isinstance(dry_run, bool):
        return _error("INVALID_ARGUMENT", "dry_run must be boolean", {"dry_run": dry_run})

    args = [
        str(REPO_ROOT / "scripts" / "rag_index.py"),
        "reindex",
        "--scope",
        scope,
        "--output",
        "json",
    ]
    if dry_run:
        args.append("--dry-run")

    result = _run_script(args, timeout=180)
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        error_code = "INDEX_REINDEX_FAILED"

        try:
            parsed = _parse_json(stderr)
            if isinstance(parsed, dict) and parsed.get("error_code"):
                error_code = parsed["error_code"]
            return _error(error_code, "rag_reindex failed", parsed)
        except json.JSONDecodeError:
            if "version mismatch" in stderr.lower():
                error_code = "INDEX_VERSION_MISMATCH"
            return _error(error_code, "rag_reindex failed", {"stderr": stderr})

    try:
        payload = _parse_json(result.stdout)
    except json.JSONDecodeError:
        return _error(
            "MALFORMED_SCRIPT_OUTPUT",
            "rag_reindex returned non-JSON output",
            {"stdout": result.stdout},
        )

    if not payload.get("ok", False):
        return _error(payload.get("error_code", "INDEX_REINDEX_FAILED"), "rag_reindex failed", payload)

    return {"ok": True, "stats": payload}


def rag_status(freshness_seconds: int = 86400) -> dict[str, Any]:
    """Return retrieval index health information."""
    if not isinstance(freshness_seconds, int) or freshness_seconds < 1:
        return _error(
            "INVALID_ARGUMENT",
            "freshness_seconds must be an integer >= 1",
            {"freshness_seconds": freshness_seconds},
        )

    args = [
        str(REPO_ROOT / "scripts" / "rag_index.py"),
        "status",
        "--freshness-seconds",
        str(freshness_seconds),
        "--output",
        "json",
    ]
    result = _run_script(args)
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        return _error("INDEX_STATUS_FAILED", "rag_status failed", {"stderr": stderr})

    try:
        payload = _parse_json(result.stdout)
    except json.JSONDecodeError:
        return _error(
            "MALFORMED_SCRIPT_OUTPUT",
            "rag_status returned non-JSON output",
            {"stdout": result.stdout},
        )

    return {"ok": True, "status": payload}
