import asyncio
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import FastAPI
from fastapi import Request
from fastapi import WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from domain.entities import User
from domain.ports.services import PubsubService
from infrastructure.config.settings import app_settings
from infrastructure.di import global_registry
from infrastructure.di import setup_global_registry
from presentation.api import dependencies
from presentation.api.routes import v1


@asynccontextmanager
async def lifespan(app: FastAPI):
    await setup_global_registry()
    yield


app = FastAPI(debug=app_settings.debug, lifespan=lifespan)


@app.middleware("http")
async def create_di_container(request: Request, call_next):
    async with global_registry.scope():
        response = await call_next(request)
        return response


app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_credentials=True)


api_router = APIRouter(prefix="/api")
api_router.include_router(v1.router)

app.include_router(api_router)


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user: Annotated[User, Depends(dependencies.get_current_user)],
    pubsub: Annotated[PubsubService, Depends(dependencies.get_pubsub_service)],
):
    await websocket.accept()
    await pubsub.subscribe(str(user.tenant_id))

    async for message in pubsub.listen():
        await websocket.send_text(message)
