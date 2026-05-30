"""
Локализатор интерфейса.

Ядро создаёт один экземпляр :class:`Localizer` и использует его метод
:meth:`Localizer.translate` (он же присвоен ярлыку ``core._``) для всех
пользовательских строк: логов, уведомлений и текстов Telegram-панели.

Строки хранятся в словарях по языкам (см. :mod:`locales.ru` и :mod:`locales.en`).
Подстановка аргументов выполняется через :meth:`str.format`, поэтому в шаблонах
используются позиционные плейсхолдеры ``{0}``, ``{1}`` и т.д.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from locales import en, ru

logger = logging.getLogger("Localizer")

DEFAULT_LANGUAGE = "ru"

#: Все доступные наборы переводов.
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "ru": ru.STRINGS,
    "en": en.STRINGS,
}


class Localizer:
    """Возвращает локализованные строки по ключу."""

    def __init__(self, language: str = DEFAULT_LANGUAGE) -> None:
        normalized = (language or DEFAULT_LANGUAGE).strip().lower()
        if normalized not in TRANSLATIONS:
            logger.warning(
                "Язык '%s' не поддерживается, использую '%s'.", language, DEFAULT_LANGUAGE
            )
            normalized = DEFAULT_LANGUAGE
        self.language = normalized
        self.strings = TRANSLATIONS[self.language]
        self.fallback = TRANSLATIONS[DEFAULT_LANGUAGE]

    def translate(self, key: str, *args: Any) -> str:
        """
        Возвращает строку по ключу с подстановкой ``args``.

        Если ключ не найден в выбранном языке — берётся язык по умолчанию,
        затем сам ключ. Ошибки форматирования не валят бота: возвращается шаблон.
        """
        template = self.strings.get(key) or self.fallback.get(key) or key
        if not args:
            return template
        try:
            return template.format(*args)
        except (IndexError, KeyError, ValueError):
            logger.debug("Не удалось подставить аргументы в строку '%s'.", key)
            return template

    #: Удобный синоним, чтобы можно было звать локализатор как функцию.
    __call__ = translate
