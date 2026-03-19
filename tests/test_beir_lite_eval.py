"""tests/test_beir_lite_eval.py - BEIR-lite harness contract tests."""

from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.io

_BEIR_PATH = Path(__file__).parent.parent / "scripts" / "beir_lite_eval.py"
_BEIR_SPEC = importlib.util.spec_from_file_location("beir_lite_eval", _BEIR_PATH)
assert _BEIR_SPEC and _BEIR_SPEC.loader
be = importlib.util.module_from_spec(_BEIR_SPEC)
sys.modules["beir_lite_eval"] = be
_BEIR_SPEC.loader.exec_module(be)

_RAG_PATH = Path(__file__).parent.parent / "scripts" / "rag_index.py"
_RAG_SPEC = importlib.util.spec_from_file_location("rag_index", _RAG_PATH)
assert _RAG_SPEC and _RAG_SPEC.loader
ri = importlib.util.module_from_spec(_RAG_SPEC)
sys.modules["rag_index"] = ri
_RAG_SPEC.loader.exec_module(ri)


@pytest.fixture
def eval_workspace(tmp_path: Path) -> dict[str, Path]:
    repo = tmp_path / "repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)

    (docs / "a.md").write_text(
        "## Retrieval Contract\nFrozen fallback rule with deterministic heading behavior.\n",
        encoding="utf-8",
    )
    (docs / "b.md").write_text(
        "## Query Validation\nQuery must be non-empty string and filter_governs is slug-validated.\n",
        encoding="utf-8",
    )

    db_path = repo / "rag-index" / "rag_index.sqlite3"
    ri.reindex(
        scope="full",
        repo_root=repo,
        db_path=db_path,
        file_paths=[docs / "a.md", docs / "b.md"],
    )

    dataset = {
        "dataset_id": "beir-lite-test",
        "version": "1.0.0",
        "queries": [
            {
                "query_id": "q1",
                "query": "frozen fallback rule",
                "relevant_source_files": ["docs/a.md"],
                "baseline_tokens": 1000,
                "rag_tokens": 200,
            },
            {
                "query_id": "q2",
                "query": "query must be non-empty string",
                "relevant_source_files": ["docs/b.md"],
                "baseline_tokens": 900,
                "rag_tokens": 180,
            },
        ],
    }

    dataset_path = repo / "dataset.json"
    dataset_path.write_text(json.dumps(dataset), encoding="utf-8")

    config = {
        "dataset_path": str(dataset_path),
        "top_k": 5,
        "filter_governs": None,
        "seed": 0,
        "index_path": str(db_path),
    }
    config_path = repo / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    return {
        "repo": repo,
        "config_path": config_path,
        "dataset_path": dataset_path,
        "db_path": db_path,
    }


def test_run_evaluation_happy_path(eval_workspace: dict[str, Path]) -> None:
    payload = be.run_evaluation(
        eval_workspace["config_path"],
        run_id_override="run-test",
        timestamp_override="2026-03-19T00:00:00+00:00",
    )

    assert payload["dataset_id"] == "beir-lite-test"
    assert payload["run_id"] == "run-test"
    assert payload["timestamp"] == "2026-03-19T00:00:00+00:00"
    assert payload["recall_at_5"] is not None
    assert payload["precision_at_5"] is not None
    assert "latency_p50_ms" in payload
    assert "latency_p95_ms" in payload
    assert "error_rate_pct" in payload
    assert "token_savings_median_pct" in payload
    assert len(payload["queries"]) == 2


def test_deterministic_check_passes_fixed_inputs(eval_workspace: dict[str, Path]) -> None:
    payload = be.run_evaluation(
        eval_workspace["config_path"],
        assert_deterministic=True,
        run_id_override="deterministic-run",
        timestamp_override="2026-03-19T00:00:00+00:00",
    )

    assert payload["aggregate"]["k"] == 5
    assert payload["run_id"] == "deterministic-run"


def test_config_missing_dataset_file_raises(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "dataset_path": str(tmp_path / "missing-dataset.json"),
                "top_k": 5,
                "filter_governs": None,
                "seed": 0,
                "index_path": str(tmp_path / "missing-index.sqlite3"),
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Dataset file does not exist"):
        be.run_evaluation(config_path)


def test_malformed_config_rejected(tmp_path: Path) -> None:
    dataset_path = tmp_path / "dataset.json"
    dataset_path.write_text(
        json.dumps(
            {
                "dataset_id": "bad",
                "version": "1.0.0",
                "queries": [
                    {
                        "query_id": "q1",
                        "query": "hello",
                        "relevant_source_files": ["docs/a.md"],
                        "baseline_tokens": 100,
                        "rag_tokens": 10,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    config_path = tmp_path / "bad-config.json"
    config_path.write_text(
        json.dumps(
            {
                "dataset_path": str(dataset_path),
                "top_k": 0,
                "filter_governs": None,
                "seed": 0,
                "index_path": str(tmp_path / "rag-index.sqlite3"),
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="top_k"):
        be.run_evaluation(config_path)


def test_main_writes_output_file(eval_workspace: dict[str, Path]) -> None:
    output_path = eval_workspace["repo"] / "result.json"
    code = be.main(
        [
            "--config",
            str(eval_workspace["config_path"]),
            "--output",
            str(output_path),
            "--run-id",
            "main-run",
            "--timestamp",
            "2026-03-19T00:00:00+00:00",
        ]
    )

    assert code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "main-run"


def test_retrieval_runtime_error_classified(eval_workspace: dict[str, Path]) -> None:
    conn = sqlite3.connect(str(eval_workspace["db_path"]))
    conn.execute("UPDATE meta SET value = ? WHERE key = ?", ("old-version", "index_version"))
    conn.commit()
    conn.close()

    payload = be.run_evaluation(eval_workspace["config_path"])
    assert payload["error_rate_pct"] == 100.0
    assert all(row["error"] is not None for row in payload["queries"])


def test_shipped_beir_lite_config_meets_sprint_1_thresholds() -> None:
    config_path = Path(__file__).parent.parent / "scripts" / "eval_data" / "beir_lite_config_v1.json"

    payload = be.run_evaluation(config_path)

    assert payload["recall_at_5"] is not None
    assert payload["precision_at_5"] is not None
    assert payload["recall_at_5"] >= 0.75
    assert payload["precision_at_5"] >= 0.60
    assert payload["error_rate_pct"] < 1.0
