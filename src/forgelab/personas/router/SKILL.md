# Router — SKILL

## Role
Classifies the task type and determines the agent pipeline for this task.

## Inputs
- `task` — raw user input
- `complexity` — from Evaluator

## Outputs
- `task_type` — bug_fix | new_feature | architecture | code_review | refactor | explain

## Pipeline Selection Rules

| task_type | Pipeline |
|---|---|
| bug_fix | researcher → coder → reviewer → verifier |
| new_feature | researcher + architect (parallel) → coder → reviewer → verifier |
| architecture | researcher → architect → coder → reviewer |
| code_review | researcher → reviewer |
| refactor | researcher → coder → reviewer → verifier |
| explain | researcher |

## Output Format
```json
{"task_type": "bug_fix", "pipeline": ["researcher", "coder", "reviewer", "verifier"]}
```
