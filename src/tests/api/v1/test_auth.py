from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from domain.entities import Tenant
from domain.entities import User
from infrastructure.persistence.memory.repositories.tenant_repository import InMemoryTenantRepository
from infrastructure.persistence.memory.repositories.user_repository import InMemoryUserRepository
from infrastructure.services.in_memory_temporary_storage_service import InMemoryTemporaryStorageService


@pytest.fixture
def tenant(in_memory_tenant_repository: InMemoryTenantRepository) -> Tenant:
    return in_memory_tenant_repository.create()


@pytest.fixture
def unregistered_user(in_memory_user_repository: InMemoryUserRepository, tenant: Tenant):
    return in_memory_user_repository.create(
        phone_number="41999999999",
        name="Test User",
        tenant_id=tenant.id,
        is_registered=False,
    )


@pytest.fixture
def registered_user(
    in_memory_user_repository: InMemoryUserRepository,
    tenant: Tenant,
    in_memory_temporary_storage_service: InMemoryTemporaryStorageService,
):
    in_memory_temporary_storage_service.set("token", {"phone_number": "41999999999", "name": "Test User"})
    return in_memory_user_repository.create(
        phone_number="41999999999",
        name="Test User",
        tenant_id=tenant.id,
        is_registered=True,
    )


def test_register_user(
    client: TestClient,
    in_memory_temporary_storage_service: InMemoryTemporaryStorageService,
    in_memory_user_repository: InMemoryUserRepository,
):
    with patch("application.services.registration_service.secrets.token_urlsafe") as token_mock:
        token_mock.return_value = "token"
        response = client.post("/api/v1/auth/register", json={"phone_number": "41999999999", "name": "Test User"})

    assert response.status_code == 200
    assert response.json()["detail"] == "A confirmation link was sent to your phone"
    assert in_memory_temporary_storage_service.get("token") == {"phone_number": "41999999999", "name": "Test User"}


def test_register_user_phone_taken(registered_user: User, client: TestClient):
    response = client.post("/api/v1/auth/register", json={"phone_number": "41999999999", "name": "Test User"})

    assert response.status_code == 409
    assert response.json()["detail"] == "Phone number taken"


def test_register_user_invalid_phone(client: TestClient):
    response = client.post("/api/v1/auth/register", json={"phone_number": "123", "name": "Test User"})

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid phone format"


def test_verify_registration(
    client: TestClient,
    unregistered_user: User,
    in_memory_temporary_storage_service: InMemoryTemporaryStorageService,
):
    response = client.post("/api/v1/auth/register/verify?token=token")

    assert response.json() == {}
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Test User",
        "phone_number": "41999999999",
        "tenant_id": 1,
        "is_registered": True,
    }
