from fastapi.testclient import TestClient

from domain.entities import User


def test_update_user(client: TestClient, mock_user: User):
    response = client.put("/api/v1/users/me", json={"name": "Updated User Name"})

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Updated User Name",
        "phone_number": "5541999999999",
        "tenant_id": 1,
        "is_registered": True,
    }


def test_update_user_no_logged_user(client: TestClient):
    response = client.put("/api/v1/users/me", json={"name": "Updated User Name"})

    assert response.status_code == 401
