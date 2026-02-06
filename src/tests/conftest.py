import datetime

import pytest

from domain.entities import Bill
from domain.entities import Category
from domain.entities import Message
from domain.entities import MessageAuthor
from domain.entities import MessageBroker
from domain.entities import Tenant
from domain.entities import User
from domain.ports.services import AMQPService
from infrastructure.persistence.memory.repositories import InMemoryDatabase
from infrastructure.persistence.memory.repositories.bill_repository import InMemoryBillRepository
from infrastructure.persistence.memory.repositories.category_repository import InMemoryCategoryRepository
from infrastructure.persistence.memory.repositories.message_repository import InMemoryMessageRepository
from infrastructure.persistence.memory.repositories.tenant_repository import InMemoryTenantRepository
from infrastructure.persistence.memory.repositories.user_repository import InMemoryUserRepository
from infrastructure.services.in_memory_temporary_storage_service import InMemoryTemporaryStorageService


@pytest.fixture
def in_memory_database() -> InMemoryDatabase:
    return InMemoryDatabase()


@pytest.fixture
def in_memory_user_repository(in_memory_database: InMemoryDatabase) -> InMemoryUserRepository:
    return InMemoryUserRepository(in_memory_database=in_memory_database)


@pytest.fixture
def in_memory_bill_repository(in_memory_database: InMemoryDatabase) -> InMemoryBillRepository:
    return InMemoryBillRepository(in_memory_database=in_memory_database)


@pytest.fixture
def in_memory_category_repository(in_memory_database: InMemoryDatabase) -> InMemoryCategoryRepository:
    return InMemoryCategoryRepository(in_memory_database=in_memory_database)


@pytest.fixture
def in_memory_message_repository(in_memory_database: InMemoryDatabase) -> InMemoryMessageRepository:
    return InMemoryMessageRepository(in_memory_database=in_memory_database)


@pytest.fixture
def in_memory_tenant_repository(in_memory_database: InMemoryDatabase) -> InMemoryTenantRepository:
    return InMemoryTenantRepository(in_memory_database=in_memory_database)


@pytest.fixture
def in_memory_temporary_storage_service() -> InMemoryTemporaryStorageService:
    return InMemoryTemporaryStorageService()


@pytest.fixture
def mock_amqp_service(mocker) -> AMQPService:
    return mocker.AsyncMock()


@pytest.fixture
def tenant(in_memory_tenant_repository: InMemoryTenantRepository) -> Tenant:
    return in_memory_tenant_repository.create()


@pytest.fixture
def default_category(in_memory_category_repository: InMemoryCategoryRepository, tenant: Tenant) -> Category:
    return in_memory_category_repository.create(
        tenant_id=tenant.id,
        name="Default Category",
        description="Default Category description",
    )


@pytest.fixture
def another_category(in_memory_category_repository: InMemoryCategoryRepository, tenant: Tenant) -> Category:
    return in_memory_category_repository.create(
        tenant_id=tenant.id,
        name="Another Category",
        description="Another Category description",
    )


@pytest.fixture
def registered_user(
    in_memory_user_repository: InMemoryUserRepository,
    tenant: Tenant,
) -> User:
    return in_memory_user_repository.create(
        phone_number="5541999999999",
        name="Test User",
        tenant_id=tenant.id,
        is_registered=True,
    )


@pytest.fixture
def registered_user_same_tenant(
    in_memory_user_repository: InMemoryUserRepository,
    tenant: Tenant,
) -> User:
    return in_memory_user_repository.create(
        phone_number="5541999999997",
        name="User Same Tenant",
        tenant_id=tenant.id,
        is_registered=True,
    )


@pytest.fixture
def another_tenant(in_memory_tenant_repository: InMemoryTenantRepository) -> Tenant:
    return in_memory_tenant_repository.create()


@pytest.fixture
def user_from_another_tenant(in_memory_user_repository: InMemoryUserRepository, another_tenant: Tenant) -> User:
    return in_memory_user_repository.create(
        phone_number="5541999999998",
        name="User From Another Tenant",
        tenant_id=another_tenant.id,
        is_registered=True,
    )


@pytest.fixture
def category_from_another_tenant(in_memory_category_repository: InMemoryCategoryRepository, another_tenant: Tenant):
    return in_memory_category_repository.create(
        tenant_id=another_tenant.id,
        name="Category From Another Tenant",
        description="Category From Another Tenant Description",
    )


@pytest.fixture
def bills(
    in_memory_bill_repository: InMemoryBillRepository,
    default_category: Category,
    another_category: Category,
    tenant: Tenant,
) -> list[Bill]:
    return [
        in_memory_bill_repository.create(
            tenant_id=tenant.id,
            category_id=default_category.id,
            date=datetime.datetime.strptime("2012-12-12", "%Y-%m-%d").date(),
            value=10.5,
        ),
        in_memory_bill_repository.create(
            tenant_id=tenant.id,
            category_id=default_category.id,
            date=datetime.datetime.strptime("2024-12-12", "%Y-%m-%d").date(),
            value=99.90,
        ),
        in_memory_bill_repository.create(
            tenant_id=tenant.id,
            category_id=another_category.id,
            date=datetime.datetime.strptime("2024-12-13", "%Y-%m-%d").date(),
            value=199.90,
        ),
    ]


@pytest.fixture
def messages(
    in_memory_message_repository: InMemoryMessageRepository,
    tenant: Tenant,
    registered_user: User,
) -> list[Message]:
    return [
        in_memory_message_repository.create(
            body="User message",
            author=MessageAuthor.USER,
            timestamp=datetime.datetime.fromisoformat("2025-01-01T13:00:00Z"),
            broker=MessageBroker.API,
            user_id=registered_user.id,
            tenant_id=tenant.id,
        ),
        in_memory_message_repository.create(
            body="Billy message",
            author=MessageAuthor.BILLY,
            timestamp=datetime.datetime.fromisoformat("2025-01-01T13:01:00Z"),
            broker=MessageBroker.API,
            user_id=registered_user.id,
            tenant_id=tenant.id,
        ),
        in_memory_message_repository.create(
            body="User whatsapp message",
            author=MessageAuthor.USER,
            timestamp=datetime.datetime.fromisoformat("2025-01-01T13:02:00Z"),
            broker=MessageBroker.WHATSAPP,
            external_message_id="userwppmsgid",
            user_id=registered_user.id,
            tenant_id=tenant.id,
        ),
        in_memory_message_repository.create(
            body="Billy whatsapp message",
            author=MessageAuthor.BILLY,
            timestamp=datetime.datetime.fromisoformat("2025-01-01T13:03:00Z"),
            broker=MessageBroker.WHATSAPP,
            external_message_id="billywppmsgid",
            user_id=registered_user.id,
            tenant_id=tenant.id,
        ),
    ]
