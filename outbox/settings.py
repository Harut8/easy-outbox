from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from outbox.env import ENV_FILE, ENV_FILE_ENCODING


class OutboxSettings(BaseSettings):
    model_config = SettingsConfigDict(
        title="Outbox Settings",
        env_file=ENV_FILE,
        env_file_encoding=ENV_FILE_ENCODING,
    )
    POSTGRES_DSN: str = Field(
        alias="DATABASE_URL",
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
    )
    RMQ_URL: str = Field(
        alias="RMQ_URL",
        default="amqp://guest:guest@localhost:5672/",
    )
    OUTBOX_QUEUE: str = Field(
        alias="OUTBOX_QUEUE",
        default="outbox",
    )


