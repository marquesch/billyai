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

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8080/ws`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


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


@app.get("/demo")
async def get():
    return HTMLResponse(html)


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
