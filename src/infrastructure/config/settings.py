from enum import Enum

from pydantic_settings import BaseSettings


class Environment(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    environment: Environment = Environment.DEVELOPMENT
    database_url: str = "postgresql+psycopg2://billy:billy@postgres:5432/billy?sslmode=disable"
    rabbitmq_url: str = "amqp://billy:billy@rabbitmq:5672//"
    redis_host: str = "redis"
    redis_port: int = 6379
    deepseek_api_key: str = ""
    user_validation_token_ttl_seconds: int = 86400
    user_pin_ttl_seconds: int = 86400
    user_token_ttl: int = 86400
    async_task_routing_key: str = "async_tasks"
    whatsapp_message_routing_key: str = "whatsapp_message"
    async_task_prefetch_count: int = 5

    @property
    def debug(self):
        return self.environment != Environment.PRODUCTION

    class Config:
        env_file = ".env"
        case_sensitve = False


app_settings = Settings()
