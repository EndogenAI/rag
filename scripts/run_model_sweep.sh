#!/usr/bin/env bash
# Run full model sweep for Study 2a (tier-2 suite)
# Usage: bash scripts/run_model_sweep.sh

set -euo pipefail

# Model matrix from docs/plans/2026-03-20-research-2a-model-landscape.md
MODELS=(
    "ollama/qwen:0.5b"
    "ollama/qwen:1.8b"
    "ollama/qwen:4b"
    "ollama/qwen:7b"
    "ollama/phi3:mini"
    "ollama/llama3:8b-instruct-q4_K_M"
    "ollama/llama3:latest"
    "ollama/gemma2:2b"
    "ollama/mistral:7b"
    "ollama/tinyllama:1.1b"
    "ollama/gemma:2b"
    "ollama/orca-mini:3b"
)

TOTAL=${#MODELS[@]}

echo "=========================================="
echo "Study 2a Full Model Sweep"
echo "=========================================="
echo "Total models: $TOTAL"
echo "Tier: 2 (9 test cases per model)"
echo "Estimated time: ~20 min per model = ~4 hours total"
echo "==========================================" 
echo ""

for i in "${!MODELS[@]}"; do
    MODEL="${MODELS[$i]}"
    MODEL_NUM=$((i + 1))
    
    echo ""
    echo "=========================================="
    echo "Model $MODEL_NUM/$TOTAL: $MODEL"
    echo "=========================================="
    
    # Ensure clean state before each model
    echo "Cleaning up any pinned models..."
    ollama ps | tail -n +2 | awk '{print $1}' | while read -r model; do
        if [ -n "$model" ]; then
            echo "  Stopping $model..."
            ollama stop "$model" || true
        fi
    done
    sleep 2
    
    # Run benchmark
    echo ""
    echo "Starting tier-2 benchmark..."
    uv run python scripts/benchmark_rag.py \
        --model "$MODEL" \
        --tier 2 \
        --no-ram-block \
        2>&1 | tee "/tmp/tier2-${MODEL//\//-}-$(date +%Y%m%d-%H%M%S).log"
    
    # Verify completion
    if [ $? -eq 0 ]; then
        echo "✓ Model $MODEL_NUM/$TOTAL complete"
    else
        echo "✗ Model $MODEL_NUM/$TOTAL FAILED (continuing to next model)"
    fi
    
    # Cleanup after each model
    echo "Cleaning up $MODEL..."
    ollama stop "${MODEL#ollama/}" || true
    sleep 3
    
    echo ""
done

echo ""
echo "=========================================="
echo "Sweep Complete!"
echo "=========================================="
echo "Results: data/benchmark-results/study-2a/"
echo "Logs: /tmp/tier2-*.log"
echo ""
echo "Next steps:"
echo "  1. Run: uv run python scripts/analyze_sweep_results.py study-2a"
echo "  2. Review: data/benchmark-results/study-2a/*.jsonl"
echo "=========================================="
