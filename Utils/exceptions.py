"""Исключения уровня приложения (инфраструктура, конфиги, плагины)."""
from __future__ import annotations


class GGSelCardinalError(Exception):
    """Базовое исключение приложения."""


class ConfigError(GGSelCardinalError):
    """Ошибка чтения или валидации конфигурации."""


class FieldRequiredError(ConfigError):
    """Обязательное поле конфигурации отсутствует."""

    def __init__(self, section: str, field: str):
        self.section = section
        self.field = field
        super().__init__(f"В секции [{section}] отсутствует обязательное поле '{field}'.")


class PluginLoadError(GGSelCardinalError):
    """Не удалось загрузить плагин."""

    def __init__(self, plugin_path: str, reason: str):
        self.plugin_path = plugin_path
        self.reason = reason
        super().__init__(f"Не удалось загрузить плагин '{plugin_path}': {reason}")
