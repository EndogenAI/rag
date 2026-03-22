#!/usr/bin/env python3
"""
Adaptive K-Selector — Parameter-aware RAG retrieval dispatcher.

Purpose
-------
Maps model parameter counts to optimal retrieval 'k' values based on
"Reasoning Density" research findings (Study 2a). Smaller models (<1.5B)
benefit from higher density (k=20), while larger models (>8B) require
aggressive noise reduction (k=5).

Tiered Logic
------------
- Tier 1: Params < 1.5B  -> k=20 (Reasoning Density Optimization)
- Tier 2: 1.5B - 8B      -> k=10 (Baseline / Balanced)
- Tier 3: Params > 8B    -> k=5  (Noise Reduction Strategy)

Usage
-----
# Get k for a specific model name
uv run python scripts/adaptive_k_selector.py ollama/llama3.1:8b

# Get k for a raw parameter count
uv run python scripts/adaptive_k_selector.py --params 1.5

# Example in sub-process
K_VAL=$(uv run python scripts/adaptive_k_selector.py qwen2.5:1.5b)
"""

import argparse
import re
import sys


def extract_parameter_count(model_name: str) -> float:
    """
    Extracts parameter count in Billions from model names.
    Matches patterns like '1.5b', '8b', '360m', '70b'.
    """
    # Normalize to lowercase
    model_name = model_name.lower()

    # regex to find patterns like 1.5b, 8b, 360m
    match = re.search(r"([0-9.]+)([bm])", model_name)
    if not match:
        return 0.0

    val_str, unit = match.groups()
    try:
        val = float(val_str)
    except ValueError:
        return 0.0

    if unit == "m":
        return val / 1000.0  # Convert Millions to Billions
    return val


def select_k(params: float) -> int:
    """
    Dispatches k based on parameter count tiers.

    Tier 1 (Dense): < 1.5B -> 20
    Tier 2 (Mid): 1.5B to 8B -> 10
    Tier 3 (Large): > 8B -> 5
    """
    if params == 0.0:
        return 10  # Default fallback

    if params < 1.5:
        return 20
    elif params <= 8.0:
        return 10
    else:
        return 5


def main():
    parser = argparse.ArgumentParser(description="Adaptive K-Selector for RAG")
    parser.add_argument("model", nargs="?", help="Model name (e.g. qwen2.5:1.5b)")
    parser.add_argument("--params", type=float, help="Explicit parameter count in Billions")

    args = parser.parse_args()

    if args.params is not None:
        params = args.params
    elif args.model:
        params = extract_parameter_count(args.model)
    else:
        parser.print_help()
        sys.exit(1)

    k = select_k(params)
    print(k)


if __name__ == "__main__":
    main()
