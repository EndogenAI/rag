#!/usr/bin/env python3
"""
Backfill machine_metadata to existing benchmark JSONL files.

Usage: uv run python scripts/backfill_machine_metadata.py
"""

import json
import platform
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None


def get_machine_metadata() -> dict:
    """Collect machine metadata for benchmark reproducibility."""
    metadata = {
        "machine_type": platform.machine(),
        "system": platform.system(),
        "processor": platform.processor(),
        "python_version": platform.python_version()
    }
    
    if psutil is not None:
        total_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        metadata["ram_gb"] = round(total_ram_gb, 1)
    else:
        metadata["ram_gb"] = "unknown"
    
    return metadata


def backfill_study_directory(study_dir: Path, machine_metadata: dict):
    """Backfill all JSONL files in a study directory."""
    jsonl_files = list(study_dir.glob("*.jsonl"))
    
    print(f"Found {len(jsonl_files)} JSONL files in {study_dir}")
    
    for jsonl_path in jsonl_files:
        print(f"  Processing {jsonl_path.name}...", end=" ")
        
        # Read all lines
        with open(jsonl_path, "r") as f:
            lines = f.readlines()
        
        # Parse, add machine_metadata, write back
        updated_lines = []
        for line in lines:
            try:
                entry = json.loads(line.strip())
                
                # Only add if not already present
                if "machine_metadata" not in entry:
                    entry["machine_metadata"] = machine_metadata
                
                updated_lines.append(json.dumps(entry, separators=(',', ':')) + "\n")
            except json.JSONDecodeError as e:
                print(f"\n    WARNING: Failed to parse line: {e}")
                updated_lines.append(line)  # Keep original if unparseable
        
        # Write back to file
        with open(jsonl_path, "w") as f:
            f.writelines(updated_lines)
        
        print(f"✓ Updated {len(updated_lines)} entries")


def main():
    repo_root = Path(__file__).parent.parent
    study_dir = repo_root / "data" / "benchmark-results" / "study-2a"
    
    if not study_dir.exists():
        print(f"ERROR: Study directory not found: {study_dir}")
        return 1
    
    # Collect machine metadata once
    machine_metadata = get_machine_metadata()
    print(f"Machine metadata to backfill:")
    print(f"  machine_type: {machine_metadata['machine_type']}")
    print(f"  system: {machine_metadata['system']}")
    print(f"  ram_gb: {machine_metadata['ram_gb']}")
    print(f"  processor: {machine_metadata['processor']}")
    print(f"  python_version: {machine_metadata['python_version']}")
    print()
    
    # Backfill all files in study-2a/
    backfill_study_directory(study_dir, machine_metadata)
    
    print("\nBackfill complete. Verifying sample entry...")
    
    # Verify by reading back one file
    sample_file = list(study_dir.glob("*.jsonl"))[0]
    with open(sample_file, "r") as f:
        first_line = f.readline()
        sample_entry = json.loads(first_line)
        
    if "machine_metadata" in sample_entry:
        print(f"✓ Verification passed: machine_metadata present in {sample_file.name}")
        print(f"  Sample: {json.dumps(sample_entry['machine_metadata'], indent=2)}")
    else:
        print(f"✗ Verification failed: machine_metadata missing in {sample_file.name}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
