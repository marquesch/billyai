from domain.ports.services import AMQPService
from infrastructure.config.settings import app_settings


class AMQPAsyncTaskDispatcher:
    def __init__(self, amqp_service: AMQPService):
        self.amqp_service = amqp_service

    async def dispatch(self, task_name: str, **kwargs):
        payload = {
            "task": task_name,
            "kwargs": kwargs,
        }

        await self.amqp_service.publish(payload, app_settings.async_task_routing_key)
