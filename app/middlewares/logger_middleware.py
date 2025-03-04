from collections.abc import Awaitable
from typing import Any, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.logger import Logger


class LoggingMiddleware(BaseMiddleware):
    """прослоечкка с логированием. Интегрируется в Dispatcher.

    так же допустимо инициализировать в роутере, например:

        ```python
        @user_router.message(CommandStart())
        async def cmd_start(message: Message, state: FSMContext, logger: Logger) -> None:
            logger.log(f"Пользователь {message.from_user.id} начал работу с ботом.", level="info")
        ```
    """

    def __init__(self, logger: Logger):
        """Инициализируем логгер."""
        self.logger = logger

    async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any],
            ) -> Any:
        """Логируем входящее событие."""
        parsed_data = self.logger.parse_data(event.model_dump() if hasattr(event, "model_dump") else event)
        self.logger.log(
            f"Входящее событие: {event.__class__.__name__}, "
            f"данные: {parsed_data}"
        )
        data["logger"] = self.logger

        try:
            # Продолжаем выполнение цепочки middleware и обработчиков
            result = await handler(event, data)

            # Логируем успешное завершение обработки
            self.logger.log(f"Событие успешно обработано: {event.__class__.__name__}")
            return result
        except Exception as e:
            # Логируем ошибки
            self.logger.log_error(
                f"Ошибка при обработке события: {event.__class__.__name__}, "
                f"ошибка: {e}", exc_info=True
            )
            raise
