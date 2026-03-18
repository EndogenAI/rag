"""dogma_governance.validate_agent

Programmatic encoding-fidelity gate for .agent.md files.

Purpose:
    Validate .agent.md role files for structural correctness and encoding fidelity:
    YAML frontmatter, required BDI section headings, cross-reference density,
    and several anti-pattern checks (heredoc writes, Fetch-before-check label,
    Phase N Review Output headings, Core Layer Impermeability).

Inputs:
    files   One or more .agent.md file paths (positional, required when not
            using --all / --skills).
    --all   Scan every *.agent.md in .github/agents/ AND every SKILL.md.
    --skills  Scan every SKILL.md in .github/skills/*/SKILL.md.
    --strict  Reserved for future use (no-op).

Outputs:
    stdout: per-file PASS/FAIL with specific gap list.

Exit codes:
    0  All checks passed.
    1  One or more checks failed.

Usage:
    dogma-validate-agent .github/agents/my-agent.agent.md
    dogma-validate-agent --all
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AGENTS_DIR = Path(".github/agents")
SKILLS_DIR = Path(".github/skills")

_SKILL_NAME_RE = re.compile(r"^[a-z][a-z0-9-]*[a-z0-9]$")
_CONSECUTIVE_HYPHENS_RE = re.compile(r"--")
SKILL_NAME_MAX_LEN = 64
SKILL_DESCRIPTION_MIN_LEN = 10
SKILL_DESCRIPTION_MAX_LEN = 1024
SKILL_BODY_MIN_LEN = 100

REQUIRED_FRONTMATTER: list[str] = ["name", "description"]

REQUIRED_SECTIONS: list[tuple[str, list[str]]] = [
    ("Beliefs & Context", ["beliefs", "context"]),
    (
        "Workflow & Intentions",
        ["workflow", "intentions", "checklist", "conventions", "playbook", "scope", "methodology"],
    ),
    ("Desired Outcomes & Acceptance", ["desired outcomes", "acceptance", "completion criteria", "guardrails"]),
]

_HEREDOC_NEGATIONS = frozenset(["never", "avoid", "don't", "dont", "do not", "wrong", "prohibited", "not use"])
_HEREDOC_PATTERN = re.compile(r"cat\s*>>?\s*\S+\s*<<\s*['\"]?EOF", re.IGNORECASE)
_CROSSREF_RE = re.compile(r"MANIFESTO\.md|AGENTS\.md")
_CITATION_RE = re.compile(r"\[([^\]]+)\]\(([^\)]+\.(md|yml)[^\)]*)\)|([A-Za-z_-]+\.(md|yml))\b")
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
_FETCH_BEFORE_CHECK_PATTERN = re.compile(r"fetch-before-check", re.IGNORECASE)
_FETCH_BEFORE_CHECK_NEGATIONS = frozenset(_HEREDOC_NEGATIONS | {"grep"})
_PHASE_N_REVIEW_RE = re.compile(r"^##\s+Phase\s+N\s+Review\s+Output", re.IGNORECASE | re.MULTILINE)
_MANIFESTO_SECTION_RE = re.compile(r"MANIFESTO\.md(?:#[a-zA-Z0-9\-_]+|\s+§\d)")
_MANIFESTO_BARE_RE = re.compile(r"MANIFESTO\.md(?!#|\s+§)")


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
        if ":" in line and not line.strip().startswith("-"):
            key, _, val = line.partition(":")
            v = val.strip()
            if len(v) >= 2 and v[0] in ('"', "'") and v[0] == v[-1]:
                v = v[1:-1]
            fm[key.strip()] = v
    return fm


def extract_headings(text: str) -> list[str]:
    """Return all Markdown H2 headings (## ...) from the document body."""
    body_start = 0
    fm_match = _FRONTMATTER_RE.match(text)
    if fm_match:
        body_start = fm_match.end()
    body = text[body_start:]
    return [line.rstrip() for line in body.splitlines() if line.startswith("## ")]


def _extract_body(text: str) -> str:
    """Return the document body after the frontmatter block."""
    fm_match = _FRONTMATTER_RE.match(text)
    return text[fm_match.end() :] if fm_match else text


def _get_frontmatter_value(text: str, key: str) -> str:
    """Return the full string value of *key* from YAML frontmatter (handles block scalars)."""
    fm_match = _FRONTMATTER_RE.match(text)
    if not fm_match:
        return ""
    lines = fm_match.group(1).splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith(f"{key}:"):
            continue
        after_colon = stripped[len(key) + 1 :].strip()
        if after_colon and after_colon not in ("|", "|-", "|+"):
            if len(after_colon) >= 2 and after_colon[0] in ('"', "'") and after_colon[0] == after_colon[-1]:
                return after_colon[1:-1]
            return after_colon
        if after_colon in ("|", "|-", "|+"):
            block: list[str] = []
            for nxt in lines[i + 1 :]:
                if nxt and not nxt[0].isspace():
                    break
                block.append(nxt.strip())
            return " ".join(filter(None, block)).strip()
    return ""


def extract_citations_from_section(text: str, section_keywords: list[str]) -> list[str]:
    """Extract .md/.yml file citations from the first heading section matching any keyword.

    Returns filenames in order of appearance.
    """
    citations: list[str] = []
    body_start = 0
    fm_match = _FRONTMATTER_RE.match(text)
    if fm_match:
        body_start = fm_match.end()

    body = text[body_start:]
    in_section = False
    section_content = []

    for line in body.splitlines():
        if re.match(r"^##\s+", line):
            if in_section:
                break
            line_lower = line.lower()
            if any(kw in line_lower for kw in section_keywords):
                in_section = True
                continue
        if in_section:
            section_content.append(line)

    section_text = "\n".join(section_content)
    for match in _CITATION_RE.finditer(section_text):
        cited_file = match.group(2) or match.group(4)
        if cited_file:
            cited_file = cited_file.split("/")[-1].split("#")[0]
            if cited_file:
                citations.append(cited_file)

    return citations


def check_citation_priority(citations: list[str]) -> list[str]:
    """Check that client-values.yml does not appear before MANIFESTO.md or AGENTS.md.

    Returns a list of error messages (empty = no violations).
    """
    errors: list[str] = []
    if "client-values.yml" not in citations:
        return []

    client_idx = citations.index("client-values.yml")
    manifesto_idx = citations.index("MANIFESTO.md") if "MANIFESTO.md" in citations else float("inf")
    agents_idx = citations.index("AGENTS.md") if "AGENTS.md" in citations else float("inf")
    max_core_idx = max(manifesto_idx, agents_idx)

    if client_idx < max_core_idx:
        errors.append(
            "Core Layer Impermeability violation: client-values.yml is cited before "
            "both MANIFESTO.md and AGENTS.md in Beliefs & Context (Deployment Layer "
            "values must be subordinate to Core Layer axioms; reorder citations)"
        )

    return errors


def manifesto_warnings(text: str) -> list[str]:
    """Return soft warnings for MANIFESTO.md citation specificity (non-blocking).

    Returns a list of warning strings; empty means no issues.
    """
    warnings: list[str] = []

    manifesto_refs = re.findall(r"MANIFESTO\.md", text)
    if manifesto_refs:
        distinct_anchored = set(_MANIFESTO_SECTION_RE.findall(text))
        if not distinct_anchored:
            warnings.append(
                "MANIFESTO specificity metric: MANIFESTO.md is cited but no section-anchored "
                "references found — add at least one MANIFESTO.md#section-name or MANIFESTO.md §N "
                "to maintain encoding fidelity (AGENTS.md cross-reference density guideline)"
            )

    for line in text.splitlines():
        if _MANIFESTO_BARE_RE.search(line):
            lower = line.lower()
            if not any(neg in lower for neg in _HEREDOC_NEGATIONS):
                warnings.append(
                    "Bare MANIFESTO.md citation found: citations should include a section anchor "
                    "(prefer MANIFESTO.md#section-name or MANIFESTO.md §N over bare MANIFESTO.md) "
                    "to maintain cross-reference specificity"
                )
                break

    return warnings


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------


def validate(file_path: Path) -> tuple[bool, list[str]]:
    """Validate a single .agent.md file. Returns (passed, list_of_failure_messages)."""
    failures: list[str] = []

    if not file_path.exists():
        return False, [f"File not found: {file_path}"]
    if not file_path.is_file():
        return False, [f"Path is not a file: {file_path}"]

    text = file_path.read_text(encoding="utf-8")

    # Check 1: YAML frontmatter
    fm = parse_frontmatter(text)
    if not fm:
        failures.append("No YAML frontmatter found (expected --- block at top of file)")
    else:
        for key in REQUIRED_FRONTMATTER:
            if not fm.get(key):
                failures.append(f"Missing or empty frontmatter field: '{key}'")

    # Check 2: required BDI sections
    headings_lower = [h.lower() for h in extract_headings(text)]
    for section_label, keywords in REQUIRED_SECTIONS:
        matched = any(kw in h for kw in keywords for h in headings_lower)
        if not matched:
            failures.append(
                f"Missing required section '{section_label}' (expected a heading matching one of: {keywords})"
            )

    # Check 3: cross-reference density
    if not _CROSSREF_RE.search(text):
        failures.append(
            "Cross-reference density too low: no back-reference to MANIFESTO.md or AGENTS.md found "
            "(add at least one link to maintain encoding fidelity)"
        )

    # Check 4: no heredoc file writes (negation-aware)
    for line in text.splitlines():
        if _HEREDOC_PATTERN.search(line):
            lower = line.lower()
            if not any(neg in lower for neg in _HEREDOC_NEGATIONS):
                failures.append(
                    "Heredoc file write detected (cat >> ... << 'EOF' pattern) outside a negation context — "
                    "use create_file / replace_string_in_file built-in tools instead "
                    "(heredocs silently corrupt Markdown containing backticks)"
                )
                break

    # Check 5: no Fetch-before-check label (negation-aware)
    for line in text.splitlines():
        if _FETCH_BEFORE_CHECK_PATTERN.search(line):
            lower = line.lower()
            if not any(neg in lower for neg in _FETCH_BEFORE_CHECK_NEGATIONS):
                failures.append(
                    "Guardrail label ordering error: 'Fetch-before-check' found — correct label is "
                    "'Check-before-fetch' (check cache first, then fetch only if absent)"
                )
                break

    # Check 6: no '## Phase N Review Output' heading
    if _PHASE_N_REVIEW_RE.search(text):
        failures.append(
            "Heading contract violation: '## Phase N Review Output' found — use '## Review Output' "
            "(defined in review.agent.md; do not restate with 'Phase N' prefix)"
        )

    # Check 7: Core Layer Impermeability (citation order in Beliefs & Context)
    citations = extract_citations_from_section(text, ["beliefs", "context"])
    failures.extend(check_citation_priority(citations))

    return len(failures) == 0, failures


def validate_skill_file(path: Path) -> list[str]:
    """Validate a SKILL.md file for encoding fidelity.

    Returns a list of error strings; empty = all checks passed.
    """
    errors: list[str] = []

    if not path.exists():
        return [f"File not found: {path}"]
    if not path.is_file():
        return [f"Path is not a file: {path}"]

    text = path.read_text(encoding="utf-8")

    fm = parse_frontmatter(text)
    if not fm:
        errors.append("No YAML frontmatter found (expected --- block at top of file)")
        return errors

    name_val = _get_frontmatter_value(text, "name")
    desc_val = _get_frontmatter_value(text, "description")

    if not name_val:
        errors.append("Missing or empty frontmatter field: 'name'")
    if not desc_val:
        errors.append("Missing or empty frontmatter field: 'description'")

    if name_val:
        if len(name_val) > SKILL_NAME_MAX_LEN:
            errors.append(f"Frontmatter 'name' exceeds {SKILL_NAME_MAX_LEN} characters (got {len(name_val)})")
        if not _SKILL_NAME_RE.match(name_val):
            errors.append(
                f"Frontmatter 'name' must match ^[a-z][a-z0-9-]*[a-z0-9]$ "
                f"(lowercase kebab-case, no leading/trailing hyphens): {name_val!r}"
            )
        elif _CONSECUTIVE_HYPHENS_RE.search(name_val):
            errors.append(f"Frontmatter 'name' must not contain consecutive hyphens: {name_val!r}")

        parent_dir = path.parent.name
        if name_val != parent_dir:
            errors.append(f"Frontmatter 'name' ({name_val!r}) must match the parent directory name ({parent_dir!r})")

    if desc_val:
        desc_len = len(desc_val)
        if desc_len < SKILL_DESCRIPTION_MIN_LEN:
            errors.append(
                f"Frontmatter 'description' is too short ({desc_len} chars, minimum {SKILL_DESCRIPTION_MIN_LEN})"
            )
        if desc_len > SKILL_DESCRIPTION_MAX_LEN:
            errors.append(
                f"Frontmatter 'description' is too long ({desc_len} chars, maximum {SKILL_DESCRIPTION_MAX_LEN})"
            )

    body = _extract_body(text)
    if not _CROSSREF_RE.search(body):
        errors.append(
            "Cross-reference density too low: no back-reference to MANIFESTO.md or AGENTS.md "
            "found in body (add at least one link to maintain encoding fidelity)"
        )

    body_stripped = body.strip()
    if len(body_stripped) < SKILL_BODY_MIN_LEN:
        errors.append(f"Body is too short ({len(body_stripped)} chars after frontmatter, minimum {SKILL_BODY_MIN_LEN})")

    if _PHASE_N_REVIEW_RE.search(text):
        errors.append(
            "Heading contract violation: '## Phase N Review Output' found — use '## Review Output' "
            "(defined in review.agent.md; do not restate with 'Phase N' prefix)"
        )

    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point for dogma-validate-agent CLI."""
    parser = argparse.ArgumentParser(
        description="Validate agent and skill files for encoding fidelity.",
        epilog="Exit 0 = all pass. Exit 1 = one or more checks failed.",
    )
    parser.add_argument(
        "files",
        nargs="*",
        metavar="file",
        help="One or more .agent.md or SKILL.md files to validate.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="scan_all",
        help="Scan every *.agent.md in .github/agents/ AND every SKILL.md.",
    )
    parser.add_argument(
        "--skills",
        action="store_true",
        dest="scan_skills",
        help="Scan every SKILL.md in .github/skills/*/SKILL.md.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Reserved for future use.",
    )
    args = parser.parse_args()

    agent_targets: list[Path] = []
    skill_targets: list[Path] = []

    if args.scan_all:
        agent_targets = sorted(AGENTS_DIR.glob("*.agent.md"))
        skill_targets = sorted(SKILLS_DIR.glob("*/SKILL.md"))
    elif args.scan_skills:
        skill_targets = sorted(SKILLS_DIR.glob("*/SKILL.md"))
    elif args.files:
        for f in args.files:
            p = Path(f)
            if p.name == "SKILL.md":
                skill_targets.append(p)
            else:
                agent_targets.append(p)
    else:
        parser.print_help()
        sys.exit(0)

    total = len(agent_targets) + len(skill_targets)
    if total == 0:
        print("No files found — nothing to validate.")
        sys.exit(0)

    overall_pass = True
    failed_count = 0

    for file_path in agent_targets:
        passed, failures = validate(file_path)
        if passed:
            print(f"PASS  {file_path}")
        else:
            overall_pass = False
            failed_count += 1
            print(f"FAIL  {file_path}")
            for msg in failures:
                print(f"      • {msg}")
        if file_path.exists():
            for w in manifesto_warnings(file_path.read_text(encoding="utf-8")):
                print(f"      ⚠ {w}")

    for file_path in skill_targets:
        errors = validate_skill_file(file_path)
        if not errors:
            print(f"PASS  {file_path}")
        else:
            overall_pass = False
            failed_count += 1
            print(f"FAIL  {file_path}")
            for msg in errors:
                print(f"      • {msg}")

    print()
    if overall_pass:
        print(f"All {total} file(s) passed.")
    else:
        print(f"{failed_count} of {total} file(s) failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
