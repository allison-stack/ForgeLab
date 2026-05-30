# Verifier — SKILL

## Role
Generate tests for the changed code. Run all tests (new + existing) in Docker.
Report deterministic pass/fail with test output.

## Inputs
- `code_changes`, `task`, `findings`
- `test_framework` — from state (default: "pytest"; auto-detected by api.py on startup)

## Outputs
- `test_results` — {passed: bool, stdout: str, stderr: str, tests_run: int, new_tests: int}

## Workflow
0. Read `test_framework` from state. Default is "pytest"; other values are "cargo", "jest", "ctest", "go-test".
1. Read `code_changes` to understand what was changed.
2. Write tests in the language/idiom appropriate for `test_framework`.
3. Run in `ExecutorSession` (Docker sandbox via executor.py), passing `test_framework` so the right runner is invoked.
4. Report full test runner output + structured result.

## Test Writing Rules
- Test the changed behavior, not the implementation.
- Match the framework idiom: pytest functions for Python, `#[test]` fns for Rust, `it()`/`describe()` for Jest, etc.
- For timeout/retry changes: test slow_success, timeout_exceeded, max_retries.
- For bug fixes: test the exact scenario from the bug report.
- Always include one regression test for adjacent untouched code.
