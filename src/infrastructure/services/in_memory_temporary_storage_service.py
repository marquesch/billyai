import json
import time
from typing import Any

from domain.exceptions import KeyNotFoundException


class InMemoryTemporaryStorageService:
    def __init__(self):
        self._database = {}

    def set(self, key: str, value: Any, expiration_seconds: int = -1) -> bool:
        json_data = json.dumps(value) if type(value) is not bytes else value
        expiry = time.time() + expiration_seconds
        self._database[key] = {"ex": expiry, "data": json_data}
        return True

    def get(self, key: str) -> Any:
        data = self._database.get(key)
        if data is None:
            raise KeyNotFoundException

        if data["ex"] < time.time():
            raise KeyNotFoundException

        return json.loads(data["data"])

    def delete(self, key: str) -> bool:
        db_data = self._database.pop(key, None)
        return db_data and db_data["ex"] > time.time()
