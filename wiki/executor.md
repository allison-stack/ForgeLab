# Executor — Docker Sandbox

**File:** `src/forgelab/executor.py`

## Purpose

Deterministic test execution. LLMs lie about whether tests pass — Docker does not. The Verifier agent generates test code; the Executor runs it and returns ground truth.

## API

### `run_test(target_code, test_code, *, framework="pytest", image="testforge-sandbox", timeout_seconds=60) → ExecutorResult`

One-shot convenience function. Starts a container, runs tests, cleans up.

**Note:** The original `executor.py` `run_test()` does not have a `framework` parameter — it always uses pytest. The verifier.py currently passes `framework=` but executor ignores it. Future enhancement: route to the correct test runner based on framework.

### `ExecutorSession` (context manager)

Long-lived container for multiple test runs. Reuses container across calls (amortizes Docker startup cost).

```python
with ExecutorSession() as session:
    result1 = session.run(target_code_v1, test_code)
    result2 = session.run(target_code_v2, test_code)  # same container
```

### `ExecutorResult` (frozen dataclass)

```python
@dataclass(frozen=True)
class ExecutorResult:
    passed: bool      # True iff pytest exit code == 0
    stdout: str       # Full test runner stdout
    stderr: str       # Full stderr (syntax errors show here)
    timed_out: bool   # True if timeout_seconds exceeded
```

## Docker Image

Default image: `testforge-sandbox`. Must have Python + pytest installed. The executor:
1. Writes `target.py` and `test_target.py` to a tmpdir mounted at `/work`
2. Runs `docker exec {container_id} pytest -q`
3. Returns stdout/stderr + exit code

## Usage in Verifier

```python
from forgelab.executor import run_test

exec_result = run_test(
    target_code=state.get("code_changes") or _TEST_STUB,
    test_code=test_code,
    framework=state.get("test_framework", "pytest"),
)
```
