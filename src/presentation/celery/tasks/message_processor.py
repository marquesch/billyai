from celery import Celery

from infrastructure.config.settings import app_settings

app = Celery(broker=app_settings.rabbitmq_url)


@app.task
def send_registration_confirmation_link(phone_number: str, confirmation_url: str) -> None:
    print(f"Sending {phone_number} confirmation link {confirmation_url}")


@app.task
def send_pin(phone_number: str, pin: str) -> None:
    print(f"Sending PIN {pin} to {phone_number}")
