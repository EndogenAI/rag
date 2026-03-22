#!/usr/bin/env bash
# Run full model sweep for Study 2a (tier-2 suite)
# Usage: bash scripts/run_model_sweep.sh
#
# RAM-filtered model list (2026-03-21):
# Phase 7: Removed qwen:7b, mistral:7b due to RAM exhaustion on 8GB systems
# Phase 8: Added llama3:8b (non-quant), quantized variants, timing tracking
# Phase 9C: Upgraded qwen → qwen2.5, llama3 → llama3.1, added deepseek-r1 reasoning
# See: .tmp/research-rag-stress-test-quantization/2026-03-21.md

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Start timer
SWEEP_START=$(date +%s)

# Model matrix with estimated per-model time (min) and size
# Format: "model|estimated_min|size_gb|notes"
MODELS=(
    "ollama/qwen2.5:0.5b|5|0.4|baseline-fast-v2.5"
    "ollama/qwen2.5:1.5b|8|0.9|fast-v2.5"
    "ollama/qwen2.5:3b|12|1.9|moderate-v2.5"
    "ollama/phi3:mini|15|2.2|variable-latency"
    "ollama/llama3.1:8b-instruct-q4_K_M|18|4.9|quantized-proven-v3.1"
    "ollama/qwen2.5:7b-instruct-q4_K_M|22|4.4|quantized-7b-v2.5"
    "ollama/mistral:7b-instruct-q4_K_M|22|4.4|quantized-7b"
    "ollama/llama3.1:8b|25|4.7|non-quant-v3.1"
    "ollama/deepseek-r1:1.5b|10|0.9|reasoning-fast"
    "ollama/deepseek-r1:7b|20|4.1|reasoning-7b"
    "ollama/gemma2:2b|8|1.6|fast-consistent"
    "ollama/tinyllama:1.1b|5|0.6|ultralight"
    "ollama/gemma:2b|8|1.7|moderate"
    "ollama/orca-mini|8|2.0|fixed-tag"
)

TOTAL=${#MODELS[@]}

# Calculate total estimated time
TOTAL_EST_MIN=0
for model_spec in "${MODELS[@]}"; do
    EST=$(echo "$model_spec" | cut -d'|' -f2)
    TOTAL_EST_MIN=$((TOTAL_EST_MIN + EST))
done
TOTAL_EST_HOURS=$((TOTAL_EST_MIN / 60))
TOTAL_EST_REMAINING_MIN=$((TOTAL_EST_MIN % 60))

echo "=========================================="
echo "Study 2a Extended Model Sweep (LLM-as-Judge)"
echo "=========================================="
echo "Total models: $TOTAL"
echo "Tier: 2 (12 test cases per model, includes source_coverage signal)"
echo "Judge model: phi3:mini (evaluates against judge rubrics)"
echo "Estimated total time: ~${TOTAL_EST_HOURS}h ${TOTAL_EST_REMAINING_MIN}m (${TOTAL_EST_MIN} min)"
echo ""
echo "New in Phase 9C (Version Upgrades + Reasoning Models):"
echo "  + qwen → qwen2.5 (all variants: 0.5b, 1.5b, 3b, 7b-q4)"
echo "  + llama3 → llama3.1 (both 8b-q4 and non-quant)"
echo "  + deepseek-r1 reasoning models (1.5b, 7b)"
echo "  + source_coverage preflight signal active"
echo ""
echo "Phase 9A-bis infrastructure:"
echo "  + LLM-as-judge evaluation (phi3:mini) for tier-2 queries"
echo "  + Rubric-based scoring (replaces pattern_match fallback)"
echo "  + All responses saved to JSONL for later analysis"
echo ""
echo "Quantized 7B comparison:"
echo "  + llama3.1:8b-q4 vs llama3.1:8b (quantization impact)"
echo "  + qwen2.5:7b-q4, mistral:7b-q4 (proven quantized)"
echo ""
echo "Excluded (RAM exhaustion on 8GB):"
echo "  - qwen:7b (4.5GB) - full precision, swaps to disk"
echo "  - mistral:7b (4.1GB) - full precision, swaps to disk"
echo "==========================================" 
echo ""
echo "Sweep started at $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

for i in "${!MODELS[@]}"; do
    MODEL_SPEC="${MODELS[$i]}"
    MODEL=$(echo "$MODEL_SPEC" | cut -d'|' -f1)
    EST_MIN=$(echo "$MODEL_SPEC" | cut -d'|' -f2)
    SIZE_GB=$(echo "$MODEL_SPEC" | cut -d'|' -f3)
    NOTES=$(echo "$MODEL_SPEC" | cut -d'|' -f4)
    MODEL_NUM=$((i + 1))
    
    # Per-model timer
    MODEL_START=$(date +%s)
    
    echo ""
    echo "=========================================="
    echo -e "${GREEN}Model $MODEL_NUM/$TOTAL: $MODEL${NC}"
    echo "  Size: ${SIZE_GB} GB | Est: ~${EST_MIN} min | Notes: ${NOTES}"
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
    
    # Build benchmark command with LLM-as-judge for tier-2 evaluation
    BENCH_CMD="uv run python scripts/benchmark_rag.py --model \"$MODEL\" --tier 2 --no-ram-block --judge-model ollama/phi3:mini"
    
    # Extended timeout for large non-quant models
    if [[ "$MODEL" == *"llama3:8b"* ]] && [[ "$MODEL" != *"q4_K_M"* ]]; then
        echo -e "${YELLOW}⚠️  Non-quantized 8B model — extending timeout to 900s (15 min)${NC}"
        BENCH_CMD="$BENCH_CMD --timeout 900"
    fi
    
    # Run benchmark
    echo ""
    echo "Starting tier-2 benchmark..."
    eval $BENCH_CMD 2>&1 | tee "/tmp/tier2-${MODEL//\//-}-$(date +%Y%m%d-%H%M%S).log"
    
    # Calculate elapsed time for this model
    MODEL_END=$(date +%s)
    MODEL_ELAPSED=$((MODEL_END - MODEL_START))
    MODEL_ELAPSED_MIN=$((MODEL_ELAPSED / 60))
    MODEL_ELAPSED_SEC=$((MODEL_ELAPSED % 60))
    
    # Verify completion and display timing
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Model $MODEL_NUM/$TOTAL complete${NC}"
        echo -e "  Actual: ${MODEL_ELAPSED_MIN}m ${MODEL_ELAPSED_SEC}s | Est: ${EST_MIN}m | Δ: $((MODEL_ELAPSED_MIN - EST_MIN))m"
    else
        echo -e "${RED}❌ Model $MODEL_NUM/$TOTAL FAILED${NC} (continuing to next model)"
        echo -e "  Failed after ${MODEL_ELAPSED_MIN}m ${MODEL_ELAPSED_SEC}s"
        
        # Health check: Verify ollama daemon is responsive after failure
        echo "Checking ollama daemon health..."
        if ! curl -sf http://localhost:11434/ >/dev/null 2>&1; then
            echo -e "${RED}⚠️  Ollama daemon unresponsive after failure${NC}"
            echo "Attempting to recover..."
            # Try unloading all models first
            ollama ps | tail -n +2 | awk '{print $1}' | while read -r model; do
                [ -n "$model" ] && ollama stop "$model" 2>/dev/null || true
            done
            sleep 5
            # Re-check
            if ! curl -sf http://localhost:11434/ >/dev/null 2>&1; then
                echo -e "${RED}❌ Ollama daemon still unresponsive — manual intervention required${NC}"
                echo "Stopping sweep. Please restart ollama and re-run."
                exit 1
            else
                echo -e "${GREEN}✓ Ollama daemon recovered${NC}"
            fi
        else
            echo -e "${GREEN}✓ Ollama daemon healthy${NC}"
        fi
    fi
    
    # Cleanup after each model
    echo "Cleaning up $MODEL..."
    ollama stop "${MODEL#ollama/}" || true
    sleep 3
    
    # Progress indicator
    COMPLETED=$MODEL_NUM
    REMAINING=$((TOTAL - COMPLETED))
    SWEEP_CURRENT=$(date +%s)
    SWEEP_ELAPSED=$((SWEEP_CURRENT - SWEEP_START))
    SWEEP_ELAPSED_MIN=$((SWEEP_ELAPSED / 60))
    echo ""
    echo -e "${GREEN}Progress: $COMPLETED/$TOTAL complete${NC} | $REMAINING remaining | Sweep elapsed: ${SWEEP_ELAPSED_MIN}m"
    echo ""
done

# Calculate total sweep time
SWEEP_END=$(date +%s)
SWEEP_TOTAL_SEC=$((SWEEP_END - SWEEP_START))
SWEEP_TOTAL_MIN=$((SWEEP_TOTAL_SEC / 60))
SWEEP_REMAINING_SEC=$((SWEEP_TOTAL_SEC % 60))
SWEEP_TOTAL_HOURS=$((SWEEP_TOTAL_MIN / 60))
SWEEP_FINAL_MIN=$((SWEEP_TOTAL_MIN % 60))

# Calculate estimate accuracy
EST_SEC=$((TOTAL_EST_MIN * 60))
DELTA_SEC=$((SWEEP_TOTAL_SEC - EST_SEC))
DELTA_MIN=$((DELTA_SEC / 60))
if [ $DELTA_SEC -ge 0 ]; then
    DELTA_SIGN="+"
else
    DELTA_SIGN=""
    DELTA_MIN=$((DELTA_MIN * -1))
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Sweep Complete!${NC}"
echo "=========================================="
echo "Finished at: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "⏱️  Timing Summary:"
echo "  Total elapsed:  ${SWEEP_TOTAL_HOURS}h ${SWEEP_FINAL_MIN}m ${SWEEP_REMAINING_SEC}s (${SWEEP_TOTAL_MIN} min)"
echo "  Estimated:      ${TOTAL_EST_HOURS}h ${TOTAL_EST_REMAINING_MIN}m (${TOTAL_EST_MIN} min)"
echo "  Δ (actual-est): ${DELTA_SIGN}${DELTA_MIN} min"
if [ $DELTA_SEC -gt 300 ]; then
    echo -e "  ${YELLOW}📊 Estimate was low — models took longer than predicted${NC}"
elif [ $DELTA_SEC -lt -300 ]; then
    echo -e "  ${GREEN}📊 Estimate was conservative — models were faster than predicted${NC}"
else
    echo -e "  ${GREEN}📊 Estimate was accurate (within 5 min tolerance)${NC}"
fi
echo ""
echo "Results: data/benchmark-results/study-2a/"
echo "Logs: /tmp/tier2-*.log"
echo ""
echo "Next steps:"
echo "  1. Run: uv run python scripts/analyze_sweep_results.py study-2a"
echo "  2. Review: data/benchmark-results/study-2a/*.jsonl"
echo "  3. Compare quantized vs non-quant performance"
echo "=========================================="
echo "Logs: /tmp/tier2-*.log"
echo ""
echo "Next steps:"
echo "  1. Run: uv run python scripts/analyze_sweep_results.py study-2a"
echo "  2. Review: data/benchmark-results/study-2a/*.jsonl"
echo "=========================================="
