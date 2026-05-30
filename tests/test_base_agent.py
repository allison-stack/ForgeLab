import textwrap
from pathlib import Path
import pytest
from forgelab.agents.base import BaseAgent, parse_agents_md


SAMPLE_AGENTS_MD = textwrap.dedent("""\
    # Test Agent

    ## System Prompt

    You are a test agent. Be helpful.

    ## Parameters
    temperature: 0.1
    top_p: 0.9
    num_ctx: 4096

    ## Output Format
    JSON only.
""")


def test_parse_agents_md_extracts_system_prompt():
    result = parse_agents_md(SAMPLE_AGENTS_MD)
    assert "You are a test agent" in result["system_prompt"]


def test_parse_agents_md_extracts_temperature():
    result = parse_agents_md(SAMPLE_AGENTS_MD)
    assert result["temperature"] == 0.1


def test_parse_agents_md_extracts_top_p():
    result = parse_agents_md(SAMPLE_AGENTS_MD)
    assert result["top_p"] == 0.9
