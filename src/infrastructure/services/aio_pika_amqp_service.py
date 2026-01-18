import json
from collections.abc import Callable

import aio_pika
from aio_pika.pool import Pool
from aio_pika.robust_connection import AbstractRobustConnection


class AioPikaPoolService:
    def __init__(self, broker_url: str):
        async def get_connection() -> AbstractRobustConnection:
            return await aio_pika.connect_robust(broker_url)

        self._connection_pool = Pool(get_connection, max_size=15)

    async def get_channel(self) -> aio_pika.Channel:
        async with self._connection_pool.acquire() as connection:
            return await connection.channel()


class AioPikaAMQPService:
    def __init__(self, channel: aio_pika.Channel):
        self._channel = channel

    async def consume(
        self,
        queue_name: str,
        callback: Callable,
        no_ack: bool = True,
        prefetch_count: int | None = None,
    ) -> None:
        async def callback_fn(message: aio_pika.IncomingMessage):
            async with message.process(requeue=True):
                payload = json.loads(message.body.decode("utf-8"))
                await callback(payload)

        if prefetch_count is not None:
            await self._channel.set_qos(prefetch_count=prefetch_count)

        queue = await self._channel.declare_queue(queue_name)

        await queue.consume(callback_fn, no_ack=no_ack)

    async def publish(self, message: dict, queue_name: str) -> None:
        payload = json.dumps(message).encode("utf-8")
        await self._channel.default_exchange.publish(aio_pika.Message(body=payload), queue_name)
