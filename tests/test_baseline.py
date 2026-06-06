from unittest.mock import patch


def test_baseline_includes_issue_text_in_prompt():
    from forgelab.baseline import run_baseline
    from pathlib import Path

    captured = {}

    def fake_llm(system, user, model=None, temperature=0.1):
        captured["user"] = user
        return "--- a/foo.py\n+++ b/foo.py\n", 100

    with patch("forgelab.baseline.call_llm", side_effect=fake_llm):
        run_baseline("fix the timeout bug", Path("/tmp"), model=None)

    assert "fix the timeout bug" in captured["user"]


def test_baseline_returns_text_and_tokens():
    from forgelab.baseline import run_baseline
    from pathlib import Path

    with patch("forgelab.baseline.call_llm", return_value=("some diff", 42)):
        with patch("forgelab.baseline._grep_relevant_files", return_value=""):
            text, tokens = run_baseline("fix bug", Path("/tmp"))

    assert text == "some diff"
    assert tokens == 42


def test_grep_relevant_files_returns_string(tmp_path):
    from forgelab.baseline import _grep_relevant_files

    (tmp_path / "foo.py").write_text("def humanize(): pass\n")
    result = _grep_relevant_files("humanize returns wrong value", tmp_path)
    assert isinstance(result, str)
