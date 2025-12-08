from fastapi import APIRouter

from presentation.api.routes.v1 import auth
from presentation.api.routes.v1 import bill
from presentation.api.routes.v1 import category

router = APIRouter(prefix="/v1")

router.include_router(auth.router)
router.include_router(category.router)
router.include_router(bill.router)
