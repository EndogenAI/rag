"""mcp_server/dogma_server.py — FastMCP server exposing dogma governance tools.

Registers 11 tools via @mcp.tool():
    validate_agent_file  — Validate a .agent.md file against AGENTS.md constraints.
    validate_synthesis   — Validate a D4 synthesis document.
    check_substrate      — Run a full CRD substrate health check.
    scaffold_agent       — Scaffold a new .agent.md stub from template.
    scaffold_workplan    — Scaffold a new docs/plans/ workplan from template.
    run_research_scout   — Fetch and cache an external URL (SSRF-safe).
    query_docs           — BM25 query over the dogma documentation corpus.
    rag_query            — Query local Phase 2 retrieval index chunks.
    rag_reindex          — Build/rebuild local Phase 2 retrieval index.
    rag_status           — Report retrieval index freshness + version health.
    prune_scratchpad     — Initialise or inspect the session scratchpad.

Transport: stdio (default for Claude Desktop / Cursor / VS Code MCP clients).

Usage (standalone):
    uv run python -m mcp_server.dogma_server

Claude Desktop config (~/.claude/claude_desktop_config.json):
    {
      "mcpServers": {
        "dogma-governance": {
          "command": "uv",
          "args": ["run", "python", "-m", "mcp_server.dogma_server"],
          "cwd": "/path/to/dogma"
        }
      }
    }

See mcp_server/README.md for full setup, Cursor config, and environment variables.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_server.tools.research import query_docs as _query_docs
from mcp_server.tools.research import run_research_scout as _run_research_scout
from mcp_server.tools.retrieval import rag_query as _rag_query
from mcp_server.tools.retrieval import rag_reindex as _rag_reindex
from mcp_server.tools.retrieval import rag_status as _rag_status
from mcp_server.tools.scaffolding import scaffold_agent as _scaffold_agent
from mcp_server.tools.scaffolding import scaffold_workplan as _scaffold_workplan
from mcp_server.tools.scratchpad import prune_scratchpad as _prune_scratchpad
from mcp_server.tools.validation import check_substrate as _check_substrate
from mcp_server.tools.validation import validate_agent_file as _validate_agent_file
from mcp_server.tools.validation import validate_synthesis as _validate_synthesis

_INSTRUCTIONS = """\
You are connected to the dogma governance toolset.

All tools operate against the dogma repository that is running this server.
File paths must be relative to or absolute within the repository root.
URLs passed to run_research_scout must use https:// and resolve to public hostnames.

Governance axioms (MANIFESTO.md):
  1. Endogenous-First — read existing docs before acting
  2. Algorithms-Before-Tokens — prefer deterministic tools over repeated prompting
  3. Local-Compute-First — minimize remote API calls

Common workflow:
  1. check_substrate() — confirm the repository is in a healthy state
  2. query_docs("topic") — find relevant guidance before making changes
  3. validate_agent_file() / validate_synthesis() — validate changes before committing
  4. scaffold_agent() / scaffold_workplan() — create new governance artefacts
    5. rag_reindex() / rag_query() — local retrieval index build + grounded lookup
    6. prune_scratchpad() — initialise today's session scratchpad for cross-agent handoffs
"""

mcp = FastMCP("dogma-governance", instructions=_INSTRUCTIONS)


# ---------------------------------------------------------------------------
# Validation tools
# ---------------------------------------------------------------------------


@mcp.tool()
def validate_agent_file(file_path: str) -> dict:
    """Validate a .agent.md or SKILL.md file against AGENTS.md encoding constraints.

    Args:
        file_path: Absolute or repo-relative path to the .agent.md or SKILL.md file.

    Returns:
        {"ok": bool, "errors": list[str], "file_path": str}
    """
    return _validate_agent_file(file_path)


@mcp.tool()
def validate_synthesis(file_path: str, min_lines: int = 80) -> dict:
    """Validate a D4 research synthesis document before archiving.

    Args:
        file_path: Absolute or repo-relative path to the synthesis Markdown file.
        min_lines: Minimum non-blank line count (default: 80).

    Returns:
        {"ok": bool, "errors": list[str], "file_path": str}
    """
    return _validate_synthesis(file_path, min_lines)


@mcp.tool()
def check_substrate() -> dict:
    """Run a full CRD substrate health check (MANIFESTO.md, AGENTS.md, key scripts).

    Returns:
        {"ok": bool, "errors": list[str], "report": str}
    """
    return _check_substrate()


# ---------------------------------------------------------------------------
# Scaffolding tools
# ---------------------------------------------------------------------------


@mcp.tool()
def scaffold_agent(
    name: str,
    description: str,
    area: str = "scripts",
    posture: str = "creator",
) -> dict:
    """Scaffold a new .agent.md stub in .github/agents/ using the project template.

    Args:
        name: Display name for the agent (e.g. 'Research Scout').
        description: One-line summary ≤ 200 characters.
        area: Area prefix used in the filename (e.g. 'research').
        posture: Tool posture — 'readonly', 'creator', or 'full'.

    Returns:
        {"ok": bool, "output_path": str | None, "errors": list[str]}
    """
    return _scaffold_agent(name, description, area, posture)


@mcp.tool()
def scaffold_workplan(slug: str, issues: str = "") -> dict:
    """Scaffold a new docs/plans/<date>-<slug>.md workplan from template.

    Args:
        slug: Dash-separated slug for the workplan (e.g. 'my-feature-sprint').
        issues: Comma-separated issue numbers (e.g. '42,43'). Optional.

    Returns:
        {"ok": bool, "output_path": str | None, "errors": list[str]}
    """
    return _scaffold_workplan(slug, issues)


# ---------------------------------------------------------------------------
# Research tools
# ---------------------------------------------------------------------------


@mcp.tool()
def run_research_scout(url: str, force: bool = False) -> dict:
    """Fetch and cache an external URL via the dogma source cache.

    The URL is SSRF-validated before any network request is made.
    Cached result is stored in .cache/sources/ as distilled Markdown.

    Args:
        url: The https:// URL to fetch and cache.
        force: If True, re-fetch even if the URL is already cached.

    Returns:
        {"ok": bool, "url": str, "cache_path": str | None, "errors": list[str]}
    """
    return _run_research_scout(url, force)


@mcp.tool()
def query_docs(query: str, scope: str = "all", top_n: int = 5) -> dict:
    """BM25 query over the dogma documentation corpus.

    Args:
        query: The search query string.
        scope: Corpus scope — 'manifesto', 'agents', 'guides', 'research',
               'toolchain', 'skills', or 'all'.
        top_n: Number of top results to return (default: 5).

    Returns:
        {"ok": bool, "results": list[dict], "errors": list[str]}
    """
    return _query_docs(query, scope, top_n)


@mcp.tool()
def rag_query(query: str, top_k: int = 5, filter_governs: str | None = None) -> dict:
    """Query the local Phase 2 retrieval index.

    Args:
        query: The search query string.
        top_k: Number of chunks to return (1-50, default: 5).
        filter_governs: Optional governs-domain slug filter.

    Returns:
        Success: {"ok": true, "results": [...], ...}
        Error:   {"ok": false, "error": {"code", "message", "details"}}
    """
    return _rag_query(query, top_k, filter_governs)


@mcp.tool()
def rag_reindex(scope: str = "incremental", dry_run: bool = False) -> dict:
    """Build or refresh the local Phase 2 retrieval index.

    Args:
        scope: Reindex scope — "full" or "incremental".
        dry_run: If true, preview changes without writing.

    Returns:
        Success: {"ok": true, "stats": {...}}
        Error:   {"ok": false, "error": {"code", "message", "details"}}
    """
    return _rag_reindex(scope, dry_run)


@mcp.tool()
def rag_status(freshness_seconds: int = 86400) -> dict:
    """Report local retrieval index health, version, and freshness.

    Args:
        freshness_seconds: Staleness threshold in seconds.

    Returns:
        Success: {"ok": true, "status": {...}}
        Error:   {"ok": false, "error": {"code", "message", "details"}}
    """
    return _rag_status(freshness_seconds)


# ---------------------------------------------------------------------------
# Session management tools
# ---------------------------------------------------------------------------


@mcp.tool()
def prune_scratchpad(branch: str = "", dry_run: bool = False) -> dict:
    """Initialise or inspect the session scratchpad for the current branch.

    Creates .tmp/<branch>/<today>.md if it does not exist (--init mode).
    Use dry_run=True to check status without writing.

    Args:
        branch: Branch slug (auto-detected from git if empty).
        dry_run: If True, only checks status without creating or modifying files.

    Returns:
        {"ok": bool, "file_path": str | None, "exists": bool,
         "lines": int | None, "errors": list[str]}
    """
    return _prune_scratchpad(branch, dry_run)


if __name__ == "__main__":
    mcp.run()
