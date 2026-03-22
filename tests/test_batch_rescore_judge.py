"""Tests for scripts/batch_rescore_judge.py

Covers:
- iter_jsonl_artifacts: yields un-rescored files, skips sibling/already-rescored,
  warns on missing directory
- rescore_artifact: happy path, malformed-line passthrough (no double-encoding),
  dry-run, in-place, non-tier-2 passthrough
- main: returns 1 when no artifacts found
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── dependency isolation ──────────────────────────────────────────────────────
# batch_rescore_judge has a module-level import: from benchmark_rag import BENCHMARK_DATA, evaluate_with_judge
# We stub the whole module before importing so the file can be loaded in tests.
_mock_brag = MagicMock()
_mock_brag.BENCHMARK_DATA = Path("data/rag-benchmarks.yml")
_mock_brag.evaluate_with_judge = MagicMock()
sys.modules.setdefault("benchmark_rag", _mock_brag)

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── helpers ───────────────────────────────────────────────────────────────────


def write_jsonl(path: Path, entries: list) -> None:
    """Write a list of dicts (or raw strings) to a JSONL file."""
    with open(path, "w") as f:
        for entry in entries:
            if isinstance(entry, str):
                f.write(entry + "\n")
            else:
                f.write(json.dumps(entry) + "\n")


# ── iter_jsonl_artifacts ──────────────────────────────────────────────────────


def test_iter_yields_unrescored_file(tmp_path):
    """A plain JSONL artifact is yielded."""
    from scripts.batch_rescore_judge import iter_jsonl_artifacts

    study_dir = tmp_path / "study-test"
    study_dir.mkdir()
    (study_dir / "artifact.jsonl").write_text("{}\n")

    with patch("scripts.batch_rescore_judge.ARTIFACT_ROOT", tmp_path):
        results = list(iter_jsonl_artifacts("study-test"))

    assert len(results) == 1
    assert results[0].name == "artifact.jsonl"


def test_iter_skips_already_rescored_filename(tmp_path):
    """Files whose name ends in *-rescored.jsonl are not yielded."""
    from scripts.batch_rescore_judge import iter_jsonl_artifacts

    study_dir = tmp_path / "study-test"
    study_dir.mkdir()
    (study_dir / "artifact-rescored.jsonl").write_text("{}\n")

    with patch("scripts.batch_rescore_judge.ARTIFACT_ROOT", tmp_path):
        results = list(iter_jsonl_artifacts("study-test"))

    assert results == []


def test_iter_skips_original_when_rescored_sibling_exists(tmp_path):
    """Original file is skipped when its *-rescored.jsonl sibling already exists."""
    from scripts.batch_rescore_judge import iter_jsonl_artifacts

    study_dir = tmp_path / "study-test"
    study_dir.mkdir()
    (study_dir / "artifact.jsonl").write_text("{}\n")
    (study_dir / "artifact-rescored.jsonl").write_text("{}\n")

    with patch("scripts.batch_rescore_judge.ARTIFACT_ROOT", tmp_path):
        results = list(iter_jsonl_artifacts("study-test"))

    assert results == []


def test_iter_warns_on_missing_directory(tmp_path, capsys):
    """Missing study directory prints a WARNING and yields nothing."""
    from scripts.batch_rescore_judge import iter_jsonl_artifacts

    with patch("scripts.batch_rescore_judge.ARTIFACT_ROOT", tmp_path):
        results = list(iter_jsonl_artifacts("does-not-exist"))

    assert results == []
    assert "WARNING" in capsys.readouterr().out


# ── rescore_artifact ──────────────────────────────────────────────────────────


@pytest.mark.io
def test_rescore_artifact_happy_path(tmp_path):
    """Tier-2 entries are rescored and written to *-rescored.jsonl."""
    from scripts.batch_rescore_judge import rescore_artifact

    test_cases = {"q1": {"id": "q1", "tier": 2, "question": "Q?", "expected_answer": "A"}}
    artifact = tmp_path / "run.jsonl"
    write_jsonl(artifact, [{"query_id": "q1", "response": "42", "retrieved_chunks": [], "score": 0.5}])

    judge_result = {"overall_score": 0.9, "judge_reasoning": "good", "preflight_signals": {}}
    with patch("scripts.batch_rescore_judge.evaluate_with_judge", return_value=judge_result):
        total, rescored = rescore_artifact(artifact, test_cases)

    assert total == 1
    assert rescored == 1

    output = tmp_path / "run-rescored.jsonl"
    assert output.exists()
    line = json.loads(output.read_text().strip())
    assert line["score"] == 0.9
    assert line["score_source"] == "llm-as-judge"
    assert line["old_score_pattern_match"] == 0.5


@pytest.mark.io
def test_rescore_artifact_malformed_line_no_double_encoding(tmp_path):
    """Malformed JSON lines are written back as raw strings — not double-encoded."""
    from scripts.batch_rescore_judge import rescore_artifact

    artifact = tmp_path / "run.jsonl"
    artifact.write_text("not-valid-json\n")

    with patch("scripts.batch_rescore_judge.evaluate_with_judge"):
        rescore_artifact(artifact, {})

    output = tmp_path / "run-rescored.jsonl"
    assert output.exists()
    # Must be the original raw string; json.dumps would wrap it in extra quotes.
    assert output.read_text().strip() == "not-valid-json"


@pytest.mark.io
def test_rescore_artifact_dry_run_no_output_file(tmp_path):
    """dry_run=True: counts tier-2 entries but writes no output file."""
    from scripts.batch_rescore_judge import rescore_artifact

    test_cases = {"q1": {"id": "q1", "tier": 2, "question": "Q?", "expected_answer": "A"}}
    artifact = tmp_path / "run.jsonl"
    write_jsonl(artifact, [{"query_id": "q1", "response": "42", "retrieved_chunks": [], "score": 0.5}])

    with patch("scripts.batch_rescore_judge.evaluate_with_judge"):
        total, rescored = rescore_artifact(artifact, test_cases, dry_run=True)

    assert rescored == 1
    assert not (tmp_path / "run-rescored.jsonl").exists()


@pytest.mark.io
def test_rescore_artifact_in_place_overwrites_original(tmp_path):
    """in_place=True: original file is updated; no *-rescored.jsonl sibling created."""
    from scripts.batch_rescore_judge import rescore_artifact

    test_cases = {"q1": {"id": "q1", "tier": 2, "question": "Q?", "expected_answer": "A"}}
    artifact = tmp_path / "run.jsonl"
    write_jsonl(artifact, [{"query_id": "q1", "response": "42", "retrieved_chunks": [], "score": 0.5}])

    judge_result = {"overall_score": 0.8, "judge_reasoning": "ok", "preflight_signals": {}}
    with patch("scripts.batch_rescore_judge.evaluate_with_judge", return_value=judge_result):
        rescore_artifact(artifact, test_cases, in_place=True)

    assert not (tmp_path / "run-rescored.jsonl").exists()
    line = json.loads(artifact.read_text().strip())
    assert line["score"] == 0.8


@pytest.mark.io
def test_rescore_artifact_non_tier2_passthrough(tmp_path):
    """Non-tier-2 entries are written unchanged; evaluate_with_judge is never called."""
    from scripts.batch_rescore_judge import rescore_artifact

    test_cases = {"q1": {"id": "q1", "tier": 1}}
    artifact = tmp_path / "run.jsonl"
    write_jsonl(artifact, [{"query_id": "q1", "score": 0.5}])

    with patch("scripts.batch_rescore_judge.evaluate_with_judge") as mock_judge:
        total, rescored = rescore_artifact(artifact, test_cases)

    mock_judge.assert_not_called()
    assert rescored == 0


@pytest.mark.io
def test_rescore_artifact_unknown_query_passthrough(tmp_path):
    """Entries whose query_id is not in test_cases are written unchanged."""
    from scripts.batch_rescore_judge import rescore_artifact

    artifact = tmp_path / "run.jsonl"
    write_jsonl(artifact, [{"query_id": "unknown-id", "score": 0.3}])

    with patch("scripts.batch_rescore_judge.evaluate_with_judge") as mock_judge:
        total, rescored = rescore_artifact(artifact, {})

    mock_judge.assert_not_called()
    assert rescored == 0


# ── main exit codes ───────────────────────────────────────────────────────────


def test_main_returns_1_when_no_artifacts(tmp_path, capsys):
    """main() returns 1 when the study directory contains no matching artifacts."""
    from scripts.batch_rescore_judge import main

    (tmp_path / "empty-study").mkdir()

    with (
        patch("scripts.batch_rescore_judge.ARTIFACT_ROOT", tmp_path),
        patch("sys.argv", ["batch_rescore_judge.py", "--study", "empty-study"]),
        patch("scripts.batch_rescore_judge.load_test_cases", return_value={}),
    ):
        result = main()

    assert result == 1
