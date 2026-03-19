#!/usr/bin/env python3
"""scripts/check_pr_closes.py

Validate pull request body contains GitHub auto-close syntax.

Purpose:
    Enforce PR body inclusion of issue auto-close directives (Closes/Fixes/Resolves)
    so merge-time closure is traceable and deterministic.

Inputs:
    --body <text>       PR body content passed inline.
    --body-file <path>  Path to file containing PR body content.

Outputs:
    stdout: Validation message and any matched close lines.

Exit codes:
    0  Valid PR body with at least one auto-close line.
    1  Missing or invalid input, or no auto-close lines found.

Usage examples:
    uv run python scripts/check_pr_closes.py --body "Summary\n\nCloses #12"
    uv run python scripts/check_pr_closes.py --body-file /tmp/pr_body.md
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

AUTO_CLOSE_RE = re.compile(r"(?im)^\s*(?:closes|fixes|resolves)\s*:??\s*#\d+\s*$")


def extract_auto_close_lines(body: str) -> list[str]:
    """Return all PR-body lines that match GitHub auto-close syntax."""
    return [line.strip() for line in body.splitlines() if AUTO_CLOSE_RE.match(line)]


def load_body(args: argparse.Namespace) -> str:
    """Load body text from inline arg or file arg."""
    if args.body is not None:
        return args.body

    if args.body_file is not None:
        return args.body_file.read_text(encoding="utf-8")

    return ""


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(description="Validate PR body contains auto-close syntax")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--body", help="PR body text")
    group.add_argument("--body-file", type=Path, help="Path to file containing PR body text")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    body = load_body(args)
    if not body.strip():
        print("ERROR: PR body is empty")
        return 1

    matches = extract_auto_close_lines(body)
    if not matches:
        print("ERROR: Missing auto-close syntax in PR body")
        print("Add at least one line like: Closes #123")
        return 1

    print("PASS: Found auto-close lines in PR body")
    for line in matches:
        print(f"- {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
