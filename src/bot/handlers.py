import logging

from aiogram import F, Router
from aiogram.types import Message
from dependency_injector.wiring import Provide, inject
from src.container import Container
from src.llm_service.text_to_sql import TextToSQLService

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text)
@inject
async def handle_query(  # noqa: D103
    message: Message,
    llm_service: TextToSQLService = Provide[Container.llm_service],
) -> None:
    try:
        if not message.text:
            return
        await message.answer(str(await llm_service.process_query(message.text)))
    except Exception:
        logger.exception(f"failed to process query: {message.text}")
