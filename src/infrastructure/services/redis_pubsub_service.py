import json
from collections.abc import AsyncIterator

from redis import asyncio as redis

from infrastructure.config.settings import app_settings

async_redis_pool = redis.ConnectionPool(host=app_settings.redis_host, port=app_settings.redis_port)


class RedisPubsubService:
    def __init__(self, client: redis.Redis):
        self._client = client
        self._pubsub = client.pubsub(ignore_subscribe_messages=True)

    async def subscribe(self, channel: str) -> None:
        await self._pubsub.subscribe(channel)

    async def publish(self, channel: str, event: str, data: dict) -> None:
        payload = {"event": event, "data": data}
        await self._client.publish(channel=channel, message=json.dumps(payload))

    async def listen(self) -> AsyncIterator[str]:
        async for message in self._pubsub.listen():
            if message is None:
                continue

            yield message["data"].decode()
