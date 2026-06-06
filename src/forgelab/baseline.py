"""Single-LLM baseline for benchmark comparison — one-shot prompt, no agents."""
import subprocess
from pathlib import Path

from forgelab.llm import call_llm


def run_baseline(
    issue_text: str,
    repo_dir: Path,
    model: str | None = None,
) -> tuple[str, int]:
    """
    One-shot LLM call: grep relevant files, build prompt, return (diff_text, tokens).
    Uses the same model as ForgeLab's Coder for a fair comparison.
    """
    relevant = _grep_relevant_files(issue_text, repo_dir)
    user = (
        f"Fix this GitHub issue:\n\n{issue_text}\n\n"
        f"Relevant files:\n{relevant}\n\n"
        "Output a unified diff that fixes the issue. Output only the diff, nothing else."
    )
    return call_llm(
        system="You are a software engineer. Output only a unified diff. No explanation.",
        user=user,
        model=model,
        temperature=0.1,
    )


def _grep_relevant_files(issue_text: str, repo_dir: Path) -> str:
    keywords = [w for w in issue_text.split() if len(w) >= 4][:5]
    seen, parts = set(), []
    for keyword in keywords:
        result = subprocess.run(
            ["grep", "-r", "-l", "--include=*.py", keyword, "."],
            capture_output=True, text=True, cwd=repo_dir,
        )
        for fpath in result.stdout.strip().splitlines()[:2]:
            if fpath in seen:
                continue
            seen.add(fpath)
            full = repo_dir / fpath
            if full.exists():
                content = full.read_text(errors="replace")[:2000]
                parts.append(f"### {fpath}\n```python\n{content}\n```")
        if len(parts) >= 3:
            break
    return "\n\n".join(parts) if parts else "(no relevant files found)"
