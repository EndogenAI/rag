"""mcp_server/tools/scaffolding.py — MCP tool implementations for scaffolding.

Tools:
    scaffold_agent     — Scaffold a new .agent.md stub from template.
    scaffold_workplan  — Scaffold a new docs/plans/ workplan from template.

Inputs:
    scaffold_agent:
        name        : str — display name for the agent (e.g. 'Research Scout')
        description : str — one-line summary ≤ 200 chars
        area        : str — area prefix (default: 'scripts')
        posture     : str — 'readonly' | 'creator' | 'full' (default: 'creator')

    scaffold_workplan:
        slug        : str — dash-separated slug (e.g. 'my-feature-sprint')
        issues      : str — comma-separated issue numbers (optional)

Outputs:
    {"ok": bool, "output_path": str | None, "errors": list[str]}

Usage:
    result = scaffold_agent("My Agent", "One-line description", area="research")
    result = scaffold_workplan("my-feature-sprint", issues="123,124")
"""

from __future__ import annotations

import re
import subprocess
import sys

from mcp_server._security import REPO_ROOT


def _run_script(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=30,
    )


def scaffold_agent(
    name: str,
    description: str,
    area: str = "scripts",
    posture: str = "creator",
) -> dict:
    """Scaffold a new .agent.md stub from template.

    Args:
        name: Display name for the agent (e.g. 'Research Scout').
        description: One-line summary ≤ 200 characters.
        area: Area prefix used in the filename (e.g. 'research').
        posture: Tool posture — 'readonly', 'creator', or 'full'.

    Returns:
        {"ok": bool, "output_path": str | None, "errors": list[str]}
    """
    if len(description) > 200:
        return {"ok": False, "output_path": None, "errors": ["description must be ≤ 200 characters"]}

    if posture not in {"readonly", "creator", "full"}:
        return {
            "ok": False,
            "output_path": None,
            "errors": [f"Invalid posture '{posture}'. Must be one of: readonly, creator, full"],
        }

    result = _run_script(
        [
            str(REPO_ROOT / "scripts" / "scaffold_agent.py"),
            "--name",
            name,
            "--description",
            description,
            "--area",
            area,
            "--posture",
            posture,
        ]
    )

    output_path: str | None = None
    if result.returncode == 0:
        # Parse the created file path from stdout (scaffold_agent.py prints "Created: <path>")
        match = re.search(r"Created:\s*(.+\.agent\.md)", result.stdout)
        if match:
            output_path = match.group(1).strip()

    output_lines = (result.stdout + result.stderr).splitlines()
    errors = [ln for ln in output_lines if "ERROR" in ln or "error" in ln.lower()] if result.returncode != 0 else []
    return {
        "ok": result.returncode == 0,
        "output_path": output_path,
        "errors": errors,
    }


def scaffold_workplan(slug: str, issues: str = "") -> dict:
    """Scaffold a new docs/plans/ workplan from template.

    Args:
        slug: Dash-separated slug for the workplan (e.g. 'my-feature-sprint').
        issues: Comma-separated issue numbers (e.g. '42,43'). Optional.

    Returns:
        {"ok": bool, "output_path": str | None, "errors": list[str]}
    """
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", slug):
        return {
            "ok": False,
            "output_path": None,
            "errors": ["slug must be lowercase alphanumeric with dashes only (e.g. 'my-workplan')"],
        }

    args = [str(REPO_ROOT / "scripts" / "scaffold_workplan.py"), slug]
    if issues:
        args += ["--issues", issues]

    result = _run_script(args)

    output_path: str | None = None
    if result.returncode == 0:
        # scaffold_workplan.py prints "Created: docs/plans/<date>-<slug>.md"
        match = re.search(r"[Cc]reated[:\s]+(.+\.md)", result.stdout)
        if not match:
            # Fallback: look for any .md path in output
            match = re.search(r"docs/plans/\S+\.md", result.stdout)
        if match:
            output_path = match.group(1).strip() if "Created" in match.group(0) else match.group(0)

    output_lines = (result.stdout + result.stderr).splitlines()
    errors = [ln for ln in output_lines if "ERROR" in ln or "error" in ln.lower()] if result.returncode != 0 else []
    return {
        "ok": result.returncode == 0,
        "output_path": output_path,
        "errors": errors,
    }
