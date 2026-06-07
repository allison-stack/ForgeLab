from unittest.mock import patch


def test_is_valid_diff_true():
    from forgelab.agents.coder import _is_valid_diff

    assert _is_valid_diff(
        "--- a/foo.py\n+++ b/foo.py\n@@ -1,1 +1,1 @@\n-old\n+new"
    ) is True


def test_is_valid_diff_false_prose():
    from forgelab.agents.coder import _is_valid_diff

    assert _is_valid_diff("Here is the fix: change line 5 to return 2.") is False


def test_is_valid_diff_false_before_after():
    from forgelab.agents.coder import _is_valid_diff

    assert _is_valid_diff("# before\nreturn 1\n# after\nreturn 2") is False


def test_coder_retries_on_bad_output():
    from forgelab.agents.coder import run

    responses = [
        ("Here is the fix: change line 5.", 10),
        ("--- a/foo.py\n+++ b/foo.py\n@@ -5,1 +5,1 @@\n-old\n+new", 20),
    ]
    state = {
        "task": "Fix line 5",
        "findings": "Found issue",
        "plan": "Change line 5",
        "interrupt": None,
        "model_in_use": "qwen2.5:1.5b",
        "session_cost": {},
    }

    with patch("forgelab.agents.coder._agent") as mock_agent:
        mock_agent.call.side_effect = responses
        result = run(state)

    assert mock_agent.call.call_count == 2
    assert "--- a/foo.py" in result["code_changes"]


def test_coder_returns_after_max_retries():
    from forgelab.agents.coder import run

    bad_output = "Here is how to fix it: just change the code."
    state = {
        "task": "Fix something",
        "findings": "None",
        "plan": "Do it",
        "interrupt": None,
        "model_in_use": "qwen2.5:1.5b",
        "session_cost": {},
    }

    with patch("forgelab.agents.coder._agent") as mock_agent:
        mock_agent.call.return_value = (bad_output, 10)
        result = run(state)

    assert mock_agent.call.call_count == 3
    assert result["code_changes"] == bad_output


def test_coder_no_retry_on_valid_diff():
    from forgelab.agents.coder import run

    valid = "--- a/foo.py\n+++ b/foo.py\n@@ -1,1 +1,1 @@\n-old\n+new"
    state = {
        "task": "Fix something",
        "findings": "None",
        "plan": "Do it",
        "interrupt": None,
        "model_in_use": "qwen2.5:1.5b",
        "session_cost": {},
    }

    with patch("forgelab.agents.coder._agent") as mock_agent:
        mock_agent.call.return_value = (valid, 15)
        result = run(state)

    assert mock_agent.call.call_count == 1
    assert result["code_changes"] == valid
