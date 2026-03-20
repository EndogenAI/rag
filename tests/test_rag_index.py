"""tests/test_rag_index.py — Phase 2 retrieval index chunking/indexing contract tests."""

from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.io

_RAG_INDEX_PATH = Path(__file__).parent.parent / "scripts" / "rag_index.py"
_RAG_INDEX_SPEC = importlib.util.spec_from_file_location("rag_index", _RAG_INDEX_PATH)
assert _RAG_INDEX_SPEC and _RAG_INDEX_SPEC.loader
ri = importlib.util.module_from_spec(_RAG_INDEX_SPEC)
sys.modules["rag_index"] = ri
_RAG_INDEX_SPEC.loader.exec_module(ri)


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    return root


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "rag-index" / "rag_index.sqlite3"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_chunk_markdown_h2_metadata_schema() -> None:
    text = """---
x-governs: [commit-discipline]
---

## Alpha
First section content words.

## Beta
Second section content words.
"""
    chunks = ri.chunk_markdown_h2(text, "docs/example.md")

    assert len(chunks) == 2
    assert chunks[0].heading == "Alpha"
    assert chunks[0].source_file == "docs/example.md"
    assert chunks[0].scope == "dogma"
    assert chunks[0].governance_tier == "core"
    assert chunks[0].partition_id == "dogma"
    assert chunks[0].retention_policy == "core-long"
    assert chunks[0].governs_csv == ",commit-discipline,"
    assert chunks[0].fallback_h2 == 0
    assert chunks[0].start_line == 5


def test_chunk_markdown_h2_frozen_fallback_rule() -> None:
    text = "No H2 headings are present in this file."
    chunks = ri.chunk_markdown_h2(text, "docs/no-heading.md")

    assert len(chunks) == 1
    assert chunks[0].heading == ri.FROZEN_H2_FALLBACK_HEADING
    assert chunks[0].fallback_h2 == 1


def test_reindex_full_is_idempotent(repo_root: Path, db_path: Path) -> None:
    a = repo_root / "docs" / "a.md"
    b = repo_root / "docs" / "b.md"
    _write(a, "## A\nchunk alpha words")
    _write(b, "## B\nchunk beta words")

    first = ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[a, b])
    second = ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[a, b])

    assert first["ok"] is True
    assert second["ok"] is True

    status = ri.status_report(db_path=db_path)
    assert status["total_chunks"] == 2


def test_reindex_incremental_updates_only_changed_files(repo_root: Path, db_path: Path) -> None:
    a = repo_root / "docs" / "a.md"
    b = repo_root / "docs" / "b.md"
    _write(a, "## A\nchunk alpha words")
    _write(b, "## B\nchunk beta words")

    ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[a, b])
    inc_unchanged = ri.reindex(scope="incremental", repo_root=repo_root, db_path=db_path, file_paths=[a, b])

    assert inc_unchanged["files_updated"] == 0
    assert inc_unchanged["files_unchanged"] == 2

    _write(b, "## B\nchunk beta words changed")
    inc_changed = ri.reindex(scope="incremental", repo_root=repo_root, db_path=db_path, file_paths=[a, b])

    assert inc_changed["files_updated"] == 1


def test_incremental_version_mismatch_requires_full(repo_root: Path, db_path: Path) -> None:
    a = repo_root / "docs" / "a.md"
    _write(a, "## A\nchunk alpha words")

    ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[a])

    conn = sqlite3.connect(str(db_path))
    conn.execute("UPDATE meta SET value = ? WHERE key = ?", ("old-version", "index_version"))
    conn.commit()
    conn.close()

    mismatch = ri.reindex(scope="incremental", repo_root=repo_root, db_path=db_path, file_paths=[a])
    assert mismatch["ok"] is False
    assert mismatch["error_code"] == "INDEX_VERSION_MISMATCH"

    repaired = ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[a])
    assert repaired["ok"] is True
    assert repaired["rebuilt_schema"] is True


def test_status_reports_freshness(repo_root: Path, db_path: Path) -> None:
    a = repo_root / "docs" / "a.md"
    _write(a, "## A\nchunk alpha words")
    ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[a])

    status = ri.status_report(db_path=db_path, freshness_seconds=3600)
    assert status["exists"] is True
    assert status["version_ok"] is True
    assert status["is_fresh"] is True


def test_query_filter_governs_behavior(repo_root: Path, db_path: Path) -> None:
    a = repo_root / "docs" / "a.md"
    b = repo_root / "docs" / "b.md"
    _write(
        a,
        """---
x-governs: [commit-discipline]
---
## A
commit guidance words for scripts
""",
    )
    _write(
        b,
        """---
x-governs: [session-management]
---
## B
session guidance words for notes
""",
    )

    ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[a, b])

    filtered = ri.query_index("guidance", top_k=5, filter_governs="commit-discipline", db_path=db_path)
    assert filtered["count"] == 1
    assert filtered["results"][0]["source_file"] == "docs/a.md"
    assert filtered["results"][0]["scope"] == "dogma"


def test_query_filter_scope_behavior(repo_root: Path, db_path: Path) -> None:
    dogma_doc = repo_root / "docs" / "a.md"
    client_doc = repo_root / "{{cookiecutter.project_slug}}" / "README.md"
    _write(dogma_doc, "## A\npolicy guidance words")
    _write(client_doc, "## B\npolicy guidance words")

    ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[dogma_doc, client_doc])

    dogma_only = ri.query_index("policy", top_k=10, filter_scope="dogma", db_path=db_path)
    client_only = ri.query_index("policy", top_k=10, filter_scope="client", db_path=db_path)

    assert dogma_only["count"] == 1
    assert dogma_only["results"][0]["source_file"] == "docs/a.md"
    assert dogma_only["results"][0]["scope"] == "dogma"

    assert client_only["count"] == 1
    assert client_only["results"][0]["source_file"] == "{{cookiecutter.project_slug}}/README.md"
    assert client_only["results"][0]["scope"] == "client"


def test_query_natural_language_with_punctuation_is_normalized(repo_root: Path, db_path: Path) -> None:
    doc = repo_root / "docs" / "a.md"
    _write(doc, "## A\nWhat does programmatic first require in this workflow")
    ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[doc])

    result = ri.query_index("What does Programmatic-First require?", top_k=5, db_path=db_path)

    assert result["ok"] is True
    assert result["normalized_query"] == "What does Programmatic First require"
    assert result["count"] >= 1


def test_query_rejects_non_alphanumeric_after_normalization(repo_root: Path, db_path: Path) -> None:
    doc = repo_root / "docs" / "a.md"
    _write(doc, "## A\nProgrammatic first requires script encoding")
    ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[doc])

    with pytest.raises(ValueError, match="alphanumeric token"):
        ri.query_index("??? --- !!!", db_path=db_path)


def test_query_defaults_to_segmented_dogma_scope(repo_root: Path, db_path: Path) -> None:
    dogma_doc = repo_root / "docs" / "a.md"
    client_doc = repo_root / "{{cookiecutter.project_slug}}" / "README.md"
    _write(dogma_doc, "## A\npolicy guidance words")
    _write(client_doc, "## B\npolicy guidance words")

    ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[dogma_doc, client_doc])

    default_query = ri.query_index("policy", top_k=10, db_path=db_path)
    assert default_query["query_mode"] == "segmented"
    assert default_query["filter_scope"] == "dogma"
    assert default_query["count"] == 1
    assert default_query["results"][0]["scope"] == "dogma"


def test_query_federation_requires_reason(repo_root: Path, db_path: Path) -> None:
    doc = repo_root / "docs" / "a.md"
    _write(doc, "## A\npolicy guidance words")
    ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[doc])

    with pytest.raises(ValueError, match="federation_reason"):
        ri.query_index("policy", allow_federation=True, db_path=db_path)


def test_query_federation_allows_cross_scope(repo_root: Path, db_path: Path) -> None:
    dogma_doc = repo_root / "docs" / "a.md"
    client_doc = repo_root / "{{cookiecutter.project_slug}}" / "README.md"
    _write(dogma_doc, "## A\npolicy guidance words")
    _write(client_doc, "## B\npolicy guidance words")

    ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[dogma_doc, client_doc])
    federated = ri.query_index(
        "policy",
        top_k=10,
        allow_federation=True,
        federation_reason="cross-scope audit",
        db_path=db_path,
    )

    assert federated["query_mode"] == "federated"
    assert federated["filter_scope"] is None
    assert federated["count"] == 2


def test_query_invalid_filter_governs_rejected() -> None:
    with pytest.raises(ValueError, match="filter_governs"):
        ri.query_index("hello", filter_governs="Bad Value")


def test_query_invalid_filter_scope_rejected() -> None:
    with pytest.raises(ValueError, match="filter_scope"):
        ri.query_index("hello", filter_scope="invalid-scope")


def test_normalize_governs_values_variants() -> None:
    assert ri.normalize_governs_values(None) == []
    assert ri.normalize_governs_values("alpha, beta, alpha") == ["alpha", "beta"]
    assert ri.normalize_governs_values(["Alpha", "beta", "alpha", ""]) == ["alpha", "beta"]
    assert ri.normalize_governs_values(123) == ["123"]


def test_parse_frontmatter_governs_edge_cases() -> None:
    assert ri.parse_frontmatter_governs("no frontmatter") == []
    assert ri.parse_frontmatter_governs("---\nfoo: bar") == []

    bad_yaml = "---\nfoo: [bar\n---\n## A\nbody"
    assert ri.parse_frontmatter_governs(bad_yaml) == []

    merged = ri.parse_frontmatter_governs(
        """---
x-governs: [session-management, commit-discipline]
governs: [commit-discipline, local-compute-first]
---
## A
body
"""
    )
    assert merged == ["session-management", "commit-discipline", "local-compute-first"]


def test_governs_csv_empty_and_populated() -> None:
    assert ri._governs_csv([]) == ","
    assert ri._governs_csv(["a", "b"]) == ",a,b,"


def test_resolve_corpus_files_skips_dirs_and_dedupes(repo_root: Path) -> None:
    _write(repo_root / "AGENTS.md", "# root")
    _write(repo_root / "client-values.yml", "org: demo")
    _write(repo_root / "docs" / "a.md", "# a")
    _write(repo_root / "{{cookiecutter.project_slug}}" / "README.md", "# template")
    _write(repo_root / ".github" / "agents" / "test.agent.md", "# test")
    (repo_root / "docs" / "subdir").mkdir(parents=True)

    files = ri._resolve_corpus_files(repo_root)
    rel = [str(p.relative_to(repo_root)) for p in files]

    assert "AGENTS.md" in rel
    assert "client-values.yml" in rel
    assert "docs/a.md" in rel
    assert "{{cookiecutter.project_slug}}/README.md" in rel
    assert all(not p.endswith("subdir") for p in rel)
    assert len(rel) == len(set(rel))


def test_reindex_default_discovery_includes_client_scope(repo_root: Path, db_path: Path) -> None:
    _write(repo_root / "AGENTS.md", "# root")
    _write(repo_root / "client-values.yml", "org: demo")
    _write(repo_root / "docs" / "a.md", "## A\npolicy guidance")
    _write(repo_root / "{{cookiecutter.project_slug}}" / "README.md", "## B\npolicy guidance")

    result = ri.reindex(scope="full", repo_root=repo_root, db_path=db_path)
    assert result["ok"] is True

    client_only = ri.query_index("policy", top_k=10, filter_scope="client", db_path=db_path)
    assert client_only["count"] >= 1
    assert all(row["scope"] == "client" for row in client_only["results"])


def test_reindex_invalid_scope_raises(repo_root: Path, db_path: Path) -> None:
    with pytest.raises(ValueError, match="Invalid scope"):
        ri.reindex(scope="bad", repo_root=repo_root, db_path=db_path, file_paths=[])


def test_reindex_dry_run_reports_expected_counts(repo_root: Path, db_path: Path) -> None:
    a = repo_root / "docs" / "a.md"
    _write(a, "## A\nchunk alpha words")

    result = ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[a], dry_run=True)

    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["files_updated"] == 1
    assert result["last_indexed"] is None
    assert result["projected_total_chunks"] is not None


def test_reindex_dry_run_projects_total_without_double_count(repo_root: Path, db_path: Path) -> None:
    a = repo_root / "docs" / "a.md"
    _write(a, "## A\nfirst content")

    first = ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[a])
    assert first["total_chunks"] == 1

    _write(a, "## A\nupdated content")
    dry = ri.reindex(scope="incremental", repo_root=repo_root, db_path=db_path, file_paths=[a], dry_run=True)
    assert dry["total_chunks"] == 1
    assert dry["projected_total_chunks"] == 1


def test_reindex_removes_missing_files(repo_root: Path, db_path: Path) -> None:
    a = repo_root / "docs" / "a.md"
    b = repo_root / "docs" / "b.md"
    _write(a, "## A\nalpha")
    _write(b, "## B\nbeta")

    ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[a, b])
    result = ri.reindex(scope="incremental", repo_root=repo_root, db_path=db_path, file_paths=[a])

    assert result["files_removed"] == 1
    status = ri.status_report(db_path=db_path)
    assert status["total_files"] == 1


def test_reindex_skips_unreadable_files(repo_root: Path, db_path: Path, mocker) -> None:
    good = repo_root / "docs" / "good.md"
    bad = repo_root / "docs" / "bad.md"
    _write(good, "## Good\ntext")
    _write(bad, "## Bad\ntext")

    original = ri._read_file_state

    def fake_read(path: Path, root: Path):
        if path.name == "bad.md":
            raise UnicodeDecodeError("utf-8", b"x", 0, 1, "bad")
        return original(path, root)

    mocker.patch.object(ri, "_read_file_state", side_effect=fake_read)
    result = ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[good, bad])
    assert result["files_total"] == 1


def test_validate_filter_governs_accepts_none_and_valid() -> None:
    assert ri._validate_filter_governs(None) is None
    assert ri._validate_filter_governs("commit-discipline") == "commit-discipline"


def test_classify_content_scope_contract() -> None:
    dogma = ri.classify_content_scope("docs/example.md")
    assert dogma["scope"] == "dogma"
    assert dogma["governance_tier"] == "core"

    client = ri.classify_content_scope("{{cookiecutter.project_slug}}/README.md")
    assert client["scope"] == "client"
    assert client["governance_tier"] == "deployment"

    windows_style = ri.classify_content_scope("{{cookiecutter.project_slug}}\\README.md")
    assert windows_style["scope"] == "client"


def test_read_file_state_uses_posix_source_path(repo_root: Path) -> None:
    p = repo_root / "docs" / "nested" / "example.md"
    _write(p, "## A\ntext")

    state = ri._read_file_state(p, repo_root)
    assert state.source_file == "docs/nested/example.md"


def test_validate_filter_scope_accepts_none_and_valid() -> None:
    assert ri._validate_filter_scope(None) is None
    assert ri._validate_filter_scope("DOGMA") == "dogma"
    assert ri._validate_filter_scope("client") == "client"


def test_query_index_argument_and_index_errors(db_path: Path) -> None:
    with pytest.raises(ValueError, match="non-empty"):
        ri.query_index("   ", db_path=db_path)

    with pytest.raises(ValueError, match="top_k"):
        ri.query_index("hello", top_k=0, db_path=db_path)

    with pytest.raises(ri.RagIndexError, match="Index not found"):
        ri.query_index("hello", db_path=db_path)


def test_query_index_version_mismatch_raises(repo_root: Path, db_path: Path) -> None:
    a = repo_root / "docs" / "a.md"
    _write(a, "## A\nhello")
    ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[a])

    conn = sqlite3.connect(str(db_path))
    conn.execute("UPDATE meta SET value = ? WHERE key = ?", ("old", "index_version"))
    conn.commit()
    conn.close()

    with pytest.raises(ri.RagIndexError, match="version mismatch"):
        ri.query_index("hello", db_path=db_path)


def test_query_index_operational_error_wrapped(mocker, db_path: Path) -> None:
    class FakeConn:
        def execute(self, sql, params=None):
            if isinstance(sql, str) and "SELECT value FROM meta" in sql:
                return self
            raise sqlite3.OperationalError("bad query")

        def fetchone(self):
            return [ri.INDEX_VERSION]

        def close(self):
            return None

        def executescript(self, _):
            return None

    mocker.patch.object(ri, "_connect", return_value=FakeConn())
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.touch()
    with pytest.raises(ri.RagIndexError, match="Invalid full-text query syntax"):
        ri.query_index("hello", db_path=db_path)


def test_status_report_invalid_freshness_raises(db_path: Path) -> None:
    with pytest.raises(ValueError, match=">= 1"):
        ri.status_report(db_path=db_path, freshness_seconds=0)


def test_status_report_missing_index(db_path: Path) -> None:
    result = ri.status_report(db_path=db_path)
    assert result["ok"] is True
    assert result["exists"] is False


def test_status_report_invalid_last_indexed_not_fresh(repo_root: Path, db_path: Path) -> None:
    a = repo_root / "docs" / "a.md"
    _write(a, "## A\nalpha")
    ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[a])

    conn = sqlite3.connect(str(db_path))
    conn.execute("UPDATE meta SET value = ? WHERE key = ?", ("not-iso", "last_indexed"))
    conn.commit()
    conn.close()

    status = ri.status_report(db_path=db_path)
    assert status["seconds_since_last_index"] is None
    assert status["is_fresh"] is False


def test_status_report_naive_last_indexed_is_normalized(repo_root: Path, db_path: Path) -> None:
    a = repo_root / "docs" / "a.md"
    _write(a, "## A\nalpha")
    ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[a])

    conn = sqlite3.connect(str(db_path))
    conn.execute("UPDATE meta SET value = ? WHERE key = ?", ("2026-03-19T00:00:00", "last_indexed"))
    conn.commit()
    conn.close()

    status = ri.status_report(db_path=db_path)
    assert isinstance(status["seconds_since_last_index"], float)


def test_health_report_pass_path(repo_root: Path, db_path: Path) -> None:
    a = repo_root / "docs" / "a.md"
    _write(a, "## A\nalpha")
    ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[a])

    health = ri.health_report(
        db_path=db_path,
        freshness_seconds=3600,
        pending_backlog=0,
        consecutive_failures=0,
        mismatch_rate=0.0,
    )
    assert health["overall"] == "pass"
    assert health["gates"]["freshness"] == "pass"


def test_health_report_warn_and_fail_paths(repo_root: Path, db_path: Path) -> None:
    a = repo_root / "docs" / "a.md"
    _write(a, "## A\nalpha")
    ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[a])

    warn_health = ri.health_report(
        db_path=db_path,
        freshness_seconds=3600,
        pending_backlog=150,
        consecutive_failures=3,
        mismatch_rate=0.003,
    )
    assert warn_health["overall"] == "warn"

    fail_health = ri.health_report(
        db_path=db_path,
        freshness_seconds=3600,
        pending_backlog=250,
        consecutive_failures=6,
        mismatch_rate=0.006,
    )
    assert fail_health["overall"] == "fail"


def test_health_report_freshness_threshold_controls_gate(repo_root: Path, db_path: Path) -> None:
    a = repo_root / "docs" / "a.md"
    _write(a, "## A\nalpha")
    ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[a])

    # Force staleness so the freshness gate classification is deterministic.
    conn = sqlite3.connect(str(db_path))
    conn.execute("UPDATE meta SET value = ? WHERE key = ?", ("2026-01-01T00:00:00+00:00", "last_indexed"))
    conn.commit()
    conn.close()

    strict = ri.health_report(db_path=db_path, freshness_seconds=1)
    relaxed = ri.health_report(db_path=db_path, freshness_seconds=10_000_000)

    assert strict["gates"]["freshness"] == "fail"
    assert strict["thresholds"]["freshness"]["warn_sec"] == 1
    assert strict["thresholds"]["freshness"]["fail_sec"] == 3
    assert relaxed["gates"]["freshness"] in {"pass", "warn"}
    assert relaxed["thresholds"]["freshness"]["warn_sec"] == 10_000_000
    assert relaxed["thresholds"]["freshness"]["fail_sec"] == 30_000_000


def test_health_report_invalid_inputs_raise(repo_root: Path, db_path: Path) -> None:
    a = repo_root / "docs" / "a.md"
    _write(a, "## A\nalpha")
    ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[a])

    with pytest.raises(ValueError, match="pending_backlog"):
        ri.health_report(db_path=db_path, pending_backlog=-1)

    with pytest.raises(ValueError, match="consecutive_failures"):
        ri.health_report(db_path=db_path, consecutive_failures=-1)

    with pytest.raises(ValueError, match="mismatch_rate"):
        ri.health_report(db_path=db_path, mismatch_rate=-0.1)


def test_local_test_report_quick_and_standard(repo_root: Path, db_path: Path) -> None:
    a = repo_root / "docs" / "a.md"
    _write(a, "## A\ngovernance guidance")
    ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[a])

    quick = ri.local_test_report(test_tier="quick", db_path=db_path)
    assert quick["tier"] == "quick"
    assert quick["verdict"] == "PASS"
    assert len(quick["failure_scenarios"]) >= 8

    standard = ri.local_test_report(test_tier="standard", db_path=db_path)
    assert standard["tier"] == "standard"
    assert any(c["name"] == "health-gates" for c in standard["checks"])


def test_local_test_report_stress_and_invalid_tier(repo_root: Path, db_path: Path) -> None:
    a = repo_root / "docs" / "a.md"
    b = repo_root / "{{cookiecutter.project_slug}}" / "README.md"
    _write(a, "## A\ngovernance guidance")
    _write(b, "## B\ngovernance guidance")
    ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[a, b])

    stress = ri.local_test_report(test_tier="stress", db_path=db_path)
    assert stress["tier"] == "stress"
    assert any(c["name"] == "federated-query" for c in stress["checks"])

    with pytest.raises(ValueError, match="test_tier"):
        ri.local_test_report(test_tier="bad", db_path=db_path)


def test_adoption_gate_report_levels(repo_root: Path, db_path: Path) -> None:
    a = repo_root / "docs" / "a.md"
    _write(a, "## A\ngovernance guidance")
    ri.reindex(scope="full", repo_root=repo_root, db_path=db_path, file_paths=[a])

    soft = ri.adoption_gate_report(enforcement_level="soft", db_path=db_path)
    medium = ri.adoption_gate_report(enforcement_level="medium", db_path=db_path)
    hard = ri.adoption_gate_report(enforcement_level="hard", db_path=db_path)

    assert soft["passed"] is True
    assert medium["passed"] is True
    assert hard["passed"] is True


def test_adoption_gate_invalid_level() -> None:
    with pytest.raises(ValueError, match="enforcement_level"):
        ri.adoption_gate_report(enforcement_level="bad")


def test_adoption_gate_report_failure_paths_without_index(db_path: Path) -> None:
    medium = ri.adoption_gate_report(enforcement_level="medium", db_path=db_path)
    hard = ri.adoption_gate_report(enforcement_level="hard", db_path=db_path)

    assert medium["passed"] is False
    assert hard["passed"] is False
    assert any("index missing" in reason for reason in medium["reasons"])
    assert any("index missing" in reason for reason in hard["reasons"])


def test_print_output_branches(capsys: pytest.CaptureFixture[str]) -> None:
    ri._print_output({"ok": True}, "json")
    assert json.loads(capsys.readouterr().out)["ok"] is True

    ri._print_output({"results": []}, "text")
    assert "No results." in capsys.readouterr().out

    ri._print_output(
        {
            "results": [
                {
                    "source_file": "docs/a.md",
                    "start_line": 1,
                    "end_line": 2,
                    "heading": "A",
                    "content": "content",
                }
            ]
        },
        "text",
    )
    out = capsys.readouterr().out
    assert "docs/a.md:1-2 [A]" in out

    ri._print_output({"a": 1}, "text")
    assert "a: 1" in capsys.readouterr().out


def test_main_reindex_success(mocker) -> None:
    mocker.patch.object(ri, "reindex", return_value={"ok": True, "scope": "incremental"})
    print_mock = mocker.patch.object(ri, "_print_output")

    code = ri.main(["reindex", "--output", "text"])
    assert code == 0
    print_mock.assert_called_once()


def test_main_reindex_error_payload_returns_1(mocker, capsys: pytest.CaptureFixture[str]) -> None:
    mocker.patch.object(ri, "reindex", return_value={"ok": False, "error_code": "X"})

    code = ri.main(["reindex"])
    assert code == 1
    assert "error_code" in capsys.readouterr().err


def test_main_query_requires_query_arg() -> None:
    with pytest.raises(SystemExit):
        ri.main(["query"])


def test_main_query_and_status_success(mocker) -> None:
    mocker.patch.object(ri, "query_index", return_value={"ok": True, "results": []})
    print_mock = mocker.patch.object(ri, "_print_output")

    query_code = ri.main(["query", "--query", "hello"])
    assert query_code == 0
    assert print_mock.call_count == 1

    mocker.patch.object(ri, "status_report", return_value={"ok": True, "exists": False})
    status_code = ri.main(["status"])
    assert status_code == 0


def test_main_query_passes_filter_scope(mocker) -> None:
    query_mock = mocker.patch.object(ri, "query_index", return_value={"ok": True, "results": []})
    mocker.patch.object(ri, "_print_output")

    code = ri.main(["query", "--query", "hello", "--filter-scope", "client"])
    assert code == 0
    assert query_mock.call_args.kwargs["filter_scope"] == "client"


def test_main_query_passes_federation_flags(mocker) -> None:
    query_mock = mocker.patch.object(ri, "query_index", return_value={"ok": True, "results": []})
    mocker.patch.object(ri, "_print_output")

    code = ri.main(
        [
            "query",
            "--query",
            "hello",
            "--allow-federation",
            "--federation-reason",
            "cross-scope audit",
        ]
    )
    assert code == 0
    assert query_mock.call_args.kwargs["allow_federation"] is True
    assert query_mock.call_args.kwargs["federation_reason"] == "cross-scope audit"


def test_main_health_command_success(mocker) -> None:
    health_mock = mocker.patch.object(ri, "health_report", return_value={"ok": True, "overall": "pass"})
    mocker.patch.object(ri, "_print_output")

    code = ri.main(["health", "--pending-backlog", "10", "--consecutive-failures", "0", "--mismatch-rate", "0.0"])
    assert code == 0
    assert health_mock.call_count == 1
    assert health_mock.call_args.kwargs["freshness_seconds"] == 600


def test_main_local_test_command_success(mocker) -> None:
    local_test_mock = mocker.patch.object(ri, "local_test_report", return_value={"ok": True, "verdict": "PASS"})
    mocker.patch.object(ri, "_print_output")

    code = ri.main(["local-test", "--test-tier", "standard", "--probe-query", "policy"])
    assert code == 0
    assert local_test_mock.call_count == 1
    assert local_test_mock.call_args.kwargs["test_tier"] == "standard"


def test_main_adoption_gate_exit_codes(mocker) -> None:
    mocker.patch.object(ri, "_print_output")

    mocker.patch.object(ri, "adoption_gate_report", return_value={"ok": True, "passed": True})
    assert ri.main(["adoption-gate", "--enforcement-level", "medium"]) == 0

    mocker.patch.object(ri, "adoption_gate_report", return_value={"ok": True, "passed": False})
    assert ri.main(["adoption-gate", "--enforcement-level", "hard"]) == 1


def test_main_exception_paths(mocker, capsys: pytest.CaptureFixture[str]) -> None:
    mocker.patch.object(ri, "query_index", side_effect=ValueError("bad args"))
    assert ri.main(["query", "--query", "hello"]) == 2
    assert "bad args" in capsys.readouterr().err

    mocker.patch.object(ri, "query_index", side_effect=ri.RagIndexError("bad index"))
    assert ri.main(["query", "--query", "hello"]) == 1
    assert "bad index" in capsys.readouterr().err

    mocker.patch.object(ri, "query_index", side_effect=OSError("disk"))
    assert ri.main(["query", "--query", "hello"]) == 1
    assert "disk" in capsys.readouterr().err
