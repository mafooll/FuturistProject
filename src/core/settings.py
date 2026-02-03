from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

env_path: Path = Path(__file__).resolve().parent.parent.parent / ".env"


class BotSettings(BaseSettings):  # noqa: D101
    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="BOT_",
        extra="ignore",
    )
    token: SecretStr = SecretStr("bot_token")


class PostgresSettingsRW(BaseSettings):  # noqa: D101
    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="POSTGRES_",
        extra="ignore",
    )
    password_rw: SecretStr = SecretStr("postgres")
    db: str = "postgres"
    user: str = "postgres"
    host: str = "postgres_container"
    port: int = 5432

    driver: str = "postgresql+asyncpg"

    @property
    def sqlalchemy_url(self) -> URL:  # noqa: D102
        return URL.create(
            drivername=self.driver,
            username=self.user,
            password=self.password_rw.get_secret_value(),
            host=self.host,
            port=self.port,
            database=self.db,
        )

    @property
    def url(self) -> str:  # noqa: D102
        return self.sqlalchemy_url.render_as_string(hide_password=False)


class PostgresSettingsRO(BaseSettings):  # noqa: D101
    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="POSTGRES_",
        extra="ignore",
    )
    password_ro: SecretStr = SecretStr("postgres")
    db: str = "postgres"
    host: str = "postgres_container"
    port: int = 5432

    driver: str = "postgresql+asyncpg"

    @property
    def sqlalchemy_url(self) -> URL:  # noqa: D102
        return URL.create(
            drivername=self.driver,
            username="readonly_user",
            password=self.password_ro.get_secret_value(),
            host=self.host,
            port=self.port,
            database=self.db,
        )

    @property
    def url(self) -> str:  # noqa: D102
        return self.sqlalchemy_url.render_as_string(hide_password=False)


class LLMSettings(BaseSettings):  # noqa: D101
    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="OPENROUTER_",
        extra="ignore",
    )

    api_key: SecretStr = SecretStr("your_openrouter_api_key")
    model: str = "your_openrouter_model_name"
