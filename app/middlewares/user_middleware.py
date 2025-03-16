from collections.abc import Awaitable
from typing import Any, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.logic.user_logic import UserLogic


class UserLogicMiddleware(BaseMiddleware):
    """Middleware для внедрения LogicFeedback."""

    def __init__(self, user_logic: UserLogic) -> None:
        """конструктор middleware.

        Args:
            logic_user: логика работы с клиентом.
        """
        self.user_logic = user_logic

    async def __call__(self,
                       handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: dict[str, Any]) -> Any:
        """Вызов middleware."""
        data["user_logic"] = self.user_logic
        return await handler(event, data)
