#!/usr/bin/env python3
"""One-time script: sample 15 tasks from SWE-bench Lite, save to benchmark/tasks.json."""
import json
import random
from pathlib import Path
from datasets import load_dataset

SEED = 42
N = 15

def main():
    print("Loading SWE-bench Lite from HuggingFace (first run downloads ~50MB)...")
    ds = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
    print(f"Loaded {len(ds)} tasks.")

    random.seed(SEED)
    indices = random.sample(range(len(ds)), N)

    tasks = []
    for i in indices:
        row = ds[i]
        tasks.append({
            "instance_id": row["instance_id"],
            "repo": f"https://github.com/{row['repo']}",
            "base_commit": row["base_commit"],
            "issue_text": row["problem_statement"],
            "fail_to_pass": json.loads(row["FAIL_TO_PASS"]),
            "pass_to_pass": json.loads(row["PASS_TO_PASS"]),
        })

    output = {
        "_meta": {"seed": SEED, "n": N, "source": "princeton-nlp/SWE-bench_Lite"},
        "tasks": tasks,
    }

    out_path = Path(__file__).parent / "tasks.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"Saved {N} tasks to {out_path}")
    for t in tasks:
        print(f"  {t['instance_id']}")

if __name__ == "__main__":
    main()
