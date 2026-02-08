import json
from typing import Any

import redis

from domain.exceptions import KeyNotFoundException
from infrastructure.config import settings

redis_pool = redis.ConnectionPool(
    host=settings.app_settings.redis_host,
    port=settings.app_settings.redis_port,
    db=0,
)


class RedisTemporaryStorageService:
    def __init__(self, redis_client: redis.Redis):
        self._client = redis_client

    def set(self, key: str, value: Any, expiration_seconds: int | None = None) -> bool:
        json_data = json.dumps(value) if type(value) != bytes else value
        return self._client.set(key, json_data, ex=expiration_seconds)

    def get(self, key: str) -> Any:
        json_data = self._client.get(key)

        if json_data is None:
            raise KeyNotFoundException

        return json.loads(json_data)

    def delete(self, key: str) -> bool:
        return bool(self._client.delete(key))
