"""Demo WebSocket server — streams a fixture JSON instead of running LangGraph."""
import asyncio
import json
import os

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware


def create_app(fixture_path: str, speed: float = 1.0) -> FastAPI:
    with open(fixture_path) as f:
        fixture = json.load(f)

    app = FastAPI(title="ForgeLab Demo")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.websocket("/ws")
    async def demo_ws(websocket: WebSocket):
        await websocket.accept()
        await websocket.receive_text()
        for entry in fixture:
            await asyncio.sleep(entry["delay_ms"] / 1000 * speed)
            await websocket.send_text(json.dumps(entry["message"]))

    return app


app = create_app(
    fixture_path=os.getenv("FORGELAB_DEMO_FIXTURE", "demo/arrow-bug-1148.json"),
    speed=float(os.getenv("FORGELAB_DEMO_SPEED", "1.0")),
)
