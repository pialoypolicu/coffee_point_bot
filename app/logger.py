import json
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Any, Literal

from aiogram.types import TelegramObject
from colorlog import ColoredFormatter
from dotenv import load_dotenv

load_dotenv()

LEVELS = Literal["debug", "info", "warning", "error", "critical"]


class Logger:
    """Класс для логирования."""

    def __init__(
            self,
            log_dir: str = "app/logs",
            log_file: str = "bot.log",
            error_log_file: str = "bot_error.log",
            max_file_size: int = 10 * 1024 * 1024,  # 10 MB
            backup_count: int = 5,  # Количество backup-файлов
            when: str = "midnight",  # Ротация логов каждый день в полночь
            ):
        """Инициализация логгера.

        :param log_file: Имя файла для обычных логов.
        :param error_log_file: Имя файла для логов ошибок.
        :param max_file_size: Максимальный размер файла (в байтах).
        :param backup_count: Количество backup-файлов.
        :param when: Периодичность ротации логов (например, "midnight", "D", "H").
        """
        self.log_dir = log_dir
        self.log_file = log_file
        self.error_log_file = error_log_file
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.when = when
        # для хранения контекста. При каждом вызове хендлера, контекст создается зааново в middlewarer
        self.context: dict[str, Any] | None = None
        # дополнительные сообщение, предлагаю сюда добавлять сообщения конкатенацией.
        # Например:
        #   self.add_message += "\nДобавляем сообщение с новой строки, что бы было более читаемо."
        self.add_message: str = ""
        self.level: LEVELS = "info"

        # Создаем директорию для логов, если она не существует
        os.makedirs("app/logs", exist_ok=True)

        # Настройка основного логгера
        self.logger = logging.getLogger("bot_logger")
        self.logger.setLevel(logging.DEBUG)

        # Настройка логгера ошибок
        self.error_logger = logging.getLogger("bot_error_logger")
        self.error_logger.setLevel(logging.ERROR)

        console_formatter = ColoredFormatter(
            "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
            secondary_log_colors={},
            style="%"
        )

        # Форматтер для логов
        formatter = logging.Formatter(
            "\n======================================================================================================\n"
            "%(asctime)s - %(name)s - %(levelname)s"
            "\n======================================================================================================\n"
            "Message: %(message)s\n"
            "Exception: %(exc_info)s\n"
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        self.error_logger.addHandler(console_handler)

        # Обработчик для обычных логов (ротация по размеру)
        log_handler = RotatingFileHandler(
            filename=os.path.join(self.log_dir, self.log_file),
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
        )
        log_handler.setFormatter(formatter)
        self.logger.addHandler(log_handler)

        # Обработчик для логов ошибок (ротация по времени)
        error_handler = TimedRotatingFileHandler(
            filename=os.path.join(self.log_dir, self.error_log_file),
            when=self.when,
            backupCount=self.backup_count,
        )
        error_handler.setFormatter(formatter)
        self.error_logger.addHandler(error_handler)

        # Добавление фильтра
        duplicate_filter = DuplicateFilter()
        self.error_logger.addFilter(duplicate_filter)

    def log(self, message: str, level: str | None = None) -> None:
        """Запись лога.

        :param message: Сообщение для логирования.
        :param level: Уровень логирования (info, warning, error, critical).
        """
        level = level or self.level
        if self.add_message:
            message += self.add_message
        if self.context:
            message = f"{message}\nContext: {json.dumps(self.context, indent=2, ensure_ascii=False)}"

        if level.lower() == "debug":
            self.logger.debug(message)
        elif level.lower() == "info":
            self.logger.info(message)
        elif level.lower() == "warning":
            self.logger.warning(message)
        elif level.lower() == "error":
            self.error_logger.error(message)
        elif level.lower() == "critical":
            self.error_logger.critical(message)
        else:
            raise ValueError(f"Неизвестный уровень логирования: {level}")

    def log_error(self, message: str,
                  exc_info: dict[str, Any] | bool | None = None,
                  context: dict[str, Any] | None = None) -> None:
        """Запись ошибки.

        :param message: Сообщение об ошибке.
        :param exc_info: Информация об исключении (если есть).
        """
        if context := context or self.context:
            message = f"{message}\nContext: {json.dumps(context, indent=2, ensure_ascii=False)}"
        self.error_logger.error(message, exc_info=exc_info)

    def cleanup_old_logs(self) -> None:
        """Очистка старых лог-файлов."""
        now = datetime.now()

        for filename in os.listdir(self.log_dir):
            file_path = os.path.join(self.log_dir, filename)
            if os.path.isfile(file_path):
                file_creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if (now - file_creation_time).days > 30:  # Удаляем файлы старше 30 дней
                    os.remove(file_path)
                    self.log(f"Удален старый лог-файл: {filename}", level="info")

    async def create_log_context(self, event: TelegramObject, data: dict[str, Any]) -> None:
        """парсим данные сообщения хендлера.

        Args:
            event: объект хендлера.
            data: содержание хендлера.
        """
        event_dump = event.model_dump()
        self.context = {
        "event_type": event_dump.get("_") if hasattr(event, "_") else event.__class__.__name__,
        "data": event_dump.get("data"),
    }

        # Информация о пользователе
        if user := event_dump.get("from_user") or data.get("event_from_user"):
            self.context |= {
                "user_tg_id": user.get("id"),
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name"),
                "username": user.get("username"),
                "full_name": user.get("full_name")
            }

        # Текст сообщения или callback-данные
        if message := event_dump.get("message") or data.get("event_message"):
            self.context |= {
                "msg_text": message.get("text"),
                "msg_id": message.get("message_id"),
                "reply_markup": message.get("reply_markup")
            }

        # Данные callback-запроса (если это нажатие кнопки)
        if callback := event_dump.get("callback_query") or data.get("event_callback_query"):
            self.context |= {
                "callback_data": callback.get("data"),
                "callback_button_text": callback.get("message", {}).get("text"),
            }

        # Состояние памяти (FSM)
        if (state := data.get("state")) and (state_data := await state.get_data()):  # Получаем данные из состояния
            self.context |= {
                "state_data": state_data,
                "state": await state.get_state(),  # Текущее состояние
            }

        # Дополнительные данные из aiogram
        if chat := event_dump.get("chat") or data.get("event_chat"):
            chat = chat.model_dump() if hasattr(chat, "model_dump") else chat
            self.context |= {
                "chat_id": chat.get("id"),
                "chat_type": chat.get("type"),
            }
        # сообщение от клиента
        if text := event_dump.get("text"):
            self.context |= {"client_text": text}

    def reset_logger_params(self) -> None:
        self.add_message = ""  # обнуляем доп сообщение.
        # если режим не указан в env, то будет инфо
        self.level = "debug" if os.getenv("DEBUG", None) == "True" else "info"

class DuplicateFilter(logging.Filter):
    def __init__(self) -> None:
        super().__init__()
        self.last_log = None

    def filter(self, record: logging.LogRecord) -> bool:
        current_log = (record.module, record.levelno, record.msg)
        if current_log == self.last_log:
            return False
        self.last_log = current_log
        return True

