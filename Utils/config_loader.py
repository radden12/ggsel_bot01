"""
Загрузчик конфигурации GGSelCardinal.

Конфиги хранятся в INI-подобном формате и читаются стандартным :mod:`configparser`.
Модуль возвращает уже провалидированные структуры, а не сырой parser, чтобы ядро не
знало о деталях формата.
"""
from __future__ import annotations

import configparser
import os
from dataclasses import dataclass, field
from typing import Dict, List

from Utils.exceptions import ConfigError, FieldRequiredError


def _new_parser() -> configparser.ConfigParser:
    # Отключаем интерполяцию: в шаблонах автоответов встречается символ '%'.
    parser = configparser.ConfigParser(interpolation=None)
    # Сохраняем регистр ключей (важно для команд автоответчика).
    parser.optionxform = str  # type: ignore[assignment]
    return parser


def _read(path: str) -> configparser.ConfigParser:
    if not os.path.exists(path):
        raise ConfigError(f"Файл конфигурации не найден: {path}")
    parser = _new_parser()
    try:
        parser.read(path, encoding="utf-8")
    except configparser.Error as exc:
        raise ConfigError(f"Не удалось прочитать {path}: {exc}") from exc
    return parser


@dataclass
class MainConfig:
    """Основные настройки приложения (``configs/_main.cfg``)."""

    ggsel_token: str
    ggsel_seller_id: str = ""
    telegram_enabled: bool = False
    telegram_token: str = ""
    telegram_admins: List[int] = field(default_factory=list)
    language: str = "ru"
    poll_interval: float = 4.0
    autoresponse_enabled: bool = True
    autodelivery_enabled: bool = True


def _require(parser: configparser.ConfigParser, section: str, key: str) -> str:
    if not parser.has_section(section):
        raise ConfigError(f"В конфиге отсутствует секция [{section}].")
    value = parser.get(section, key, fallback="").strip()
    if not value:
        raise FieldRequiredError(section, key)
    return value


def load_main_config(path: str) -> MainConfig:
    """Читает и валидирует основной конфиг."""
    parser = _read(path)

    ggsel_token = _require(parser, "GGSel", "token")
    seller_id = parser.get("GGSel", "seller_id", fallback="").strip()

    tg_enabled = parser.getboolean("Telegram", "enabled", fallback=False)
    tg_token = parser.get("Telegram", "token", fallback="").strip()
    admins_raw = parser.get("Telegram", "admins", fallback="").strip()
    admins: List[int] = []
    for chunk in admins_raw.replace(";", ",").split(","):
        chunk = chunk.strip()
        if chunk.isdigit():
            admins.append(int(chunk))

    if tg_enabled and not tg_token:
        raise FieldRequiredError("Telegram", "token")

    return MainConfig(
        ggsel_token=ggsel_token,
        ggsel_seller_id=seller_id,
        telegram_enabled=tg_enabled,
        telegram_token=tg_token,
        telegram_admins=admins,
        language=parser.get("Other", "language", fallback="ru").strip() or "ru",
        poll_interval=parser.getfloat("Other", "poll_interval", fallback=4.0),
        autoresponse_enabled=parser.getboolean("Other", "autoresponse", fallback=True),
        autodelivery_enabled=parser.getboolean("Other", "autodelivery", fallback=True),
    )


@dataclass
class AutoResponseEntry:
    """Одна команда автоответчика."""

    command: str
    response: str
    telegram_notify: bool = False


def load_auto_response_config(path: str) -> Dict[str, AutoResponseEntry]:
    """
    Читает конфиг автоответчика.

    Каждая секция — отдельная команда. Ключ ``response`` обязателен.
    """
    if not os.path.exists(path):
        return {}
    parser = _read(path)
    entries: Dict[str, AutoResponseEntry] = {}
    for section in parser.sections():
        response = parser.get(section, "response", fallback="").strip()
        if not response:
            continue
        entries[section.lower()] = AutoResponseEntry(
            command=section,
            response=response,
            telegram_notify=parser.getboolean(section, "telegramNotification", fallback=False),
        )
    return entries


@dataclass
class AutoDeliveryEntry:
    """Правило автовыдачи для товара."""

    lot: str
    message: str
    products_file: str = ""
    enabled: bool = True


def load_auto_delivery_config(path: str) -> Dict[str, AutoDeliveryEntry]:
    """Читает конфиг автовыдачи. Ключ секции — название/идентификатор лота."""
    if not os.path.exists(path):
        return {}
    parser = _read(path)
    entries: Dict[str, AutoDeliveryEntry] = {}
    for section in parser.sections():
        message = parser.get(section, "response", fallback="").strip()
        if not message:
            continue
        entries[section.lower()] = AutoDeliveryEntry(
            lot=section,
            message=message,
            products_file=parser.get(section, "productsFileName", fallback="").strip(),
            enabled=parser.getboolean(section, "enabled", fallback=True),
        )
    return entries
