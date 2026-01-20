import json
import time
from typing import Any

from domain.exceptions import KeyNotFoundException


class InMemoryTemporaryStorageService:
    def __init__(self):
        self._database = {}

    def set(self, key: str, value: Any, expiration_seconds: int = 0) -> bool:
        json_data = json.dumps(value) if type(value) is not bytes else value
        expiry = time.time() + expiration_seconds if expiration_seconds > 0 else 0
        self._database[key] = {"ex": expiry, "data": json_data}
        return True

    def get(self, key: str) -> Any:
        data = self._database.get(key)

        if data is None or (data["ex"] and data["ex"] <= time.time()):
            raise KeyNotFoundException

        return json.loads(data["data"])

    def delete(self, key: str) -> bool:
        data = self._database.pop(key, None)
        return bool(data and (not data["ex"] or data["ex"] > time.time()))
