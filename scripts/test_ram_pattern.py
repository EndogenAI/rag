#!/usr/bin/env python3
"""
Test RAM consumption pattern across multiple queries without model unloading.

Usage: uv run python scripts/test_ram_pattern.py --model ollama/phi3:mini --num-queries 4

This helps answer: Does RAM stabilize or degrade when the model stays loaded?
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

try:
    import psutil
except ImportError:
    print("ERROR: psutil required. Run: uv pip install psutil")
    sys.exit(1)

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from rag_index import answer_query


def get_ram_gb():
    """Return available RAM in GB."""
    mem = psutil.virtual_memory()
    return mem.available / (1024**3)


def check_model_loaded(model_name):
    """Check if model is currently loaded via ollama ps."""
    try:
        result = subprocess.run(
            ["ollama", "ps"],
            capture_output=True,
            text=True,
            timeout=5
        )
        # Extract model tag without ollama/ prefix
        tag = model_name.replace("ollama/", "")
        return tag in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def main():
    parser = argparse.ArgumentParser(description="Test RAM pattern across queries")
    parser.add_argument("--model", required=True, help="Model to test (e.g., ollama/phi3:mini)")
    parser.add_argument("--num-queries", type=int, default=4, help="Number of queries to run")
    parser.add_argument("--cooldown", type=int, default=2, 
                        help="Cooldown seconds between queries (default: 2, use 0 to disable)")
    args = parser.parse_args()

    print(f"Testing RAM pattern: {args.model} across {args.num_queries} queries")
    print(f"Cooldown between queries: {args.cooldown}s")
    print("=" * 70)

    # Test queries (reuse from benchmark tier-2)
    queries = [
        "If I'm working on a research task, which agent should I delegate to, and what tools does that agent have access to?",
        "I need to create a new session scratchpad and write an encoding checkpoint. What skills or procedures should I follow, and what script do I run?",
        "Can a subagent commit directly to the repository if the Review agent has approved their changes?",
        "The Research Scout agent wants to fetch an external URL. According to its posture, is it allowed to use the terminal tool?"
    ]

    # Baseline: Unload all models
    print("\n🧹 Pre-test cleanup...")
    subprocess.run(["ollama", "stop", args.model.replace("ollama/", "")], 
                   capture_output=True, timeout=10)
    time.sleep(2)
    
    baseline_ram = get_ram_gb()
    print(f"   Baseline RAM (no models loaded): {baseline_ram:.1f} GB\n")

    # Run queries and measure RAM after each
    ram_immediate = []  # RAM immediately after query
    ram_after_cooldown = []  # RAM after cooldown period
    
    for i, query in enumerate(queries[:args.num_queries], 1):
        print(f"Query {i}: {query[:60]}...")
        
        # Check if model is loaded before query
        was_loaded = check_model_loaded(args.model)
        print(f"   Model loaded before query? {was_loaded}")
        
        # Run query
        start = time.time()
        result = answer_query(query, model=args.model, top_k=5)
        duration = time.time() - start
        
        success = result.get("ok", False)
        print(f"   Query completed: {success} ({duration:.1f}s)")
        
        # Measure RAM immediately after query
        ram_now = get_ram_gb()
        ram_immediate.append(ram_now)
        print(f"   RAM immediately after query: {ram_now:.1f} GB")
        
        # Cooldown period
        if args.cooldown > 0:
            print(f"   Cooling down for {args.cooldown}s...")
            time.sleep(args.cooldown)
            
            # Measure RAM after cooldown
            ram_cooled = get_ram_gb()
            ram_after_cooldown.append(ram_cooled)
            
            # Check if model is still loaded
            is_loaded = check_model_loaded(args.model)
            print(f"   Model still loaded after cooldown? {is_loaded}")
            print(f"   RAM after cooldown: {ram_cooled:.1f} GB")
            
            # Calculate delta from immediate measurement
            cooldown_delta = ram_cooled - ram_now
            if abs(cooldown_delta) > 0.1:
                print(f"   Cooldown effect: {cooldown_delta:+.1f} GB")
        else:
            # No cooldown - just copy immediate value
            ram_after_cooldown.append(ram_now)
            time.sleep(1)  # Brief pause for stability
        
        # Calculate delta from baseline
        delta = ram_after_cooldown[-1] - baseline_ram
        print(f"   Delta from baseline: {delta:+.1f} GB\n")

    # Analysis
    print("=" * 70)
    print("RESULTS:")
    print(f"  Baseline (no model): {baseline_ram:.1f} GB")
    
    for i in range(len(ram_immediate)):
        delta_from_baseline = ram_after_cooldown[i] - baseline_ram
        delta_from_prev = (ram_after_cooldown[i] - ram_after_cooldown[i-1]) if i > 0 else 0
        
        if args.cooldown > 0:
            cooldown_effect = ram_after_cooldown[i] - ram_immediate[i]
            print(f"  Query {i+1}: {ram_immediate[i]:.1f} GB → {ram_after_cooldown[i]:.1f} GB "
                  f"(cooldown: {cooldown_effect:+.1f} GB, baseline: {delta_from_baseline:+.1f} GB)")
        else:
            print(f"  Query {i+1}: {ram_immediate[i]:.1f} GB "
                  f"(baseline: {delta_from_baseline:+.1f} GB, prev: {delta_from_prev:+.1f} GB)")
    
    print("\nPATTERN ANALYSIS:")
    if len(ram_after_cooldown) > 1:
        # Check if RAM is stable (variance < 0.2 GB)
        variance = max(ram_after_cooldown) - min(ram_after_cooldown)
        if variance < 0.2:
            print(f"  ✅ STABLE: RAM variance {variance:.2f} GB < 0.2 GB")
            print("  → Model stays loaded, no accumulation detected")
            print("  → Unloading between queries is WASTEFUL")
        else:
            # Check if RAM is decreasing (accumulation)
            trend = ram_after_cooldown[-1] - ram_after_cooldown[0]
            if trend < -0.3:
                print(f"  ⚠️  DEGRADING: RAM decreased {-trend:.1f} GB from Q1 to Q{len(ram_after_cooldown)}")
                print("  → Something is consuming RAM across queries")
                print("  → Auto-unload between queries is NECESSARY")
            else:
                print(f"  📊 VARIABLE: RAM variance {variance:.2f} GB (not clearly stable or degrading)")
                print("  → May depend on query complexity or system load")
    
    # Cooldown effectiveness analysis
    if args.cooldown > 0 and len(ram_immediate) > 0:
        print("\nCOOLDOWN EFFECTIVENESS:")
        cooldown_effects = [ram_after_cooldown[i] - ram_immediate[i] 
                           for i in range(len(ram_immediate))]
        avg_cooldown_effect = sum(cooldown_effects) / len(cooldown_effects)
        max_cooldown_effect = max(cooldown_effects)
        
        if avg_cooldown_effect > 0.1:
            print(f"  ✅ HELPFUL: Avg +{avg_cooldown_effect:.2f} GB recovered per cooldown")
            print(f"  → Best recovery: +{max_cooldown_effect:.1f} GB")
            print(f"  → Cooldown period of {args.cooldown}s allows memory release")
        elif avg_cooldown_effect < -0.1:
            print(f"  ⚠️  HARMFUL: Avg {avg_cooldown_effect:.2f} GB lost per cooldown")
            print(f"  → Something consuming memory during cooldown")
        else:
            print(f"  ➡️  NEUTRAL: Avg {avg_cooldown_effect:+.2f} GB change (< 0.1 GB threshold)")
            print(f"  → Cooldown has minimal effect on RAM recovery")
            print(f"  → Consider testing longer cooldown or explicit unload")
    
    print("\nRECOMMENDATION:")
    if len(ram_after_cooldown) > 1:
        final_ram = ram_after_cooldown[-1]
        if variance < 0.2:
            print("  Keep model loaded across queries with same model.")
            print("  Only unload when switching models or at benchmark end.")
        else:
            if args.cooldown > 0 and avg_cooldown_effect > 0.1:
                print(f"  Use {args.cooldown}s cooldown between queries to allow natural memory release.")
                print("  This is more efficient than explicit unload/reload.")
            else:
                print("  Continue RAM floor monitoring + auto-unload.")
                print("  Degradation detected — current strategy is correct.")


if __name__ == "__main__":
    main()
