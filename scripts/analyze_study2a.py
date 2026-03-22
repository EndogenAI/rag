#!/usr/bin/env python3
"""Quick analysis of Study 2a rescored results."""

import argparse
import json
from collections import defaultdict
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Quick analysis of Study 2a rescored results.")
    parser.add_argument("--study", type=str, default="study-2a", help="Study directory name")
    parser.add_argument("--model", type=str, help="Filter by model name prefix (e.g., granite3.3-2b)")
    args = parser.parse_args()

    artifacts_dir = Path(f"data/benchmark-results/{args.study}")
    if not artifacts_dir.exists():
        print(f"Error: Directory {artifacts_dir} not found.")
        return

    pattern = f"{args.model}*-rescored.jsonl" if args.model else "*-rescored.jsonl"
    rescored_files = list(artifacts_dir.glob(pattern))

    if not rescored_files:
        print(f"No rescored artifact files found in {artifacts_dir} with pattern {pattern}\n")
        return

    print(f"Found {len(rescored_files)} rescored artifact files in {args.study}\n")

    # Aggregate by query
    query_scores = defaultdict(list)
    query_retrievals = defaultdict(list)

    for f in rescored_files:
        with open(f) as file:
            for line in file:
                data = json.loads(line)
                qid = data.get("query_id")
                score = data.get("score", 0.0)
                # Fix: retrieval data is in "retrieved_chunks" field, not "retrieval"
                retrieved_chunks = data.get("retrieved_chunks", [])
                query_scores[qid].append(score)
                query_retrievals[qid].append(len(retrieved_chunks))

    # Calculate query statistics
    query_stats = []
    total_score = 0
    total_items = 0
    for qid in sorted(query_scores.keys()):
        scores = query_scores[qid]
        retrievals = query_retrievals[qid]
        avg_score = sum(scores) / len(scores)
        total_score += sum(scores)
        total_items += len(scores)
        min_score = min(scores)
        max_score = max(scores)
        variance = max_score - min_score
        avg_sources = sum(retrievals) / len(retrievals)
        zero_retrieval_count = sum(1 for r in retrievals if r == 0)
        query_stats.append((qid, avg_score, min_score, max_score, variance, avg_sources, zero_retrieval_count))

    # Overall aggregate score
    overall_avg = total_score / total_items if total_items > 0 else 0
    print(f"OVERALL AGGREGATE SCORE: {overall_avg:.3f}\n")

    # Sort by average score (worst first)
    query_stats.sort(key=lambda x: x[1])

    print("=" * 90)
    print("WORST PERFORMING QUERIES (Bottom 5):")
    print("=" * 90)
    for qid, avg, mn, mx, var, sources, zero_ret in query_stats[:5]:
        print(f"\nQuery: {qid}")
        print(f"  Avg Score: {avg:.3f}  (range: {mn:.2f}–{mx:.2f}, variance: {var:.2f})")
        print(f"  Avg Sources: {sources:.1f}  ({zero_ret}/{len(rescored_files)} models had 0 sources)")

    print("\n" + "=" * 90)
    print("BEST PERFORMING QUERIES (Top 5):")
    print("=" * 90)
    for qid, avg, mn, mx, var, sources, zero_ret in query_stats[-5:]:
        print(f"\nQuery: {qid}")
        print(f"  Avg Score: {avg:.3f}  (range: {mn:.2f}–{mx:.2f}, variance: {var:.2f})")
        print(f"  Avg Sources: {sources:.1f}  ({zero_ret}/{len(rescored_files)} models had 0 sources)")

    print("\n" + "=" * 90)
    print("SUMMARY STATISTICS:")
    print("=" * 90)
    print(f"  • Total unique queries: {len(query_stats)}")
    print(f"  • Queries with avg score < 0.50: {sum(1 for s in query_stats if s[1] < 0.5)}")
    print(f"  • Queries with avg score ≥ 0.80: {sum(1 for s in query_stats if s[1] >= 0.8)}")
    avg_variance = sum(s[4] for s in query_stats) / len(query_stats) if len(query_stats) > 0 else 0
    print(f"  • Average variance across all queries: {avg_variance:.2f}")


if __name__ == "__main__":
    main()
