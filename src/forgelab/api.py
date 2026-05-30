"""
FastAPI backend — WebSocket streaming for LangGraph workflow events.
Each node completion streams a set of typed messages to the connected client.
"""
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from forgelab.graph import build_graph
from forgelab.state import WorkflowState

app = FastAPI(title="ForgeLab API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_graph = build_graph()
_BASE_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

_AGENT_MODELS = {
    "evaluator": _BASE_MODEL,
    "router": _BASE_MODEL,
    "researcher": _BASE_MODEL,
    "architect": _BASE_MODEL,
    "coder": _BASE_MODEL,
    "reviewer": _BASE_MODEL,
    "verifier": f"{_BASE_MODEL} + docker",
}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    async def send(msg: dict):
        await websocket.send_text(json.dumps(msg))

    try:
        data = json.loads(await websocket.receive_text())
        if data.get("type") != "task":
            await send({"type": "error", "message": "Expected {type: 'task'}"})
            return

        task = data["task"]
        model_in_use = _BASE_MODEL

        cwd = Path.cwd()
        if (cwd / "Cargo.toml").exists():
            detected_framework = "cargo"
        elif (cwd / "package.json").exists() and "jest" in (cwd / "package.json").read_text():
            detected_framework = "jest"
        elif (cwd / "CMakeLists.txt").exists():
            detected_framework = "ctest"
        elif (cwd / "go.mod").exists():
            detected_framework = "go-test"
        else:
            detected_framework = "pytest"

        initial_state = WorkflowState(
            task=task,
            task_type=None,
            complexity=None,
            upgrade_recommendation=None,
            model_in_use=model_in_use,
            findings=None,
            plan=None,
            code_changes=None,
            review_feedback=None,
            test_results=None,
            test_framework=detected_framework,
            agent_messages=[],
            session_cost={},
            interrupt=None,
        )

        ts = lambda: datetime.now().strftime("%H:%M:%S")  # noqa: E731

        try:
            async for event in _graph.astream(initial_state, stream_mode="updates"):
                for node_name, update in event.items():
                    if not isinstance(update, dict):
                        continue
                    await send({"type": "agent_status", "agent": node_name, "status": "running"})

                    cost_entry = update.get("session_cost", {}).get(node_name, {})
                    if cost_entry:
                        await send({
                            "type": "cost_update",
                            "agent": node_name,
                            "tokens": cost_entry.get("tokens", 0),
                            "cost_usd": cost_entry.get("cost_usd", 0.0),
                        })

                    if node_name == "evaluator" and update.get("upgrade_recommendation"):
                        rec = update["upgrade_recommendation"]
                        await send({"type": "upgrade_prompt", **rec})
                        try:
                            resp = json.loads(
                                await asyncio.wait_for(websocket.receive_text(), timeout=30)
                            )
                            if resp.get("type") == "upgrade_response" and resp.get("accepted"):
                                model_in_use = rec["recommended_model"]
                        except asyncio.TimeoutError:
                            pass

                    content = _format_content(node_name, update)
                    if content:
                        status = "reviewing" if node_name == "reviewer" else "done"
                        await send({
                            "type": "chat_message",
                            "agent": node_name,
                            "model": _AGENT_MODELS.get(node_name, model_in_use),
                            "content": content,
                            "ts": ts(),
                        })
                        await send({"type": "agent_status", "agent": node_name, "status": status})

                    if node_name == "researcher" and update.get("findings"):
                        await send({"type": "browser_update", "url": "codebase + web", "scanning": False})

                    if node_name == "verifier" and update.get("test_results"):
                        tr = update["test_results"]
                        for i in range(tr.get("tests_run", 0)):
                            await send({
                                "type": "test_result",
                                "name": f"test_{i+1}",
                                "passed": tr["passed"],
                                "duration_ms": 150,
                            })

            await send({"type": "workflow_complete", "summary": {}})
        except Exception as exc:
            await send({"type": "error", "message": str(exc)})

    except WebSocketDisconnect:
        pass


def _fmt_verifier(tr: dict) -> str:
    verdict = "✅ PASS" if tr.get("passed") else "❌ FAIL"
    stdout = (tr.get("stdout") or "").strip()
    stderr = (tr.get("stderr") or "").strip()
    tests_run = tr.get("tests_run", 0)
    timed_out = tr.get("timed_out", False)
    lines = [f"{verdict}  ({tests_run} test{'s' if tests_run != 1 else ''} run)"]
    if timed_out:
        lines.append("⏱ Timed out")
    if stdout:
        lines.append(f"\n```\n{stdout[:800]}\n```")
    if stderr and not tr.get("passed"):
        lines.append(f"\n```\n{stderr[:400]}\n```")
    return "\n".join(lines)


def _format_content(node: str, update: dict) -> str:
    mapping = {
        "evaluator": lambda u: f"Complexity: **{u.get('complexity')}**",
        "router": lambda u: f"Task type: `{u.get('task_type')}`",
        "researcher": lambda u: u.get("findings", ""),
        "architect": lambda u: u.get("plan", ""),
        "coder": lambda u: u.get("code_changes", ""),
        "reviewer": lambda u: u.get("review_feedback", ""),
        "verifier": lambda u: _fmt_verifier(u.get("test_results", {})),
    }
    fn = mapping.get(node)
    return fn(update) if fn else ""
