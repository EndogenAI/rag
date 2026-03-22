"""Tests for scripts/backfill_machine_metadata.py

Covers:
- get_machine_metadata: returns dict with all required keys, correct types
- backfill_study_directory: injects metadata, idempotent on existing fields,
  handles malformed JSON, handles empty directory
- main: success path, empty directory (no IndexError), missing study dir returns 1
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── helpers ───────────────────────────────────────────────────────────────────


def write_jsonl_file(path: Path, entries: list) -> None:
    with open(path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


_FAKE_META = {
    "machine_type": "arm64",
    "system": "Darwin",
    "processor": "Apple M2",
    "python_version": "3.11.0",
    "ram_gb": 16.0,
}


# ── get_machine_metadata ──────────────────────────────────────────────────────


def test_get_machine_metadata_has_all_keys():
    """All required keys are present in the returned dict."""
    from scripts.backfill_machine_metadata import get_machine_metadata

    meta = get_machine_metadata()
    for key in ("machine_type", "system", "processor", "python_version", "ram_gb"):
        assert key in meta, f"Missing key: {key}"


def test_get_machine_metadata_types():
    """ram_gb is numeric; string fields are non-empty strings."""
    from scripts.backfill_machine_metadata import get_machine_metadata

    meta = get_machine_metadata()
    assert isinstance(meta["ram_gb"], (int, float))
    assert meta["ram_gb"] > 0
    for key in ("machine_type", "system", "python_version"):
        assert isinstance(meta[key], str)


# ── backfill_study_directory ──────────────────────────────────────────────────


@pytest.mark.io
def test_backfill_injects_machine_metadata(tmp_path):
    """machine_metadata is added to JSONL entries that lack it."""
    from scripts.backfill_machine_metadata import backfill_study_directory

    jsonl = tmp_path / "run.jsonl"
    write_jsonl_file(jsonl, [{"query_id": "q1", "score": 0.5}])

    backfill_study_directory(tmp_path, _FAKE_META)

    entry = json.loads(jsonl.read_text().strip())
    assert entry["machine_metadata"] == _FAKE_META


@pytest.mark.io
def test_backfill_is_idempotent(tmp_path):
    """Entries that already have machine_metadata are left unchanged."""
    from scripts.backfill_machine_metadata import backfill_study_directory

    original_meta = {
        "machine_type": "x86_64",
        "system": "Linux",
        "processor": "Intel",
        "python_version": "3.10.0",
        "ram_gb": 8.0,
    }
    jsonl = tmp_path / "run.jsonl"
    write_jsonl_file(jsonl, [{"query_id": "q1", "machine_metadata": original_meta}])

    new_meta = {**_FAKE_META, "machine_type": "arm64", "ram_gb": 32.0}
    backfill_study_directory(tmp_path, new_meta)

    entry = json.loads(jsonl.read_text().strip())
    assert entry["machine_metadata"] == original_meta


@pytest.mark.io
def test_backfill_handles_malformed_json_line(tmp_path):
    """Malformed JSON lines are preserved unchanged; no exception is raised."""
    from scripts.backfill_machine_metadata import backfill_study_directory

    jsonl = tmp_path / "run.jsonl"
    jsonl.write_text("not-valid-json\n")

    backfill_study_directory(tmp_path, _FAKE_META)  # must not raise

    assert "not-valid-json" in jsonl.read_text()


@pytest.mark.io
def test_backfill_empty_directory_no_crash(tmp_path):
    """Empty study directory (no .jsonl files) does not raise an exception."""
    from scripts.backfill_machine_metadata import backfill_study_directory

    # tmp_path has no .jsonl files — must not raise
    backfill_study_directory(tmp_path, _FAKE_META)


@pytest.mark.io
def test_backfill_multiple_entries(tmp_path):
    """All JSONL entries in a multi-entry file receive machine_metadata."""
    from scripts.backfill_machine_metadata import backfill_study_directory

    jsonl = tmp_path / "run.jsonl"
    write_jsonl_file(
        jsonl,
        [
            {"query_id": "q1", "score": 0.5},
            {"query_id": "q2", "score": 0.8},
        ],
    )

    backfill_study_directory(tmp_path, _FAKE_META)

    lines = jsonl.read_text().strip().splitlines()
    assert len(lines) == 2
    for line in lines:
        entry = json.loads(line)
        assert entry["machine_metadata"] == _FAKE_META


# ── main ──────────────────────────────────────────────────────────────────────


@pytest.mark.io
def test_main_missing_study_dir_returns_1(tmp_path):
    """main() returns 1 when the hard-coded study directory does not exist."""
    import scripts.backfill_machine_metadata as mod

    # Point the script's __file__ to a location where study-2a doesn't exist
    with patch.object(mod, "__file__", str(tmp_path / "scripts" / "backfill_machine_metadata.py")):
        result = mod.main()

    assert result == 1


@pytest.mark.io
def test_main_empty_dir_returns_0_no_index_error(tmp_path):
    """main() returns 0 when study dir exists but has no .jsonl files (guard against IndexError)."""
    import scripts.backfill_machine_metadata as mod

    study_dir = tmp_path / "data" / "benchmark-results" / "study-2a"
    study_dir.mkdir(parents=True)

    with patch.object(mod, "__file__", str(tmp_path / "scripts" / "backfill_machine_metadata.py")):
        result = mod.main()

    assert result == 0


@pytest.mark.io
def test_main_success_verifies_metadata(tmp_path):
    """main() returns 0 and metadata is present in the backfilled file."""
    import scripts.backfill_machine_metadata as mod

    study_dir = tmp_path / "data" / "benchmark-results" / "study-2a"
    study_dir.mkdir(parents=True)
    write_jsonl_file(study_dir / "artifact.jsonl", [{"query_id": "q1", "score": 0.5}])

    with patch.object(mod, "__file__", str(tmp_path / "scripts" / "backfill_machine_metadata.py")):
        result = mod.main()

    assert result == 0

    entry = json.loads((study_dir / "artifact.jsonl").read_text().split("\n")[0])
    assert "machine_metadata" in entry
