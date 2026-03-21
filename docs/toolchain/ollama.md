# `ollama` — Curated Agent Reference

> **Agent instruction**: use this file as your first lookup for Ollama model management patterns before constructing any `ollama` command.
> Canonical safety rules are encoded in [AGENTS.md § Ollama Model Management](../../AGENTS.md#ollama-model-management) and the Guardrails section.

---

## Architecture: How Ollama Works

Ollama runs as a **background daemon** (`ollama serve`, usually auto-started at login on macOS). It exposes an HTTP API at `http://localhost:11434/`. Client calls (`ollama pull`, `benchmark_rag.py`, LiteLLM) talk to the daemon — they do **not** each start their own server.

The daemon:
- **Auto-loads** a model into RAM on first API request for that model
- **Auto-unloads** a model after it has been idle for ~5 minutes (configurable via `OLLAMA_KEEP_ALIVE`)
- **Only holds one model in VRAM/RAM at a time** on hardware without discrete GPU (MacBook Air)

---

## The One Hard Rule: Never `ollama run`

```bash
# ❌ NEVER do this in an agent session
ollama run llama3:8b-instruct-q4_K_M

# ✅ Correct: pull to disk only; let the API load on demand
ollama pull llama3:8b-instruct-q4_K_M
```

**Why**: `ollama run` opens an interactive REPL and **pins the model in RAM** for the lifetime of that terminal process. If you then try to benchmark a second model, the daemon attempts to load it alongside the first — on 16 GB MacBook Air this causes OOM swap, system lag, or a crash. The models pulled during this sprint total ~14 GB; two loaded simultaneously will exhaust physical RAM.

---

## Pre-Benchmark Checklist (Always Run Before `benchmark_rag.py`)

```bash
# 1. Confirm no model is currently pinned in RAM
ollama ps           # empty table = safe to proceed

# 2. If a model IS pinned, unload it first
ollama stop <model-name>

# 3. Check available disk space — need ≥ (largest_model_size + 2 GB headroom)
df -h /
```

The benchmark script (`scripts/benchmark_rag.py`) enforces steps 1 and 3 automatically via a preflight check at startup.

---

## Model Management Commands

```bash
# List all downloaded models (with sizes)
ollama list

# Pull a model to disk (does NOT load into RAM)
ollama pull llama3:8b-instruct-q4_K_M

# Check what is currently loaded in RAM
ollama ps

# Unload a currently-loaded model from RAM
ollama stop llama3:8b-instruct-q4_K_M

# Permanently delete a model from disk (free space; re-pull later)
ollama rm llama3:latest

# Verify daemon is running
curl -sf http://localhost:11434/   # should return: Ollama is running
```

---

## Disk Space Guidance (MacBook Air 16 GB / ~14 GB free disk)

| Model | Approx Size | Notes |
|-------|------------|-------|
| `llama3:latest` (8B fp16) | 4.7 GB | Baseline; can be removed during a q4 sweep |
| `llama3:8b-instruct-q4_K_M` | 4.9 GB | Primary quantization target |
| `phi3:latest` (mini) | 2.2 GB | Baseline phi3 |
| `phi3:mini` | 2.2 GB | Effectively same as phi3:latest on Ollama |

**Rule of thumb for this hardware:**
- Keep at most **two models on disk at once** during an active sweep
- Before pulling a new model, run `df -h /` — require ≥ model_size + 2 GB free
- To free space temporarily: `ollama rm llama3:latest` (re-pull when needed with `ollama pull`)

---

## LiteLLM / benchmark_rag.py Model String Format

When passing models to `benchmark_rag.py --model`, use the LiteLLM Ollama prefix:

```bash
# Format: ollama/<model-name-as-listed-by-ollama-list>
uv run python scripts/benchmark_rag.py --model ollama/llama3:8b-instruct-q4_K_M --tier 1 --top-k 3
uv run python scripts/benchmark_rag.py --model ollama/phi3:mini --tier 1 --top-k 3
```

---

## Known Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Benchmark latency spikes to 2–3× baseline | Two models loaded simultaneously | `ollama stop <model>` to unload the second; re-run |
| `error: model not found` | Model pulled under a different tag | Run `ollama list` to see exact tag string |
| System fan spins up during pull, then hangs | Disk nearly full during write | Check `df -h /`; `ollama rm` a large model first |
| `ollama ps` shows model still loaded after benchmark | Daemon KEEP_ALIVE hasn't elapsed | `ollama stop <model>` to force unload immediately |
