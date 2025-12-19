from collections.abc import Generator
from typing import Annotated

import redis
from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from application.services.authentication_service import AuthenticationService
from application.services.bill_service import BillService
from application.services.category_service import CategoryService
from application.services.registration_service import RegistrationService
from domain.exceptions import AuthError
from domain.ports.repositories import BillRepository
from domain.ports.repositories import CategoryRepository
from domain.ports.repositories import MessageRepository
from domain.ports.repositories import TenantRepository
from domain.ports.repositories import UserRepository
from domain.ports.services import TemporaryStorageService
from domain.ports.services import UserEncodingService
from infrastructure.config import settings
from infrastructure.config.settings import app_settings
from infrastructure.persistence.database import db_session
from infrastructure.persistence.database.repositories.bill_repository import DBBillRepository
from infrastructure.persistence.database.repositories.category_repository import DBCategoryRepository
from infrastructure.persistence.database.repositories.message_repository import DBMessageRepository
from infrastructure.persistence.database.repositories.tenant_repository import DBTenantRepository
from infrastructure.persistence.database.repositories.user_repository import DBUserRepository
from infrastructure.services.jwt_encoding_service import JWTUserEncodingService
from infrastructure.services.redis_temporary_storage_service import RedisTemporaryStorageService

security = HTTPBearer()


def get_session() -> Generator[Session, None, None]:
    if settings.app_settings.environment == "testing":
        yield None
        return

    with db_session() as session:
        yield session


def get_redis_client() -> redis.Redis:
    from infrastructure.services.redis_temporary_storage_service import pool

    return redis.Redis(connection_pool=pool)


def get_tenant_repository(session: Annotated[Session, Depends(get_session)]) -> TenantRepository:
    match settings.app_settings.environment:
        case "testing":
            return None
        case _:
            return DBTenantRepository(session)


def get_user_repository(session: Annotated[Session, Depends(get_session)]) -> UserRepository:
    match settings.app_settings.environment:
        case "testing":
            return None
        case _:
            return DBUserRepository(session)


def get_bill_repository(session: Annotated[Session, Depends(get_session)]) -> BillRepository:
    match settings.app_settings.environment:
        case "testing":
            return None
        case _:
            return DBBillRepository(session)


def get_category_repository(session: Annotated[Session, Depends(get_session)]) -> CategoryRepository:
    match settings.app_settings.environment:
        case "testing":
            return None
        case _:
            return DBCategoryRepository(session)


def get_message_repository(session: Annotated[Session, Depends(get_session)]) -> MessageRepository:
    match settings.app_settings.environment:
        case "testing":
            return None
        case _:
            return DBMessageRepository(session)


def get_temporary_storage_service(
    redis_client: Annotated[redis.Redis, Depends(get_redis_client)],
) -> TemporaryStorageService:
    match settings.app_settings.environment:
        case "testing":
            return None
        case _:
            return RedisTemporaryStorageService(redis_client)


def get_user_encoding_service() -> UserEncodingService:
    match settings.app_settings.environment:
        case "testing":
            return None
        case _:
            return JWTUserEncodingService()


def get_authentication_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    temporary_storage_service: Annotated[TemporaryStorageService, Depends(get_temporary_storage_service)],
    user_encoding_service: Annotated[UserEncodingService, Depends(get_user_encoding_service)],
) -> AuthenticationService:
    return AuthenticationService(
        user_repository,
        temporary_storage_service,
        user_encoding_service,
        app_settings.user_pin_ttl_seconds,
        app_settings.user_token_ttl,
    )


def get_registration_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    tenant_repository: Annotated[UserRepository, Depends(get_tenant_repository)],
    category_repository: Annotated[CategoryRepository, Depends(get_category_repository)],
    temporary_storage_service: Annotated[TemporaryStorageService, Depends(get_temporary_storage_service)],
) -> RegistrationService:
    return RegistrationService(
        user_repository,
        tenant_repository,
        category_repository,
        temporary_storage_service,
        app_settings.user_validation_token_ttl_seconds,
    )


def get_category_service(
    category_repository: Annotated[CategoryRepository, Depends(get_category_repository)],
) -> CategoryService:
    return CategoryService(category_repository)


def get_bill_service(
    bill_repository: Annotated[BillRepository, Depends(get_bill_repository)],
    category_repository: Annotated[CategoryRepository, Depends(get_category_repository)],
) -> BillService:
    return BillService(bill_repository, category_repository)


def get_current_user(
    authentication_service: Annotated[AuthenticationService, Depends(get_authentication_service)],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
):
    try:
        return authentication_service.authenticate_user(credentials.credentials)
    except AuthError as e:
        raise HTTPException(401) from e
