#!/usr/bin/env python3
"""
Benchmark local RAG performance across different models using defined test suites.

Usage: uv run python scripts/benchmark_rag.py --model ollama/phi3 --tier 1

Model Lifecycle Safety (One-In, One-Out Protocol):
  Before loading any model, this script verifies no other models are pinned in RAM
  via `ollama ps`. If a model is loaded, use `ollama stop <model>` to unload it.
  On 16GB RAM systems, two concurrently-pinned models cause OOM swap or crash.
  Enable with --model-lifecycle-check (exits with code 3 if model already loaded).

Configuration Validation:
  Validates required benchmark data file exists at data/rag-benchmarks.yml.
  If missing, exits with code 1.

RAM Readiness Check:
  Requires ≥6GB available RAM before loading any model. If RAM < 6GB, exits with
  code 2. Override with --skip-ram-check (not recommended on constrained hardware).

Dry-Run Mode:
  Use --dry-run to validate configuration and pre-flight checks without running
  inference. Logs planned models, configs, and resource checks; exits 0 if valid.

Exit Codes:
  0 = success/dry-run complete
  1 = config error (missing benchmark data file)
  2 = RAM insufficient (<6GB available)
  3 = model lifecycle violation (model already loaded)
"""

import argparse
import json
import os
import platform
import subprocess
import sys
import yaml
import time
from pathlib import Path
from datetime import datetime

try:
    import psutil
except ImportError:
    psutil = None

REPO_ROOT = Path(__file__).parent.parent
BENCHMARK_DATA = REPO_ROOT / "data" / "rag-benchmarks.yml"
BENCHMARK_RESULTS = REPO_ROOT / ".cache" / "rag-benchmarks"
ARTIFACT_ROOT = REPO_ROOT / "data" / "benchmark-results"
INDEX_FILE = ARTIFACT_ROOT / "index.jsonl"

# Minimum free disk space required before benchmarking (bytes)
_MIN_FREE_DISK_BYTES = 2 * 1024 ** 3  # 2 GB headroom

# Minimum available RAM required before loading a model (bytes)
_MIN_RAM_BYTES = 6 * 1024 ** 3  # 6 GB


def check_ram_availability(min_ram_bytes: int = _MIN_RAM_BYTES, skip_check: bool = False) -> tuple[bool, str]:
    """Check available RAM meets minimum threshold.
    
    Returns:
        (is_ok, message): (True, info_msg) if OK or skipped; (False, error_msg) if insufficient.
    """
    if skip_check:
        return True, "RAM check skipped (--skip-ram-check)"
    
    if psutil is None:
        return True, "RAM check unavailable (psutil not installed)"
    
    available_bytes = psutil.virtual_memory().available
    available_gb = available_bytes / 1024 ** 3
    required_gb = min_ram_bytes / 1024 ** 3
    
    if available_bytes < min_ram_bytes:
        return False, f"Insufficient RAM: {available_gb:.1f} GB available, {required_gb:.1f} GB required"
    
    return True, f"RAM OK: {available_gb:.1f} GB available (≥{required_gb:.1f} GB required)"


def check_model_lifecycle(enforce: bool = False) -> tuple[bool, str, list[str]]:
    """Check that no Ollama models are pinned in RAM (One-In, One-Out protocol).
    
    Args:
        enforce: If True, return (False, ...) when models are loaded; if False, warn only.
    
    Returns:
        (is_ok, message, loaded_models): loaded_models is list of model names currently pinned.
    """
    try:
        result = subprocess.run(
            ["ollama", "ps"], capture_output=True, text=True, timeout=10
        )
        lines = [l for l in result.stdout.strip().splitlines() if l and not l.startswith("NAME")]
        loaded_models = [l.split()[0] for l in lines if l]  # Extract model names
        
        if loaded_models:
            model_list = ", ".join(loaded_models)
            if enforce:
                return False, f"Model lifecycle violation: {model_list} currently loaded. Run `ollama stop <model>` first.", loaded_models
            else:
                return True, f"WARNING: Models loaded: {model_list}. May cause OOM.", loaded_models
        else:
            return True, "Model lifecycle OK: no models currently loaded", []
    except FileNotFoundError:
        return True, "ollama not on PATH (daemon may be running via API)", []
    except subprocess.TimeoutExpired:
        return True, "WARNING: `ollama ps` timed out", []


def run_ollama_preflight(model_lifecycle_check: bool = False, skip_ram_check: bool = False, dry_run: bool = False):
    """Check that no Ollama models are pinned in RAM and disk space is adequate.

    Warns and optionally aborts if:
    - Any model is currently loaded (would cause OOM when a second model loads)
    - Available disk space falls below 2 GB
    - Available RAM falls below 6 GB

    See docs/toolchain/ollama.md for the full safety rationale.
    
    Args:
        model_lifecycle_check: If True, exit with code 3 if models are loaded.
        skip_ram_check: If True, skip RAM availability check.
        dry_run: If True, print all checks but don't abort.
    """
    warnings = []
    errors = []

    # 1. Model Lifecycle Check
    lifecycle_ok, lifecycle_msg, loaded_models = check_model_lifecycle(enforce=model_lifecycle_check)
    if not lifecycle_ok:
        errors.append(lifecycle_msg)
    elif "WARNING" in lifecycle_msg or "loaded" in lifecycle_msg.lower():
        warnings.append(lifecycle_msg)
    else:
        print(f"✓ {lifecycle_msg}", file=sys.stderr if not dry_run else sys.stdout, flush=True)

    # 2. RAM Check
    ram_ok, ram_msg = check_ram_availability(skip_check=skip_ram_check)
    if not ram_ok:
        errors.append(ram_msg)
    else:
        print(f"✓ {ram_msg}", file=sys.stderr if not dry_run else sys.stdout, flush=True)

    # 3. Check available disk space
    try:
        stat = os.statvfs("/")
        free_bytes = stat.f_bavail * stat.f_frsize
        free_gb = free_bytes / 1024 ** 3
        if free_bytes < _MIN_FREE_DISK_BYTES:
            warnings.append(
                f"WARNING: Only {free_gb:.1f} GB free on /. "
                "Benchmarking requires ≥2 GB headroom beyond the model size. "
                "Run `ollama rm <model>` to free disk before pulling or benchmarking."
            )
        else:
            print(f"✓ Disk OK: {free_gb:.1f} GB free (≥2 GB required)", file=sys.stderr if not dry_run else sys.stdout, flush=True)
    except OSError:
        pass  # non-POSIX platform; skip

    for w in warnings:
        print(w, file=sys.stderr, flush=True)

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr, flush=True)
        if not dry_run:
            if not ram_ok:
                sys.exit(2)  # RAM error
            if not lifecycle_ok:
                sys.exit(3)  # Model lifecycle error

    if warnings and not dry_run:
        print(
            "Preflight warnings above. Proceeding — fix them if you see OOM or "
            "unexplained latency spikes.",
            file=sys.stderr,
            flush=True,
        )

def get_machine_metadata() -> dict:
    """Collect machine metadata for benchmark reproducibility.
    
    Returns:
        Dict with machine_type, system, ram_gb, processor, python_version
    """
    metadata = {
        "machine_type": platform.machine(),  # e.g., "arm64", "x86_64"
        "system": platform.system(),  # e.g., "Darwin", "Linux", "Windows"
        "processor": platform.processor(),  # e.g., "arm"
        "python_version": platform.python_version()
    }
    
    # RAM detection (prefer psutil if available)
    if psutil is not None:
        total_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        metadata["ram_gb"] = round(total_ram_gb, 1)
    else:
        metadata["ram_gb"] = "unknown"
    
    return metadata


def run_rag_answer(query: str, model: str, top_k: int = 10, template_path: str = None) -> dict:
    """Run the rag_index.py answer command and return JSON."""
    cmd = [
        "uv", "run", "python", "scripts/rag_index.py", "answer",
        "--query", query,
        "--model", model,
        "--top-k", str(top_k),
        "--output", "json"
    ]
    if template_path:
        cmd.extend(["--template-path", template_path])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        return {"ok": False, "error": e.stderr}
    except json.JSONDecodeError:
        return {"ok": False, "error": "Invalid JSON output"}

def evaluate_response(answer: str, test_case: dict) -> dict:
    """Evaluate a RAG answer against expected patterns and entities."""
    metrics = {
        "entity_recall": 0.0,
        "pattern_match": 0.0,
        "source_fidelity": 0.0,
        "hallucination_detected": False,
        "overall_score": 0.0
    }
    
    # 1. Entity Recall
    entities = test_case.get("expected_entities", [])
    if entities:
        hits = sum(1 for e in entities if e.lower() in answer.lower())
        metrics["entity_recall"] = hits / len(entities)
        
    # 2. Pattern Match
    patterns = test_case.get("expected_patterns", [])
    if patterns:
        hits = sum(1 for p in patterns if p.lower() in answer.lower())
        metrics["pattern_match"] = hits / len(patterns)
        
    # 3. Source Fidelity
    source = test_case.get("expected_source", "")
    if source and source.lower() in answer.lower():
        metrics["source_fidelity"] = 1.0
        
    # 4. Hallucination Detection (Simple heuristic)
    hallucination_keys = ["Batman", "Amelia Harper", "fictional", "invented"]
    if any(k.lower() in answer.lower() for k in hallucination_keys):
        metrics["hallucination_detected"] = True
        
    # Weighted Average
    weights = {"entity_recall": 0.4, "pattern_match": 0.4, "source_fidelity": 0.2}
    metrics["overall_score"] = (
        metrics["entity_recall"] * weights["entity_recall"] +
        metrics["pattern_match"] * weights["pattern_match"] +
        metrics["source_fidelity"] * weights["source_fidelity"]
    )
    if metrics["hallucination_detected"]:
        metrics["overall_score"] *= 0.5 # Penalty
        
    return metrics


def detect_study_id(model: str, tier: int = None, localization: str = None) -> str:
    """Auto-detect study identifier based on research purpose.
    
    Study mapping:
    - study-2a: Local Model Landscape for RAG Synthesis (model selection/evaluation)
      All model benchmarks default here unless localization variant is specified
    
    - study-2b: Token Savings from RAG Component Localization (efficiency measurement)
      Activated when localization configuration is specified (future: --localization flag)
      Uses Study 2a's recommended model subset
    
    Args:
        model: LiteLLM model string (e.g., "ollama/phi3" or "ollama/qwen:0.5b")
        tier: Optional tier filter (1 or 2)
        localization: Optional localization variant (e.g., "r-local", "ra-local", "fully-local")
    
    Returns:
        Study identifier string ("study-2a" or "study-2b")
    """
    # Study 2b: Token savings measurement (requires explicit localization configuration)
    if localization and localization in ["r-local", "ra-local", "fully-local", "fully-remote"]:
        return "study-2b"
    
    # Study 2a: Model landscape exploration (default for all basic benchmarking)
    return "study-2a"


def write_jsonl_artifacts(
    model: str,
    study_id: str,
    test_cases: list,
    results: dict,
    query_details: list
) -> tuple[Path, Path]:
    """Write structured JSONL artifacts for individual model run and update index.
    
    Args:
        model: LiteLLM model string
        study_id: Study identifier (e.g., "study-2a")
        test_cases: List of test case dicts
        results: Aggregate results dict
        query_details: List of per-query detail dicts (query, response, latency, chunks, etc.)
    
    Returns:
        (model_report_path, index_path): Paths to written artifacts
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    # Create study directory
    study_dir = ARTIFACT_ROOT / study_id
    study_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate model report filename
    model_tag = model.replace("ollama/", "").replace("/", "-").replace(":", "-")
    report_filename = f"{model_tag}-{timestamp.replace(':', '-')}.jsonl"
    report_path = study_dir / report_filename
    
    # Write individual model report (one line per query)
    with open(report_path, "w") as f:
        for detail in query_details:
            line = json.dumps(detail, separators=(',', ':'))
            f.write(line + "\n")
    
    # Append to index file
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    index_entry = {
        "timestamp": timestamp,
        "model": model,
        "study": study_id,
        "phase": results.get("tier"),
        "score_avg": results.get("average_score", 0.0),
        "latency_avg_sec": sum(d.get("latency_sec", 0) for d in query_details) / len(query_details) if query_details else 0,
        "queries_total": len(test_cases),
        "queries_passed": sum(1 for d in query_details if d.get("score", 0) > 0.5),
        "report_path": f"{study_id}/{report_filename}"
    }
    with open(INDEX_FILE, "a") as f:
        line = json.dumps(index_entry, separators=(',', ':'))
        f.write(line + "\n")
    
    return report_path, INDEX_FILE

def main():
    parser = argparse.ArgumentParser(description="Benchmark RAG models")
    parser.add_argument("--model", required=True, help="LiteLLM model string (e.g. ollama/phi3)")
    parser.add_argument("--tier", type=int, choices=[1, 2], help="Filter by test tier")
    parser.add_argument("--study-id", help="Study identifier (e.g., study-2a, study-2b). Auto-detected if not specified.")
    parser.add_argument("--localization", choices=["fully-remote", "r-local", "ra-local", "fully-local"], 
                        help="Localization configuration for Study 2b token savings measurement")
    parser.add_argument("--top-k", type=int, default=10, help="Retrieval top-k")
    parser.add_argument("--template-path", help="Path to custom prompt template")
    parser.add_argument("--governance-boost-off", action="store_true", help="Disable governance boost in retrieval")
    parser.add_argument("--output-json", action="store_true", help="Print result as JSON")
    parser.add_argument("--dry-run", action="store_true", help="Validate config and run pre-flight checks without inference")
    parser.add_argument("--model-lifecycle-check", action="store_true", help="Enforce One-In, One-Out: exit if models already loaded")
    parser.add_argument("--skip-ram-check", action="store_true", help="Skip 6GB RAM requirement check (not recommended)")
    args = parser.parse_args()
    
    if not BENCHMARK_DATA.exists():
        print(f"ERROR: Benchmark data missing at {BENCHMARK_DATA}")
        return 1

    run_ollama_preflight(
        model_lifecycle_check=args.model_lifecycle_check,
        skip_ram_check=args.skip_ram_check,
        dry_run=args.dry_run
    )
    
    # Auto-detect study ID if not provided
    study_id = args.study_id or detect_study_id(args.model, args.tier, args.localization)
        
    with open(BENCHMARK_DATA, "r") as f:
        data = yaml.safe_load(f)
        all_tests = data.get("test_cases", data) if isinstance(data, dict) else data
        
    test_cases = [t for t in all_tests if args.tier is None or t["tier"] == args.tier]
    
    if args.dry_run:
        print(f"\n=== DRY RUN MODE ===")
        print(f"Model: {args.model}")
        print(f"Study ID: {study_id}")
        print(f"Tier filter: {args.tier or 'all'}")
        print(f"Top-k: {args.top_k}")
        print(f"Template: {args.template_path or 'default'}")
        print(f"Governance boost: {'OFF' if args.governance_boost_off else 'ON'}")
        print(f"Test cases: {len(test_cases)}")
        print(f"\nPlanned inference calls:")
        for i, tc in enumerate(test_cases, 1):
            print(f"  {i}. [{tc['id']}] {tc['query'][:60]}...")
        print(f"\nArtifact output:")
        print(f"  Model report: data/benchmark-results/{study_id}/<model>-<timestamp>.jsonl")
        print(f"  Index: data/benchmark-results/index.jsonl")
        print(f"\nDry-run complete — {len(test_cases)} test cases planned, 0 models loaded")
        return 0
    
    BENCHMARK_RESULTS.mkdir(parents=True, exist_ok=True)
    results = {
        "timestamp": datetime.now().isoformat(),
        "model": args.model,
        "tier": args.tier,
        "top_k": args.top_k,
        "benchmarks": []
    }
    
    # Collect machine metadata once at the start of benchmarking
    machine_metadata = get_machine_metadata()
    
    query_details = []  # Collect detailed per-query results for JSONL artifacts
    total_score = 0
    print(f"Benchmarking {args.model} on {len(test_cases)} cases (study: {study_id})...")
    
    for tc in test_cases:
        print(f" - Running '{tc['id']}'...", flush=True)
        start_time = time.time()
        payload = run_rag_answer(tc["query"], args.model, args.top_k, args.template_path)
        duration = time.time() - start_time
        
        # Log basic status regardless of success
        if not payload.get("ok"):
            print(f"   [FAILED] {payload.get('error')}", flush=True)
        
        answer = payload.get("answer", "")
        metrics = evaluate_response(answer, tc)
        metrics["latency_sec"] = duration
        metrics["id"] = tc["id"]
        
        print(f"   Latency: {duration:.2f}s | Score: {metrics['overall_score']:.2f}", flush=True)
        
        results["benchmarks"].append(metrics)
        total_score += metrics["overall_score"]
        
        # Collect detailed query info for JSONL artifact
        # Note: rag_index.py answer_query returns retrieval.sources (file list),
        # not full chunk details. retrieved_chunks will be source files only until
        # answer_query is enhanced to return full chunk metadata.
        retrieval_data = payload.get("retrieval", {})
        retrieved_sources = retrieval_data.get("sources", [])
        
        # Format as list of source filenames (placeholder until full chunks available)
        chunk_refs = retrieved_sources if isinstance(retrieved_sources, list) else []
        
        query_detail = {
            "query_id": tc["id"],
            "query": tc["query"],
            "response": answer,
            "latency_sec": round(duration, 2),
            "retrieved_chunks": chunk_refs,
            "score": round(metrics["overall_score"], 3),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model_metadata": {
                "tag": args.model,
                "size_params": "unknown",  # Could be extracted from model name if needed
                "quantization": "default",
                "ollama_version": "unknown"
            },
            "machine_metadata": machine_metadata
        }
        query_details.append(query_detail)

    avg_score = total_score / len(test_cases) if test_cases else 0
    results["average_score"] = avg_score
    print(f"\nFinal Average Score: {avg_score:.2f}", flush=True)
    
    # Write existing JSON output (backward compat)
    filename = f"bench_{args.model.replace('/', '_')}_t{args.tier or 'all'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path = BENCHMARK_RESULTS / filename
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved results to {out_path}")
    
    # Write new JSONL artifacts
    report_path, index_path = write_jsonl_artifacts(
        args.model,
        study_id,
        test_cases,
        results,
        query_details
    )
    print(f"JSONL artifacts written:")
    print(f"  Model report: {report_path}")
    print(f"  Index updated: {index_path}")
    
    if args.output_json:
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
