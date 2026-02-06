import json
from collections.abc import Awaitable
from collections.abc import Callable

import pytest
import redis
from fakeredis import aioredis

from infrastructure.services.redis_pubsub_service import RedisPubsubService


@pytest.fixture
async def redis_client():
    client = aioredis.FakeRedis()
    yield client
    await client.flushall()
    await client.close()


@pytest.fixture
async def pubsub_service(redis_client: aioredis.FakeRedis) -> RedisPubsubService:
    return RedisPubsubService(redis_client)


@pytest.fixture
async def redis_pubsub(redis_client: aioredis.FakeRedis) -> redis.asyncio.client.PubSub:
    return redis_client.pubsub()


@pytest.fixture
async def publish_message(redis_client: aioredis.FakeRedis) -> Callable[[str, str, dict], Awaitable[None]]:
    async def publish_message(channel, payload):
        return await redis_client.publish(channel, payload)

    return publish_message


@pytest.fixture
async def pubsub_subscribed_to_channel(redis_pubsub: redis.asyncio.client.PubSub) -> redis.asyncio.client.PubSub:
    await redis_pubsub.subscribe("test-channel")
    await redis_pubsub.get_message()
    print(type(redis_pubsub))
    return redis_pubsub


@pytest.mark.asyncio
class TestRedisPubsubService:
    async def test_publish_formats_data_correctly(
        self,
        redis_client: aioredis.FakeRedis,
        pubsub_subscribed_to_channel,
        pubsub_service: RedisPubsubService,
    ):
        await pubsub_service.publish("test-channel", "user_signup", {"id": 1, "name": "Alice"})

        message = await pubsub_subscribed_to_channel.get_message(ignore_subscribe_messages=True, timeout=1.0)
        assert message is not None

        decoded_payload = json.loads(message["data"].decode())
        assert decoded_payload == {
            "event": "user_signup",
            "data": {"id": 1, "name": "Alice"},
        }

    async def test_subscribe_and_listen(
        self,
        pubsub_service: RedisPubsubService,
        redis_client: aioredis.FakeRedis,
        publish_message: Callable[[str, str, dict], Awaitable[None]],
    ):
        await pubsub_service.subscribe("chat-room")
        await publish_message("chat-room", json.dumps({"event": "msg", "data": {"text": "hello"}}))

        async for msg in pubsub_service.listen():
            break

        assert msg == json.dumps({"event": "msg", "data": {"text": "hello"}})
