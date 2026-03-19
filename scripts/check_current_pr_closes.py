#!/usr/bin/env python3
"""scripts/check_current_pr_closes.py

Validate auto-close syntax in the open PR body for the current branch.

Purpose:
    Local pre-push enforcement for PR body closure syntax. If an open PR exists
    for the current branch, ensure it contains at least one valid auto-close line.

Inputs:
    --repo <owner/name>  Optional repository override (default: derived from origin).
    --branch <name>      Optional branch override (default: current git branch).

Outputs:
    stdout: Validation pass/fail messages and matched close lines.

Exit codes:
    0  No open PR for branch, or open PR has valid auto-close syntax.
    1  Open PR exists but missing auto-close syntax, or command failure.

Usage examples:
    uv run python scripts/check_current_pr_closes.py
    uv run python scripts/check_current_pr_closes.py --repo EndogenAI/rag --branch sprint/rag-sprint-1
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess

AUTO_CLOSE_RE = re.compile(r"(?im)^\s*(?:closes|fixes|resolves)\s*:??\s*#\d+\s*$")


def run_cmd(cmd: list[str]) -> str:
    """Run shell command and return stdout or raise RuntimeError."""
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"Command failed: {' '.join(cmd)}")
    return result.stdout


def parse_repo_from_origin(remote_url: str) -> str:
    """Extract owner/repo from a GitHub origin URL."""
    m = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$", remote_url.strip())
    if not m:
        raise RuntimeError(f"Could not parse GitHub repo from origin URL: {remote_url.strip()}")
    return f"{m.group('owner')}/{m.group('repo')}"


def get_current_branch() -> str:
    """Return current git branch name."""
    return run_cmd(["git", "branch", "--show-current"]).strip()


def get_repo_from_origin() -> str:
    """Return owner/repo parsed from origin remote URL."""
    origin_url = run_cmd(["git", "remote", "get-url", "origin"])
    return parse_repo_from_origin(origin_url)


def get_open_pr(repo: str, branch: str) -> dict | None:
    """Return open PR metadata for branch, or None if no open PR exists."""
    out = run_cmd(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            repo,
            "--head",
            branch,
            "--state",
            "open",
            "--limit",
            "1",
            "--json",
            "number,body,url,title",
        ]
    )
    items = json.loads(out)
    if not items:
        return None
    return items[0]


def extract_auto_close_lines(body: str) -> list[str]:
    """Return all PR-body lines that match GitHub auto-close syntax."""
    return [line.strip() for line in body.splitlines() if AUTO_CLOSE_RE.match(line)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate auto-close syntax for open PR on current branch")
    parser.add_argument("--repo", help="owner/name repository (default: parse from origin)")
    parser.add_argument("--branch", help="branch name (default: current branch)")
    args = parser.parse_args(argv)

    try:
        repo = args.repo or get_repo_from_origin()
        branch = args.branch or get_current_branch()
        pr = get_open_pr(repo, branch)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 1

    if pr is None:
        print(f"SKIP: No open PR found for {repo}:{branch}")
        return 0

    matches = extract_auto_close_lines(pr.get("body") or "")
    if not matches:
        print(f"ERROR: Open PR #{pr['number']} is missing auto-close syntax")
        print(f"PR URL: {pr['url']}")
        print("Add at least one line like: Closes #123")
        return 1

    print(f"PASS: Open PR #{pr['number']} includes auto-close syntax")
    print(f"PR URL: {pr['url']}")
    for line in matches:
        print(f"- {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
