# https://python-dependency-injector.ets-labs.org/examples/fastapi-sqlalchemy.html

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class DatabaseManager:  # noqa: D101
    def __init__(  # noqa: D107
        self,
        db_url: str,
        echo: bool = False,
        **engine_kwargs: dict[str, str | int],
    ) -> None:
        self._engine: AsyncEngine = create_async_engine(
            db_url,
            echo=echo,
            pool_pre_ping=True,
            **engine_kwargs,
        )

        self._session_factory: async_sessionmaker[AsyncSession] = (
            async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )
        )

    async def close(self) -> None:  # noqa: D102
        await self._engine.dispose()

    @asynccontextmanager
    async def session(  # noqa: D102
        self, commit: bool = False
    ) -> AsyncGenerator[AsyncSession]:
        session: AsyncSession = self._session_factory()

        try:
            yield session
            if commit:
                await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
