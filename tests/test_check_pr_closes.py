#!/usr/bin/env python3
"""Test suite for scripts/check_pr_closes.py."""

import sys
from pathlib import Path

# Add scripts/ to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from check_pr_closes import extract_auto_close_lines, main


class TestExtractAutoCloseLines:
    """Test extraction of close syntax lines from PR body text."""

    def test_extracts_closes_line(self):
        body = "Summary\n\nCloses #13\n"
        assert extract_auto_close_lines(body) == ["Closes #13"]

    def test_extracts_case_insensitive_keywords(self):
        body = "fixes #2\nRESOLVES #9\n"
        assert extract_auto_close_lines(body) == ["fixes #2", "RESOLVES #9"]

    def test_extracts_colon_variant(self):
        body = "Closes: #11\n"
        assert extract_auto_close_lines(body) == ["Closes: #11"]

    def test_returns_empty_when_missing(self):
        body = "Summary only\nNo closing syntax here\n"
        assert extract_auto_close_lines(body) == []


class TestMain:
    """Test CLI entrypoint behavior."""

    def test_main_passes_with_inline_body(self, capsys):
        code = main(["--body", "Summary\n\nCloses #1"])
        out = capsys.readouterr().out
        assert code == 0
        assert "PASS" in out

    def test_main_fails_when_missing_closes(self, capsys):
        code = main(["--body", "Summary only"])
        out = capsys.readouterr().out
        assert code == 1
        assert "Missing auto-close syntax" in out

    def test_main_reads_body_file(self, tmp_path, capsys):
        body_file = tmp_path / "pr_body.md"
        body_file.write_text("Details\n\nResolves #7\n", encoding="utf-8")
        code = main(["--body-file", str(body_file)])
        out = capsys.readouterr().out
        assert code == 0
        assert "Resolves #7" in out
