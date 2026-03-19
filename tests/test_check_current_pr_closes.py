#!/usr/bin/env python3
"""Test suite for scripts/check_current_pr_closes.py."""

from __future__ import annotations

import sys
from pathlib import Path

# Add scripts/ to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import check_current_pr_closes as mod


def test_parse_repo_from_https_origin():
    assert mod.parse_repo_from_origin("https://github.com/EndogenAI/rag.git\n") == "EndogenAI/rag"


def test_parse_repo_from_ssh_origin():
    assert mod.parse_repo_from_origin("git@github.com:EndogenAI/rag.git\n") == "EndogenAI/rag"


def test_extract_auto_close_lines():
    body = "Summary\n\nCloses #1\nFixes: #2\n"
    assert mod.extract_auto_close_lines(body) == ["Closes #1", "Fixes: #2"]


def test_main_skip_when_no_open_pr(monkeypatch, capsys):
    monkeypatch.setattr(mod, "get_repo_from_origin", lambda: "EndogenAI/rag")
    monkeypatch.setattr(mod, "get_current_branch", lambda: "feature/no-pr")
    monkeypatch.setattr(mod, "get_open_pr", lambda repo, branch: None)

    code = mod.main([])
    out = capsys.readouterr().out
    assert code == 0
    assert "SKIP" in out


def test_main_fails_when_pr_missing_closes(monkeypatch, capsys):
    monkeypatch.setattr(mod, "get_repo_from_origin", lambda: "EndogenAI/rag")
    monkeypatch.setattr(mod, "get_current_branch", lambda: "feature/has-pr")
    monkeypatch.setattr(
        mod,
        "get_open_pr",
        lambda repo, branch: {"number": 13, "body": "No close lines", "url": "https://example.test/pr/13"},
    )

    code = mod.main([])
    out = capsys.readouterr().out
    assert code == 1
    assert "missing auto-close syntax" in out.lower()


def test_main_passes_when_pr_has_closes(monkeypatch, capsys):
    monkeypatch.setattr(mod, "get_repo_from_origin", lambda: "EndogenAI/rag")
    monkeypatch.setattr(mod, "get_current_branch", lambda: "feature/has-pr")
    monkeypatch.setattr(
        mod,
        "get_open_pr",
        lambda repo, branch: {
            "number": 13,
            "body": "Summary\n\nCloses #13\n",
            "url": "https://example.test/pr/13",
        },
    )

    code = mod.main([])
    out = capsys.readouterr().out
    assert code == 0
    assert "PASS" in out
    assert "Closes #13" in out


def test_main_returns_error_on_runtime_failure(monkeypatch, capsys):
    monkeypatch.setattr(mod, "get_repo_from_origin", lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    code = mod.main([])
    out = capsys.readouterr().out
    assert code == 1
    assert "ERROR" in out
