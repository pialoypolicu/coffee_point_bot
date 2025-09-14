from collections.abc import Awaitable
from typing import Any, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.configs import current_chat_id
from app.logic.user_logic import UserLogic


class UserLogicMiddleware(BaseMiddleware):
    """Middleware для внедрения LogicFeedback."""

    def __init__(self, user_logic: UserLogic) -> None:
        """конструктор middleware.

        Args:
            user_logic: логика работы с клиентом.
        """
        self.user_logic = user_logic

    async def __call__(self,
                       handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: dict[str, Any]) -> Any:
        """Вызов middleware."""
        # Определяем chat_id в зависимости от типа события.
        # эта фича позволит иметь значение chat_id по дефолту в классе UserLogic, обращаться можно будет к self.chat_id.

        # DeepSeek: Я рекомендую использовать подход с contextvars, так как он:
        # - Безопасен для асинхронной среды
        # - Не требует изменения состояния объекта UserLogic
        # - Корректно работает при одновременных запросах
        # - Соответствует принципам функционального программирования
        chat_id = None

        if isinstance(event, Message):
            chat_id = event.chat.id
        elif isinstance(event, CallbackQuery):
            chat_id = event.message.chat.id

        # Устанавливаем chat_id в контекстную переменную
        if chat_id is not None:
            token = current_chat_id.set(chat_id)
        data["user_logic"] = self.user_logic
        try:
            return await handler(event, data)
        finally:
            # Восстанавливаем предыдущее значение контекстной переменной
            if chat_id is not None:
                current_chat_id.reset(token)
