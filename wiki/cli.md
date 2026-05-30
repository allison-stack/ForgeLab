# CLI — `src/forgelab/cli.py`

## Purpose

Makes ForgeLab an installable CLI tool. After `pip install forgelab`, users run `forgelab start` from the root of any target repository.

## Commands

```bash
forgelab start                          # start on 127.0.0.1:8000
forgelab start --port 9000              # custom port
forgelab start --host 0.0.0.0           # expose on all interfaces
forgelab start --reload                 # auto-reload on code changes (dev)
```

## How it works

`main()` parses args and builds a `uvicorn` command as a subprocess:
```python
[sys.executable, "-m", "uvicorn", "forgelab.api:app", "--host", ..., "--port", ...]
```

Using `sys.executable` ensures the same Python environment that has forgelab installed is the one running uvicorn.

## pyproject.toml entry point

```toml
[project.scripts]
forgelab = "forgelab.cli:main"
```

This is what makes `forgelab` available as a shell command after `pip install`.

## Persona data bundling

```toml
[tool.hatch.build.targets.wheel.force-include]
"src/forgelab/personas" = "forgelab/personas"
```

Persona files travel inside the wheel so `BaseAgent` can find them via `Path(__file__).parent.parent / "personas"` regardless of where forgelab is installed.
