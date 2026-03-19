"""scripts/beir_lite_eval.py - BEIR-lite retrieval evaluation and instrumentation harness.

Purpose:
    Run a reproducible BEIR-lite style evaluation against the Phase 2
    retrieval substrate (`scripts/rag_index.py`) and emit machine-readable
    metrics for quality and runtime instrumentation.

Inputs:
    --config PATH            JSON config file defining dataset path, top_k,
                             filter_governs behavior, seed, and index path.
    --output PATH            Optional JSON output path.
    --assert-deterministic   Re-run retrieval metrics and fail if Recall@K or
                             Precision@K drift on fixed inputs.
    --run-id TEXT            Optional run identifier override.
    --timestamp TEXT         Optional ISO-8601 timestamp override.

Config schema (JSON):
    {
      "dataset_path": "scripts/eval_data/beir_lite_v1.json",
      "top_k": 5,
      "filter_governs": null,
      "seed": 0,
      "index_path": "rag-index/rag_index.sqlite3"
    }

Dataset schema (JSON):
    {
      "dataset_id": "beir-lite-v1",
      "version": "1.0.0",
      "queries": [
        {
          "query_id": "q1",
          "query": "text",
          "relevant_source_files": ["docs/file.md"],
          "baseline_tokens": 100,
          "rag_tokens": 20
        }
      ]
    }

Outputs:
    JSON payload with per-query metrics plus aggregate metrics including:
    Recall@K, Precision@K, latency p50/p95, error rate, and token savings.

Usage:
    uv run python scripts/beir_lite_eval.py --config scripts/eval_data/beir_lite_config_v1.json
    uv run python scripts/beir_lite_eval.py --config scripts/eval_data/beir_lite_config_v1.json --assert-deterministic

Exit codes:
    0 - success
    1 - runtime or retrieval error
    2 - validation or input schema error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import rag_index as ri

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_SCHEMA_PATH = REPO_ROOT / "scripts" / "schemas" / "beir_lite_instrumentation.schema.json"


class BeirLiteEvalError(RuntimeError):
    """Raised when evaluation cannot complete due to runtime failures."""


@dataclass(frozen=True)
class EvalConfig:
    """Validated BEIR-lite runner configuration."""

    dataset_path: Path
    index_path: Path
    top_k: int
    filter_governs: str | None
    seed: int


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"JSON file does not exist: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON at {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object at root in {path}")
    return data


def _resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def load_config(config_path: Path) -> EvalConfig:
    """Load and validate config JSON."""
    raw = _load_json(config_path)
    required = {"dataset_path", "top_k", "filter_governs", "seed", "index_path"}
    missing = sorted([key for key in required if key not in raw])
    if missing:
        raise ValueError(f"Config missing required keys: {', '.join(missing)}")

    top_k = raw["top_k"]
    if not isinstance(top_k, int) or not (1 <= top_k <= 50):
        raise ValueError("Config field 'top_k' must be an integer between 1 and 50")

    seed = raw["seed"]
    if not isinstance(seed, int):
        raise ValueError("Config field 'seed' must be an integer")

    filter_governs = raw["filter_governs"]
    if filter_governs is not None and not isinstance(filter_governs, str):
        raise ValueError("Config field 'filter_governs' must be null or string")
    if isinstance(filter_governs, str):
        filter_governs = ri._validate_filter_governs(filter_governs)

    dataset_path_val = raw["dataset_path"]
    index_path_val = raw["index_path"]
    if not isinstance(dataset_path_val, str) or not dataset_path_val.strip():
        raise ValueError("Config field 'dataset_path' must be a non-empty string")
    if not isinstance(index_path_val, str) or not index_path_val.strip():
        raise ValueError("Config field 'index_path' must be a non-empty string")

    dataset_path = _resolve_path(dataset_path_val)
    index_path = _resolve_path(index_path_val)
    if not dataset_path.exists():
        raise ValueError(f"Dataset file does not exist: {dataset_path}")

    return EvalConfig(
        dataset_path=dataset_path,
        index_path=index_path,
        top_k=top_k,
        filter_governs=filter_governs,
        seed=seed,
    )


def _validate_query_item(item: dict[str, Any], idx: int) -> dict[str, Any]:
    required = {"query_id", "query", "relevant_source_files", "baseline_tokens", "rag_tokens"}
    missing = sorted([key for key in required if key not in item])
    if missing:
        raise ValueError(f"Dataset query #{idx + 1} missing keys: {', '.join(missing)}")

    query_id = item["query_id"]
    query = item["query"]
    relevant = item["relevant_source_files"]
    baseline_tokens = item["baseline_tokens"]
    rag_tokens = item["rag_tokens"]

    if not isinstance(query_id, str) or not query_id.strip():
        raise ValueError(f"Dataset query #{idx + 1}: 'query_id' must be a non-empty string")
    if not isinstance(query, str) or not query.strip():
        raise ValueError(f"Dataset query #{idx + 1}: 'query' must be a non-empty string")

    if not isinstance(relevant, list) or not relevant:
        raise ValueError(f"Dataset query #{idx + 1}: 'relevant_source_files' must be a non-empty list")

    relevant_files: list[str] = []
    for value in relevant:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Dataset query #{idx + 1}: 'relevant_source_files' entries must be non-empty strings")
        relevant_files.append(value.strip())

    if not isinstance(baseline_tokens, int) or baseline_tokens <= 0:
        raise ValueError(f"Dataset query #{idx + 1}: 'baseline_tokens' must be a positive integer")
    if not isinstance(rag_tokens, int) or rag_tokens < 0:
        raise ValueError(f"Dataset query #{idx + 1}: 'rag_tokens' must be a non-negative integer")
    if rag_tokens > baseline_tokens:
        raise ValueError(f"Dataset query #{idx + 1}: 'rag_tokens' cannot exceed 'baseline_tokens'")

    return {
        "query_id": query_id.strip(),
        "query": query.strip(),
        "relevant_source_files": sorted(set(relevant_files)),
        "baseline_tokens": baseline_tokens,
        "rag_tokens": rag_tokens,
    }


def load_dataset(dataset_path: Path) -> dict[str, Any]:
    """Load and validate dataset JSON."""
    raw = _load_json(dataset_path)
    required = {"dataset_id", "version", "queries"}
    missing = sorted([key for key in required if key not in raw])
    if missing:
        raise ValueError(f"Dataset missing required keys: {', '.join(missing)}")

    dataset_id = raw["dataset_id"]
    version = raw["version"]
    queries = raw["queries"]

    if not isinstance(dataset_id, str) or not dataset_id.strip():
        raise ValueError("Dataset field 'dataset_id' must be a non-empty string")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("Dataset field 'version' must be a non-empty string")
    if not isinstance(queries, list) or not queries:
        raise ValueError("Dataset field 'queries' must be a non-empty list")

    validated: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for idx, item in enumerate(queries):
        if not isinstance(item, dict):
            raise ValueError(f"Dataset query #{idx + 1} must be an object")
        query_item = _validate_query_item(item, idx)
        if query_item["query_id"] in seen_ids:
            raise ValueError(f"Duplicate query_id in dataset: {query_item['query_id']}")
        seen_ids.add(query_item["query_id"])
        validated.append(query_item)

    # Force deterministic processing order.
    validated.sort(key=lambda item: item["query_id"])

    return {
        "dataset_id": dataset_id.strip(),
        "version": version.strip(),
        "queries": validated,
    }


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    if pct <= 0:
        return min(values)
    if pct >= 100:
        return max(values)

    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]

    rank = (pct / 100.0) * (len(ordered) - 1)
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    fraction = rank - low
    return ordered[low] + (ordered[high] - ordered[low]) * fraction


def _round3(value: float) -> float:
    return round(value, 3)


def _build_run_id(dataset_id: str, dataset_version: str, config: EvalConfig) -> str:
    seed_data = {
        "dataset_id": dataset_id,
        "dataset_version": dataset_version,
        "top_k": config.top_k,
        "filter_governs": config.filter_governs,
        "seed": config.seed,
    }
    digest = hashlib.sha256(json.dumps(seed_data, sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:16]


def _run_retrieval_pass(config: EvalConfig, dataset: dict[str, Any]) -> dict[str, Any]:
    per_query: list[dict[str, Any]] = []
    recall_values: list[float] = []
    precision_values: list[float] = []
    latency_ms_values: list[float] = []
    token_savings_values: list[float] = []
    error_count = 0

    for item in dataset["queries"]:
        query = item["query"]
        query_id = item["query_id"]
        relevant = set(item["relevant_source_files"])

        started = time.perf_counter()
        error_message: str | None = None
        retrieved_files: list[str] = []

        try:
            result = ri.query_index(
                query,
                top_k=config.top_k,
                filter_governs=config.filter_governs,
                db_path=config.index_path,
            )
            retrieved_files = [row["source_file"] for row in result.get("results", [])]
        except (ri.RagIndexError, ValueError) as exc:
            error_count += 1
            error_message = str(exc)

        elapsed_ms = (time.perf_counter() - started) * 1000.0
        latency_ms_values.append(elapsed_ms)

        retrieved_set = set(retrieved_files)
        true_positives = len(relevant.intersection(retrieved_set))
        recall = true_positives / len(relevant)
        precision = true_positives / float(config.top_k)

        baseline_tokens = item["baseline_tokens"]
        rag_tokens = item["rag_tokens"]
        token_savings_pct = ((baseline_tokens - rag_tokens) / baseline_tokens) * 100.0

        recall_values.append(recall)
        precision_values.append(precision)
        token_savings_values.append(token_savings_pct)

        per_query.append(
            {
                "query_id": query_id,
                "query": query,
                "relevant_source_files": sorted(relevant),
                "retrieved_source_files": sorted(retrieved_set),
                "true_positive_count": true_positives,
                "retrieved_count": len(retrieved_set),
                "recall_at_k": _round3(recall),
                "precision_at_k": _round3(precision),
                "latency_ms": _round3(elapsed_ms),
                "token_savings_pct": _round3(token_savings_pct),
                "error": error_message,
            }
        )

    total = len(dataset["queries"])
    return {
        "queries": per_query,
        "aggregate": {
            "recall_at_k": _round3(statistics.mean(recall_values)),
            "precision_at_k": _round3(statistics.mean(precision_values)),
            "latency_p50_ms": _round3(_percentile(latency_ms_values, 50)),
            "latency_p95_ms": _round3(_percentile(latency_ms_values, 95)),
            "error_rate_pct": _round3((error_count / float(total)) * 100.0),
            "token_savings_median_pct": _round3(statistics.median(token_savings_values)),
        },
    }


def _assert_deterministic_retrieval_metrics(config: EvalConfig, dataset: dict[str, Any]) -> None:
    first = _run_retrieval_pass(config, dataset)
    second = _run_retrieval_pass(config, dataset)

    first_pairs = [
        (row["query_id"], row["recall_at_k"], row["precision_at_k"], row["true_positive_count"])
        for row in first["queries"]
    ]
    second_pairs = [
        (row["query_id"], row["recall_at_k"], row["precision_at_k"], row["true_positive_count"])
        for row in second["queries"]
    ]
    if first_pairs != second_pairs:
        raise BeirLiteEvalError("Determinism check failed: per-query retrieval metrics changed across reruns")

    first_agg = first["aggregate"]
    second_agg = second["aggregate"]
    if (
        first_agg["recall_at_k"] != second_agg["recall_at_k"]
        or first_agg["precision_at_k"] != second_agg["precision_at_k"]
    ):
        raise BeirLiteEvalError("Determinism check failed: aggregate retrieval metrics changed across reruns")


def _load_output_schema() -> dict[str, Any]:
    schema = _load_json(OUTPUT_SCHEMA_PATH)
    if not isinstance(schema.get("required"), list):
        raise ValueError("Output schema must include a 'required' list")
    return schema


def _validate_output_schema(payload: dict[str, Any], schema: dict[str, Any]) -> None:
    required_fields = schema.get("required", [])
    missing = [key for key in required_fields if key not in payload]
    if missing:
        raise BeirLiteEvalError(f"Output payload missing required schema fields: {', '.join(missing)}")


def run_evaluation(
    config_path: Path,
    *,
    run_id_override: str | None = None,
    timestamp_override: str | None = None,
    assert_deterministic: bool = False,
) -> dict[str, Any]:
    """Execute BEIR-lite evaluation and return machine-readable payload."""
    config = load_config(config_path)
    # Seed global RNG so the config seed has concrete semantics for any stochastic extensions.
    random.seed(config.seed)
    dataset = load_dataset(config.dataset_path)

    if assert_deterministic:
        _assert_deterministic_retrieval_metrics(config, dataset)

    run = _run_retrieval_pass(config, dataset)
    aggregate = run["aggregate"]
    timestamp = timestamp_override or datetime.now(timezone.utc).isoformat()
    run_id = run_id_override or _build_run_id(dataset["dataset_id"], dataset["version"], config)

    payload = {
        "schema_version": "beir-lite-eval-v1",
        "timestamp": timestamp,
        "run_id": run_id,
        "dataset_id": dataset["dataset_id"],
        "dataset_version": dataset["version"],
        "top_k": config.top_k,
        "filter_governs": config.filter_governs,
        "seed": config.seed,
        "index_path": str(config.index_path),
        "recall_at_5": aggregate["recall_at_k"] if config.top_k == 5 else None,
        "precision_at_5": aggregate["precision_at_k"] if config.top_k == 5 else None,
        "latency_p50_ms": aggregate["latency_p50_ms"],
        "latency_p95_ms": aggregate["latency_p95_ms"],
        "error_rate_pct": aggregate["error_rate_pct"],
        "token_savings_median_pct": aggregate["token_savings_median_pct"],
        "aggregate": {
            "recall_at_k": aggregate["recall_at_k"],
            "precision_at_k": aggregate["precision_at_k"],
            "k": config.top_k,
        },
        "queries": run["queries"],
    }

    schema = _load_output_schema()
    _validate_output_schema(payload, schema)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run BEIR-lite retrieval evaluation and instrumentation")
    parser.add_argument("--config", required=True, help="Path to BEIR-lite config JSON")
    parser.add_argument("--output", help="Optional output JSON path")
    parser.add_argument("--assert-deterministic", action="store_true")
    parser.add_argument("--run-id")
    parser.add_argument("--timestamp")

    args = parser.parse_args(argv)

    try:
        config_path = Path(args.config)
        payload = run_evaluation(
            config_path,
            run_id_override=args.run_id,
            timestamp_override=args.timestamp,
            assert_deterministic=args.assert_deterministic,
        )

        if args.output:
            output_path = Path(args.output)
            if not output_path.is_absolute():
                output_path = REPO_ROOT / output_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        else:
            print(json.dumps(payload, indent=2))
        return 0
    except (ValueError, BeirLiteEvalError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except (ri.RagIndexError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
