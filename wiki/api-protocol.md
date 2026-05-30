# WebSocket API Protocol

**File:** `src/forgelab/api.py`

## Endpoints

- `GET /health` → `{"status": "ok"}` (health check)
- `WS /ws` — bidirectional workflow stream

## Server → Client Messages

All messages are JSON objects with a `type` discriminator.

```typescript
// Agent changed state
{ type: "agent_status", agent: AgentName, status: "running"|"done"|"reviewing" }

// Agent produced output
{ type: "chat_message", agent: AgentName, model: string, content: string, ts: string }

// Token usage update
{ type: "cost_update", agent: AgentName, tokens: number, cost_usd: number }

// Evaluator recommends a premium model
{ type: "upgrade_prompt", recommended_model: string, benchmark_reason: string, score: string, cost_per_1m: string }

// Researcher browsed a URL
{ type: "browser_update", url: string, scanning: boolean }

// Verifier ran a test
{ type: "test_result", name: string, passed: boolean, duration_ms: number }

// Workflow finished
{ type: "workflow_complete", summary: object }

// Error occurred
{ type: "error", message: string }
```

## Client → Server Messages

```json
{"type": "task", "task": "<user task text>"}
{"type": "upgrade_response", "accepted": true|false}
{"type": "interrupt", "text": "<user injection>"}
```

## Upgrade Prompt Flow

1. Evaluator recommends premium model → api.py sends `upgrade_prompt`
2. api.py waits up to 30 seconds for `upgrade_response`
3. If `accepted: true` → `model_in_use` switches to recommended model
4. If `accepted: false` or timeout → continues with local Ollama model

## Test Framework Detection (on task arrival)

```python
if (cwd / "Cargo.toml").exists():           → "cargo"
elif "jest" in (cwd / "package.json").read_text(): → "jest"
elif (cwd / "CMakeLists.txt").exists():     → "ctest"
elif (cwd / "go.mod").exists():             → "go-test"
else:                                        → "pytest"
```

## CORS

Allows `http://localhost:5173` (Vite dev server). Add production origins here before deploying.
