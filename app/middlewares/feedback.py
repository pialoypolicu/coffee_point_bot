from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.logic.feedback import LogicFeedback


class LogicFeedbackMiddleware(BaseMiddleware):
    """Middleware для внедрения LogicFeedback."""

    def __init__(self, logic_feedback: LogicFeedback) -> None:
        """конструктор middleware.

        Args:
            logic_feedback: логика для работы с отзывами
        """
        self.logic_feedback = logic_feedback

    async def __call__(self,
                       handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: dict[str, Any]) -> Any:
        """Вызоваа middleware."""
        data["logic_feedback"] = self.logic_feedback
        return await handler(event, data)
