from domain.ports.services import AMQPService
from infrastructure.config.settings import app_settings


class AMQPWhatsappBrokerMessageService:
    def __init__(self, amqp_service: AMQPService):
        self._amqp_service = amqp_service

    async def send_message(self, message_body: str, phone_number: str) -> None:
        payload = {"message_body": message_body, "phone_number": phone_number}

        await self._amqp_service.publish(payload, queue_name=app_settings.whatsapp_message_routing_key)
