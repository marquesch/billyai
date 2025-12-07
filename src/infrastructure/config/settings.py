from enum import Enum

from pydantic_settings import BaseSettings


class Environment(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    environment: Environment = Environment.DEVELOPMENT
    database_url: str = ""
    redis_host: str = ""
    redis_port: int

    @property
    def debug(self):
        return self.environment != Environment.PRODUCTION

    class Config:
        env_file = ".env"
        case_sensitve = False


app_settings = Settings()
