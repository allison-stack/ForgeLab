# Agent Persona Files

## Location

Persona files are **bundled as package data** inside the installed package:

```
src/forgelab/personas/
├── _shared/
│   └── MEMORY_SCHEMA.md    # WorkflowState field reference (human-readable)
├── evaluator/
│   ├── SKILL.md            # What this agent does and how
│   ├── SOUL.md             # Character, values, communication style
│   └── AGENTS.md           # System prompt + LLM parameters
├── router/
│   └── ...
└── (architect, coder, researcher, reviewer, verifier — same pattern)
```

**Runtime resolution:** `Path(__file__).parent.parent / "personas"` in `agents/base.py`. This resolves to the installed package location, NEVER the target repo.

## File Formats

### SKILL.md
Defines the agent's functional role: inputs (state fields read), outputs (state fields written), workflow steps, and output format.

### SOUL.md
Defines the agent's character: cognitive style, values, communication style, signature behaviors, what it refuses. This is what makes the same base model behave differently per role.

### AGENTS.md
The operational specification read by `BaseAgent` at init time. Must follow this structure:

```markdown
# {Agent Name} Agent

## System Prompt

{Full system prompt text here — this becomes the "system" message}

## Parameters
temperature: 0.1
top_p: 0.95
num_ctx: 8192

## Tools
{list of tools, or "none"}

## Output Format
{description of expected output format}
```

**Critical:** `parse_agents_md()` in `agents/base.py` extracts the system prompt between `## System Prompt` and the next `##` heading, and parses `temperature`, `top_p`, `num_ctx` from the Parameters section.

## Agent Parameters

| Agent | Temp | Reason |
|-------|------|--------|
| evaluator | 0.0 | Deterministic JSON output required |
| router | 0.0 | Deterministic JSON output required |
| researcher | 0.3 | Some creativity in synthesis, citations anchor truth |
| architect | 0.4 | Design requires flexibility within structure |
| coder | 0.1 | Near-deterministic code generation |
| reviewer | 0.5 | Intentionally higher — adversarial perspective needs variability |
| verifier | 0.1 | Near-deterministic test generation |
