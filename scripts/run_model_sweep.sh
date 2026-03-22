#!/usr/bin/env bash
# Run full model sweep for Study 2a (tier-2 suite)
# Usage:
#   bash scripts/run_model_sweep.sh [--variant baseline|optiona|optionb|optionc] [--models MODEL1,MODEL2,...]
#
# Variants:
#   baseline: top-k=10, standard template, study-id=study-2a (default)
#   optiona:  top-k=20, standard template, study-id=study-2a-topk20
#   optionb:  top-k=10, enhanced agent-workflow prompt, study-id=study-2a-optionb
#   optionc:  top-k=20, reasoning-first template (rag_answer_optionc.md), study-id=study-2a-optionc
#
# Examples:
#   bash scripts/run_model_sweep.sh --variant optionb
#   bash scripts/run_model_sweep.sh --variant optiona --models granite3.3:2b,qwen2.5:1.5b
#
# RAM-filtered model list (2026-03-21):
# Phase 7: Removed qwen:7b, mistral:7b due to RAM exhaustion on 8GB systems
# Phase 8: Added llama3:8b (non-quant), quantized variants, timing tracking
# Phase 9C: Upgraded qwen → qwen2.5, llama3 → llama3.1, added deepseek-r1 reasoning
# See: .tmp/research-rag-stress-test-quantization/2026-03-21.md

set -euo pipefail

# Parse command-line arguments
VARIANT="baseline"
CUSTOM_MODELS=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --variant)
            VARIANT="$2"
            shift 2
            ;;
        --models)
            CUSTOM_MODELS="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--variant baseline|optiona|optionb] [--models MODEL1,MODEL2,...] [--dry-run]"
            exit 1
            ;;
    esac
done

# Reasoning Density: Extract parameter count and calculate k
extract_param_count() {
    local model_name="$1"
    # Matches patterns like 1.5b, 8b, 360m in qwen2.5:1.5b or smollm:360m
    local count_str=$(echo "$model_name" | grep -oEi '[0-9.]+[bm]' | head -1 | tr '[:upper:]' '[:lower:]')
    if [[ -z "$count_str" ]]; then echo "0.0"; return; fi
    
    local num=$(echo "$count_str" | sed 's/[bm]//g')
    local unit=$(echo "$count_str" | grep -o '[bm]')
    
    if [[ "$unit" == "m" ]]; then
        # Convert M to B (e.g. 360m -> 0.36)
        echo "$num" | awk '{print $1/1000}'
    else
        echo "$num"
    fi
}

get_k_size() {
    local params="$1"
    # Result of awk is a float, so we use bc or awk for comparison
    local is_ultra_low=$(echo "$params < 1.1" | bc -l)
    local is_baseline=$(echo "$params >= 1.1 && $params < 1.5" | bc -l)
    local is_peak=$(echo "$params >= 1.5 && $params < 2.1" | bc -l)
    
    if [[ "$is_ultra_low" -eq 1 ]]; then echo "5"
    elif [[ "$is_baseline" -eq 1 ]]; then echo "10"
    elif [[ "$is_peak" -eq 1 ]]; then echo "20"
    else echo "10"; fi # > 2.0B Noise Reduction
}

# Configure study parameters based on variant
case "$VARIANT" in
    baseline)
        STUDY_ID="study-2a"
        TOP_K=10
        TEMPLATE_PATH=""
        VARIANT_DESC="Baseline (top-k=10, standard prompt)"
        ;;
    optiona)
        STUDY_ID="study-2a-topk20"
        TOP_K=20
        TEMPLATE_PATH=""
        VARIANT_DESC="Option A (top-k=20, standard prompt)"
        ;;
    optionb)
        STUDY_ID="study-2a-optionb"
        TOP_K=10
        TEMPLATE_PATH="docs/templates/rag_answer_optionb.md"
        VARIANT_DESC="Option B (top-k=10, enhanced agent-workflow prompt)"
        ;;
    optionc)
        STUDY_ID="study-2a-optionc"
        TOP_K=20
        TEMPLATE_PATH="docs/templates/rag_answer_optionb.md"
        VARIANT_DESC="Option C (top-k=20, enhanced agent-workflow prompt)"
        ;;
    *)
        echo "Invalid variant: $VARIANT"
        echo "Supported: baseline, optiona, optionb, optionc"
        exit 1
        ;;
esac

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Start timer
SWEEP_START=$(date +%s)

# Model matrix with estimated per-model time (min) and size
# Format: "model|estimated_min|size_gb|notes"
# Phase 9C-1: Ultra-small + Small models (17 models, ~3-4h sweep)
ALL_MODELS=(
    # Ultra-small tier (<1B)
    "ollama/smollm:135m|4|0.08|ultralight-135m"
    "ollama/smollm:360m|4|0.21|ultralight-360m"
    "ollama/tinyllama:1.1b|5|0.6|ultralight"
    
    # Small tier (1-2B)
    "ollama/qwen2.5:0.5b|5|0.4|baseline-fast-v2.5"
    "ollama/qwen2.5:1.5b|8|0.9|fast-v2.5"
    "ollama/granite3.1-moe:1b|7|0.8|moe-1b-128k-ctx"
    "ollama/deepseek-coder:1.3b|8|0.8|coding-specialist"
    "ollama/deepseek-r1:1.5b|10|0.9|reasoning-fast"
    "ollama/deepscaler:1.5b|9|0.9|math-specialist"
    "ollama/smollm:1.7b|8|1.0|smollm-largest"
    "ollama/codegemma:2b|9|1.6|google-coding"
    "ollama/falcon3:1b|7|0.6|depth-upscale-1b"
    "ollama/gemma:2b|8|1.7|moderate"
    "ollama/gemma2:2b|8|1.6|fast-consistent"
    "ollama/granite3.3:2b|9|1.2|ibm-reasoning-v3.3"
    "ollama/phi3:mini|15|2.2|judge-model-kept"
    "ollama/orca-mini|8|2.0|fixed-tag"
    
    # Mid-tier (7-9B) - Phase 4
    "ollama/qwen2.5:7b|60|4.7|fast-v2.5-mid"
    "ollama/llama3.1:8b|70|4.9|meta-baseline-mid"
    "ollama/gemma2:9b|80|5.4|google-consistent-mid"
)

# Filter models if --models flag was used
if [ -n "$CUSTOM_MODELS" ]; then
    IFS=',' read -ra CUSTOM_MODEL_ARRAY <<< "$CUSTOM_MODELS"
    MODELS=()
    for custom in "${CUSTOM_MODEL_ARRAY[@]}"; do
        for model_spec in "${ALL_MODELS[@]}"; do
            if [[ "$model_spec" == *"$custom"* ]]; then
                MODELS+=("$model_spec")
                break
            fi
        done
    done
    if [ ${#MODELS[@]} -eq 0 ]; then
        echo -e "${RED}Error: No matching models found for: $CUSTOM_MODELS${NC}"
        exit 1
    fi
    echo -e "${YELLOW}Running custom subset: ${#MODELS[@]} models${NC}"
else
    MODELS=("${ALL_MODELS[@]}")
fi

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
echo "Study 2a Phase 9C-1: Ultra-small + Small Model Sweep"
echo "=========================================="
echo "Total models: $TOTAL"
echo "Tier: 2 (12 test cases per model, includes source_coverage signal)"
echo "Judge model: phi3:mini (evaluates against judge rubrics)"
echo "Estimated total time: ~${TOTAL_EST_HOURS}h ${TOTAL_EST_REMAINING_MIN}m (${TOTAL_EST_MIN} min)"
echo ""
echo "Phase 9C-1 Scope (Ultra-small + Small tiers):"
echo "  • Ultra-small (<1B): smollm:135m/360m, tinyllama:1.1b"
echo "  • Small (1-2B): qwen2.5, deepseek-r1, deepseek-coder, granite3.1-moe,"
echo "    codegemma, falcon3, gemma/gemma2, granite3.3, smollm:1.7b, phi3:mini, orca-mini"
echo ""
echo "Model categories tested:"
echo "  1. Coding specialists: deepseek-coder (2T tokens), codegemma (Google)"
echo "  2. Reasoning models: deepseek-r1"
echo "  3. MoE efficiency: granite3.1-moe (128K context, low-latency)"
echo "  4. Ultra-small: smollm (135M-1.7B HuggingFace models)"
echo "  5. Enterprise: granite3.3 (IBM improved reasoning)"
echo "  6. General-purpose: qwen2.5, gemma/gemma2, phi3, orca-mini, falcon3"
echo ""
echo "Infrastructure:"
echo "  + Disk cycling active: models removed after benchmarking (phi3:mini kept)"
echo "  + source_coverage preflight signal validates retrieval completeness"
echo "  + LLM-as-judge evaluation for tier-2 queries"
echo "  + Dynamic k-tuning (v2.0) enabled: reasoning-density mapping based on params"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "=========================================="
    echo "| Model | Params | Dynamic K | Variant K (Used) |"
    echo "=========================================="
fi

for i in "${!MODELS[@]}"; do
    MODEL_SPEC="${MODELS[$i]}"
    MODEL=$(echo "$MODEL_SPEC" | cut -d'|' -f1)
    
    # Calculate Dynamic K
    MODEL_TAG="${MODEL##*/}"
    PARAMS=$(extract_param_count "$MODEL_TAG")
    K=$(get_k_size "$PARAMS")
    
    if [ "$DRY_RUN" = true ]; then
        echo "| $MODEL_TAG | ${PARAMS}B | k=$K | k=$TOP_K |"
        continue
    fi
    
    EST_MIN=$(echo "$MODEL_SPEC" | cut -d'|' -f2)
    SIZE_GB=$(echo "$MODEL_SPEC" | cut -d'|' -f3)
    NOTES=$(echo "$MODEL_SPEC" | cut -d'|' -f4)
    MODEL_NUM=$((i + 1))
    
    # Per-model timer
    MODEL_START=$(date +%s)
    
    echo ""
    echo "=========================================="
    echo -e "${GREEN}Model $MODEL_NUM/$TOTAL: $MODEL${NC}"
    echo "  Size: ${SIZE_GB} GB | Est: ~${EST_MIN} min | Variant K: $TOP_K (Dynamic: $K) | Notes: ${NOTES}"
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
    
    # Pre-flight: Verify model exists on disk (prevents tag mismatch failures)
    if ! ollama list | tail -n +2 | grep -q "^${MODEL_TAG}"; then
        echo -e "${YELLOW}⚠️  Model ${MODEL_TAG} not found on disk${NC}"
        echo "   Attempting to pull..."
        if ollama pull "${MODEL_TAG}"; then
            echo -e "${GREEN}✓ Successfully pulled ${MODEL_TAG}${NC}"
            sleep 2  # Allow daemon registry to update
            
            # DEBUG: Show what we're looking for and what's available
            echo "DEBUG: Searching for model tag: '${MODEL_TAG}'"
            echo "DEBUG: Current ollama list output:"
            ollama list | head -5
            
            # Verify model appeared in registry
            if ! ollama list | tail -n +2 | grep -q "^${MODEL_TAG}"; then
                echo "DEBUG: Model not found on first check, retrying..."
                # Not found immediately - retry with backoff
                verified=false
                for attempt in {1..5}; do
                    echo "DEBUG: Retry attempt $attempt/5"
                    sleep 1
                    if ollama list | tail -n +2 | grep -q "^${MODEL_TAG}"; then
                        verified=true
                        break
                    fi
                done
            else
                verified=true
            fi
            
            if [ "$verified" != true ]; then
                echo -e "${RED}✗ Pull succeeded but model not in registry after 7s. Skipping.${NC}"
                echo "DEBUG: Final ollama list output:"
                ollama list | head -5
                continue
            fi
        else
            echo -e "${RED}✗ Failed to pull ${MODEL_TAG}. Skipping.${NC}"
            continue  # Skip to next model
        fi
    else
        echo -e "${GREEN}✓ Model ${MODEL_TAG} verified on disk${NC}"
    fi
    
    # Build benchmark command (tier-2, pattern-matching only)
    # Judge scoring deferred to batch phase after all models complete (RAM efficiency)
    # Use variant's configured TOP_K (dynamic K is shown for reference only in dry-run)
    BENCH_CMD="uv run python scripts/benchmark_rag.py --model \"$MODEL\" --tier 2 --no-ram-block --study-id \"$STUDY_ID\" --top-k $TOP_K"
    
    # Add template path parameter if variant specifies custom template
    if [ -n "$TEMPLATE_PATH" ]; then
        BENCH_CMD="$BENCH_CMD --template-path \"$TEMPLATE_PATH\""
    fi
    
    # Extended timeout for large non-quant models
    if [[ "$MODEL" == *"llama3:8b"* ]] && [[ "$MODEL" != *"q4_K_M"* ]]; then
        echo -e "${YELLOW}⚠️  Non-quantized 8B model — extending timeout to 900s (15 min)${NC}"
        BENCH_CMD="$BENCH_CMD --timeout 900"
    fi
    
    # Run benchmark with retry on exit code 2 (model not found)
    echo ""
    echo "Starting tier-2 benchmark with top-k=$K..."
    MAX_RETRIES=1
    RETRY_COUNT=0
    BENCH_EXIT_CODE=1
    
    while [ $RETRY_COUNT -le $MAX_RETRIES ]; do
        eval $BENCH_CMD 2>&1 | tee "/tmp/tier2-${MODEL//\//-}-$(date +%Y%m%d-%H%M%S).log"
        BENCH_EXIT_CODE=$?
        
        if [ $BENCH_EXIT_CODE -eq 0 ]; then
            # Success
            break
        elif [ $BENCH_EXIT_CODE -eq 2 ] && [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            # Exit code 2 = model not found (fast-fail) — retry once after re-pull
            echo -e "${YELLOW}⚠️  Benchmark reported model not found (exit 2). Attempting re-pull...${NC}"
            if ollama pull "${MODEL_TAG}"; then
                echo -e "${GREEN}✓ Re-pull successful. Retrying benchmark...${NC}"
                RETRY_COUNT=$((RETRY_COUNT + 1))
            else
                echo -e "${RED}✗ Re-pull failed. Skipping model.${NC}"
                break
            fi
        else
            # Other failure or max retries exceeded
            break
        fi
    done
    
    # Calculate elapsed time for this model
    MODEL_END=$(date +%s)
    MODEL_ELAPSED=$((MODEL_END - MODEL_START))
    MODEL_ELAPSED_MIN=$((MODEL_ELAPSED / 60))
    MODEL_ELAPSED_SEC=$((MODEL_ELAPSED % 60))
    
    # Verify completion and display timing
    if [ $BENCH_EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✓ Model $MODEL_NUM/$TOTAL complete${NC}"
        echo -e "  Actual: ${MODEL_ELAPSED_MIN}m ${MODEL_ELAPSED_SEC}s | Est: ${EST_MIN}m | Δ: $((MODEL_ELAPSED_MIN - EST_MIN))m"
    else
        echo -e "${RED}❌ Model $MODEL_NUM/$TOTAL FAILED${NC} (exit code: $BENCH_EXIT_CODE, continuing to next model)"
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
    
    # Disk cycling: remove model to free space (skip judge model)
    MODEL_NAME="${MODEL#ollama/}"
    if [[ "$MODEL_NAME" != "phi3:mini" ]]; then
        echo "  Removing model from disk to free space..."
        if ollama rm "$MODEL_NAME" 2>/dev/null; then
            echo -e "${GREEN}  ✓ Removed $MODEL_NAME from disk${NC}"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Removed: $MODEL_NAME" >> /tmp/sweep-disk-cycling.log
        else
            echo -e "${YELLOW}  ⚠️  Model $MODEL_NAME not found or already removed${NC}"
        fi
    else
        echo -e "${YELLOW}  ⊘ Keeping phi3:mini (judge model) on disk${NC}"
    fi
    
    # Verify available disk space
    DISK_AVAIL=$(df -h / | tail -1 | awk '{print $4}')
    echo "  Available disk space: $DISK_AVAIL"
    
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
echo "Results: data/benchmark-results/${STUDY_ID}/"
echo "Logs: /tmp/tier2-*.log"
echo ""

# Run batch judge scoring automatically
echo "=========================================="
echo "Running batch judge scoring..."
echo "=========================================="
if uv run python scripts/batch_rescore_judge.py --study "$STUDY_ID"; then
    echo -e "${GREEN}✓ Judge scoring completed successfully${NC}"
    JUDGE_STATUS="completed"
else
    echo -e "${RED}✗ Judge scoring failed (exit code: $?)${NC}"
    echo "  You can retry manually: uv run python scripts/batch_rescore_judge.py --study $STUDY_ID"
    JUDGE_STATUS="failed"
fi
echo ""

echo "Next steps:"
echo "  1. Run: uv run python scripts/analyze_sweep_results.py ${STUDY_ID}"
echo "  2. Review: data/benchmark-results/${STUDY_ID}/*.jsonl"
echo "  3. Compare quantized vs non-quant performance"
echo "  Note: Judge scoring ${JUDGE_STATUS} automatically"
echo "=========================================="
