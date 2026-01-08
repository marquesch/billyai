import inspect
from collections.abc import Callable
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any
from typing import TypeVar

import redis

from application.services.bill_service import BillService
from application.services.category_service import CategoryService
from application.services.registration_service import RegistrationService
from domain.ports.repositories import BillRepository
from domain.ports.repositories import CategoryRepository
from domain.ports.repositories import MessageRepository
from domain.ports.repositories import TenantRepository
from domain.ports.repositories import UserRepository
from domain.ports.services import AIAgentService
from domain.ports.services import AMQPService
from domain.ports.services import TemporaryStorageService
from infrastructure.config.settings import app_settings
from infrastructure.persistence.database import SessionLocal
from infrastructure.persistence.database.repositories.bill_repository import DBBillRepository
from infrastructure.persistence.database.repositories.category_repository import DBCategoryRepository
from infrastructure.persistence.database.repositories.message_repository import DBMessageRepository
from infrastructure.persistence.database.repositories.tenant_repository import DBTenantRepository
from infrastructure.persistence.database.repositories.user_repository import DBUserRepository
from infrastructure.services.aio_pika_amqp_service import AioPikaAMQPMessagingService
from infrastructure.services.aio_pika_amqp_service import AioPikaPoolService
from infrastructure.services.pydanticai_agent_service import PydanticAIAgentService
from infrastructure.services.redis_temporary_storage_service import RedisTemporaryStorageService
from infrastructure.services.redis_temporary_storage_service import pool

T = TypeVar("T")

_current_registry_container: ContextVar["DIContainer | None"] = ContextVar("current_registry", default=None)
_singletons: dict[type, Any] = {}


class DIContainer:
    def __init__(
        self,
        factories: dict[type, Callable],
        dependencies: dict[type, list[type]],
    ):
        self._factories = factories
        self._dependencies = dependencies
        self._instances: dict[type, Any] = {}

    async def get(self, cls: type[T]) -> T:
        if cls in _singletons:
            return _singletons[cls]

        if cls in self._instances:
            return self._instances[cls]

        if cls not in self._factories:
            raise ValueError(f"No factory registered for '{cls.__name__}'")

        deps = [await self.get(dep_cls) for dep_cls in self._dependencies[cls]]

        result = self._factories[cls](*deps)

        if inspect.iscoroutine(result):
            result = await result

        self._instances[cls] = result
        return result

    def commit(self):
        from infrastructure.persistence.database import SessionLocal

        session = self._instances.get(SessionLocal)
        if session is not None:
            session.commit()

    async def close(self):
        for obj in self._instances.values():
            if hasattr(obj, "close"):
                close_method = obj.close()
                if inspect.iscoroutine(close_method):
                    await close_method
        self._instances.clear()


class DIRegistry:
    def __init__(self):
        self._factories: dict[type, Callable] = {}
        self._dependencies: dict[type, list[type]] = {}
        self._instances: dict[type, Any] = {}

    def register(
        self,
        interface: type,
        factory: Callable,
        dependencies: list[type] | None = None,
        is_singleton: bool = False,
    ) -> None:
        self._factories[interface] = factory
        self._dependencies[interface] = dependencies or []

        if is_singleton:
            temp_container = self.create_container()
            singleton = temp_container.get(interface)
            _singletons[interface] = singleton

    def create_container(self) -> DIContainer:
        return DIContainer(
            factories=self._factories.copy(),
            dependencies=self._dependencies.copy(),
        )

    @asynccontextmanager
    async def scope(self):
        container = self.create_container()
        token = _current_registry_container.set(container)
        try:
            yield container
            container.commit()
        finally:
            await container.close()
            _current_registry_container.reset(token)


def get_current_container() -> DIContainer:
    container = _current_registry_container.get()
    if container is None:
        raise RuntimeError("No active DI scope. Use 'async with registry.scope()' first.")
    return container


async def resolve(cls: type[T]) -> T:
    return await get_current_container().get(cls)


global_registry = DIRegistry()


async def setup_global_registry() -> None:
    global_registry.register(SessionLocal, factory=SessionLocal)

    global_registry.register(
        UserRepository,
        factory=lambda db_session: DBUserRepository(db_session),
        dependencies=[SessionLocal],
    )

    global_registry.register(
        BillRepository,
        factory=lambda db_session: DBBillRepository(db_session),
        dependencies=[SessionLocal],
    )

    global_registry.register(
        CategoryRepository,
        factory=lambda db_session: DBCategoryRepository(db_session),
        dependencies=[SessionLocal],
    )

    global_registry.register(
        CategoryService,
        factory=lambda category_repository: CategoryService(category_repository),
        dependencies=[CategoryRepository],
    )

    global_registry.register(
        BillService,
        factory=lambda bill_repository, category_repository: BillService(bill_repository, category_repository),
        dependencies=[BillRepository, CategoryRepository],
    )

    global_registry.register(
        MessageRepository,
        factory=lambda db_session: DBMessageRepository(db_session),
        dependencies=[SessionLocal],
    )

    global_registry.register(
        TenantRepository,
        factory=lambda db_session: DBTenantRepository(db_session),
        dependencies=[SessionLocal],
    )

    global_registry.register(
        TemporaryStorageService,
        factory=lambda: RedisTemporaryStorageService(redis.Redis(connection_pool=pool)),
    )

    global_registry.register(
        RegistrationService,
        factory=lambda user_repository,
        tenant_repository,
        category_repository,
        temporary_storage_service: RegistrationService(
            user_repository,
            tenant_repository,
            category_repository,
            temporary_storage_service,
            user_validation_token_ttl_seconds=3600,
        ),
        dependencies=[UserRepository, TenantRepository, CategoryRepository, TemporaryStorageService],
    )

    global_registry.register(
        AIAgentService,
        factory=lambda registration_service,
        temp_storage_service,
        message_repository,
        user_repository,
        bill_service,
        category_service: PydanticAIAgentService(
            registration_service,
            temp_storage_service,
            message_repository,
            user_repository,
            bill_service,
            category_service,
            3600,
        ),
        dependencies=[
            RegistrationService,
            TemporaryStorageService,
            MessageRepository,
            UserRepository,
            BillService,
            CategoryService,
        ],
    )

    def get_broker_url():
        if app_settings.environment != "test":
            return app_settings.rabbitmq_url

    def get_aio_pika_pool_service():
        if app_settings.environment != "test":
            return AioPikaPoolService(get_broker_url())

    global_registry.register(
        AioPikaPoolService,
        factory=get_aio_pika_pool_service,
    )

    async def get_amqp_service(amqp_pool_service: AioPikaPoolService):
        return AioPikaAMQPMessagingService(await amqp_pool_service.get_channel())

    global_registry.register(
        AMQPService,
        factory=get_amqp_service,
        dependencies=[AioPikaPoolService],
    )
