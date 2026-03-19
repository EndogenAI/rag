"""tests/test_mcp_retrieval.py — MCP retrieval contract tests for rag_query/reindex/status."""

from __future__ import annotations

import json
import subprocess
from typing import Any, cast

import pytest

pytestmark = pytest.mark.io


def _completed(returncode: int = 0, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


class TestRagQuery:
    def test_invalid_query_rejected(self):
        from mcp_server.tools.retrieval import rag_query

        result = rag_query("   ")
        assert result["ok"] is False
        assert result["error"]["code"] == "INVALID_ARGUMENT"

    def test_invalid_filter_governs_rejected(self):
        from mcp_server.tools.retrieval import rag_query

        result = rag_query("test", filter_governs="Bad Value")
        assert result["ok"] is False
        assert result["error"]["code"] == "INVALID_ARGUMENT"

    def test_invalid_top_k_rejected(self):
        from mcp_server.tools.retrieval import rag_query

        result = rag_query("test", top_k=0)
        assert result["ok"] is False
        assert result["error"]["code"] == "INVALID_ARGUMENT"

    def test_non_string_filter_governs_rejected(self):
        from mcp_server.tools.retrieval import rag_query

        result = rag_query("test", filter_governs=cast(Any, 123))
        assert result["ok"] is False
        assert result["error"]["code"] == "INVALID_ARGUMENT"

    def test_success_payload(self, mocker):
        from mcp_server.tools.retrieval import rag_query

        payload = {
            "ok": True,
            "query": "commit",
            "top_k": 3,
            "count": 1,
            "results": [{"source_file": "AGENTS.md", "heading": "Programmatic-First Principle"}],
        }
        mocker.patch("mcp_server.tools.retrieval._run_script", return_value=_completed(0, json.dumps(payload)))

        result = rag_query("commit", top_k=3)
        assert result["ok"] is True
        assert result["count"] == 1

    def test_index_not_found_error_mapping(self, mocker):
        from mcp_server.tools.retrieval import rag_query

        mocker.patch(
            "mcp_server.tools.retrieval._run_script",
            return_value=_completed(1, "", "ERROR: Index not found at rag-index/rag_index.sqlite3"),
        )
        result = rag_query("commit")
        assert result["ok"] is False
        assert result["error"]["code"] == "INDEX_NOT_FOUND"

    def test_version_mismatch_error_mapping(self, mocker):
        from mcp_server.tools.retrieval import rag_query

        mocker.patch(
            "mcp_server.tools.retrieval._run_script",
            return_value=_completed(1, "", "ERROR: index version mismatch"),
        )
        result = rag_query("commit")
        assert result["ok"] is False
        assert result["error"]["code"] == "INDEX_VERSION_MISMATCH"

    def test_invalid_argument_error_mapping(self, mocker):
        from mcp_server.tools.retrieval import rag_query

        mocker.patch(
            "mcp_server.tools.retrieval._run_script",
            return_value=_completed(1, "", "ERROR: Invalid filter"),
        )
        result = rag_query("commit")
        assert result["ok"] is False
        assert result["error"]["code"] == "INVALID_ARGUMENT"

    def test_malformed_json_output_returns_error(self, mocker):
        from mcp_server.tools.retrieval import rag_query

        mocker.patch("mcp_server.tools.retrieval._run_script", return_value=_completed(0, "not-json"))
        result = rag_query("commit")
        assert result["ok"] is False
        assert result["error"]["code"] == "MALFORMED_SCRIPT_OUTPUT"

    def test_filter_governs_is_forwarded_when_present(self, mocker):
        from mcp_server.tools.retrieval import rag_query

        run_mock = mocker.patch(
            "mcp_server.tools.retrieval._run_script",
            return_value=_completed(0, json.dumps({"ok": True, "results": []})),
        )
        rag_query("commit", filter_governs="commit-discipline")
        args = run_mock.call_args.args[0]
        assert "--filter-governs" in args
        assert "commit-discipline" in args


class TestRagReindex:
    def test_invalid_scope_rejected(self):
        from mcp_server.tools.retrieval import rag_reindex

        result = rag_reindex(scope="bad")
        assert result["ok"] is False
        assert result["error"]["code"] == "INVALID_ARGUMENT"

    def test_success_payload(self, mocker):
        from mcp_server.tools.retrieval import rag_reindex

        payload = {"ok": True, "scope": "incremental", "files_updated": 1, "chunks_indexed": 3}
        mocker.patch("mcp_server.tools.retrieval._run_script", return_value=_completed(0, json.dumps(payload)))

        result = rag_reindex(scope="incremental")
        assert result["ok"] is True
        assert result["stats"]["files_updated"] == 1

    def test_invalid_dry_run_type_rejected(self):
        from mcp_server.tools.retrieval import rag_reindex

        result = rag_reindex(scope="incremental", dry_run=cast(Any, "yes"))
        assert result["ok"] is False
        assert result["error"]["code"] == "INVALID_ARGUMENT"

    def test_json_error_payload_preserved(self, mocker):
        from mcp_server.tools.retrieval import rag_reindex

        error_payload = {
            "ok": False,
            "error_code": "INDEX_VERSION_MISMATCH",
            "expected_version": "phase2-v1",
            "actual_version": "phase1-v0",
        }
        mocker.patch(
            "mcp_server.tools.retrieval._run_script",
            return_value=_completed(1, "", json.dumps(error_payload)),
        )

        result = rag_reindex(scope="incremental")
        assert result["ok"] is False
        assert result["error"]["code"] == "INDEX_VERSION_MISMATCH"

    def test_dry_run_flag_is_forwarded(self, mocker):
        from mcp_server.tools.retrieval import rag_reindex

        run_mock = mocker.patch(
            "mcp_server.tools.retrieval._run_script",
            return_value=_completed(0, json.dumps({"ok": True})),
        )
        result = rag_reindex(scope="incremental", dry_run=True)

        assert result["ok"] is True
        args = run_mock.call_args.args[0]
        assert "--dry-run" in args
        assert run_mock.call_args.kwargs["timeout"] == 180

    def test_non_json_stderr_version_mismatch_maps_error(self, mocker):
        from mcp_server.tools.retrieval import rag_reindex

        mocker.patch(
            "mcp_server.tools.retrieval._run_script",
            return_value=_completed(1, "", "index version mismatch"),
        )
        result = rag_reindex(scope="incremental")
        assert result["ok"] is False
        assert result["error"]["code"] == "INDEX_VERSION_MISMATCH"

    def test_malformed_success_json_returns_error(self, mocker):
        from mcp_server.tools.retrieval import rag_reindex

        mocker.patch("mcp_server.tools.retrieval._run_script", return_value=_completed(0, "not-json"))
        result = rag_reindex(scope="incremental")
        assert result["ok"] is False
        assert result["error"]["code"] == "MALFORMED_SCRIPT_OUTPUT"

    def test_ok_false_payload_maps_error_code(self, mocker):
        from mcp_server.tools.retrieval import rag_reindex

        payload = {"ok": False, "error_code": "INDEX_REINDEX_FAILED"}
        mocker.patch("mcp_server.tools.retrieval._run_script", return_value=_completed(0, json.dumps(payload)))
        result = rag_reindex(scope="incremental")
        assert result["ok"] is False
        assert result["error"]["code"] == "INDEX_REINDEX_FAILED"


class TestRagStatus:
    def test_invalid_freshness_rejected(self):
        from mcp_server.tools.retrieval import rag_status

        result = rag_status(freshness_seconds=0)
        assert result["ok"] is False
        assert result["error"]["code"] == "INVALID_ARGUMENT"

    def test_success_payload(self, mocker):
        from mcp_server.tools.retrieval import rag_status

        payload = {"ok": True, "exists": True, "is_fresh": True, "version_ok": True}
        mocker.patch("mcp_server.tools.retrieval._run_script", return_value=_completed(0, json.dumps(payload)))

        result = rag_status()
        assert result["ok"] is True
        assert result["status"]["is_fresh"] is True

    def test_subprocess_failure_returns_error(self, mocker):
        from mcp_server.tools.retrieval import rag_status

        mocker.patch(
            "mcp_server.tools.retrieval._run_script",
            return_value=_completed(1, "", "status failed"),
        )
        result = rag_status()
        assert result["ok"] is False
        assert result["error"]["code"] == "INDEX_STATUS_FAILED"

    def test_malformed_json_returns_error(self, mocker):
        from mcp_server.tools.retrieval import rag_status

        mocker.patch("mcp_server.tools.retrieval._run_script", return_value=_completed(0, "not-json"))
        result = rag_status()
        assert result["ok"] is False
        assert result["error"]["code"] == "MALFORMED_SCRIPT_OUTPUT"


def test_run_script_wraps_subprocess_run(mocker):
    from mcp_server.tools import retrieval

    run_mock = mocker.patch("mcp_server.tools.retrieval.subprocess.run", return_value=_completed(0, "{}"))
    result = retrieval._run_script(["scripts/rag_index.py", "status"], timeout=7)

    assert result.returncode == 0
    assert run_mock.call_args.kwargs["timeout"] == 7
    assert run_mock.call_args.kwargs["capture_output"] is True
    assert run_mock.call_args.kwargs["text"] is True


def test_parse_json_empty_and_valid_payloads():
    from mcp_server.tools.retrieval import _parse_json

    assert _parse_json("   ") == {}
    assert _parse_json('{"ok": true}') == {"ok": True}


def test_parse_json_invalid_raises():
    from mcp_server.tools.retrieval import _parse_json

    with pytest.raises(json.JSONDecodeError):
        _parse_json("not-json")
