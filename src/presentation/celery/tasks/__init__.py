from collections.abc import Callable

from celery import Task
from infrastructure.di.celery import celery_registry


class DITask(Task):
    dependencies = []

    def __call__(self, *args, **kwargs):
        for dep_cls in self.dependencies:
            attr_name = dep_cls.__name__.lower()
            setattr(self, attr_name, celery_registry.get(dep_cls))

        try:
            return super().__call__(*args, **kwargs)
        finally:
            for dep_cls in self.dependencies:
                attr_name = dep_cls.__name__.lower()
                if hasattr(self, attr_name):
                    delattr(self, attr_name)
            celery_registry.clear()
