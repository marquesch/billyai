import threading
from typing import Any

from infrastructure.di import DIRegistry


class CeleryDIRegistry(DIRegistry):
    def __init__(self):
        super().__init__()
        self._local = threading.local()
        self._local.instances: dict[type, Any] = {}
        self._instances: dict[type, Any] = self._local.instances


celery_registry = CeleryDIRegistry()
