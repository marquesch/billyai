import json

import fakeredis
import pytest

from domain.exceptions import KeyNotFoundException
from infrastructure.services.redis_temporary_storage_service import RedisTemporaryStorageService


@pytest.fixture
def redis_client():
    client = fakeredis.FakeRedis()
    yield client
    client.flushall()


@pytest.fixture
def storage_service(redis_client: fakeredis.FakeRedis) -> RedisTemporaryStorageService:
    return RedisTemporaryStorageService(redis_client)


def test_set_and_get_success(storage_service: RedisTemporaryStorageService):
    key = "session_123"
    data = {"user_id": 1, "role": "admin"}

    storage_service.set(key, data, expiration_seconds=60)
    result = storage_service.get(key)

    assert result == data


def test_get_raises_exception_when_key_missing(storage_service: RedisTemporaryStorageService):
    with pytest.raises(KeyNotFoundException):
        storage_service.get("non_existent_key")


def test_set_with_bytes_data(storage_service: RedisTemporaryStorageService):
    key = "raw_data"
    data = {"user_id": "1", "role": "admin"}
    raw_bytes = json.dumps(data).encode()

    storage_service.set(key, raw_bytes, expiration_seconds=10)
    result = storage_service.get(key)

    assert data == result


def test_delete_key(storage_service: RedisTemporaryStorageService, redis_client: fakeredis.FakeRedis):
    key = "delete_me"
    storage_service.set(key, {"temp": "data"})

    deleted = storage_service.delete(key)

    assert deleted is True
    assert redis_client.get(key) is None


def test_delete_non_existent_key_returns_false(storage_service: RedisTemporaryStorageService):
    result = storage_service.delete("not_here")

    assert result is False
