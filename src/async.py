import asyncio
import importlib

from domain.ports.services import AMQPService
from infrastructure.config.settings import app_settings
from infrastructure.di import global_registry
from infrastructure.di import setup_global_registry


async def callback(payload: dict):
    try:
        module = importlib.import_module(payload["module"])
        func = getattr(module, payload["func"])

        async with global_registry.scope() as di_registry:
            print(f"running {payload['func']} func")
            await func(**payload["kwargs"])
            print(f"done running {payload['func']} func")
    except Exception as e:
        print(e)


async def main():
    await setup_global_registry()

    async with global_registry.scope() as di_registry:
        amqp_service: AMQPService = await di_registry.get(AMQPService)
        await amqp_service.consume(app_settings.async_task_routing_key, callback)
        await asyncio.Future()


if __name__ == "__main__":
    print("starting to run")
    asyncio.run(main())
