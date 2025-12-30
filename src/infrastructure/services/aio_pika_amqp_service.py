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


class AioPikaAMQPMessagingService:
    def __init__(self, channel: aio_pika.Channel):
        self._channel = channel

    async def consume(self, queue_name: str, callback: Callable) -> None:
        async def callback_fn(message: aio_pika.Message):
            payload = json.loads(message.body.decode("utf-8"))
            await callback(payload)

        queue = await self._channel.declare_queue(queue_name)

        await queue.consume(callback_fn, no_ack=True)

    async def publish(self, message: dict, routing_key: str) -> None:
        payload = json.dumps(message).encode("utf-8")
        await self._channel.default_exchange.publish(aio_pika.Message(body=payload), routing_key)
