"""
Executor — the deterministic ground truth of the system.

Runs generated test code against target code and returns a hard pass/fail.
LLMs hallucinate test results; an actual test runner does not.

Docker path (preferred): isolated container, no host dependencies pollute results.
Subprocess fallback: runs in a temp dir on the host when Docker is unavailable.
  — Same pass/fail semantics, less isolation. Acceptable for local dev use.

To add a new framework: add one row to _FRAMEWORK_CONFIG. Nothing else changes.
"""

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self


@dataclass(frozen=True)
class ExecutorResult:
    passed: bool
    stdout: str
    stderr: str
    timed_out: bool


@dataclass(frozen=True)
class _FrameworkConfig:
    image: str                         # Docker image
    setup_cmd: list[str] | None        # Run once in container after start (None = not needed)
    target_file: str                   # Filename for target/implementation code
    test_file: str                     # Filename for test code
    test_cmd: list[str]                # Test command inside Docker
    subprocess_test_cmd: list[str]     # Test command for subprocess fallback
    extra_files: dict[str, str] = field(default_factory=dict)  # Scaffold files (Cargo.toml etc.)


_FRAMEWORK_CONFIG: dict[str, _FrameworkConfig] = {
    "pytest": _FrameworkConfig(
        image="python:3.12-slim",
        setup_cmd=["pip", "install", "pytest", "-q"],
        target_file="target.py",
        test_file="test_target.py",
        test_cmd=["pytest", "-q"],
        # Use `python -m pytest` so the fallback picks up the active venv's pytest,
        # not a different pytest that might be on PATH.
        subprocess_test_cmd=[sys.executable, "-m", "pytest", "-q"],
    ),
    "cargo": _FrameworkConfig(
        image="rust:1-slim",
        setup_cmd=None,
        target_file="src/lib.rs",
        test_file="tests/integration_test.rs",
        test_cmd=["cargo", "test"],
        subprocess_test_cmd=["cargo", "test"],
        extra_files={
            "Cargo.toml": (
                '[package]\nname = "sandbox"\nversion = "0.1.0"\nedition = "2021"\n\n'
                '[lib]\nname = "sandbox"\npath = "src/lib.rs"\n'
            ),
        },
    ),
    "jest": _FrameworkConfig(
        image="node:20-slim",
        setup_cmd=["npm", "install", "--save-dev", "jest"],
        target_file="target.js",
        test_file="target.test.js",
        test_cmd=["npx", "jest", "--no-coverage"],
        subprocess_test_cmd=["npx", "jest", "--no-coverage"],
        extra_files={
            "package.json": '{"name":"sandbox","version":"1.0.0","scripts":{"test":"jest"}}\n',
        },
    ),
    "go-test": _FrameworkConfig(
        image="golang:1.22-alpine",
        setup_cmd=None,
        target_file="pkg.go",
        test_file="pkg_test.go",
        test_cmd=["go", "test", "./..."],
        subprocess_test_cmd=["go", "test", "./..."],
        extra_files={
            "go.mod": "module sandbox\n\ngo 1.22\n",
        },
    ),
    # ctest needs a full CMake configure+build before tests run — non-trivial to sandbox.
    # Falls back to pytest until a proper CMake scaffold is added.
    "ctest": _FrameworkConfig(
        image="python:3.12-slim",
        setup_cmd=["pip", "install", "pytest", "-q"],
        target_file="target.py",
        test_file="test_target.py",
        test_cmd=["pytest", "-q"],
        subprocess_test_cmd=[sys.executable, "-m", "pytest", "-q"],
    ),
}

_DEFAULT_FRAMEWORK = "pytest"


def _docker_available() -> bool:
    """Return True if the Docker daemon is reachable."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


class ExecutorSession:
    """
    Long-lived execution context for a single workflow cycle.

    If Docker is available: starts a container, installs the test framework
    once, and re-uses it across multiple run() calls (amortises startup cost).

    If Docker is unavailable: runs tests directly via subprocess in a temp
    directory on the host. Same pass/fail semantics, less isolation.
    """

    def __init__(self, framework: str = _DEFAULT_FRAMEWORK, timeout_seconds: int = 60) -> None:
        self._cfg = _FRAMEWORK_CONFIG.get(framework, _FRAMEWORK_CONFIG[_DEFAULT_FRAMEWORK])
        self.timeout_seconds = timeout_seconds
        self._use_docker = _docker_available()
        self._tmpdir: str | None = None
        self._container_id: str | None = None

    def __enter__(self) -> Self:
        self._tmpdir = tempfile.mkdtemp()

        # Write scaffold files (Cargo.toml, go.mod, package.json, etc.)
        for filename, content in self._cfg.extra_files.items():
            dest = Path(self._tmpdir, filename)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")

        if self._use_docker:
            result = subprocess.run(
                ["docker", "run", "-d", "--rm",
                 "-v", f"{self._tmpdir}:/work", "-w", "/work",
                 self._cfg.image, "sleep", "3600"],
                capture_output=True, text=True, check=True,
            )
            self._container_id = result.stdout.strip()
            if self._cfg.setup_cmd:
                subprocess.run(
                    ["docker", "exec", self._container_id] + self._cfg.setup_cmd,
                    capture_output=True, check=True,
                )

        return self

    def __exit__(self, *_exc: object) -> None:
        if self._container_id:
            subprocess.run(["docker", "rm", "-f", self._container_id], capture_output=True)
            self._container_id = None
        if self._tmpdir:
            shutil.rmtree(self._tmpdir, ignore_errors=True)
            self._tmpdir = None

    def run(self, target_code: str, test_code: str) -> ExecutorResult:
        """Write target + test files and execute the test runner."""
        if self._tmpdir is None:
            raise RuntimeError("ExecutorSession.run() called outside a 'with' block")

        target_path = Path(self._tmpdir, self._cfg.target_file)
        test_path = Path(self._tmpdir, self._cfg.test_file)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(target_code, encoding="utf-8")
        test_path.write_text(test_code, encoding="utf-8")

        if self._use_docker:
            cmd = ["docker", "exec", self._container_id] + self._cfg.test_cmd
            kwargs: dict = {}
        else:
            cmd = self._cfg.subprocess_test_cmd
            # Run directly in the tmpdir so relative imports and file paths resolve
            kwargs = {"cwd": self._tmpdir}

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=self.timeout_seconds, **kwargs,
            )
            return ExecutorResult(
                passed=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                timed_out=False,
            )
        except subprocess.TimeoutExpired as e:
            return ExecutorResult(
                passed=False,
                stdout=str(e.stdout) or "",
                stderr=str(e.stderr) or "",
                timed_out=True,
            )


def run_test(
    target_code: str,
    test_code: str,
    *,
    framework: str = _DEFAULT_FRAMEWORK,
    timeout_seconds: int = 60,
) -> ExecutorResult:
    """
    One-shot convenience wrapper. For multiple runs in one cycle, use
    ExecutorSession directly to amortise container startup.
    """
    with ExecutorSession(framework=framework, timeout_seconds=timeout_seconds) as session:
        return session.run(target_code, test_code)
