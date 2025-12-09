from fastapi import APIRouter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from infrastructure.config.settings import app_settings
from presentation.api.routes import v1

app = FastAPI(debug=app_settings.debug)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_credentials=True)

router = APIRouter(prefix="/api")
router.include_router(v1.router)

app.include_router(router)
