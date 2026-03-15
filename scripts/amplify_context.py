"""amplify_context.py — Context-Sensitive Axiom Amplification.

Purpose:
    Programmatic encoding of the Context-Sensitive Amplification lookup table
    from AGENTS.md. Given a task-type keyword, returns the amplified axiom
    name and expression hint for the session encoding checkpoint.

Inputs:
    Positional argument: task-type keyword (e.g. "research", "commit", "script")
    OR --list to print the full table.

Outputs:
    Matched row printed to stdout (text or JSON).
    Non-zero exit on no match or --list.

Usage:
    uv run python scripts/amplify_context.py research
    uv run python scripts/amplify_context.py commit --format json
    uv run python scripts/amplify_context.py --list

Exit codes:
    0 = keyword matched, result printed
    1 = no match (all rows printed as reference) or --list flag used
    2 = invalid arguments
"""

import argparse
import json
import sys

# ---------------------------------------------------------------------------
# Amplification table — hardcoded from AGENTS.md § Context-Sensitive Amplification
# ---------------------------------------------------------------------------

AMPLIFICATION_TABLE: list[dict[str, str]] = [
    {
        "keywords": "research|survey|scout|synthesize",
        "keyword_list": ["research", "survey", "scout", "synthesize"],
        "amplify": "Endogenous-First",
        "expression_hint": "Read prior docs and cached sources before reaching outward",
    },
    {
        "keywords": "commit|push|review|merge|pr",
        "keyword_list": ["commit", "push", "review", "merge", "pr"],
        "amplify": "Documentation-First",
        "expression_hint": "Every changed workflow/agent/script must have accompanying docs",
    },
    {
        "keywords": "script|automate|encode|ci",
        "keyword_list": ["script", "automate", "encode", "ci"],
        "amplify": "Programmatic-First",
        "expression_hint": "If done twice interactively → encode as script before third time",
    },
    {
        "keywords": "agent|skill|authoring|fleet",
        "keyword_list": ["agent", "skill", "authoring", "fleet"],
        "amplify": "Endogenous-First + Minimal Posture",
        "expression_hint": "Read existing fleet before spawning; carry only required tools",
    },
    {
        "keywords": "local|inference|model|cost",
        "keyword_list": ["local", "inference", "model", "cost"],
        "amplify": "Local Compute-First",
        "expression_hint": "Prefer local model invocation; document when external API is required",
    },
]


def find_match(keyword: str) -> dict[str, str] | None:
    """Return the first matching row for the given keyword (case-insensitive)."""
    kw = keyword.strip().lower()
    for row in AMPLIFICATION_TABLE:
        if kw in row["keyword_list"]:
            return row
    return None


def format_row_text(row: dict[str, str]) -> str:
    return f"Amplified principle: {row['amplify']}\nExpression hint:     {row['expression_hint']}"


def format_row_json(row: dict[str, str]) -> str:
    return json.dumps({"amplify": row["amplify"], "expression_hint": row["expression_hint"]}, indent=2)


def print_table() -> None:
    """Print the full amplification table as a reference."""
    print("Context-Sensitive Amplification Table (from AGENTS.md)\n")
    header = f"{'Keyword(s)':<30} {'Amplified Principle':<35} Expression Hint"
    print(header)
    print("-" * len(header))
    for row in AMPLIFICATION_TABLE:
        keywords_display = "|".join(row["keyword_list"])
        print(f"{keywords_display:<30} {row['amplify']:<35} {row['expression_hint']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Return the amplified axiom for a given task-type keyword.",
        epilog="Source: AGENTS.md § Context-Sensitive Amplification",
    )
    parser.add_argument(
        "keyword",
        nargs="?",
        default=None,
        help="Task-type keyword (research, commit, script, agent, local, …)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print the full amplification table and exit 1.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )

    args = parser.parse_args()

    if args.list:
        print_table()
        sys.exit(1)

    if args.keyword is None:
        parser.print_help()
        sys.exit(2)

    match = find_match(args.keyword)
    if match is None:
        print(
            f"No match for keyword '{args.keyword}'. Valid keywords are shown in the table below.\n",
            file=sys.stderr,
        )
        print_table()
        sys.exit(1)

    if args.format == "json":
        print(format_row_json(match))
    else:
        print(format_row_text(match))

    sys.exit(0)


if __name__ == "__main__":
    main()
