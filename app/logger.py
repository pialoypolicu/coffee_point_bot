import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Any

from colorlog import ColoredFormatter


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

        # Создаем директорию для логов, если она не существует
        os.makedirs("app/logs", exist_ok=True)

        # Настройка основного логгера
        self.logger = logging.getLogger("bot_logger")
        self.logger.setLevel(logging.INFO)

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
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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

    def log(self, message: str, level: str = "info") -> None:
        """Запись лога.

        :param message: Сообщение для логирования.
        :param level: Уровень логирования (info, warning, error, critical).
        """
        if level.lower() == "info":
            self.logger.info(message)
        elif level.lower() == "warning":
            self.logger.warning(message)
        elif level.lower() == "error":
            self.error_logger.error(message)
        elif level.lower() == "critical":
            self.error_logger.critical(message)
        else:
            raise ValueError(f"Неизвестный уровень логирования: {level}")

    def log_error(self, message: str, exc_info: dict[str, Any] | bool | None = None) -> None:
        """Запись ошибки.

        :param message: Сообщение об ошибке.
        :param exc_info: Информация об исключении (если есть).
        """
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
