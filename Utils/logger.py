"""
Конфигурация логирования GGSelCardinal.

Используется :func:`logging.config.dictConfig`. Формат вывода в консоль —
цветной и компактный, в файл — подробный с датой.
"""
from __future__ import annotations

import logging
import os

try:
    from colorama import Fore, Style, init as _colorama_init
    _colorama_init()
    _COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }
    _RESET = Style.RESET_ALL
except Exception:  # colorama может отсутствовать на этапе раннего импорта
    _COLORS = {}
    _RESET = ""

LOG_FILE = os.path.join("logs", "ggsel.log")


class ColorFormatter(logging.Formatter):
    """Подкрашивает уровень логирования в консоли."""

    def format(self, record: logging.LogRecord) -> str:
        color = _COLORS.get(record.levelname, "")
        record.levelcolor = f"{color}{record.levelname}{_RESET}"
        return super().format(record)


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "()": "Utils.logger.ColorFormatter",
            "format": "[%(asctime)s] %(levelcolor)s | %(name)s | %(message)s",
            "datefmt": "%H:%M:%S",
        },
        "file": {
            "format": "[%(asctime)s] %(levelname)s | %(name)s | %(funcName)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
            "level": "INFO",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "file",
            "level": "DEBUG",
            "filename": LOG_FILE,
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
        },
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["console", "file"],
    },
}
