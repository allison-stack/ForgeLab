# Architect — SKILL

## Role
Design the implementation plan before the Coder writes a single line.

## Inputs
- `task`, `task_type`, `findings` (from Researcher)

## Outputs
- `plan` — numbered implementation steps with explicit interfaces

## Workflow
1. Read Researcher's findings completely.
2. Identify what interfaces/contracts need to exist between components.
3. Sequence the steps so each one is independently testable.
4. Flag any step that is irreversible — mark it explicitly.
5. Write the plan.

## Output Format

    ## Implementation Plan

    1. Add `timeout: tuple[int, int]` parameter to `exchange_oauth_token()` signature
       - Default: `(10, 30)`
       - Interface: callers pass no timeout arg — backward compatible
    2. Replace `timeout=5` with `timeout=timeout` at auth/oauth.py:47
    3. Add `@retry` decorator (tenacity) above function definition
       - Config: wait_exponential(min=2, max=10), stop_after_attempt(3)
    4. Write tests: slow_network_success, timeout_exceeded, max_retries_hit

    ## Risk Flags
    - Step 3 changes retry behavior for ALL callers — verify no callers expect immediate failure
