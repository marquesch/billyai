import pytest
from fastapi.testclient import TestClient

from domain.entities import User
from domain.ports.services import AMQPService
from infrastructure.persistence.memory.repositories.bill_repository import InMemoryBillRepository
from infrastructure.persistence.memory.repositories.category_repository import InMemoryCategoryRepository
from infrastructure.persistence.memory.repositories.message_repository import InMemoryMessageRepository
from infrastructure.persistence.memory.repositories.tenant_repository import InMemoryTenantRepository
from infrastructure.persistence.memory.repositories.user_repository import InMemoryUserRepository
from infrastructure.services.in_memory_temporary_storage_service import InMemoryTemporaryStorageService
from presentation.api import app
from presentation.api import dependencies


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def repositories_override(
    in_memory_user_repository: InMemoryUserRepository,
    in_memory_bill_repository: InMemoryBillRepository,
    in_memory_category_repository: InMemoryCategoryRepository,
    in_memory_message_repository: InMemoryMessageRepository,
    in_memory_tenant_repository: InMemoryTenantRepository,
    in_memory_temporary_storage_service: InMemoryTemporaryStorageService,
    mock_amqp_service: AMQPService,
):
    app.dependency_overrides = {
        dependencies.get_user_repository: lambda: in_memory_user_repository,
        dependencies.get_bill_repository: lambda: in_memory_bill_repository,
        dependencies.get_category_repository: lambda: in_memory_category_repository,
        dependencies.get_message_repository: lambda: in_memory_message_repository,
        dependencies.get_tenant_repository: lambda: in_memory_tenant_repository,
        dependencies.get_temporary_storage_service: lambda: in_memory_temporary_storage_service,
        dependencies.get_amqp_channel: lambda: mock_amqp_service,
    }


@pytest.fixture
def mock_async_task_dispatcher_service(mocker) -> mock.AsyncMock():
    async_task_dispatcher_service_mock = mocker.AsyncMock()
    app.dependency_overrides[dependencies.get_async_task_dispatcher_service] = (
        lambda: async_task_dispatcher_service_mock
    )
    return async_task_dispatcher_service_mock


@pytest.fixture
def unregistered_user(
    in_memory_temporary_storage_service: InMemoryTemporaryStorageService,
):
    in_memory_temporary_storage_service.set("token", {"phone_number": "5541999999999", "name": "Test User"})


@pytest.fixture
def user_login_initiated(registered_user: User, in_memory_temporary_storage_service: InMemoryTemporaryStorageService):
    in_memory_temporary_storage_service.set(
        f"user:{registered_user.id}:pin",
        {"pin": "999999", "user_phone": registered_user.phone_number},
    )
    return registered_user


@pytest.fixture
def mock_user(registered_user: User) -> User:
    app.dependency_overrides[dependencies.get_current_user] = lambda: registered_user
    return registered_user


@pytest.fixture
def mock_user_same_tenant(registered_user_same_tenant: User):
    app.dependency_overrides[dependencies.get_current_user] = lambda: registered_user_same_tenant
    return registered_user_same_tenant


@pytest.fixture
def mock_user_from_another_tenant(user_from_another_tenant: User) -> User:
    app.dependency_overrides[dependencies.get_current_user] = lambda: user_from_another_tenant
    return user_from_another_tenant
