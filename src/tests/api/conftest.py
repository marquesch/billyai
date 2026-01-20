import pytest
from fastapi.testclient import TestClient

from infrastructure.persistence.memory.repositories.bill_repository import InMemoryBillRepository
from infrastructure.persistence.memory.repositories.category_repository import InMemoryCategoryRepository
from infrastructure.persistence.memory.repositories.message_repository import InMemoryMessageRepository
from infrastructure.persistence.memory.repositories.tenant_repository import InMemoryTenantRepository
from infrastructure.persistence.memory.repositories.user_repository import InMemoryUserRepository
from infrastructure.services.in_memory_temporary_storage_service import InMemoryTemporaryStorageService
from presentation.api import app
from presentation.api import dependencies


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def in_memory_user_repository(in_memory_user_repository: InMemoryUserRepository) -> InMemoryUserRepository:
    app.dependency_overrides[dependencies.get_user_repository] = lambda: in_memory_user_repository
    return in_memory_user_repository


@pytest.fixture
def in_memory_bill_repository(in_memory_bill_repository: InMemoryBillRepository) -> InMemoryBillRepository:
    app.dependency_overrides[dependencies.get_bill_repository] = lambda: in_memory_bill_repository
    return in_memory_bill_repository


@pytest.fixture
def in_memory_category_repository(
    in_memory_category_repository: InMemoryCategoryRepository,
) -> InMemoryCategoryRepository:
    app.dependency_overrides[dependencies.get_category_repository] = lambda: in_memory_category_repository
    return in_memory_category_repository


@pytest.fixture
def in_memory_message_repository(in_memory_message_repository: InMemoryMessageRepository) -> InMemoryMessageRepository:
    app.dependency_overrides[dependencies.get_message_repository] = lambda: in_memory_message_repository
    return in_memory_message_repository


@pytest.fixture
def in_memory_tenant_repository(in_memory_tenant_repository: InMemoryTenantRepository) -> InMemoryTenantRepository:
    app.dependency_overrides[dependencies.get_tenant_repository] = lambda: in_memory_tenant_repository
    return in_memory_tenant_repository


@pytest.fixture
def in_memory_temporary_storage_service(
    in_memory_temporary_storage_service: InMemoryTemporaryStorageService,
) -> InMemoryTemporaryStorageService:
    app.dependency_overrides[dependencies.get_temporary_storage_service] = lambda: in_memory_temporary_storage_service
    return in_memory_temporary_storage_service
