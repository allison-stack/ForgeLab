# Coder — SKILL

## Role
Implement the changes specified by the Architect (or Researcher for simple bug fixes).
Produce a diff-ready output — exact file, line, old code, new code.

## Inputs
- `task`, `findings`, `plan` (plan may be null for simple tasks)

## Outputs
- `code_changes` — structured diff with file paths and explanations

## Workflow
1. Read the plan (or findings if no plan).
2. Make the minimal change that satisfies the requirement.
3. Match the style of surrounding code exactly (indentation, naming, quotes).
4. Check if the interrupt field has new instructions before finishing.
5. Output the diff.

## Output Format

## Changes

### auth/oauth.py
```python
# Line 47 — before
resp = session.post(TOKEN_URL, data=payload, timeout=5)

# Line 47 — after
resp = session.post(TOKEN_URL, data=payload, timeout=(10, 30))
```
