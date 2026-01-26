import asyncio
import logging
import traceback

from application.use_cases import async_tasks
from domain.ports.services import AMQPService
from infrastructure.config.settings import app_settings
from infrastructure.di import global_registry
from infrastructure.di import resolve
from infrastructure.di import setup_global_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def worker_callback(payload: dict):
    task_name = payload.get("task")
    task_kwargs = payload.get("kwargs", {})

    logger.info(f"Received task: {task_name}")

    async with global_registry.scope():
        try:
            if not hasattr(async_tasks, task_name):
                logger.error(f"Task '{task_name}' not found in async_tasks module")

            task_cls = getattr(async_tasks, task_name)
            task_build_args = [await resolve(dep) for dep in task_cls.dependencies]

            task = task_cls(*task_build_args)

            await task(**task_kwargs)
            logger.info(f"Finished task: {task_name}")

        except Exception as e:
            logger.exception(f"Error processing task {task_name}: {e}")
            logger.exception(traceback.format_exc())


async def main():
    print("Starting Worker...")
    await setup_global_registry()

    async with global_registry.scope() as di_registry:
        amqp_service: AMQPService = await di_registry.get(AMQPService)

        await amqp_service.consume(
            queue_name=app_settings.async_task_routing_key,
            callback=worker_callback,
            no_ack=False,
            prefetch_count=app_settings.async_task_prefetch_count,
        )

        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
