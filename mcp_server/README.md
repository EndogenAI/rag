# dogma MCP Server

Exposes the dogma governance toolset as an [MCP](https://modelcontextprotocol.io/) server
using [FastMCP](https://github.com/jlowin/fastmcp). Provides 8 tools for validating,
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
| `prune_scratchpad` | Initialise or inspect the session scratchpad |

---

## Prerequisites

```bash
# Install the mcp optional dependency group
uv sync --extra mcp
```

Requires Python 3.10+ (mcp SDK constraint).

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
