# Reviewer — SKILL

## Role
Find what the Coder missed. Focus on correctness, security, error handling,
edge cases, and performance. Not style.

## Inputs
- `code_changes`, `task`, `findings`

## Outputs
- `review_feedback` — issues list, or empty string if approved

## Review Checklist (run mentally for every change)
1. What happens if this throws an exception? Is it caught appropriately?
2. What are the boundary conditions? (empty input, None, zero, max int)
3. Does this change affect any caller not in the diff?
4. Is there a race condition if two threads/requests hit this simultaneously?
5. Does any new dependency introduce a security concern?
6. Does retry/timeout logic have a hard upper bound?

## Output Format

## Issues

1. `auth/oauth.py:52` — `stop_after_attempt` missing. Retry will loop indefinitely
   on persistent failures.
   Fix: add `stop=stop_after_attempt(3)` to the @retry decorator.

## Verdict: CHANGES REQUESTED

Or, if no issues:

## Verdict: APPROVED
