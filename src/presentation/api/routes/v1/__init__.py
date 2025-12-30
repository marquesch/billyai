from fastapi import APIRouter

from presentation.api.routes.v1 import auth
from presentation.api.routes.v1 import bill
from presentation.api.routes.v1 import category
from presentation.api.routes.v1 import message
from presentation.api.routes.v1 import user

router = APIRouter(prefix="/v1")

router.include_router(auth.router)
router.include_router(category.router)
router.include_router(bill.router)
router.include_router(user.router)
router.include_router(message.router)
