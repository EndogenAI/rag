"""mcp_server/tools/research.py — MCP tool implementations for research and docs query.

Tools:
    run_research_scout — Fetch and cache an external URL via the dogma source cache.
    query_docs         — BM25 query over the dogma documentation corpus.

Inputs:
    run_research_scout:
        url   : str — https:// URL to fetch and cache (SSRF-validated)
        force : bool — re-fetch even if already cached (default: False)

    query_docs:
        query  : str — search query string
        scope  : str — corpus scope: 'manifesto' | 'agents' | 'guides' | 'research' |
                       'toolchain' | 'skills' | 'all' (default: 'all')
        top_n  : int  — number of results to return (default: 5)

Outputs:
    run_research_scout: {"ok": bool, "url": str, "cache_path": str | None, "errors": list[str]}
    query_docs:         {"ok": bool, "results": list[dict], "errors": list[str]}

Usage:
    result = run_research_scout("https://modelcontextprotocol.io/docs/overview")
    result = query_docs("session scratchpad architecture", scope="research", top_n=3)
"""

from __future__ import annotations

import json
import subprocess
import sys

from mcp_server._security import REPO_ROOT, validate_url

_VALID_SCOPES: frozenset[str] = frozenset({"manifesto", "agents", "guides", "research", "toolchain", "skills", "all"})


def _run_script(args: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=timeout,
    )


def run_research_scout(url: str, force: bool = False) -> dict:
    """Fetch and cache an external URL via the dogma source cache (fetch_source.py).

    The URL is SSRF-validated before any network call is made (https:// only,
    no private/loopback/link-local destinations).

    Args:
        url: The https:// URL to fetch and cache.
        force: If True, re-fetch even if the URL is already in .cache/sources/.

    Returns:
        {"ok": bool, "url": str, "cache_path": str | None, "errors": list[str]}
    """
    try:
        safe_url = validate_url(url)
    except ValueError as exc:
        return {"ok": False, "url": url, "cache_path": None, "errors": [str(exc)]}

    args = [str(REPO_ROOT / "scripts" / "fetch_source.py"), safe_url]
    if force:
        args.append("--force")

    result = _run_script(args, timeout=120)

    cache_path: str | None = None
    if result.returncode == 0:
        # fetch_source.py prints the cache path on success
        for line in result.stdout.splitlines():
            if ".cache/sources/" in line:
                cache_path = line.strip().split()[-1]
                break

    output_lines = (result.stdout + result.stderr).splitlines()
    errors = [ln for ln in output_lines if "ERROR" in ln or "error" in ln.lower()] if result.returncode != 0 else []
    return {
        "ok": result.returncode == 0,
        "url": safe_url,
        "cache_path": cache_path,
        "errors": errors,
    }


def query_docs(query: str, scope: str = "all", top_n: int = 5) -> dict:
    """BM25 query over the dogma documentation corpus.

    Args:
        query: The search query string.
        scope: Corpus scope — one of: manifesto, agents, guides, research,
               toolchain, skills, all.
        top_n: Number of top results to return (default: 5).

    Returns:
        {"ok": bool, "results": list[dict], "errors": list[str]}
    """
    if scope not in _VALID_SCOPES:
        return {
            "ok": False,
            "results": [],
            "errors": [f"Invalid scope '{scope}'. Must be one of: {sorted(_VALID_SCOPES)}"],
        }

    result = _run_script(
        [
            str(REPO_ROOT / "scripts" / "query_docs.py"),
            query,
            "--scope",
            scope,
            "--top-n",
            str(top_n),
            "--output",
            "json",
        ]
    )

    if result.returncode != 0:
        return {
            "ok": False,
            "results": [],
            "errors": [ln for ln in (result.stdout + result.stderr).splitlines() if ln.strip()],
        }

    try:
        results = json.loads(result.stdout)
    except json.JSONDecodeError:
        results = [{"raw": result.stdout}]

    return {"ok": True, "results": results, "errors": []}
