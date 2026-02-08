from enum import Enum

from pydantic_settings import BaseSettings


class Environment(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    environment: Environment = Environment.DEVELOPMENT

    database_user: str = "billy"
    database_password: str = "billy"
    database_host: str = "postgres"
    database_port: int = 5432
    database_db: str = "billy"

    rabbitmq_user: str = "billy"
    rabbitmq_password: str = "billy"
    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672

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
    def rabbitmq_uri(self):
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}//"

    @property
    def database_uri(self):
        return (
            f"postgresql+psycopg://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_db}?sslmode=disable"
        )

    @property
    def debug(self):
        return self.environment != Environment.PRODUCTION

    class Config:
        env_file = ".env"
        case_sensitve = False


app_settings = Settings()
