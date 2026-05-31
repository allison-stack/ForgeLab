import subprocess
import sys


def test_demo_help_shows_subcommand():
    result = subprocess.run(
        [sys.executable, "-m", "forgelab.cli", "demo", "--help"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "--fixture" in result.stdout
    assert "--speed" in result.stdout
    assert "--port" in result.stdout


def test_forgelab_help_lists_demo():
    result = subprocess.run(
        [sys.executable, "-m", "forgelab.cli", "--help"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "demo" in result.stdout
