import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest


def _write_file(repo_dir: Path, rel_path: str, content: str) -> None:
    (repo_dir / rel_path).parent.mkdir(parents=True, exist_ok=True)
    (repo_dir / rel_path).write_text(content)


def _make_diff(rel_path: str, old_line: str, new_line: str) -> str:
    return (
        f"--- a/{rel_path}\n"
        f"+++ b/{rel_path}\n"
        f"@@ -1,3 +1,3 @@\n"
        f" def foo():\n"
        f"-    {old_line}\n"
        f"+    {new_line}\n"
        f" \n"
    )


def test_level1_clean_diff_applies(tmp_path):
    from forgelab.patch_applier import apply_patch

    _write_file(tmp_path, "mylib/foo.py", "def foo():\n    return 1\n \n")
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)

    diff = _make_diff("mylib/foo.py", "return 1", "return 2")
    status = apply_patch(diff, tmp_path)

    assert status == "applied"
    assert "return 2" in (tmp_path / "mylib/foo.py").read_text()


def test_level2_strips_markdown_fences(tmp_path):
    from forgelab.patch_applier import apply_patch

    _write_file(tmp_path, "mylib/foo.py", "def foo():\n    return 1\n \n")
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)

    diff = _make_diff("mylib/foo.py", "return 1", "return 2")
    wrapped = f"```diff\n{diff}\n```"
    status = apply_patch(wrapped, tmp_path)

    assert status == "stripped"
    assert "return 2" in (tmp_path / "mylib/foo.py").read_text()


def test_level3_llm_reformatter_called(tmp_path):
    from forgelab.patch_applier import apply_patch

    _write_file(tmp_path, "mylib/foo.py", "def foo():\n    return 1\n \n")
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)

    valid_diff = _make_diff("mylib/foo.py", "return 1", "return 2")

    with patch("forgelab.patch_applier.call_llm", return_value=(valid_diff, 50)):
        status = apply_patch("this is not a diff at all", tmp_path)

    assert status == "reformatted"


def test_level4_parse_error_when_all_fail(tmp_path):
    from forgelab.patch_applier import apply_patch

    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)

    with patch("forgelab.patch_applier.call_llm", return_value=("still not a diff", 50)):
        status = apply_patch("not a diff", tmp_path)

    assert status == "parse_error"
