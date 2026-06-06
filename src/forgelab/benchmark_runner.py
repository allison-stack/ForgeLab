"""Orchestrates the ForgeLab benchmark run against SWE-bench Lite tasks."""
import asyncio
import csv
import json
import os
import subprocess
from pathlib import Path

from forgelab.graph import build_graph
from forgelab.state import WorkflowState
from forgelab.patch_applier import apply_patch
from forgelab.baseline import run_baseline


def run_benchmark(
    tasks_path: str = "benchmark/tasks.json",
    output_dir: str = "benchmark/results",
    model: str | None = None,
) -> None:
    data = json.loads(Path(tasks_path).read_text())
    tasks = data["tasks"] if isinstance(data, dict) else data

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    graph = build_graph()
    results = []

    for i, task in enumerate(tasks, 1):
        print(f"\n[{i}/{len(tasks)}] {task['instance_id']}")
        result = asyncio.run(_run_task(graph, task, out, model))
        results.append(result)
        _print_task_result(result)

    _write_results(results, out)
    _print_summary(results)


async def _run_task(graph, task: dict, out: Path, model: str | None) -> dict:
    instance_id = task["instance_id"]
    repo_dir = out.parent / "repos" / instance_id

    _setup_repo(task["repo"], task["base_commit"], repo_dir)

    result = {
        "instance_id": instance_id,
        "forgelab_passed": False,
        "forgelab_iterations": 1,
        "forgelab_tokens": 0,
        "forgelab_parse_error": False,
        "baseline_passed": False,
        "baseline_parse_error": False,
        "fail_to_pass_tests": task["fail_to_pass"],
        "regression": False,
    }

    # Build initial WorkflowState with all required fields
    state: WorkflowState = {
        "task": task["issue_text"],
        "task_type": None,
        "complexity": None,
        "upgrade_recommendation": None,
        "model_in_use": model or os.environ.get("FORGELAB_MODEL", "claude-sonnet-4-5"),
        "findings": None,
        "plan": None,
        "code_changes": None,
        "review_feedback": None,
        "test_results": None,
        "test_framework": "pytest",
        "agent_messages": [],
        "session_cost": {},
        "interrupt": None,
    }
    forgelab_result = await graph.ainvoke(state)

    result["forgelab_tokens"] = sum(
        v.get("tokens", 0)
        for v in forgelab_result.get("session_cost", {}).values()
    )
    result["forgelab_iterations"] = _count_iterations(forgelab_result)

    patch_status = apply_patch(forgelab_result.get("code_changes") or "", repo_dir, model)
    if patch_status == "parse_error":
        result["forgelab_parse_error"] = True
    else:
        passed, regression = _run_tests(repo_dir, task["fail_to_pass"], task["pass_to_pass"])
        result["forgelab_passed"] = passed
        result["regression"] = regression

    # Reset repo for baseline
    subprocess.run(["git", "checkout", "."], cwd=repo_dir, capture_output=True)

    baseline_diff, _ = run_baseline(task["issue_text"], repo_dir, model)
    baseline_status = apply_patch(baseline_diff, repo_dir, model)
    if baseline_status == "parse_error":
        result["baseline_parse_error"] = True
    else:
        result["baseline_passed"], _ = _run_tests(
            repo_dir, task["fail_to_pass"], task["pass_to_pass"]
        )

    subprocess.run(["git", "checkout", "."], cwd=repo_dir, capture_output=True)
    return result


def _setup_repo(repo_url: str, base_commit: str, repo_dir: Path) -> None:
    if not repo_dir.exists():
        repo_dir.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", repo_url, str(repo_dir)], check=True)
    subprocess.run(["git", "checkout", base_commit], cwd=repo_dir, capture_output=True)


def _run_tests(
    repo_dir: Path, fail_to_pass: list[str], pass_to_pass: list[str]
) -> tuple[bool, bool]:
    ftp = subprocess.run(
        ["python", "-m", "pytest"] + fail_to_pass + ["-x", "--tb=no", "-q"],
        cwd=repo_dir, capture_output=True, text=True, timeout=120,
    )
    passed = ftp.returncode == 0

    regression = False
    if pass_to_pass:
        ptp = subprocess.run(
            ["python", "-m", "pytest"] + pass_to_pass + ["-x", "--tb=no", "-q"],
            cwd=repo_dir, capture_output=True, text=True, timeout=120,
        )
        regression = ptp.returncode != 0

    return passed, regression


def _count_iterations(forgelab_result: dict) -> int:
    feedback = forgelab_result.get("review_feedback") or ""
    return 2 if "CHANGES REQUESTED" in feedback.upper() else 1


def _write_results(results: list[dict], out: Path) -> None:
    (out / "results.json").write_text(json.dumps(results, indent=2))
    with open(out / "summary.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)


def _print_task_result(result: dict) -> None:
    fl = "PASS" if result["forgelab_passed"] else "FAIL"
    bl = "PASS" if result["baseline_passed"] else "FAIL"
    pe = " (parse error)" if result["forgelab_parse_error"] else ""
    print(f"  ForgeLab: {fl}{pe}  Baseline: {bl}")


def _print_summary(results: list[dict]) -> None:
    n = len(results)
    fl_pass = sum(1 for r in results if r["forgelab_passed"])
    bl_pass = sum(1 for r in results if r["baseline_passed"])
    fl_parse = sum(1 for r in results if r["forgelab_parse_error"])
    bl_parse = sum(1 for r in results if r["baseline_parse_error"])
    avg_iter = sum(r["forgelab_iterations"] for r in results) / n if n else 0

    print(f"\n{'='*60}")
    print(f"Benchmark complete: {n} tasks")
    print(f"ForgeLab:  {fl_pass}/{n} passed ({fl_pass/n*100:.1f}%) | "
          f"{fl_parse} parse errors | avg {avg_iter:.1f} iterations")
    print(f"Baseline:  {bl_pass}/{n} passed ({bl_pass/n*100:.1f}%) | "
          f"{bl_parse} parse errors")
    print("Reference: Claude Sonnet 4.6 scored 79.6% on full SWE-bench Lite (April 2025)")
    print(f"{'='*60}")
