"""Apply a unified diff to files in a repository directory — 3-level fallback."""
import re
import subprocess
from pathlib import Path

from forgelab.llm import call_llm


def apply_patch(code_changes: str, repo_dir: Path, model: str | None = None) -> str:
    """
    Apply code_changes to repo_dir. Returns one of:
    'applied'     — Level 1: parsed and applied directly
    'stripped'    — Level 2: markdown fences stripped, then applied
    'reformatted' — Level 3: LLM converted to diff, then applied
    'parse_error' — all levels failed; caller should mark task as failed
    """
    has_fences = bool(re.search(r"^```", code_changes, re.MULTILINE))
    if not has_fences and _try_apply(code_changes, repo_dir):
        return "applied"

    stripped = re.sub(r"```[^\n]*\n?", "", code_changes).strip()
    if _try_apply(stripped, repo_dir):
        return "stripped"

    reformatted, _ = call_llm(
        system="Convert the following code changes into a unified diff. Output only the diff, nothing else.",
        user=code_changes,
        model=model,
        temperature=0.0,
    )
    reformatted = re.sub(r"```[^\n]*\n?", "", reformatted).strip()
    if _try_apply(reformatted, repo_dir):
        return "reformatted"

    return "parse_error"


def _try_apply(text: str, repo_dir: Path) -> bool:
    """Dry-run then apply a unified diff. Returns True on success."""
    dry = subprocess.run(
        ["patch", "-p1", "--dry-run", "--silent"],
        input=text, capture_output=True, text=True, cwd=repo_dir,
    )
    if dry.returncode != 0:
        return False
    result = subprocess.run(
        ["patch", "-p1", "--silent"],
        input=text, capture_output=True, text=True, cwd=repo_dir,
    )
    return result.returncode == 0
