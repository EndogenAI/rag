"""dogma_governance.check_health

Composite health check: runs validate_agent and validate_synthesis against files
found by walking a directory tree.

Purpose:
    Scan a project root for agent files (.github/agents/*.agent.md) and synthesis
    documents (docs/research/*.md, excluding sources/ and README.md), run the
    appropriate validator on each, and return a summary of pass/fail counts.

Inputs:
    --directory DIR   Root directory to scan (default: CWD).
    --format json|summary  Output format (default: summary).

Outputs:
    Summary or JSON report with total checked, pass count, fail count, and list
    of failures with error messages.

Exit codes:
    0  All files pass (or no files found).
    1  One or more files fail.

Usage:
    dogma-check-health
    dogma-check-health --directory /path/to/repo --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dogma_governance.validate_agent import validate as validate_agent_file
from dogma_governance.validate_synthesis import validate as validate_synthesis_file

# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def run_health_check(directory: Path) -> dict:
    """Walk *directory* and validate all agent and synthesis files.

    Returns a dict:
        {
            "total": int,
            "passed": int,
            "failed": int,
            "failures": [{"file": str, "errors": [str]}]
        }
    """
    failures: list[dict] = []
    passed = 0
    total = 0

    # Agent files
    agents_dir = directory / ".github" / "agents"
    if agents_dir.is_dir():
        for agent_file in sorted(agents_dir.glob("*.agent.md")):
            total += 1
            ok, errors = validate_agent_file(agent_file)
            if ok:
                passed += 1
            else:
                failures.append({"file": str(agent_file), "errors": errors})

    # Synthesis files
    research_dir = directory / "docs" / "research"
    if research_dir.is_dir():
        for md_file in sorted(research_dir.glob("*.md")):
            if md_file.name == "README.md":
                continue
            total += 1
            ok, errors = validate_synthesis_file(md_file, min_lines=80)
            if ok:
                passed += 1
            else:
                failures.append({"file": str(md_file), "errors": errors})

    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "failures": failures,
    }


def format_summary(report: dict) -> str:
    """Render a human-readable health summary."""
    lines = [f"Health check: {report['total']} files checked, {report['passed']} passed, {report['failed']} failed."]
    for item in report["failures"]:
        lines.append(f"  FAIL {item['file']}")
        for err in item["errors"]:
            lines.append(f"       • {err}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point for dogma-check-health CLI."""
    parser = argparse.ArgumentParser(
        description="Run composite governance health check against a project directory.",
        epilog="Exit 0 = all pass. Exit 1 = one or more files fail.",
    )
    parser.add_argument(
        "--directory",
        default=None,
        metavar="DIR",
        help="Root directory to scan (default: current working directory).",
    )
    parser.add_argument(
        "--format",
        choices=["json", "summary"],
        default="summary",
        help="Output format: summary (default) or json.",
    )
    args = parser.parse_args()

    directory = Path(args.directory).expanduser().resolve() if args.directory else Path.cwd()

    report = run_health_check(directory)

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(format_summary(report))

    sys.exit(0 if report["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
