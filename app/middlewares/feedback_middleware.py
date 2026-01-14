from collections.abc import Awaitable
from typing import Any, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.configs import current_chat_id
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
        """Вызова middleware."""
        chat_id = None

        if isinstance(event, Message):
            chat_id = event.chat.id
        elif isinstance(event, CallbackQuery):
            chat_id = event.message.chat.id

        # Устанавливаем chat_id в контекстную переменную
        if chat_id is not None:
            token = current_chat_id.set(chat_id)
        data["logic_feedback"] = self.logic_feedback
        try:
            return await handler(event, data)
        finally:
            # Восстанавливаем предыдущее значение контекстной переменной
            if chat_id is not None:
                current_chat_id.reset(token)
