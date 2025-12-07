from fastapi import APIRouter

from api.routes.v1 import auth
from api.routes.v1 import category

router = APIRouter(prefix="/v1")

router.include_router(auth.router)
router.include_router(category.router)
