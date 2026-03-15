"""Tests for scripts/amplify_context.py."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SCRIPT = Path(__file__).parent.parent / "scripts" / "amplify_context.py"


def run_script(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# Import-level tests (fast, no subprocess)
# ---------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from amplify_context import AMPLIFICATION_TABLE, find_match  # noqa: E402


def test_table_has_five_rows():
    assert len(AMPLIFICATION_TABLE) == 5


@pytest.mark.parametrize(
    "keyword,expected_amplify",
    [
        ("research", "Endogenous-First"),
        ("survey", "Endogenous-First"),
        ("scout", "Endogenous-First"),
        ("synthesize", "Endogenous-First"),
        ("commit", "Documentation-First"),
        ("push", "Documentation-First"),
        ("review", "Documentation-First"),
        ("merge", "Documentation-First"),
        ("pr", "Documentation-First"),
        ("script", "Programmatic-First"),
        ("automate", "Programmatic-First"),
        ("encode", "Programmatic-First"),
        ("ci", "Programmatic-First"),
        ("agent", "Endogenous-First + Minimal Posture"),
        ("skill", "Endogenous-First + Minimal Posture"),
        ("authoring", "Endogenous-First + Minimal Posture"),
        ("fleet", "Endogenous-First + Minimal Posture"),
        ("local", "Local Compute-First"),
        ("inference", "Local Compute-First"),
        ("model", "Local Compute-First"),
        ("cost", "Local Compute-First"),
    ],
)
def test_find_match_all_keywords(keyword: str, expected_amplify: str):
    result = find_match(keyword)
    assert result is not None, f"Expected match for keyword '{keyword}'"
    assert result["amplify"] == expected_amplify


def test_find_match_no_match():
    assert find_match("unknownxyz") is None


def test_find_match_case_insensitive():
    assert find_match("RESEARCH") is not None
    assert find_match("Research") is not None


# ---------------------------------------------------------------------------
# CLI exit-code tests (subprocess)
# ---------------------------------------------------------------------------


def test_keyword_research_exit_0():
    result = run_script("research")
    assert result.returncode == 0
    assert "Endogenous-First" in result.stdout


def test_keyword_commit_exit_0():
    result = run_script("commit")
    assert result.returncode == 0
    assert "Documentation-First" in result.stdout


def test_keyword_script_exit_0():
    result = run_script("script")
    assert result.returncode == 0
    assert "Programmatic-First" in result.stdout


def test_keyword_agent_exit_0():
    result = run_script("agent")
    assert result.returncode == 0
    assert "Endogenous-First" in result.stdout
    assert "Minimal Posture" in result.stdout


def test_keyword_local_exit_0():
    result = run_script("local")
    assert result.returncode == 0
    assert "Local Compute-First" in result.stdout


def test_no_match_exits_1():
    result = run_script("unknownxyz")
    assert result.returncode == 1


def test_no_match_prints_table_to_stderr():
    result = run_script("unknownxyz")
    assert "Endogenous-First" in result.stdout or "Endogenous-First" in result.stderr


def test_list_flag_exits_1():
    result = run_script("--list")
    assert result.returncode == 1


def test_list_flag_prints_all_rows():
    result = run_script("--list")
    assert "Endogenous-First" in result.stdout
    assert "Documentation-First" in result.stdout
    assert "Programmatic-First" in result.stdout
    assert "Local Compute-First" in result.stdout


def test_format_json_exit_0():
    result = run_script("research", "--format", "json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["amplify"] == "Endogenous-First"
    assert "expression_hint" in data


def test_format_json_no_match_exits_1():
    result = run_script("unknownxyz", "--format", "json")
    assert result.returncode == 1


def test_no_args_exits_2():
    result = run_script()
    assert result.returncode == 2


def test_invalid_format_exits_nonzero():
    result = run_script("research", "--format", "xml")
    assert result.returncode != 0
