import inspect
from collections.abc import Callable

from domain.ports.services import AMQPService
from infrastructure.config.settings import app_settings
from infrastructure.di import resolve


class AsyncTask:
    def __init__(self, routing_key: str, func: Callable):
        self._amqp_service = None
        self._func = func
        self._routing_key = routing_key
        self._func_module = inspect.getmodule(func).__name__
        self._func_name = func.__name__

    async def __call__(self, *args, **kwargs):
        return await self._func(*args, **kwargs)

    async def delay(self, **kwargs):
        message = {
            "module": self._func_module,
            "func": self._func_name,
            "kwargs": kwargs,
        }

        amqp_service = await resolve(AMQPService)
        await amqp_service.publish(message, self._routing_key)


def async_task(func: Callable) -> AsyncTask:
    return AsyncTask(app_settings.async_task_routing_key, func)
