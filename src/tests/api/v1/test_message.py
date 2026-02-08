from unittest import mock

import freezegun
from fastapi.testclient import TestClient

from domain.entities import Message
from domain.entities import User


def test_message_index(client: TestClient, mock_user: User, in_memory_messages: list[Message]):
    response = client.get("/api/v1/messages/")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "body": "User message",
            "author": "USER",
            "timestamp": "2025-01-01T13:00:00+00:00",
            "external_message_id": None,
            "broker": "API",
            "user_id": 1,
            "tenant_id": 1,
        },
        {
            "id": 2,
            "body": "Billy message",
            "author": "BILLY",
            "timestamp": "2025-01-01T13:01:00+00:00",
            "external_message_id": None,
            "broker": "API",
            "user_id": 1,
            "tenant_id": 1,
        },
        {
            "id": 3,
            "body": "User whatsapp message",
            "author": "USER",
            "timestamp": "2025-01-01T13:02:00+00:00",
            "external_message_id": "userwppmsgid",
            "broker": "WHATSAPP",
            "user_id": 1,
            "tenant_id": 1,
        },
        {
            "id": 4,
            "body": "Billy whatsapp message",
            "author": "BILLY",
            "timestamp": "2025-01-01T13:03:00+00:00",
            "external_message_id": "billywppmsgid",
            "broker": "WHATSAPP",
            "user_id": 1,
            "tenant_id": 1,
        },
    ]


def test_message_index_user_from_same_tenant(
    client: TestClient,
    mock_user_same_tenant: User,
    in_memory_messages: list[Message],
):
    response = client.get("/api/v1/messages/")

    assert response.status_code == 200
    assert response.json() == []


def test_message_index_user_from_another_tenant(
    client: TestClient,
    mock_user_from_another_tenant: User,
    in_memory_messages: list[Message],
):
    response = client.get("/api/v1/messages/")

    assert response.status_code == 200
    assert response.json() == []


def test_create_message(
    client: TestClient,
    mock_user: User,
    freezer: freezegun.api.FrozenDateTimeFactory,
    mock_async_task_dispatcher_service: mock.AsyncMock,
):
    freezer.move_to("2025-01-01T13:00:00Z")

    response = client.post(
        "/api/v1/messages/",
        json={
            "body": "Hey billy!",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "body": "Hey billy!",
        "author": "USER",
        "timestamp": "2025-01-01T13:00:00+00:00",
        "broker": "API",
        "external_message_id": None,
        "tenant_id": 1,
        "user_id": 1,
    }

    mock_async_task_dispatcher_service.dispatch.assert_called_with("process_message", message_id=1)
