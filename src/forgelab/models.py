"""
Central registry for LLM model IDs.

Every agent's default model lives here so swapping models is a 1-file change.
Currently emulating the model lineup available at the workplace deployment.
"""

AUTHOR_MODEL = "openai/gpt-oss-120b:free"
JUDGE_MODEL = "poolside/laguna-m.1:free"
ADVERSARY_MODEL = "openai/gpt-oss-120b:free"
