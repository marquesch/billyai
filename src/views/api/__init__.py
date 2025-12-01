from views.api.v1 import v1_router
from fastapi import APIRouter

api_router = APIRouter(prefix="/api")


api_router.include_router(v1_router)
