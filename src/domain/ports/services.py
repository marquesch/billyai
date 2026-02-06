from collections.abc import AsyncIterator
from collections.abc import Callable
from typing import Any
from typing import Protocol


class TemporaryStorageService(Protocol):
    def set(self, key: str, value: Any, expiration_seconds: int | None) -> bool: ...
    def get(self, key: str) -> Any: ...
    def delete(self, key: str) -> bool: ...


class UserEncodingService(Protocol):
    def encode(self, phone_number: str) -> str: ...
    def decode(self, token: str) -> str: ...


class AIAgentService(Protocol):
    async def run(self, message_body: str, phone_number: str) -> str: ...


class AMQPService(Protocol):
    async def consume(
        self,
        queue_name: str,
        callback: Callable,
        no_ack: bool = True,
        prefetch_count: int | None = None,
    ) -> None: ...
    async def publish(self, message: dict, queue_name: str) -> None: ...


class PubsubService(Protocol):
    async def subscribe(self, channel: str) -> None: ...
    async def publish(self, channel: str, event: str, data: dict) -> None: ...
    async def listen(self) -> AsyncIterator: ...


class AsyncTaskDispatcherService(Protocol):
    async def dispatch(self, task_name: str, **kwargs) -> None: ...


class WhatsappBrokerMessageService(Protocol):
    async def send_message(self, message_body: str, phone_number: str) -> None: ...
