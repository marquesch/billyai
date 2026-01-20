from collections.abc import Generator
from typing import Annotated

import redis
from aio_pika import RobustChannel
from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from application.services.async_task_service import AsyncTaskService
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
from domain.ports.services import AIAgentService
from domain.ports.services import AMQPService
from domain.ports.services import AsyncTaskDispatcherService
from domain.ports.services import PubsubService
from domain.ports.services import TemporaryStorageService
from domain.ports.services import UserEncodingService
from domain.ports.services import WhatsappBrokerMessageService
from infrastructure.config import settings
from infrastructure.config.settings import app_settings
from infrastructure.persistence.database import db_session
from infrastructure.persistence.database.repositories.bill_repository import DBBillRepository
from infrastructure.persistence.database.repositories.category_repository import DBCategoryRepository
from infrastructure.persistence.database.repositories.message_repository import DBMessageRepository
from infrastructure.persistence.database.repositories.tenant_repository import DBTenantRepository
from infrastructure.persistence.database.repositories.user_repository import DBUserRepository
from infrastructure.services.aio_pika_amqp_service import AioPikaAMQPService
from infrastructure.services.aio_pika_amqp_service import AioPikaPoolService
from infrastructure.services.amqp_async_task_dispatcher import AMQPAsyncTaskDispatcherService
from infrastructure.services.amqp_whatsapp_broker_message_service import AMQPWhatsappBrokerMessageService
from infrastructure.services.jwt_encoding_service import JWTUserEncodingService
from infrastructure.services.pydanticai_agent_service import PydanticAIAgentService
from infrastructure.services.redis_pubsub_service import RedisPubsubService
from infrastructure.services.redis_temporary_storage_service import RedisTemporaryStorageService

security = HTTPBearer()

aio_pika_pool_service = AioPikaPoolService(app_settings.rabbitmq_url)


def get_session() -> Generator[Session, None, None]:
    if settings.app_settings.environment == "testing":
        yield None
        return

    with db_session() as session:
        yield session


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


def get_temporary_storage_service() -> TemporaryStorageService:
    from infrastructure.services.redis_temporary_storage_service import redis_pool

    match settings.app_settings.environment:
        case "testing":
            return None
        case _:
            return RedisTemporaryStorageService(redis.Redis(connection_pool=redis_pool))


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


async def get_amqp_channel() -> RobustChannel:
    return await aio_pika_pool_service.get_channel()


def get_amqp_service(channel: Annotated[RobustChannel, Depends(get_amqp_channel)]) -> AMQPService:
    return AioPikaAMQPService(channel)


async def get_pubsub_service() -> PubsubService:
    from infrastructure.services.redis_pubsub_service import async_redis_pool

    if app_settings.environment != "testing":
        return RedisPubsubService(client=redis.asyncio.Redis(connection_pool=async_redis_pool))


def get_async_task_dispatcher_service(amqp_service: Annotated[AMQPService, Depends(get_amqp_service)]) -> AsyncTaskDispatcherService:
    if app_settings.environment != "testing":
        return AMQPAsyncTaskDispatcherService(amqp_service)


def get_whatsapp_broker_message_service(
    amqp_service: Annotated[AMQPService, Depends(get_amqp_service)],
) -> WhatsappBrokerMessageService:
    if app_settings.environment != "testing":
        return AMQPWhatsappBrokerMessageService(amqp_service)


def get_ai_agent_service(
    registration_service: Annotated[RegistrationService, Depends(get_registration_service)],
    temp_storage_service: Annotated[TemporaryStorageService, Depends(get_temporary_storage_service)],
    message_repo: Annotated[MessageRepository, Depends(get_message_repository)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    bill_service: Annotated[BillService, Depends(get_bill_service)],
    category_service: Annotated[CategoryService, Depends(get_category_service)],
) -> AIAgentService:
    if app_settings.environment != "testing":
        return PydanticAIAgentService(
            registration_service=registration_service,
            temp_storage_service=temp_storage_service,
            message_repository=message_repo,
            user_repository=user_repo,
            bill_service=bill_service,
            category_service=category_service,
            message_history_ttl_seconds=3600,
        )


def get_async_task_service(
    async_task_dispatcher: Annotated[AsyncTaskDispatcherService, Depends(get_async_task_dispatcher_service)],
    message_repo: Annotated[MessageRepository, Depends(get_message_repository)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    tenant_repo: Annotated[UserRepository, Depends(get_tenant_repository)],
    ai_agent_service: Annotated[AIAgentService, Depends(get_ai_agent_service)],
    pubsub_service: Annotated[PubsubService, Depends(get_pubsub_service)],
    whatasapp_broker_message_service: Annotated[
        WhatsappBrokerMessageService,
        Depends(get_whatsapp_broker_message_service),
    ],
) -> AsyncTaskService:
    if app_settings.environment != "testing":
        return AsyncTaskService(
            async_task_dispatcher=async_task_dispatcher,
            message_repo=message_repo,
            user_repo=user_repo,
            tenant_repo=tenant_repo,
            ai_agent_service=ai_agent_service,
            pubsub_service=pubsub_service,
            whatsapp_broker_message_service=whatasapp_broker_message_service,
        )
