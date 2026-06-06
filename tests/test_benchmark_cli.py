import subprocess
import sys


def test_benchmark_help_shows_subcommand():
    result = subprocess.run(
        [sys.executable, "-m", "forgelab.cli", "benchmark", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "--tasks" in result.stdout
    assert "--output" in result.stdout


def test_forgelab_help_lists_benchmark():
    result = subprocess.run(
        [sys.executable, "-m", "forgelab.cli", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "benchmark" in result.stdout


def test_benchmark_exits_if_tasks_file_missing():
    result = subprocess.run(
        [sys.executable, "-m", "forgelab.cli", "benchmark",
         "--tasks", "nonexistent.json"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "not found" in result.stderr or "not found" in result.stdout
