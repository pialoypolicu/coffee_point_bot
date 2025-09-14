import logging
from threading import Lock
from typing import Any, Optional

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

logger = logging.getLogger(__name__)

class MessageManager:
    """Сервис для управления сообщениями с безопасной обработкой ошибок."""

    _instance = None
    _lock = Lock()

    def __new__(cls, bot: Bot | None = None):
        """Патерн singleton."""
        with cls._lock:
            if cls._instance is None:
                if bot is None:
                    raise ValueError("Bot instance is required for first initialization")
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, bot: Bot | None = None):
        """Инициализация менеджера сообщений.

        Args:
            bot: Экземпляр бота для работы с API Telegram
        """
        if self._initialized:
            return
        self.bot = bot
        self.message_registry: dict[int, list[int]] = {}
        self._initialized = True
        logger.info("MessageManager initialized")

    async def delete_messages(
            self,
            chat_id: int,
            message_ids: list[int]
            ) -> None:
        """Удаляет несколько сообщений с обработкой ошибок.

        Args:
            chat_id: id чата
            message_ids: спиоскк айдишников сообщений.
        """
        for msg_id in message_ids:
            try:
                await self.bot.delete_message(chat_id, msg_id)
                # Удаляем из реестра при успешном удалении
                if chat_id in self.message_registry and msg_id in self.message_registry[chat_id]:
                    self.message_registry[chat_id].remove(msg_id)
            except TelegramBadRequest as e:
                if "message to delete not found" in str(e).lower():
                    logger.debug(f"Message {msg_id} already deleted")
                else:
                    logger.error(f"Failed to delete message {msg_id}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error deleting message {msg_id}: {e}")

    async def safe_edit_reply_markup(
            self,
            chat_id: int,
            message_id: int,
            reply_markup: Any | None = None
            ) -> bool:
        """Безопасно изменяет разметку сообщения.

        Args:
            chat_id: id чата
            message_id: id сообщения.
            reply_markup: схема телеграм клавиатуры.
        """
        try:
            await self.bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=reply_markup
            )
            return True
        except TelegramBadRequest as e:
            if "message is not modified" in str(e).lower():
                logger.debug(f"Message {message_id} not modified")
                return True
            logger.error(f"Failed to edit message markup {message_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error editing message {message_id}: {e}")
            return False

    async def track_message(self, chat_id: int, message_id: int) -> None:
        """Добавляет сообщение в реестр для отслеживания.

        Args:
            chat_id: id чата.
            message_id: id сообщения.
        """
        if chat_id not in self.message_registry:
            self.message_registry[chat_id] = []
        if message_id not in self.message_registry[chat_id]:
            self.message_registry[chat_id].append(message_id)

    async def safe_edit_text(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        **kwargs
    ) -> bool:
        """Безопасно изменяет текст сообщения.

        Args:
            chat_id: ID чата
            message_id: ID сообщения для редактирования
            text: Новый текст сообщения
            **kwargs: Дополнительные параметры для edit_message_text

        Returns:
            True если редактирование успешно, False в противном случае
        """
        try:
            await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                **kwargs
            )
            return True
        except TelegramBadRequest as e:
            if "message is not modified" in str(e).lower():
                logger.debug(f"Message {message_id} text not modified")
                return True
            elif "message to edit not found" in str(e).lower():
                logger.warning(f"Message {message_id} not found for editing")
                return False
            else:
                logger.error(f"Failed to edit message text {message_id}: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error editing message text {message_id}: {e}")
            return False

    async def safe_edit_message(
        self,
        chat_id: int,
        message_id: int,
        text: Optional[str] = None,
        reply_markup: Optional[Any] = None,
        **kwargs
    ) -> bool:
        """Безопасно изменяет сообщение (текст и/или разметку).

        Args:
            chat_id: ID чата
            message_id: ID сообщения для редактирования
            text: Новый текст сообщения (опционально)
            reply_markup: Новая разметка клавиатуры (опционально)
            **kwargs: Дополнительные параметры

        Returns:
            True если редактирование успешно, False в противном случае
        """
        try:
            # Если нужно изменить и текст, и разметку
            if text is not None and reply_markup is not None:
                await self.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    reply_markup=reply_markup,
                    **kwargs
                )
            # Если нужно изменить только текст
            elif text is not None:
                await self.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    **kwargs
                )
            # Если нужно изменить только разметку
            elif reply_markup is not None:
                await self.bot.edit_message_reply_markup(
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=reply_markup
                )
            else:
                logger.warning("Nothing to edit - neither text nor reply_markup provided")
                return False

            return True
        except TelegramBadRequest as e:
            if "message is not modified" in str(e).lower():
                logger.debug(f"Message {message_id} not modified")
                return True
            elif "message to edit not found" in str(e).lower():
                logger.warning(f"Message {message_id} not found for editing")
                return False
            else:
                logger.error(f"Failed to edit message {message_id}: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error editing message {message_id}: {e}")
            return False

    async def cleanup_chat_messages(self, chat_id: int) -> None:
        """Очищает все отслеживаемые сообщения в чате.

        Args:
            chat_id: id чата
        """
        if chat_id in self.message_registry:
            await self.delete_messages(chat_id, self.message_registry[chat_id].copy())
            self.message_registry[chat_id] = []

    async def safe_send_message(
            self,
            chat_id: int,
            text: str,
            **kwargs
        ) -> Optional[Message]:
        """Безопасно отправляет сообщение с обработкой ошибок.

        Args:
            chat_id: id чвта.
            text: текст сообщения.
            kwargs: кварги.
        """
        try:
            message = await self.bot.send_message(chat_id, text, **kwargs)
            await self.track_message(chat_id, message.message_id)
            return message
        except Exception as e:
            logger.error(f"Failed to send message to {chat_id}: {e}")
            return None

    @staticmethod
    async def safe_callback_answer(callback: CallbackQuery, message: str = "", show_alert: bool = False) -> None:
        """Безопасно отвечает на callback-запрос.

        callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
        message: Объект сообщщения.
        show_alert: флаг, который выводит поп-ап сообщение.
        """
        try:
            await callback.answer(message, show_alert=show_alert)
        except Exception as e:
            logger.error(f"Failed to answer callback: {e}")
