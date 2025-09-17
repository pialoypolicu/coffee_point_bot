from collections.abc import Awaitable
from typing import Any, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.services.message_manager import MessageManager


class MessageManagerMiddleware(BaseMiddleware):
    """Middleware для внедрения MessageManager в обработчики."""

    def __init__(self) -> None:
        """Инициализация middleware.

        MessageManager будет создаваться один раз при первом использовании.
        """
        self.message_manager = None
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        """Обработка вызова middleware.

        Args:
            handler: Обработчик события
            event: Событие Telegram
            data: Данные события
        """
        # Получаем бота из данных
        bot = data.get("bot")
        if not bot:
            # Если бота нет в данных, пытаемся получить из события
            if hasattr(event, "bot") and event.bot:
                bot = event.bot
            else:
                # Если бот все равно не доступен, пропускаем внедрение
                return await handler(event, data)

        # Создаем или получаем экземпляр MessageManager
        if self.message_manager is None:
            self.message_manager = MessageManager(bot)

        # Внедряем MessageManager в данные
        data["message_manager"] = self.message_manager

        # Вызываем обработчик
        return await handler(event, data)
