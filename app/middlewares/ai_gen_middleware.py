from collections.abc import Awaitable
from typing import Any, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.logic.ai_gen_logic import AIGeneratorLogic


class AIGenLogicMiddleware(BaseMiddleware):
    """Middleware для внедрения AIGeneratorLogic."""

    def __init__(self, aigen_logic: AIGeneratorLogic) -> None:
        """конструктор middleware.

        Args:
            aigen_logic: логика работы с openai.
        """
        self.aigen_logic = aigen_logic

    async def __call__(self,
                       handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: dict[str, Any]) -> Any:
        """Вызов middleware."""
        data["aigen_logic"] = self.aigen_logic
        return await handler(event, data)
