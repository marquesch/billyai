from unittest import mock

from fastapi.testclient import TestClient

from domain.entities import MessageAuthor
from domain.entities import MessageBroker
from domain.entities import User
from infrastructure.persistence.memory.repositories.message_repository import InMemoryMessageRepository
from infrastructure.persistence.memory.repositories.user_repository import InMemoryUserRepository
from infrastructure.services.in_memory_temporary_storage_service import InMemoryTemporaryStorageService


def test_register_user_10_digits(
    client: TestClient,
    in_memory_temporary_storage_service: InMemoryTemporaryStorageService,
    in_memory_user_repository: InMemoryUserRepository,
):
    with mock.patch("application.services.registration_service.secrets.token_urlsafe") as token_mock:
        token_mock.return_value = "token"
        response = client.post("/api/v1/auth/register", json={"phone_number": "4199999999", "name": "Test User"})

    assert response.status_code == 200
    assert response.json()["detail"] == "A confirmation link was sent to your phone"
    assert in_memory_temporary_storage_service.get("token") == {"phone_number": "5541999999999", "name": "Test User"}


def test_register_user_11_digits(
    client: TestClient,
    in_memory_temporary_storage_service: InMemoryTemporaryStorageService,
    in_memory_user_repository: InMemoryUserRepository,
):
    with mock.patch("application.services.registration_service.secrets.token_urlsafe") as token_mock:
        token_mock.return_value = "token"
        response = client.post("/api/v1/auth/register", json={"phone_number": "41999999999", "name": "Test User"})

    assert response.status_code == 200
    assert response.json()["detail"] == "A confirmation link was sent to your phone"
    assert in_memory_temporary_storage_service.get("token") == {"phone_number": "5541999999999", "name": "Test User"}


def test_register_user_12_digits(
    client: TestClient,
    in_memory_temporary_storage_service: InMemoryTemporaryStorageService,
    in_memory_user_repository: InMemoryUserRepository,
):
    with mock.patch("application.services.registration_service.secrets.token_urlsafe") as token_mock:
        token_mock.return_value = "token"
        response = client.post("/api/v1/auth/register", json={"phone_number": "554199999999", "name": "Test User"})

    assert response.status_code == 200
    assert response.json()["detail"] == "A confirmation link was sent to your phone"
    assert in_memory_temporary_storage_service.get("token") == {"phone_number": "5541999999999", "name": "Test User"}


def test_register_user_13_digits(
    client: TestClient,
    in_memory_temporary_storage_service: InMemoryTemporaryStorageService,
    in_memory_user_repository: InMemoryUserRepository,
):
    with mock.patch("application.services.registration_service.secrets.token_urlsafe") as token_mock:
        token_mock.return_value = "token"
        response = client.post("/api/v1/auth/register", json={"phone_number": "5541999999999", "name": "Test User"})

    assert response.status_code == 200
    assert response.json()["detail"] == "A confirmation link was sent to your phone"
    assert in_memory_temporary_storage_service.get("token") == {"phone_number": "5541999999999", "name": "Test User"}


def test_register_user_phone_taken(in_memory_registered_user: User, client: TestClient):
    response = client.post("/api/v1/auth/register", json={"phone_number": "41999999999", "name": "Test User"})

    assert response.status_code == 409
    assert response.json()["detail"] == "Phone number taken"


def test_register_user_invalid_phone(client: TestClient):
    response = client.post("/api/v1/auth/register", json={"phone_number": "123", "name": "Test User"})

    assert response.status_code == 422
    assert "Invalid phone number format" in response.json()["detail"][0]["msg"]


def test_verify_registration(
    client: TestClient,
    in_memory_unregistered_user: User,
):
    response = client.post("/api/v1/auth/register/verify?token=token")

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Test User",
        "phone_number": "5541999999999",
        "tenant_id": 1,
        "is_registered": True,
    }


def test_verify_registration_with_created_user(
    client: TestClient,
    in_memory_registered_user: User,
    in_memory_unregistered_user: User,
    in_memory_temporary_storage_service: InMemoryTemporaryStorageService,
):
    response = client.post("/api/v1/auth/register/verify?token=token")

    assert response.status_code == 409
    assert response.json()["detail"] == "Phone number taken"


def test_verify_registration_with_invalid_token(client: TestClient):
    response = client.post("/api/v1/auth/register/verify?token=token")

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid token"


def test_login(
    client: TestClient,
    mock_async_task_dispatcher_service: mock.AsyncMock,
    in_memory_message_repository: InMemoryMessageRepository,
    in_memory_registered_user: User,
):
    response = client.post("/api/v1/auth/login", json={"phone_number": "41999999999"})

    message = in_memory_message_repository.get_by_id(1)

    assert response.status_code == 200
    mock_async_task_dispatcher_service.dispatch.assert_called_with("process_message", message_id=1)
    assert message.body.startswith("Seu PIN é ")
    assert message.author == MessageAuthor.SYSTEM
    assert message.broker == MessageBroker.WHATSAPP


def test_login_non_existent_phone_number(client: TestClient):
    response = client.post("/api/v1/auth/login", json={"phone_number": "41999999999"})

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_login_invalid_phone_number_format(client: TestClient):
    response = client.post("/api/v1/auth/login", json={"phone_number": "123"})

    assert response.status_code == 422
    assert "Invalid phone number format" in response.json()["detail"][0]["msg"]


def test_verify_login(client: TestClient, user_login_initiated: User):
    response = client.post("/api/v1/auth/login/verify", json={"pin": "999999", "phone_number": "41999999999"})

    assert response.status_code == 200
    assert "token" in response.json()
