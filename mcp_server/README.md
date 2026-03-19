# dogma MCP Server

Exposes the dogma governance toolset as an [MCP](https://modelcontextprotocol.io/) server
using [FastMCP](https://github.com/jlowin/fastmcp). Provides 11 tools for validating,
scaffolding, researching, and managing sessions within the dogma repository.

---

## Tools

| Tool | Description |
|------|-------------|
| `validate_agent_file` | Validate a `.agent.md` file against AGENTS.md constraints |
| `validate_synthesis` | Validate a D4 synthesis doc before archiving |
| `check_substrate` | Full CRD substrate health check |
| `scaffold_agent` | Scaffold a new `.agent.md` stub from template |
| `scaffold_workplan` | Scaffold a new `docs/plans/` workplan from template |
| `run_research_scout` | Fetch and cache an external URL (SSRF-safe) |
| `query_docs` | BM25 query over the dogma documentation corpus |
| `rag_query` | Query local H2-chunk retrieval index with metadata filters |
| `rag_reindex` | Build/rebuild local retrieval index (`full` or `incremental`) |
| `rag_status` | Report index health, version compatibility, and freshness |
| `prune_scratchpad` | Initialise or inspect the session scratchpad |

---

## Prerequisites

```bash
# Install the mcp optional dependency group
uv sync --extra mcp
```

Requires Python 3.10+ (mcp SDK constraint).

---

## VS Code Quickstart (Clean Machine)

This path takes you from clone to first successful retrieval (`rag_query`).

1. Clone and enter the repository.

```bash
git clone https://github.com/EndogenAI/dogma.git
cd dogma
```

2. Install dependencies for MCP and development checks.

```bash
uv sync --extra mcp --extra dev
```

3. Confirm MCP server config exists for VS Code Copilot.

```bash
cat .vscode/mcp.json
```

Expected server entry:

```json
{
  "servers": {
    "dogma-governance": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "python", "-m", "mcp_server.dogma_server"]
    }
  }
}
```

4. Bootstrap retrieval index (first run).

```bash
uv run python scripts/rag_index.py reindex --scope full --output json
```

5. Verify index health.

```bash
uv run python scripts/rag_index.py status --output json
```

Expected signal: `"ok": true`, `"version_ok": true`, and `"total_files" > 0`.

6. Open VS Code in this repo, then open Copilot Chat and run an MCP call to `rag_query`.

Suggested first query:

- tool: `rag_query`
- args: `query="programmatic first"`, `top_k=3`

Expected signal: response has `ok: true` and `count >= 1` with chunk metadata.

If you want to validate the same path from terminal (same MCP wrapper functions):

```bash
uv run python -c "import json; from mcp_server.tools.retrieval import rag_query; print(json.dumps(rag_query('programmatic first', top_k=3), indent=2))"
```

---

## Retrieval Bootstrap and Tool Usage

Use these tools through MCP clients (VS Code, Cursor, Claude Desktop). CLI equivalents are shown for local verification.

| MCP tool | Purpose | Typical call | CLI equivalent |
|---|---|---|---|
| `rag_reindex` | Build or refresh index | `scope="full"` (first build), `scope="incremental"` (daily updates), optional `dry_run=true` | `uv run python scripts/rag_index.py reindex --scope full --output json` |
| `rag_status` | Check index health, version, and freshness | `freshness_seconds=86400` (default) | `uv run python scripts/rag_index.py status --output json` |
| `rag_query` | Retrieve H2-grounded chunks | `query="..."`, `top_k=5`, optional `filter_governs="local-compute-first"` | `uv run python scripts/rag_index.py query --query "..." --top-k 5 --output json` |

Operational pattern:

1. Run `rag_reindex(scope="full")` once on first setup.
2. Run `rag_status()` before query-heavy sessions.
3. Use `rag_query()` for grounded retrieval.
4. Use `rag_reindex(scope="incremental")` after major doc changes.

---

## Retrieval Architecture Flow

The retrieval path is deterministic and local-first.

```text
Markdown corpus
  (AGENTS.md, MANIFESTO.md, docs/**, .github/agents/*.agent.md, .github/skills/**)
        |
        v
scripts/rag_index.py reindex
  - H2 chunking + frozen fallback
  - metadata extraction (governs/x-governs)
        |
        v
rag-index/rag_index.sqlite3 (FTS5)
        |
        v
mcp_server/tools/retrieval.py
  - rag_reindex
  - rag_status
  - rag_query
        |
        v
MCP client (VS Code / Cursor / Claude)
        |
        v
Grounded retrieval results (chunk + source file + line range + governs)
```

---

## Index Storage and Benchmark Evidence

### Local Index Path and Gitignore

- Default local index path: `rag-index/rag_index.sqlite3` (created by `scripts/rag_index.py`).
- Index storage is local-only and excluded from commits via `.gitignore` entry `rag-index/`.
- This keeps retrieval state reproducible per machine without introducing generated DB artifacts into git history.

### Apple Silicon Reindex Benchmark (Cold + Warm)

Environment and dataset from measured run:

- machine: `macOS-26.3-arm64-arm-64bit`
- processor: `arm`
- benchmark index path: `rag-index/rag_index.sqlite3`
- corpus size during run: `363` files, `2465` total chunks

Reproducible benchmark commands (default local index path):

```bash
# Cold full reindex (clear default local index first)
uv run python -c "from pathlib import Path; Path('rag-index/rag_index.sqlite3').unlink(missing_ok=True); Path('rag-index/rag_index.sqlite3-journal').unlink(missing_ok=True)"
/usr/bin/time -p uv run python scripts/rag_index.py reindex --scope full --output json

# Warm full reindex (same corpus immediately after cold run)
/usr/bin/time -p uv run python scripts/rag_index.py reindex --scope full --output json

# Warm incremental reindex (no corpus changes expected)
/usr/bin/time -p uv run python scripts/rag_index.py reindex --scope incremental --output json
```

Measured results (Apple Silicon):

| Run | Elapsed | files_updated | files_unchanged | total_chunks |
|---|---:|---:|---:|---:|
| cold_full | 0.794s | 363 | 0 | 2465 |
| warm_full | 1.148s | 363 | 0 | 2465 |
| warm_incremental | 0.083s | 0 | 363 | 2465 |

---

## Troubleshooting

### Server startup failures

- Symptom: MCP server does not appear in client tools.
- Check: run `uv sync --extra mcp` and restart the client.
- Check: verify `.vscode/mcp.json` command is `uv run python -m mcp_server.dogma_server`.
- Check: run server directly to confirm import path works:

```bash
uv run python -m mcp_server.dogma_server
```

### Indexing failures (`rag_reindex`)

- Symptom: `ok: false` with `INDEX_REINDEX_FAILED` or version mismatch.
- Check full rebuild:

```bash
uv run python scripts/rag_index.py reindex --scope full --output json
```

- Check status immediately after:

```bash
uv run python scripts/rag_index.py status --output json
```

- If index is stale, rerun with `scope="incremental"` after content updates.

### Query failures (`rag_query`)

- Symptom: `INDEX_NOT_FOUND`.
- Fix: run `rag_reindex(scope="full")` first.

- Symptom: `INVALID_ARGUMENT`.
- Fixes:
  - Ensure `query` is non-empty.
  - Ensure `top_k` is between 1 and 50.
  - Ensure `filter_governs` matches `^[a-z0-9][a-z0-9-]*$`.
  - If query includes punctuation or `-`, retry with plain words (for example `"programmatic first"`).

- Symptom: successful call with `count: 0`.
- Fixes:
  - Broaden query terms.
  - Remove restrictive `filter_governs`.
  - Confirm corpus is indexed (`total_files > 0` in `rag_status`).

---

## Claude Desktop Setup

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dogma-governance": {
      "command": "uv",
      "args": ["run", "python", "-m", "mcp_server.dogma_server"],
      "cwd": "/absolute/path/to/your/dogma-clone"
    }
  }
}
```

Restart Claude Desktop after saving. The server appears under **Tools** in the sidebar.

---

## Cursor Setup

Add to `.cursor/mcp.json` (project-scoped) or `~/.cursor/mcp.json` (global):

```json
{
  "mcpServers": {
    "dogma-governance": {
      "command": "uv",
      "args": ["run", "python", "-m", "mcp_server.dogma_server"],
      "cwd": "/absolute/path/to/your/dogma-clone"
    }
  }
}
```

---

## VS Code + GitHub Copilot Setup

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "dogma-governance": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "python", "-m", "mcp_server.dogma_server"]
    }
  }
}
```

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Default | Description |
|----------|---------|-------------|
| `DOGMA_MCP_PORT` | `8000` | Port for HTTP transport mode (if using SSE/HTTP) |
| `DOGMA_MCP_AUTH_TOKEN` | _(empty)_ | Optional bearer token for HTTP transport auth |

The default transport is **stdio**, which does not use `DOGMA_MCP_PORT`. These variables
are reserved for future HTTP transport support.

---

## Security Model

- **Path traversal protection**: all file path arguments are resolved and checked against
  `REPO_ROOT` before any script is invoked. Paths outside the repo root are rejected.
- **SSRF protection**: `run_research_scout` validates URLs before fetching — blocks
  RFC 1918 private ranges, loopback, IPv6 link-local, and non-https schemes.
- **Subprocess isolation**: all tools invoke existing dogma scripts via `sys.executable`
  with an explicit argument list (no `shell=True`). Environment is inherited from the
  launched server process.

---

## Running in HTTP Mode (Advanced)

To expose the server over HTTP (e.g. for remote MCP clients):

```bash
DOGMA_MCP_PORT=8000 uv run python -m mcp_server.dogma_server --transport streamable-http
```

> **Note**: HTTP mode is not authenticated by default. Use `DOGMA_MCP_AUTH_TOKEN` and a
> reverse proxy with TLS for production deployments.

---

## Development

```bash
# Run tests
uv run pytest tests/test_mcp_server.py -v

# Lint
uv run ruff check mcp_server/

# Type-check (optional)
uv run mypy mcp_server/
```

---

## Module Reference (Concise)

### `mcp_server/dogma_server.py`
- `mcp`: FastMCP app instance (`dogma-governance`)
- Registers 11 tool functions from `mcp_server/tools/*`

### `mcp_server/_security.py`
- `validate_repo_path(file_path: str) -> Path`
  - Rejects paths outside repository root (path traversal guard)
- `validate_url(url: str) -> str`
  - Enforces https-only and blocks private/loopback/link-local targets (SSRF guard)

### `mcp_server/tools/validation.py`
- `validate_agent_file(file_path: str) -> dict`
  - Runs `scripts/validate_agent_files.py` on a repo-scoped path
- `validate_synthesis(file_path: str, min_lines: int = 80) -> dict`
  - Runs `scripts/validate_synthesis.py` with line threshold
- `check_substrate() -> dict`
  - Runs `scripts/check_substrate_health.py` and returns report summary

### `mcp_server/tools/scaffolding.py`
- `scaffold_agent(name: str, description: str, area: str = "general", posture: str = "readonly") -> dict`
  - Wraps `scripts/scaffold_agent.py` with input validation
- `scaffold_workplan(slug: str, issues: str = "") -> dict`
  - Wraps `scripts/scaffold_workplan.py` for plan skeleton creation

### `mcp_server/tools/research.py`
- `run_research_scout(url: str, force: bool = False) -> dict`
  - URL validation + `scripts/fetch_source.py`
- `query_docs(query: str, scope: str = "all", top_n: int = 5) -> dict`
  - Wraps `scripts/query_docs.py` for BM25 search results

### `mcp_server/tools/retrieval.py`
- `rag_query(query: str, top_k: int = 5, filter_governs: str | None = None) -> dict`
  - Wraps `scripts/rag_index.py query` and returns structured query results
- `rag_reindex(scope: str = "incremental", dry_run: bool = False) -> dict`
  - Wraps `scripts/rag_index.py reindex` with full/incremental modes
- `rag_status(freshness_seconds: int = 86400) -> dict`
  - Wraps `scripts/rag_index.py status` for freshness/version reporting

### `mcp_server/tools/scratchpad.py`
- `prune_scratchpad(branch: str = "", dry_run: bool = False) -> dict`
  - Wraps `scripts/prune_scratchpad.py` (`--init`/`--check-only`)
  - Supports explicit branch-targeted daily scratchpad path via `--file`
