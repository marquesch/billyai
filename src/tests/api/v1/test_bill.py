from fastapi.testclient import TestClient

from domain.entities import Bill
from domain.entities import Category
from domain.entities import User


def test_index(client: TestClient, mock_user: User, in_memory_bills: list[Bill]):
    response = client.get("/api/v1/bills/")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "value": 10.5,
            "date": "2012-12-12",
            "category_id": 1,
            "tenant_id": 1,
        },
        {
            "id": 2,
            "value": 99.9,
            "date": "2024-12-12",
            "category_id": 1,
            "tenant_id": 1,
        },
        {
            "id": 3,
            "value": 199.90,
            "date": "2024-12-13",
            "category_id": 2,
            "tenant_id": 1,
        },
    ]


def test_index_filter_by_date_range(client: TestClient, mock_user: User, in_memory_bills: list[Bill]):
    response = client.get("/api/v1/bills/?date_range=2012-12-12&date_range=2012-12-13")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "value": 10.5,
            "date": "2012-12-12",
            "category_id": 1,
            "tenant_id": 1,
        },
    ]


def test_index_filter_by_category_id(client: TestClient, mock_user: User, in_memory_bills: list[Bill]):
    response = client.get("/api/v1/bills/?category_id=2")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 3,
            "value": 199.90,
            "date": "2024-12-13",
            "category_id": 2,
            "tenant_id": 1,
        },
    ]


def test_index_filter_by_value_range(client: TestClient, mock_user: User, in_memory_bills: list[Bill]):
    response = client.get("/api/v1/bills/?value_range=99&value_range=200")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 2,
            "value": 99.9,
            "date": "2024-12-12",
            "category_id": 1,
            "tenant_id": 1,
        },
        {
            "id": 3,
            "value": 199.90,
            "date": "2024-12-13",
            "category_id": 2,
            "tenant_id": 1,
        },
    ]


def test_index_same_tenant(client: TestClient, mock_user_same_tenant: User, in_memory_bills: list[Bill]):
    response = client.get("/api/v1/bills/")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "value": 10.5,
            "date": "2012-12-12",
            "category_id": 1,
            "tenant_id": 1,
        },
        {
            "id": 2,
            "value": 99.9,
            "date": "2024-12-12",
            "category_id": 1,
            "tenant_id": 1,
        },
        {
            "id": 3,
            "value": 199.90,
            "date": "2024-12-13",
            "category_id": 2,
            "tenant_id": 1,
        },
    ]


def test_index_not_showing_for_user_from_another_tenant(
    client: TestClient,
    in_memory_bills: list[Bill],
    mock_user_from_another_tenant: User,
):
    response = client.get("/api/v1/bills/")

    assert response.status_code == 200
    assert response.json() == []


def test_index_no_logged_user(client: TestClient):
    response = client.get("/api/v1/bills/")

    assert response.status_code == 401


def test_get_bill(client: TestClient, mock_user: User, in_memory_bills: list[Bill]):
    response = client.get("/api/v1/bills/1")

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "value": 10.5,
        "date": "2012-12-12",
        "category_id": 1,
        "tenant_id": 1,
    }


def test_get_bill_user_same_tenant(client: TestClient, mock_user_same_tenant: User, in_memory_bills: list[Bill]):
    response = client.get("/api/v1/bills/1")

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "value": 10.5,
        "date": "2012-12-12",
        "category_id": 1,
        "tenant_id": 1,
    }


def test_get_bill_no_logged_user(client: TestClient):
    response = client.get("/api/v1/bills/1")

    assert response.status_code == 401


def test_get_bill_for_user_from_another_tenant(
    client: TestClient,
    in_memory_bills: list[Bill],
    mock_user_from_another_tenant: User,
):
    response = client.get("/api/v1/bills/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "Bill not found"


def test_create_bill(
    client: TestClient,
    in_memory_default_category: Category,
    mock_user: User,
):
    response = client.post(
        "/api/v1/bills/",
        json={
            "date": "2025-01-01",
            "value": 15.50,
            "category_id": 1,
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "value": 15.5,
        "category_id": 1,
        "date": "2025-01-01",
        "tenant_id": 1,
    }


def test_create_bill_no_logged_user(client: TestClient):
    response = client.post(
        "/api/v1/bills/",
        json={
            "date": "2025-01-01",
            "value": 15.50,
            "category_id": 1,
        },
    )

    assert response.status_code == 401


def test_create_bill_inexistent_category(client: TestClient, mock_user: User):
    response = client.post(
        "/api/v1/bills/",
        json={
            "date": "2025-01-01",
            "value": 15.50,
            "category_id": 5,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_create_bill_with_category_from_another_tenant(
    client: TestClient,
    in_memory_default_category: Category,
    mock_user_from_another_tenant: User,
):
    response = client.post(
        "/api/v1/bills/",
        json={
            "date": "2025-01-01",
            "value": 15.50,
            "category_id": 1,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_update_bill(
    client: TestClient,
    mock_user: User,
    in_memory_default_category: Category,
    in_memory_another_category: Category,
    in_memory_bills: list[Bill],
):
    response = client.put(
        "/api/v1/bills/1",
        json={
            "date": "2013-12-12",
            "value": "69.90",
            "category_id": 2,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "date": "2013-12-12",
        "value": 69.90,
        "category_id": 2,
        "tenant_id": 1,
    }


def test_update_bill_from_another_tenant(
    client: TestClient,
    mock_user_from_another_tenant: User,
    in_memory_default_category: Category,
    in_memory_another_category: Category,
    in_memory_bills: list[Bill],
):
    response = client.put(
        "/api/v1/bills/1",
        json={
            "date": "2013-12-12",
            "value": "69.90",
            "category_id": 2,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Bill not found"


def test_update_bill_inexistent_category_id(
    client: TestClient,
    mock_user: User,
    in_memory_default_category: Category,
    in_memory_bills: list[Bill],
):
    response = client.put(
        "/api/v1/bills/1",
        json={
            "date": "2013-12-12",
            "value": "69.90",
            "category_id": 5,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_update_bill_with_category_from_another_tenant(
    client: TestClient,
    mock_user: User,
    in_memory_default_category: Category,
    in_memory_bills: list[Bill],
    in_memory_category_from_another_tenant: Category,
):
    response = client.put(
        "/api/v1/bills/1",
        json={
            "date": "2013-12-12",
            "value": "69.90",
            "category_id": 3,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"
