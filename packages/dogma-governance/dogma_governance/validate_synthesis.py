"""dogma_governance.validate_synthesis

Programmatic quality gate for D3/D4 synthesis documents.

Purpose:
    Validate D3 per-source synthesis reports (docs/research/sources/<slug>.md)
    and D4 issue synthesis documents (docs/research/<slug>.md) before archiving.
    Document type is detected automatically: D3 if path contains /sources/,
    D4 otherwise.

Inputs:
    files           One or more synthesis document paths (positional, required).
    --min-lines N   Minimum non-blank line count (default: 80).
    --strict        Reserved for future use (no-op).
    --allow-final-edit  Suppress the WARNING when a Final-status doc is modified.

Outputs:
    stdout: per-file PASS/FAIL with specific failure list.

Exit codes:
    0  All checks passed.
    1  One or more checks failed.

Usage:
    dogma-validate-synthesis docs/research/my-topic.md
    dogma-validate-synthesis docs/research/sources/my-source.md --min-lines 150
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

D3_REQUIRED_SECTIONS: list[tuple[str, list[str]]] = [
    ("Citation", ["citation"]),
    ("Research Question", ["research question"]),
    ("Theoretical Framework", ["theoretical"]),
    ("Methodology", ["methodology", "source type"]),
    ("Key Claims", ["key claims", "key findings"]),
    ("Critical Assessment", ["critical assessment"]),
    ("Cross-Source Connections", ["cross-source", "connection to other"]),
    ("Project Relevance", ["project relevance", "relevance to endogenai"]),
]

D4_REQUIRED_HEADINGS: list[str] = [
    "## 1. Executive Summary",
    "## 2. Hypothesis Validation",
    "## 3. Pattern Catalog",
]

D4_MIN_HEADING_COUNT = 4

D3_REQUIRED_FRONTMATTER: list[str] = ["slug", "title", "cache_path"]
D3_URL_KEYS: list[str] = ["url", "source_url"]

D4_REQUIRED_FRONTMATTER: list[str] = ["title", "status"]

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)

_AXIOM_NAMES: tuple[str, ...] = (
    "Endogenous-First",
    "Algorithms Before Tokens",
    "Local Compute-First",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def parse_frontmatter(text: str) -> dict[str, str]:
    """Return a flat dict of YAML frontmatter key → raw string value."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fm: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm


def extract_headings(text: str) -> list[str]:
    """Return all Markdown H2 headings (## ...) found in the document body."""
    body_start = 0
    fm_match = _FRONTMATTER_RE.match(text)
    if fm_match:
        body_start = fm_match.end()
    body = text[body_start:]
    return [line.rstrip() for line in body.splitlines() if line.startswith("## ")]


def non_blank_line_count(text: str) -> int:
    """Count non-blank lines in the document (including frontmatter)."""
    return sum(1 for line in text.splitlines() if line.strip())


def is_d3(file_path: Path) -> bool:
    """Return True if *file_path* is a D3 per-source synthesis document (under sources/)."""
    return "sources" in file_path.parts


def check_final_status_modified(file_path: Path, allow_final_edit: bool) -> None:
    """Warn when a Final- or Published-status doc has uncommitted modifications.

    Uses git diff to detect modification. Prints a WARNING unless allow_final_edit is True.
    Does NOT call sys.exit — advisory only.
    """
    fm = parse_frontmatter(file_path.read_text(encoding="utf-8"))
    status = fm.get("status", "").strip().lower()
    if status not in ("final", "published"):
        return

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        modified_files = result.stdout.strip().splitlines()
    except FileNotFoundError:
        return

    try:
        cwd = Path.cwd()
        resolved_target = file_path.resolve()
        is_modified = any((cwd / Path(f)).resolve() == resolved_target for f in modified_files)
    except Exception:
        return

    if is_modified and not allow_final_edit:
        print(
            "WARNING: Final-status research doc modified — manual review gate recommended "
            "before committing. Use --allow-final-edit to suppress."
        )


def check_axiom_citations(lines: list[str], filepath: str) -> None:
    """Warn when an axiom name appears without a MANIFESTO.md §-reference on the same line.

    Prints WARN messages to stdout. Non-blocking (advisory only).
    """
    for i, line in enumerate(lines, start=1):
        for axiom in _AXIOM_NAMES:
            if axiom in line and "MANIFESTO.md §" not in line:
                print(f"WARN: bare axiom name without §-reference: line {i} in {filepath}")


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------


def validate(file_path: Path, min_lines: int) -> tuple[bool, list[str]]:
    """Validate *file_path*. Returns (passed, list_of_failure_messages)."""
    failures: list[str] = []

    if not file_path.exists():
        return False, [f"File not found: {file_path}"]
    if not file_path.is_file():
        return False, [f"Path is not a file: {file_path}"]

    text = file_path.read_text(encoding="utf-8")

    # Check 1: minimum non-blank line count
    actual_lines = non_blank_line_count(text)
    if actual_lines < min_lines:
        failures.append(f"Line count too low: {actual_lines} non-blank lines (minimum: {min_lines})")

    # Check 2: required section headings
    present_headings = extract_headings(text)
    present_set = set(present_headings)

    if is_d3(file_path):
        heading_text_lower = [h.lower() for h in present_headings]
        for section_name, keywords in D3_REQUIRED_SECTIONS:
            matched = any(kw in h for kw in keywords for h in heading_text_lower)
            if not matched:
                failures.append(
                    f"Missing required D3 section '{section_name}' (expected a heading matching one of: {keywords})"
                )
    else:
        for heading in D4_REQUIRED_HEADINGS:
            if heading not in present_set:
                keyword = heading.split(".", 1)[-1].strip()
                if not any(keyword.lower() in h.lower() for h in present_headings):
                    failures.append(f"Missing required section heading: '{heading}'")
        if len(present_headings) < D4_MIN_HEADING_COUNT:
            failures.append(
                f"D4 synthesis must have ≥ {D4_MIN_HEADING_COUNT} ## headings; found {len(present_headings)}"
            )

    # Check 3: required frontmatter fields
    fm = parse_frontmatter(text)
    if not fm:
        failures.append("No YAML frontmatter found (expected --- block at top of file)")
    else:
        if is_d3(file_path):
            for key in D3_REQUIRED_FRONTMATTER:
                if not fm.get(key):
                    failures.append(f"Missing or empty frontmatter field: '{key}'")
            if not any(fm.get(k) for k in D3_URL_KEYS):
                failures.append(f"Missing frontmatter URL field: one of {D3_URL_KEYS} must be present and non-empty")
        else:
            for key in D4_REQUIRED_FRONTMATTER:
                if not fm.get(key):
                    failures.append(f"Missing or empty frontmatter field: '{key}'")

    return len(failures) == 0, failures


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point for dogma-validate-synthesis CLI."""
    parser = argparse.ArgumentParser(
        description="Validate a D3/D4 synthesis document before archiving.",
        epilog="Exit 0 = pass. Exit 1 = one or more checks failed.",
    )
    parser.add_argument(
        "files",
        metavar="<file>",
        nargs="+",
        help="Path(s) to synthesis document(s) to validate.",
    )
    parser.add_argument(
        "--min-lines",
        type=int,
        default=80,
        metavar="N",
        help="Minimum non-blank line count (default: 80).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Reserved for future use — currently a no-op.",
    )
    parser.add_argument(
        "--allow-final-edit",
        action="store_true",
        help="Suppress the WARNING emitted when a Final- or Published-status doc is modified.",
    )
    args = parser.parse_args()

    overall_passed = True
    for file_arg in args.files:
        file_path = Path(file_arg)
        doc_type = "D3 (per-source)" if is_d3(file_path) else "D4 (issue synthesis)"

        print(f"validate_synthesis: {file_path}  [{doc_type}]")

        passed, failures = validate(file_path, args.min_lines)

        if not is_d3(file_path) and file_path.exists():
            check_axiom_citations(file_path.read_text(encoding="utf-8").splitlines(), str(file_path))
            check_final_status_modified(file_path, args.allow_final_edit)

        if passed:
            print("PASS — all checks passed.")
        else:
            print(f"FAIL — {len(failures)} check(s) failed:")
            for i, msg in enumerate(failures, 1):
                print(f"  {i}. {msg}")
            overall_passed = False

    sys.exit(0 if overall_passed else 1)


if __name__ == "__main__":
    main()
