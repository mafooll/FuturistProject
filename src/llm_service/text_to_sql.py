import logging
from pathlib import Path
from typing import TypedDict

from openai import AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.settings import LLMSettings
from src.database.manager import DatabaseManager

logger = logging.getLogger(__name__)


class ErrorRecord(TypedDict):  # noqa: D101
    sql: str
    error: str


class TextToSQLService:  # noqa: D101
    MAX_RETRIES = 3
    PROMPT_DIR_NAME = "prompts"
    ON_START_PROMPT_FILE = "on_start.md"
    ON_ERROR_PROMPT_FILE = "on_error.md"

    def __init__(  # noqa: D107
        self,
        llm_settings: LLMSettings,
        db_manager: DatabaseManager,
    ) -> None:
        self.llm_settings = llm_settings
        self.db_manager = db_manager
        self.max_retries = self.MAX_RETRIES

        self.client = AsyncOpenAI(
            api_key=llm_settings.api_key.get_secret_value(),
            base_url="https://openrouter.ai/api/v1",
        )

        self.prompts_dir = Path(__file__).parent / self.PROMPT_DIR_NAME
        self.on_start_prompt = self._load_prompt(self.ON_START_PROMPT_FILE)
        self.on_error_prompt = self._load_prompt(self.ON_ERROR_PROMPT_FILE)

    def _load_prompt(self, filename: str) -> str:
        prompt_path = self.prompts_dir / filename

        if not prompt_path.exists():
            raise FileNotFoundError(f"prompt file not found: {prompt_path}")

        content = prompt_path.read_text(encoding="utf-8")
        logger.debug(f"loaded prompt from {filename}")
        return content

    async def _call_llm(
        self,
        user_message: str,
        system_prompt: str | None = None,
    ) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.llm_settings.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt or self.on_start_prompt,
                    },
                    {"role": "user", "content": user_message},
                ],
            )
            if not response.choices[0].message.content:
                raise ValueError("llm returned empty response")
            sql_query = response.choices[0].message.content.strip()
            logger.debug(f"llm generated sql: {sql_query}")
            return sql_query
        except Exception as llm_error:
            logger.error(f"llm call failed: {llm_error}")
            raise

    def _validate_sql(self, sql_query: str) -> None:
        normalized = sql_query.strip().upper()
        if not normalized.startswith("SELECT"):
            raise ValueError(
                f"only SELECT queries are allowed, got: {sql_query[:50]}"
            )

    async def _execute_sql(self, session: AsyncSession, sql_query: str) -> int:
        if not sql_query.strip():
            raise ValueError("empty sql query")

        result = await session.execute(text(sql_query))
        row = result.fetchone()

        if row is None or row[0] is None:
            raise ValueError("query returned no results or NULL")

        try:
            return int(row[0])
        except (TypeError, ValueError, OverflowError) as e:
            raise ValueError(
                f"query returned non-numeric value: {row[0]} "
                f"(type: {type(row[0]).__name__})"
            ) from e

    def _format_error_prompt(
        self, user_query: str, error_history: list[ErrorRecord]
    ) -> str:
        if not error_history:
            error_history_text = "ошибок пока не было"
            last_error = ""
        else:
            error_parts: list[str] = []
            for attempt_number, error_record in enumerate(error_history, 1):
                sql = error_record.get("sql", "N/A")
                error = error_record.get("error", "N/A")
                error_parts.append(
                    f"попытка {attempt_number}\n"
                    f"sql-query: {sql}\n"
                    f"ошибка: {error}\n"
                )
            error_history_text = "\n".join(error_parts).strip()
            last_error = error_history[-1].get("error", "")

        try:
            return self.on_error_prompt.format(
                user_query=user_query,
                error_history=error_history_text,
                last_error=last_error,
            )

        except KeyError as key_error:
            raise RuntimeError(
                f"error on formatting on_error.md: {key_error}"
            ) from key_error

    async def process_query(  # noqa: D102
        self,
        user_query: str,
    ) -> int:
        logger.info(f"user query: {user_query}")

        error_history: list[ErrorRecord] = []
        sql_query: str = ""

        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"attempt {attempt + 1}/{self.max_retries} "
                    f"for query: {user_query}"
                )

                if attempt == 0:
                    sql_query = await self._call_llm(user_query)
                else:
                    error_prompt = self._format_error_prompt(
                        user_query, error_history
                    )
                    sql_query = await self._call_llm(
                        user_message=user_query,
                        system_prompt=error_prompt,
                    )

                self._validate_sql(sql_query)

                async with self.db_manager.session() as session:
                    result = await self._execute_sql(session, sql_query)
                    logger.info(
                        f"query succeeded on {attempt + 1} attempt "
                        f"result: {result}"
                    )
                    return result

            except Exception as error:
                error_message = str(error)
                logger.warning(f"attempt {attempt + 1} failed: {error_message}")

                error_history.append(
                    {
                        "sql": sql_query,
                        "error": error_message,
                    }
                )

                if attempt == self.max_retries - 1:
                    raise Exception(
                        f"failed to execute query after "
                        f"{self.max_retries} attempts: {error_message}"
                    ) from error

        raise Exception("unexpected error")
