import json
import pytest
from fastapi.testclient import TestClient


def _make_fixture(tmp_path, entries):
    p = tmp_path / "fixture.json"
    p.write_text(json.dumps(entries))
    return str(p)


def test_streams_all_messages_in_order(tmp_path):
    from forgelab.demo_server import create_app

    entries = [
        {"delay_ms": 0, "message": {"type": "agent_status", "agent": "evaluator", "status": "running"}},
        {"delay_ms": 0, "message": {"type": "chat_message", "agent": "evaluator", "content": "hi", "ts": "00:00"}},
        {"delay_ms": 0, "message": {"type": "workflow_complete", "summary": {}}},
    ]
    app = create_app(_make_fixture(tmp_path, entries), speed=1.0)
    client = TestClient(app)

    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"type": "task", "task": "anything"}))
        msgs = [json.loads(ws.receive_text()) for _ in entries]

    assert msgs[0] == {"type": "agent_status", "agent": "evaluator", "status": "running"}
    assert msgs[1]["type"] == "chat_message"
    assert msgs[2] == {"type": "workflow_complete", "summary": {}}


def test_speed_multiplier_scales_delays(tmp_path, monkeypatch):
    import asyncio
    from forgelab.demo_server import create_app

    slept = []

    async def fake_sleep(seconds):
        slept.append(seconds)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    entries = [
        {"delay_ms": 1000, "message": {"type": "workflow_complete", "summary": {}}},
    ]
    app = create_app(_make_fixture(tmp_path, entries), speed=0.5)
    client = TestClient(app)

    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"type": "task", "task": "x"}))
        ws.receive_text()

    assert slept == [pytest.approx(0.5)]


def test_health_endpoint(tmp_path):
    from forgelab.demo_server import create_app

    app = create_app(_make_fixture(tmp_path, []), speed=1.0)
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
