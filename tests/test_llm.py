import pytest
from unittest.mock import patch, MagicMock
from forgelab.llm import call_llm, get_client


def test_call_llm_returns_text_and_tokens():
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "hello"
    mock_response.usage.total_tokens = 42

    with patch("forgelab.llm._get_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_client_fn.return_value = mock_client

        text, tokens = call_llm(system="sys", user="usr")

    assert text == "hello"
    assert tokens == 42


def test_call_llm_uses_ollama_base_url(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    client = get_client()
    assert client is not None
