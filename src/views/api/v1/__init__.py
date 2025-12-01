from fastapi import APIRouter

from views.api.v1.auth import auth_router
from views.api.v1.category import category_router

v1_router = APIRouter(prefix="/v1")

v1_router.include_router(auth_router)
v1_router.include_router(category_router)
