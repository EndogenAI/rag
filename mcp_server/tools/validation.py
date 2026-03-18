"""mcp_server/tools/validation.py — MCP tool implementations for governance validation.

Tools:
    validate_agent_file  — Validate a .agent.md file against AGENTS.md constraints.
    validate_synthesis   — Validate a D4 research synthesis document.
    check_substrate      — Run a full CRD substrate health check.

Inputs:
    file_path : str — path to the file to validate (must be within repo root)
    min_lines : int — (validate_synthesis only) minimum non-blank line count

Outputs:
    All tools return: {"ok": bool, "errors": list[str], "file_path": str}
    check_substrate returns: {"ok": bool, "errors": list[str], "report": str}

Usage (via MCP client or direct call):
    result = validate_agent_file(".github/agents/review.agent.md")
    result = validate_synthesis("docs/research/my-doc.md")
    result = check_substrate()
"""

from __future__ import annotations

import subprocess
import sys

from mcp_server._security import REPO_ROOT, validate_repo_path


def _run_script(args: list[str]) -> subprocess.CompletedProcess:
    """Run a dogma script via the current Python interpreter capturing output."""
    return subprocess.run(
        [sys.executable, *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=60,
    )


def validate_agent_file(file_path: str) -> dict:
    """Validate a .agent.md or SKILL.md file against AGENTS.md encoding constraints.

    Args:
        file_path: Absolute or repo-relative path to the .agent.md or SKILL.md file.

    Returns:
        {"ok": bool, "errors": list[str], "file_path": str}
    """
    try:
        resolved = validate_repo_path(file_path)
    except ValueError as exc:
        return {"ok": False, "errors": [str(exc)], "file_path": file_path}

    result = _run_script(
        [
            str(REPO_ROOT / "scripts" / "validate_agent_files.py"),
            str(resolved),
        ]
    )
    output_lines = (result.stdout + result.stderr).splitlines()
    errors = [ln for ln in output_lines if ln.strip()] if result.returncode != 0 else []
    return {
        "ok": result.returncode == 0,
        "errors": errors,
        "file_path": str(resolved),
    }


def validate_synthesis(file_path: str, min_lines: int = 80) -> dict:
    """Validate a D4 research synthesis document before archiving.

    Args:
        file_path: Absolute or repo-relative path to the synthesis Markdown file.
        min_lines: Minimum non-blank line count (default: 80).

    Returns:
        {"ok": bool, "errors": list[str], "file_path": str}
    """
    try:
        resolved = validate_repo_path(file_path)
    except ValueError as exc:
        return {"ok": False, "errors": [str(exc)], "file_path": file_path}

    result = _run_script(
        [
            str(REPO_ROOT / "scripts" / "validate_synthesis.py"),
            "--min-lines",
            str(min_lines),
            str(resolved),
        ]
    )
    output_lines = (result.stdout + result.stderr).splitlines()
    errors = [ln for ln in output_lines if ln.strip()] if result.returncode != 0 else []
    return {
        "ok": result.returncode == 0,
        "errors": errors,
        "file_path": str(resolved),
    }


def check_substrate() -> dict:
    """Run a full CRD substrate health check for dogma startup files.

    Returns:
        {"ok": bool, "errors": list[str], "report": str}
    """
    result = _run_script(
        [
            str(REPO_ROOT / "scripts" / "check_substrate_health.py"),
        ]
    )
    report = (result.stdout + result.stderr).strip()
    errors = [ln for ln in report.splitlines() if "BLOCK" in ln or "ERROR" in ln]
    return {
        "ok": result.returncode == 0,
        "errors": errors,
        "report": report,
    }
