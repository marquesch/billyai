import pytest

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
