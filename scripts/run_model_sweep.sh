#!/usr/bin/env bash
# Run full model sweep for Study 2a (tier-2 suite)
# Usage: bash scripts/run_model_sweep.sh
#
# RAM-filtered model list (2026-03-21):
# Removed qwen:7b, mistral:7b, llama3:latest due to RAM exhaustion on 8GB systems
# See: .tmp/research-rag-stress-test-quantization/2026-03-21.md Phase 7

set -euo pipefail

# Model matrix (RAM-compatible: ≤ 5GB for 8GB system)
MODELS=(
    "ollama/qwen:0.5b"
    "ollama/qwen:1.8b"
    "ollama/qwen:4b"
    "ollama/phi3:mini"
    "ollama/llama3:8b-instruct-q4_K_M"
    "ollama/gemma2:2b"
    "ollama/tinyllama:1.1b"
    "ollama/gemma:2b"
    "ollama/orca-mini:3b"
)

TOTAL=${#MODELS[@]}

echo "=========================================="
echo "Study 2a RAM-Filtered Model Sweep"
echo "=========================================="
echo "Total models: $TOTAL (RAM-compatible only)"
echo "Tier: 2 (9 test cases per model)"
echo "Estimated time: ~20 min per model = ~3 hours total"
echo ""
echo "Excluded (RAM exhaustion on 8GB):"
echo "  - qwen:7b (4.5GB)"
echo "  - mistral:7b (4.1GB)"
echo "  - llama3:latest (~8GB)"
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
