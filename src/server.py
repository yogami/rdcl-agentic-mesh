import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from src.state import GlobalState
from src.simulate import simulate

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Determine policy from environment to let us test both
    policy = os.environ.get("MESH_POLICY", "agentic")
    # Start simulation logic in background
    task = asyncio.create_task(simulate(policy, 15, 86400)) # Run forever basically
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    q = GlobalState.register_client()
    try:
        await websocket.send_json(GlobalState.get_state())
        while True:
            state = await q.get()
            await websocket.send_json(state)
    except Exception:
        pass
    finally:
        GlobalState.unregister_client(q)

dashboard_dir = os.path.join(os.path.dirname(__file__), "../dashboard")
if os.path.exists(dashboard_dir):
    app.mount("/", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")
