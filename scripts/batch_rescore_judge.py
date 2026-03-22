#!/usr/bin/env python3
"""Batch rescore tier-2 RAG benchmark responses using LLM-as-judge evaluation.

This script rescores existing JSONL benchmark artifacts with phi3:mini judge model
after the sweep completes, enabling RAM-efficient sweeps that defer judge evaluation.

Usage:
    # Rescore all recent artifacts in study-2a (default)
    uv run python scripts/batch_rescore_judge.py

    # Rescore specific study
    uv run python scripts/batch_rescore_judge.py --study study-2b

    # Dry-run mode (show what would be rescored)
    uv run python scripts/batch_rescore_judge.py --dry-run

    # Rescore and overwrite original files
    uv run python scripts/batch_rescore_judge.py --in-place

Workflow:
    1. Read all JSONL artifacts from data/benchmark-results/<study>/
    2. Load test cases from data/rag-benchmarks.yml
    3. Load phi3:mini judge model once
    4. For each tier-2 query response:
       - Call evaluate_with_judge() to get LLM-as-judge score
       - Update score field (preserve all other fields)
    5. Write rescored artifacts to *-rescored.jsonl (or overwrite if --in-place)

RAM efficiency:
    - Judge model loaded once for all responses (vs. per-query during sweep)
    - Peak RAM: phi3:mini (2.2 GB) only, no test models
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Iterator

import yaml

# Import from benchmark_rag.py
try:
    from benchmark_rag import evaluate_with_judge, BENCHMARK_DATA
except ImportError:
    print("ERROR: Could not import from benchmark_rag.py. Run from repo root.")
    sys.exit(1)

ARTIFACT_ROOT = Path("data/benchmark-results")


def load_test_cases(tier: int = None) -> dict:
    """Load test cases from YAML config, indexed by query_id.

    Args:
        tier: Optional tier filter (1 or 2)

    Returns:
        Dict mapping query_id -> test_case dict
    """
    with open(BENCHMARK_DATA, "r") as f:
        data = yaml.safe_load(f)
        all_tests = data.get("test_cases", data) if isinstance(data, dict) else data

    test_cases = [t for t in all_tests if tier is None or t["tier"] == tier]
    return {tc["id"]: tc for tc in test_cases}


def iter_jsonl_artifacts(study_id: str, pattern: str = "*.jsonl") -> Iterator[Path]:
    """Iterate over JSONL artifact files in a study directory.

    Args:
        study_id: Study identifier (e.g., "study-2a")
        pattern: Glob pattern for JSONL files (default: *.jsonl)

    Yields:
        Path objects for each matching JSONL file
    """
    study_dir = ARTIFACT_ROOT / study_id
    if not study_dir.exists():
        print(f"WARNING: Study directory not found: {study_dir}")
        return

    for path in sorted(study_dir.glob(pattern)):
        # Skip already-rescored files
        if "-rescored.jsonl" in path.name:
            continue
            
        # Skip original files if a rescored sibling already exists
        rescored_path = path.with_name(f"{path.stem}-rescored.jsonl")
        if rescored_path.exists():
            continue
            
        yield path


def rescore_artifact(
    artifact_path: Path,
    test_cases: dict,
    judge_model: str = "ollama/phi3:mini",
    dry_run: bool = False,
    in_place: bool = False,
) -> tuple[int, int]:
    """Rescore tier-2 queries in a single JSONL artifact file.

    Args:
        artifact_path: Path to JSONL artifact file
        test_cases: Dict mapping query_id -> test_case
        judge_model: LiteLLM model string for judge
        dry_run: If True, only count queries without rescoring
        in_place: If True, overwrite original file; else write to *-rescored.jsonl

    Returns:
        (total_queries, rescored_count) tuple
    """
    rescored_lines = []
    total_queries = 0
    rescored_count = 0

    with open(artifact_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            total_queries += 1
            query_detail = json.loads(line)
            query_id = query_detail.get("query_id")
            test_case = test_cases.get(query_id)

            # Skip if not tier-2 or test case not found
            if not test_case or test_case.get("tier") != 2:
                rescored_lines.append(query_detail)
                continue

            # Extract response and retrieved_chunks
            response = query_detail.get("response", "")
            retrieved_chunks = query_detail.get("retrieved_chunks", [])

            if dry_run:
                rescored_count += 1
                rescored_lines.append(query_detail)
                continue

            # Call judge to get new score
            try:
                judge_result = evaluate_with_judge(
                    answer=response, test_case=test_case, judge_model=judge_model, retrieved_chunks=retrieved_chunks
                )

                # Update score field (preserve all other fields)
                old_score = query_detail.get("score", 0.0)
                new_score = judge_result.get("overall_score", 0.0)
                query_detail["score"] = round(new_score, 3)

                # Add judge metadata
                query_detail["judge_reasoning"] = judge_result.get("judge_reasoning", "")
                query_detail["judge_preflight"] = judge_result.get("preflight_signals", {})
                query_detail["score_source"] = "llm-as-judge"
                query_detail["old_score_pattern_match"] = round(old_score, 3)

                rescored_count += 1
                print(f"  {query_id}: {old_score:.2f} → {new_score:.2f}")

            except Exception as e:
                print(f"  WARNING: Failed to rescore {query_id}: {e}")
                # Keep original on error

            rescored_lines.append(query_detail)

    # Write rescored artifact
    if not dry_run:
        if in_place:
            output_path = artifact_path
        else:
            output_path = artifact_path.with_name(artifact_path.stem + "-rescored.jsonl")

        with open(output_path, "w") as f:
            for detail in rescored_lines:
                line = json.dumps(detail, separators=(",", ":"))
                f.write(line + "\n")

        print(f"  Wrote: {output_path}")

    return total_queries, rescored_count


def main():
    parser = argparse.ArgumentParser(description="Batch rescore tier-2 RAG responses with LLM-as-judge")
    parser.add_argument("--study", default="study-2a", help="Study identifier (default: study-2a)")
    parser.add_argument(
        "--judge-model", default="ollama/phi3:mini", help="LiteLLM judge model (default: ollama/phi3:mini)"
    )
    parser.add_argument("--dry-run", action="store_true", help="Count queries without rescoring")
    parser.add_argument("--in-place", action="store_true", help="Overwrite original files (default: write *-rescored.jsonl)")
    parser.add_argument("--pattern", default="*.jsonl", help="Glob pattern for JSONL files (default: *.jsonl)")

    args = parser.parse_args()

    # Load test cases (tier-2 only)
    print(f"Loading tier-2 test cases from {BENCHMARK_DATA}...")
    test_cases = load_test_cases(tier=2)
    print(f"  Loaded {len(test_cases)} tier-2 test cases")

    # Find artifacts
    print(f"\nScanning {ARTIFACT_ROOT / args.study}/ for {args.pattern}...")
    artifacts = list(iter_jsonl_artifacts(args.study, args.pattern))
    if not artifacts:
        print(f"ERROR: No artifacts found in {ARTIFACT_ROOT / args.study}/")
        return 1

    print(f"  Found {len(artifacts)} artifact files")

    if args.dry_run:
        print("\n[DRY-RUN MODE] Would rescore:")
    else:
        print(f"\nRescoring with judge model: {args.judge_model}")

    # Rescore each artifact
    total_queries_all = 0
    rescored_count_all = 0

    for artifact_path in artifacts:
        print(f"\n{artifact_path.name}")
        total, rescored = rescore_artifact(
            artifact_path,
            test_cases,
            judge_model=args.judge_model,
            dry_run=args.dry_run,
            in_place=args.in_place,
        )
        total_queries_all += total
        rescored_count_all += rescored

    # Summary
    print("\n" + "=" * 60)
    print(f"Total queries: {total_queries_all}")
    print(f"Tier-2 rescored: {rescored_count_all}")
    if args.dry_run:
        print("\n[DRY-RUN] No files were modified. Run without --dry-run to rescore.")
    else:
        print(f"\nRescored artifacts written to: {ARTIFACT_ROOT / args.study}/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
