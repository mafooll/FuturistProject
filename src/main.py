from asyncio import run
from logging import DEBUG, basicConfig

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from src.bot.handlers import router
from src.container import Container

basicConfig(
    level=DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


async def main() -> None:  # noqa: D103
    container = Container()
    container.wire(modules=["src.bot.handlers"])

    bot_settings = container.bot_settings()

    bot = Bot(
        token=bot_settings.token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.include_router(router)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await container.database_manager_rw().close()
        await container.database_manager_ro().close()


if __name__ == "__main__":
    run(main())
