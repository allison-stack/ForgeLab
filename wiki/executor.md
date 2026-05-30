# Executor — `src/forgelab/executor.py`

## Purpose

Deterministic test execution. LLMs hallucinate test results — an actual test runner does not. The Verifier agent generates test code; the Executor runs it and returns ground truth.

## Docker is optional

The executor has two paths, chosen automatically at runtime:

| Docker available? | Behaviour |
|---|---|
| Yes | Tests run in an isolated container — clean environment, no host dependency pollution |
| No | Tests run directly via `subprocess` in a temp directory — same pass/fail result, less isolation |

**Detection:** `_docker_available()` calls `docker info` with a 5-second timeout. If Docker isn't installed or the daemon isn't running, the subprocess path is used automatically. No config needed.

This means `pip install forgelab` is the only hard requirement. Docker is a nice-to-have that improves isolation but is never a blocker.

## Multi-framework support

The `_FRAMEWORK_CONFIG` dispatch table maps each `test_framework` string to everything the executor needs. Adding a new language means adding one row here — nothing else changes.

| Framework | Docker image | Test command | Subprocess fallback |
|---|---|---|---|
| `pytest` | `python:3.12-slim` | `pytest -q` | `python -m pytest -q` |
| `cargo` | `rust:1-slim` | `cargo test` | `cargo test` |
| `jest` | `node:20-slim` | `npx jest --no-coverage` | `npx jest --no-coverage` |
| `go-test` | `golang:1.22-alpine` | `go test ./...` | `go test ./...` |
| `ctest` | *(falls back to pytest)* | — | — |

**Why `python -m pytest` for the subprocess fallback?** This ensures the fallback uses the same Python environment that ForgeLab is installed into (the active venv), not a different `pytest` that might be on `PATH` from a different Python version.

**Why is ctest a fallback?** CMake requires a configure + build step before tests run. That's non-trivial to sandbox generically. It falls back to pytest until a proper CMake scaffold is built.

## API

### `run_test(target_code, test_code, *, framework="pytest", timeout_seconds=60) → ExecutorResult`

One-shot convenience. Starts a container (or subprocess), runs tests, tears down. Use this for single calls.

### `ExecutorSession` (context manager)

Long-lived session for multiple test runs in the same cycle. Reuses the container across calls — amortises Docker startup (~1–2s) across mutations or retry loops.

```python
with ExecutorSession(framework="pytest") as session:
    result_v1 = session.run(original_code, test_code)
    result_v2 = session.run(fixed_code, test_code)   # same container, fast
```

### `ExecutorResult` (frozen dataclass)

```python
@dataclass(frozen=True)
class ExecutorResult:
    passed: bool        # True iff test runner exit code == 0
    stdout: str         # Full test runner stdout
    stderr: str         # Full stderr (syntax errors appear here)
    timed_out: bool     # True if timeout_seconds was exceeded
```

## Scaffold files

Some frameworks need project structure beyond just source + test files. These are written to the temp directory before the container/subprocess starts:

| Framework | Extra files |
|---|---|
| `cargo` | `Cargo.toml` (minimal lib crate pointing to `src/lib.rs`) |
| `jest` | `package.json` (minimal Jest config) |
| `go-test` | `go.mod` (module declaration) |

## Usage in Verifier

```python
from forgelab.executor import run_test

exec_result = run_test(
    target_code=state.get("code_changes") or _TEST_STUB,
    test_code=test_code,
    framework=state.get("test_framework", "pytest"),
)
```
