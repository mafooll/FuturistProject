from dependency_injector import containers, providers
from src.core.settings import (
    BotSettings,
    LLMSettings,
    PostgresSettingsRO,
    PostgresSettingsRW,
)
from src.database.manager import DatabaseManager
from src.llm_service.text_to_sql import TextToSQLService


class Container(containers.DeclarativeContainer):  # noqa: D101
    bot_settings: providers.Provider[BotSettings] = (
        providers.ThreadSafeSingleton(BotSettings)
    )
    llm_settings: providers.Provider[LLMSettings] = (
        providers.ThreadSafeSingleton(LLMSettings)
    )
    postgres_settings_rw: providers.Provider[PostgresSettingsRW] = (
        providers.ThreadSafeSingleton(PostgresSettingsRW)
    )

    postgres_settings_ro: providers.Provider[PostgresSettingsRO] = (
        providers.ThreadSafeSingleton(PostgresSettingsRO)
    )

    database_manager_rw: providers.Provider[DatabaseManager] = (
        providers.ThreadSafeSingleton(
            DatabaseManager,
            db_url=postgres_settings_rw.provided.sqlalchemy_url,
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600,
        )
    )

    database_manager_ro: providers.Provider[DatabaseManager] = (
        providers.ThreadSafeSingleton(
            DatabaseManager,
            db_url=postgres_settings_ro.provided.sqlalchemy_url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
        )
    )

    llm_service: providers.Provider[TextToSQLService] = providers.Singleton(
        TextToSQLService,
        llm_settings=llm_settings,
        db_manager=database_manager_ro
    )
