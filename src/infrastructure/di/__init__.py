from collections.abc import Callable
from contextlib import contextmanager
from typing import Any


class DIRegistry:
    def __init__(self):
        self._factories: dict[type, Callable] = {}
        self._dependencies: dict[type, list[type]] = {}
        self._instances: dict[type, Any] = {}

    def register(
        self,
        cls: type,
        factory: Callable,
        dependencies: list[type] | None = None,
    ):
        self._factories[cls] = factory
        self._dependencies[cls] = dependencies or []

    def get(self, cls: type) -> Any:
        if cls in self._instances:
            return self._instances[cls]

        if cls not in self._factories:
            raise ValueError(f"Class '{cls.__name__}' not registered")

        deps = [self.get(dep_cls) for dep_cls in self._dependencies[cls]]

        self._instances[cls] = self._factories[cls](*deps)
        return self._instances[cls]

    def clear(self):
        for obj in self._instances.values():
            if hasattr(obj, "close"):
                obj.close()
        self._instances.clear()

    @contextmanager
    def scope(self):
        try:
            yield self
        finally:
            self.clear()
