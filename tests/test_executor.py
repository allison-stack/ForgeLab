from unittest.mock import patch
from forgelab.executor import ExecutorSession

_TARGET = "def add(a, b):\n    return a + b\n"
_PASS = "from target import add\ndef test_ok(): assert add(2, 3) == 5\n"
_FAIL = "from target import add\ndef test_bad(): assert add(2, 3) == 99\n"


def _session():
    """ExecutorSession with Docker forcibly disabled."""
    return patch("forgelab.executor._docker_available", return_value=False)


def test_subprocess_fallback_passing_tests():
    with _session():
        with ExecutorSession(framework="pytest", timeout_seconds=30) as s:
            assert s._use_docker is False
            result = s.run(_TARGET, _PASS)
    assert result.passed is True
    assert result.timed_out is False


def test_subprocess_fallback_failing_tests():
    with _session():
        with ExecutorSession(framework="pytest", timeout_seconds=30) as s:
            result = s.run(_TARGET, _FAIL)
    assert result.passed is False
    assert result.timed_out is False
    assert "assert 5 == 99" in result.stdout
