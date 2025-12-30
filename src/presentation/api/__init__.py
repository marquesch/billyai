from contextlib import asynccontextmanager

from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware

from infrastructure.config.settings import app_settings
from infrastructure.di import global_registry
from infrastructure.di import setup_global_registry
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


router = APIRouter(prefix="/api")
router.include_router(v1.router)

app.include_router(router)
