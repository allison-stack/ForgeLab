import json
from pathlib import Path
from unittest.mock import patch, AsyncMock


def _make_tasks_json(tmp_path: Path, n: int = 2) -> Path:
    tasks = [
        {
            "instance_id": f"repo__issue-{i}",
            "repo": "https://github.com/example/repo",
            "base_commit": "abc123",
            "issue_text": f"Fix bug {i}",
            "fail_to_pass": [f"tests/test_foo.py::test_{i}"],
            "pass_to_pass": [],
        }
        for i in range(n)
    ]
    p = tmp_path / "tasks.json"
    p.write_text(json.dumps({"_meta": {"seed": 42, "n": n}, "tasks": tasks}))
    return p


def test_write_results_creates_json_and_csv(tmp_path):
    from forgelab.benchmark_runner import _write_results

    results = [
        {
            "instance_id": "a__b-1",
            "forgelab_passed": True,
            "forgelab_iterations": 1,
            "forgelab_tokens": 100,
            "forgelab_parse_error": False,
            "baseline_passed": False,
            "baseline_parse_error": False,
            "fail_to_pass_tests": ["test_foo"],
            "regression": False,
        }
    ]
    _write_results(results, tmp_path)

    assert (tmp_path / "results.json").exists()
    assert (tmp_path / "summary.csv").exists()
    loaded = json.loads((tmp_path / "results.json").read_text())
    assert loaded[0]["instance_id"] == "a__b-1"


def test_count_iterations_approved_first_pass():
    from forgelab.benchmark_runner import _count_iterations

    result = {"review_feedback": "Verdict: APPROVED"}
    assert _count_iterations(result) == 1


def test_count_iterations_changes_requested():
    from forgelab.benchmark_runner import _count_iterations

    result = {"review_feedback": "CHANGES REQUESTED — add error handling"}
    assert _count_iterations(result) == 2


def test_print_summary_outputs_pass_rates(capsys):
    from forgelab.benchmark_runner import _print_summary

    results = [
        {"forgelab_passed": True,  "baseline_passed": False,
         "forgelab_parse_error": False, "baseline_parse_error": False,
         "forgelab_iterations": 1},
        {"forgelab_passed": False, "baseline_passed": False,
         "forgelab_parse_error": True, "baseline_parse_error": False,
         "forgelab_iterations": 1},
    ]
    _print_summary(results)
    out = capsys.readouterr().out
    assert "1/2" in out
    assert "50.0%" in out
