"""tests/test_governance_package.py

Tests for all four dogma_governance modules:
  - validate_agent (validate_agent.py)
  - validate_synthesis (validate_synthesis.py)
  - detect_drift (detect_drift.py)
  - check_health (check_health.py)

Uses tmp_path (pytest built-in) for all temp file creation.
Uses mocker.patch() from pytest-mock for sys.exit assertions.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from dogma_governance import check_health, detect_drift, validate_agent, validate_synthesis

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

MINIMAL_VALID_AGENT = """\
---
name: test-agent
description: A test agent for unit tests
---

## Beliefs & Context

This agent reads [MANIFESTO.md](MANIFESTO.md#1-endogenous-first) and [AGENTS.md](AGENTS.md) first.

## Workflow & Intentions

1. Read context
2. Perform task

## Desired Outcomes & Acceptance

- All checks pass
"""

MINIMAL_VALID_D4 = """\
---
title: Test Synthesis Document
status: Draft
---

## 1. Executive Summary

Summary here.

## 2. Hypothesis Validation

Validation here.

## 3. Pattern Catalog

Patterns here.

## 4. Recommendations

Recommendations here.

## 5. Sources

Sources here.

## 6. Project Relevance

Relevance here.

## 7. Open Questions

Questions here.

## 8. Appendix

Appendix here.

""" + "\n".join([f"Line {i}" for i in range(80)])


MINIMAL_VALID_D3 = """\
---
slug: test-source
title: Test Source Title
cache_path: .cache/sources/test-source.md
url: https://example.com/test
---

## Citation

Some citation here.

## Research Question

What is the research question?

## Theoretical Framework

The theoretical framework.

## Methodology

The methodology used.

## Key Claims

The key claims.

## Critical Assessment

Critical assessment.

## Cross-Source Connections

Cross-source connections.

## Project Relevance

Project relevance to EndogenAI.

""" + "\n".join([f"Line {i}" for i in range(80)])


# ---------------------------------------------------------------------------
# validate_agent tests
# ---------------------------------------------------------------------------


class TestValidateAgent:
    """Tests for dogma_governance.validate_agent."""

    def test_valid_agent_passes(self, tmp_path: Path) -> None:
        """A well-formed agent file should pass all checks."""
        agent_file = tmp_path / "good.agent.md"
        agent_file.write_text(MINIMAL_VALID_AGENT, encoding="utf-8")
        passed, failures = validate_agent.validate(agent_file)
        assert passed is True
        assert failures == []

    def test_missing_name_fails(self, tmp_path: Path) -> None:
        """Agent file with no 'name' frontmatter field must fail."""
        content = MINIMAL_VALID_AGENT.replace("name: test-agent\n", "")
        agent_file = tmp_path / "no-name.agent.md"
        agent_file.write_text(content, encoding="utf-8")
        passed, failures = validate_agent.validate(agent_file)
        assert passed is False
        assert any("name" in f for f in failures)

    def test_missing_sections_fails(self, tmp_path: Path) -> None:
        """Agent file missing required BDI sections must fail."""
        content = """\
---
name: minimal-agent
description: Missing sections
---

Some content with AGENTS.md reference.
"""
        agent_file = tmp_path / "missing-sections.agent.md"
        agent_file.write_text(content, encoding="utf-8")
        passed, failures = validate_agent.validate(agent_file)
        assert passed is False
        # Should flag multiple missing sections
        assert len(failures) >= 2

    def test_heredoc_pattern_triggers_error(self, tmp_path: Path) -> None:
        """Agent file containing a heredoc write pattern must fail."""
        content = MINIMAL_VALID_AGENT + "\n```\ncat >> /tmp/out << EOF\nsome content\nEOF\n```\n"
        agent_file = tmp_path / "heredoc.agent.md"
        agent_file.write_text(content, encoding="utf-8")
        passed, failures = validate_agent.validate(agent_file)
        assert passed is False
        assert any("heredoc" in f.lower() or "cat >>" in f.lower() for f in failures)

    def test_heredoc_in_negation_context_passes(self, tmp_path: Path) -> None:
        """Heredoc mention in a 'never use' guardrail line should NOT trigger a failure."""
        content = MINIMAL_VALID_AGENT + "\nNEVER use cat >> file << EOF for writing.\n"
        agent_file = tmp_path / "negated-heredoc.agent.md"
        agent_file.write_text(content, encoding="utf-8")
        passed, failures = validate_agent.validate(agent_file)
        assert passed is True

    def test_fetch_before_check_label_triggers_error(self, tmp_path: Path) -> None:
        """Agent file with 'Fetch-before-check' (wrong label) must fail."""
        content = MINIMAL_VALID_AGENT + "\nUse the Fetch-before-check pattern.\n"
        agent_file = tmp_path / "fbc.agent.md"
        agent_file.write_text(content, encoding="utf-8")
        passed, failures = validate_agent.validate(agent_file)
        assert passed is False
        assert any("fetch-before-check" in f.lower() or "check-before-fetch" in f.lower() for f in failures)

    def test_missing_crossref_fails(self, tmp_path: Path) -> None:
        """Agent file with no MANIFESTO.md or AGENTS.md reference must fail."""
        content = """\
---
name: no-refs
description: No cross-references
---

## Beliefs & Context

Context without references.

## Workflow & Intentions

Work here.

## Desired Outcomes & Acceptance

Done.
"""
        agent_file = tmp_path / "no-refs.agent.md"
        agent_file.write_text(content, encoding="utf-8")
        passed, failures = validate_agent.validate(agent_file)
        assert passed is False
        assert any("cross-reference" in f.lower() for f in failures)

    def test_file_not_found_returns_failure(self, tmp_path: Path) -> None:
        """Passing a non-existent path must return (False, [error])."""
        passed, failures = validate_agent.validate(tmp_path / "ghost.agent.md")
        assert passed is False
        assert len(failures) == 1
        assert "not found" in failures[0].lower()


class TestValidateAgentMain:
    """Tests for validate_agent.main() exit codes."""

    def test_main_exits_0_on_valid_file(self, tmp_path: Path, mocker) -> None:
        """main() should call sys.exit(0) or not call sys.exit at all when all pass."""
        agent_file = tmp_path / "good.agent.md"
        agent_file.write_text(MINIMAL_VALID_AGENT, encoding="utf-8")
        mock_exit = mocker.patch("sys.exit")
        mocker.patch("sys.argv", ["dogma-validate-agent", str(agent_file)])
        validate_agent.main()
        # Should exit 0 (or complete without calling sys.exit(1))
        for call in mock_exit.call_args_list:
            assert call.args[0] != 1

    def test_main_exits_1_on_invalid_file(self, tmp_path: Path, mocker) -> None:
        """main() must call sys.exit(1) when a file fails."""
        bad_file = tmp_path / "bad.agent.md"
        bad_file.write_text("no frontmatter at all\n", encoding="utf-8")
        mock_exit = mocker.patch("sys.exit")
        mocker.patch("sys.argv", ["dogma-validate-agent", str(bad_file)])
        validate_agent.main()
        assert any(call.args[0] == 1 for call in mock_exit.call_args_list)


# ---------------------------------------------------------------------------
# validate_synthesis tests
# ---------------------------------------------------------------------------


class TestValidateSynthesis:
    """Tests for dogma_governance.validate_synthesis."""

    def test_valid_d4_passes(self, tmp_path: Path) -> None:
        """A well-formed D4 synthesis document should pass."""
        doc = tmp_path / "my-topic.md"
        doc.write_text(MINIMAL_VALID_D4, encoding="utf-8")
        passed, failures = validate_synthesis.validate(doc, min_lines=80)
        assert passed is True
        assert failures == []

    def test_missing_headings_fails(self, tmp_path: Path) -> None:
        """D4 doc missing required headings must fail."""
        content = """\
---
title: Incomplete
status: Draft
---

## 1. Executive Summary

Only one heading.

""" + "\n".join([f"Line {i}" for i in range(80)])
        doc = tmp_path / "incomplete.md"
        doc.write_text(content, encoding="utf-8")
        passed, failures = validate_synthesis.validate(doc, min_lines=80)
        assert passed is False
        assert any("heading" in f.lower() or "section" in f.lower() for f in failures)

    def test_missing_frontmatter_fails(self, tmp_path: Path) -> None:
        """D4 doc with no frontmatter must fail."""
        content = "## 1. Executive Summary\n\nSome content.\n" * 10
        doc = tmp_path / "no-fm.md"
        doc.write_text(content, encoding="utf-8")
        passed, failures = validate_synthesis.validate(doc, min_lines=80)
        assert passed is False
        assert any("frontmatter" in f.lower() for f in failures)

    def test_missing_title_frontmatter_fails(self, tmp_path: Path) -> None:
        """D4 doc missing 'title' in frontmatter must fail."""
        content = MINIMAL_VALID_D4.replace("title: Test Synthesis Document\n", "")
        doc = tmp_path / "no-title.md"
        doc.write_text(content, encoding="utf-8")
        passed, failures = validate_synthesis.validate(doc, min_lines=80)
        assert passed is False
        assert any("title" in f for f in failures)

    def test_valid_d3_passes(self, tmp_path: Path) -> None:
        """A well-formed D3 per-source synthesis should pass."""
        sources_dir = tmp_path / "sources"
        sources_dir.mkdir()
        doc = sources_dir / "my-source.md"
        doc.write_text(MINIMAL_VALID_D3, encoding="utf-8")
        passed, failures = validate_synthesis.validate(doc, min_lines=80)
        assert passed is True, failures

    def test_d3_missing_section_fails(self, tmp_path: Path) -> None:
        """D3 doc missing a required section must fail."""
        content = MINIMAL_VALID_D3.replace("## Citation\n\nSome citation here.\n", "")
        sources_dir = tmp_path / "sources"
        sources_dir.mkdir()
        doc = sources_dir / "missing.md"
        doc.write_text(content, encoding="utf-8")
        passed, failures = validate_synthesis.validate(doc, min_lines=80)
        assert passed is False
        assert any("citation" in f.lower() for f in failures)

    def test_low_line_count_fails(self, tmp_path: Path) -> None:
        """D4 doc with fewer non-blank lines than minimum must fail."""
        content = """\
---
title: Short
status: Draft
---

## 1. Executive Summary

Too short.
"""
        doc = tmp_path / "short.md"
        doc.write_text(content, encoding="utf-8")
        passed, failures = validate_synthesis.validate(doc, min_lines=80)
        assert passed is False
        assert any("line count" in f.lower() for f in failures)


class TestValidateSynthesisMain:
    """Tests for validate_synthesis.main() exit codes."""

    def test_main_exits_0_on_valid_doc(self, tmp_path: Path, mocker) -> None:
        """main() should not exit with code 1 when synthesis passes."""
        doc = tmp_path / "valid.md"
        doc.write_text(MINIMAL_VALID_D4, encoding="utf-8")
        mock_exit = mocker.patch("sys.exit")
        mocker.patch("sys.argv", ["dogma-validate-synthesis", str(doc)])
        validate_synthesis.main()
        for call in mock_exit.call_args_list:
            assert call.args[0] != 1

    def test_main_exits_1_on_invalid_doc(self, tmp_path: Path, mocker) -> None:
        """main() must call sys.exit(1) when syntax fails."""
        doc = tmp_path / "bad.md"
        doc.write_text("no frontmatter\n", encoding="utf-8")
        mock_exit = mocker.patch("sys.exit")
        mocker.patch("sys.argv", ["dogma-validate-synthesis", str(doc)])
        validate_synthesis.main()
        assert any(call.args[0] == 1 for call in mock_exit.call_args_list)


# ---------------------------------------------------------------------------
# detect_drift tests
# ---------------------------------------------------------------------------


AGENT_ALL_WATERMARKS = """\
---
name: full-agent
description: Agent with all watermarks
---

## Beliefs & Context

Governs: Endogenous-First — read from AGENTS.md before acting.
Algorithms Before Tokens: prefer deterministic solutions.
Local Compute-First: minimize token usage.
encode-before-act before any external call.
morphogenetic seed idea.
programmatic-first principle in action.

## Workflow & Intentions

Do things.

## Desired Outcomes & Acceptance

Done.
"""

AGENT_NO_WATERMARKS = """\
---
name: empty-agent
description: Agent with no watermarks at all
---

## Beliefs & Context

No references here.

## Workflow & Intentions

Work.

## Desired Outcomes & Acceptance

Done.
"""


class TestDetectDrift:
    """Tests for dogma_governance.detect_drift."""

    def test_all_watermarks_scores_1(self, tmp_path: Path) -> None:
        """Agent file containing all watermark phrases should score 1.0."""
        agent_file = tmp_path / "full.agent.md"
        agent_file.write_text(AGENT_ALL_WATERMARKS, encoding="utf-8")
        result = detect_drift.score_agent_file(agent_file)
        assert result["drift_score"] == 1.0
        assert result["missing"] == []

    def test_no_watermarks_scores_0(self, tmp_path: Path) -> None:
        """Agent file with no watermark phrases should score 0.0."""
        agent_file = tmp_path / "empty.agent.md"
        agent_file.write_text(AGENT_NO_WATERMARKS, encoding="utf-8")
        result = detect_drift.score_agent_file(agent_file)
        assert result["drift_score"] == 0.0
        assert set(result["missing"]) == set(detect_drift.WATERMARK_PHRASES)

    def test_fleet_analysis_aggregates(self, tmp_path: Path) -> None:
        """build_report should aggregate fleet_avg from multiple results."""
        full = tmp_path / "full.agent.md"
        full.write_text(AGENT_ALL_WATERMARKS, encoding="utf-8")
        empty = tmp_path / "empty.agent.md"
        empty.write_text(AGENT_NO_WATERMARKS, encoding="utf-8")

        results = [
            detect_drift.score_agent_file(full),
            detect_drift.score_agent_file(empty),
        ]
        report = detect_drift.build_report(results, threshold=0.33)

        assert report["fleet_avg"] == pytest.approx(0.5, abs=0.01)
        assert len(report["below_threshold"]) == 1
        assert str(empty) in report["below_threshold"][0]

    def test_format_summary_renders(self, tmp_path: Path) -> None:
        """format_summary should include score and file name."""
        result = {"drift_score": 0.5, "file": "my.agent.md", "missing": ["morphogenetic seed"]}
        report = {"agents": [result], "fleet_avg": 0.5, "below_threshold": []}
        summary = detect_drift.format_summary(report, threshold=0.33)
        assert "my.agent.md" in summary
        assert "0.50" in summary


class TestDetectDriftMain:
    """Tests for detect_drift.main() exit codes."""

    def test_main_exits_0_no_fail_below(self, tmp_path: Path, mocker) -> None:
        """main() without --fail-below should exit 0 regardless of scores."""
        agent_file = tmp_path / "empty.agent.md"
        agent_file.write_text(AGENT_NO_WATERMARKS, encoding="utf-8")
        mocker.patch("sys.argv", ["dogma-detect-drift", "--agents-dir", str(tmp_path)])
        result = detect_drift.main()
        assert result == 0

    def test_main_exits_1_when_fail_below_triggered(self, tmp_path: Path, mocker) -> None:
        """main() with --fail-below 0.5 should return 1 when agents score below that."""
        agent_file = tmp_path / "empty.agent.md"
        agent_file.write_text(AGENT_NO_WATERMARKS, encoding="utf-8")
        mocker.patch(
            "sys.argv",
            ["dogma-detect-drift", "--agents-dir", str(tmp_path), "--fail-below", "0.5"],
        )
        result = detect_drift.main()
        assert result == 1


# ---------------------------------------------------------------------------
# check_health tests
# ---------------------------------------------------------------------------


class TestCheckHealth:
    """Tests for dogma_governance.check_health."""

    def test_no_files_found_returns_zero_counts(self, tmp_path: Path) -> None:
        """Scanning a directory with no agent/synthesis files should return zeros."""
        report = check_health.run_health_check(tmp_path)
        assert report["total"] == 0
        assert report["passed"] == 0
        assert report["failed"] == 0
        assert report["failures"] == []

    def test_valid_agent_file_counted_as_pass(self, tmp_path: Path) -> None:
        """A valid agent file should increment passed count."""
        agents_dir = tmp_path / ".github" / "agents"
        agents_dir.mkdir(parents=True)
        agent_file = agents_dir / "test.agent.md"
        agent_file.write_text(MINIMAL_VALID_AGENT, encoding="utf-8")

        report = check_health.run_health_check(tmp_path)
        assert report["total"] == 1
        assert report["passed"] == 1
        assert report["failed"] == 0

    def test_invalid_agent_file_counted_as_fail(self, tmp_path: Path) -> None:
        """An invalid agent file should increment failed count."""
        agents_dir = tmp_path / ".github" / "agents"
        agents_dir.mkdir(parents=True)
        agent_file = agents_dir / "bad.agent.md"
        agent_file.write_text("no frontmatter\n", encoding="utf-8")

        report = check_health.run_health_check(tmp_path)
        assert report["failed"] == 1
        assert len(report["failures"]) == 1

    def test_mixed_files_correct_counts(self, tmp_path: Path) -> None:
        """Mixed pass/fail files should produce correct total/passed/failed counts."""
        agents_dir = tmp_path / ".github" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "good.agent.md").write_text(MINIMAL_VALID_AGENT, encoding="utf-8")
        (agents_dir / "bad.agent.md").write_text("broken\n", encoding="utf-8")

        report = check_health.run_health_check(tmp_path)
        assert report["total"] == 2
        assert report["passed"] == 1
        assert report["failed"] == 1

    def test_readme_excluded_from_synthesis_scan(self, tmp_path: Path) -> None:
        """README.md in docs/research/ should be excluded from synthesis scan."""
        research_dir = tmp_path / "docs" / "research"
        research_dir.mkdir(parents=True)
        (research_dir / "README.md").write_text("# readme\n", encoding="utf-8")

        report = check_health.run_health_check(tmp_path)
        assert report["total"] == 0


class TestCheckHealthMain:
    """Tests for check_health.main() exit codes."""

    def test_main_exits_0_when_no_files(self, tmp_path: Path, mocker) -> None:
        """main() with no files found should exit 0."""
        mock_exit = mocker.patch("sys.exit")
        mocker.patch("sys.argv", ["dogma-check-health", "--directory", str(tmp_path)])
        check_health.main()
        for call in mock_exit.call_args_list:
            assert call.args[0] != 1

    def test_main_exits_1_on_failures(self, tmp_path: Path, mocker) -> None:
        """main() must call sys.exit(1) when health check finds failures."""
        agents_dir = tmp_path / ".github" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "bad.agent.md").write_text("broken\n", encoding="utf-8")
        mock_exit = mocker.patch("sys.exit")
        mocker.patch("sys.argv", ["dogma-check-health", "--directory", str(tmp_path)])
        check_health.main()
        assert any(call.args[0] == 1 for call in mock_exit.call_args_list)

    def test_main_json_format(self, tmp_path: Path, mocker, capsys) -> None:
        """main() with --format json should emit JSON to stdout."""
        mocker.patch("sys.exit")
        mocker.patch("sys.argv", ["dogma-check-health", "--directory", str(tmp_path), "--format", "json"])
        check_health.main()
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "total" in data

    def test_synthesis_files_included_in_health_check(self, tmp_path: Path) -> None:
        """Synthesis docs under docs/research/ should be scanned (excluding README.md)."""
        research_dir = tmp_path / "docs" / "research"
        research_dir.mkdir(parents=True)
        (research_dir / "README.md").write_text("# readme\n", encoding="utf-8")
        (research_dir / "bad-doc.md").write_text("no frontmatter\n", encoding="utf-8")

        report = check_health.run_health_check(tmp_path)
        assert report["total"] == 1
        assert report["failed"] == 1


# ---------------------------------------------------------------------------
# Additional validate_agent tests (skill files + citation order)
# ---------------------------------------------------------------------------


MINIMAL_VALID_SKILL = """\
---
name: my-skill
description: A minimal valid skill for testing purposes in this suite
---

## Overview

This skill governs the following. See [AGENTS.md](AGENTS.md) for governing constraints.

Detailed enough body content to exceed the 100-character minimum body size requirement.
Additional lines to ensure we definitely pass the body length check.
"""


class TestValidateSkillFile:
    """Tests for validate_agent.validate_skill_file()."""

    def test_valid_skill_passes(self, tmp_path: Path) -> None:
        """A well-formed SKILL.md should pass all checks."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(MINIMAL_VALID_SKILL, encoding="utf-8")
        errors = validate_agent.validate_skill_file(skill_file)
        assert errors == []

    def test_skill_missing_name_fails(self, tmp_path: Path) -> None:
        """SKILL.md with missing 'name' must fail."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        content = MINIMAL_VALID_SKILL.replace("name: my-skill\n", "")
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(content, encoding="utf-8")
        errors = validate_agent.validate_skill_file(skill_file)
        assert any("name" in e for e in errors)

    def test_skill_name_mismatch_fails(self, tmp_path: Path) -> None:
        """SKILL.md whose name doesn't match parent dir must fail."""
        skill_dir = tmp_path / "other-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(MINIMAL_VALID_SKILL, encoding="utf-8")  # name: my-skill != other-skill
        errors = validate_agent.validate_skill_file(skill_file)
        assert any("parent directory" in e for e in errors)

    def test_skill_no_crossref_fails(self, tmp_path: Path) -> None:
        """SKILL.md body without AGENTS.md or MANIFESTO.md reference must fail."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        content = MINIMAL_VALID_SKILL.replace("[AGENTS.md](AGENTS.md)", "nothing here")
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(content, encoding="utf-8")
        errors = validate_agent.validate_skill_file(skill_file)
        assert any("cross-reference" in e.lower() for e in errors)

    def test_skill_body_too_short_fails(self, tmp_path: Path) -> None:
        """SKILL.md with a very short body must fail."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        content = "---\nname: my-skill\ndescription: A minimal valid skill\n---\n\nSee AGENTS.md.\n"
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(content, encoding="utf-8")
        errors = validate_agent.validate_skill_file(skill_file)
        assert any("too short" in e or "body" in e.lower() for e in errors)

    def test_skill_file_not_found(self, tmp_path: Path) -> None:
        """Passing a non-existent SKILL.md path must return errors."""
        errors = validate_agent.validate_skill_file(tmp_path / "ghost" / "SKILL.md")
        assert len(errors) == 1
        assert "not found" in errors[0].lower()


class TestCitationPriority:
    """Tests for validate_agent.check_citation_priority()."""

    def test_client_values_before_manifesto_fails(self) -> None:
        """client-values.yml before MANIFESTO.md is a Core Layer Impermeability violation."""
        citations = ["client-values.yml", "MANIFESTO.md", "AGENTS.md"]
        errors = validate_agent.check_citation_priority(citations)
        assert len(errors) == 1
        assert "impermeability" in errors[0].lower()

    def test_client_values_after_manifesto_passes(self) -> None:
        """client-values.yml after MANIFESTO.md and AGENTS.md is fine."""
        citations = ["MANIFESTO.md", "AGENTS.md", "client-values.yml"]
        errors = validate_agent.check_citation_priority(citations)
        assert errors == []

    def test_no_client_values_passes(self) -> None:
        """Citations without client-values.yml should always pass."""
        errors = validate_agent.check_citation_priority(["MANIFESTO.md", "AGENTS.md"])
        assert errors == []


class TestManifestoWarnings:
    """Tests for validate_agent.manifesto_warnings()."""

    def test_anchored_manifesto_no_warning(self) -> None:
        """Anchored MANIFESTO.md#section reference should produce no warnings."""
        text = "See [MANIFESTO.md#endogenous-first](MANIFESTO.md#endogenous-first) for details.\n"
        warnings = validate_agent.manifesto_warnings(text)
        assert warnings == []

    def test_bare_manifesto_warns(self) -> None:
        """Bare MANIFESTO.md reference without anchor should produce a warning."""
        text = "Read MANIFESTO.md for the axioms.\n"
        warnings = validate_agent.manifesto_warnings(text)
        assert len(warnings) >= 1

    def test_no_manifesto_reference_no_warnings(self) -> None:
        """Text with no MANIFESTO.md mention should produce no warnings."""
        text = "This file has no manifesto reference at all.\n"
        warnings = validate_agent.manifesto_warnings(text)
        assert warnings == []


# ---------------------------------------------------------------------------
# Additional detect_drift tests (file output, summary format)
# ---------------------------------------------------------------------------


class TestDetectDriftExtra:
    """Additional detect_drift tests for file output and edge cases."""

    def test_main_writes_json_to_output_file(self, tmp_path: Path, mocker) -> None:
        """main() with --output should write JSON to the named file."""
        agent_file = tmp_path / "agent.agent.md"
        agent_file.write_text(AGENT_ALL_WATERMARKS, encoding="utf-8")
        out_file = tmp_path / "report.json"
        mocker.patch(
            "sys.argv",
            ["dogma-detect-drift", "--agents-dir", str(tmp_path), "--output", str(out_file)],
        )
        detect_drift.main()
        assert out_file.exists()
        data = json.loads(out_file.read_text())
        assert "agents" in data

    def test_main_summary_format_prints(self, tmp_path: Path, mocker, capsys) -> None:
        """main() with --format summary should print human-readable output."""
        agent_file = tmp_path / "agent.agent.md"
        agent_file.write_text(AGENT_ALL_WATERMARKS, encoding="utf-8")
        mocker.patch(
            "sys.argv",
            ["dogma-detect-drift", "--agents-dir", str(tmp_path), "--format", "summary"],
        )
        detect_drift.main()
        captured = capsys.readouterr()
        assert "Fleet average" in captured.out

    def test_empty_agents_dir_returns_0(self, tmp_path: Path, mocker) -> None:
        """main() with an empty agents dir should return 0 (no agents = no failure)."""
        empty_dir = tmp_path / "agents"
        empty_dir.mkdir()
        mocker.patch("sys.argv", ["dogma-detect-drift", "--agents-dir", str(empty_dir)])
        result = detect_drift.main()
        assert result == 0

    def test_invalid_agents_dir_returns_1(self, tmp_path: Path, mocker) -> None:
        """main() with a non-existent agents dir should return 1."""
        mocker.patch(
            "sys.argv",
            ["dogma-detect-drift", "--agents-dir", str(tmp_path / "nonexistent")],
        )
        result = detect_drift.main()
        assert result == 1
