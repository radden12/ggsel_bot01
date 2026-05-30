"""
Мелкие переиспользуемые инструменты ядра: работа с консолью, форматирование текста,
подстановка переменных в шаблоны автоответов и т.п.

Намеренно держим тут только чистые функции без состояния.
"""
from __future__ import annotations

import os
import re
import sys
import time
from typing import Mapping

try:
    from colorama import Fore, Style
    _PALETTE = {
        "red": Fore.RED,
        "green": Fore.GREEN,
        "yellow": Fore.YELLOW,
        "blue": Fore.BLUE,
        "cyan": Fore.CYAN,
        "magenta": Fore.MAGENTA,
    }
    _RESET = Style.RESET_ALL
except Exception:
    _PALETTE = {}
    _RESET = ""

_PLACEHOLDER_RE = re.compile(r"\$([a-zA-Z_][a-zA-Z0-9_]*)")


def colorize(text: str, color: str) -> str:
    """Возвращает текст, окрашенный для вывода в терминал."""
    prefix = _PALETTE.get(color, "")
    return f"{prefix}{text}{_RESET}" if prefix else text


def set_console_title(title: str) -> None:
    """Меняет заголовок окна терминала (Windows / *nix)."""
    try:
        if os.name == "nt":
            os.system(f"title {title}")
        else:
            sys.stdout.write(f"\33]0;{title}\a")
            sys.stdout.flush()
    except Exception:
        pass


def now_ms() -> int:
    """Текущее время в миллисекундах."""
    return int(time.time() * 1000)


def render_template(template: str, variables: Mapping[str, str]) -> str:
    """
    Подставляет ``$name`` плейсхолдеры из ``variables`` в ``template``.

    Неизвестные плейсхолдеры остаются как есть, чтобы не терять данные.
    """
    def _replace(match: re.Match) -> str:
        key = match.group(1)
        return str(variables.get(key, match.group(0)))

    return _PLACEHOLDER_RE.sub(_replace, template)


def shorten(text: str, limit: int = 50) -> str:
    """Обрезает строку до ``limit`` символов, добавляя многоточие."""
    text = text.replace("\n", " ").strip()
    return text if len(text) <= limit else text[: limit - 1] + "\u2026"


def cache_file(name: str) -> str:
    """Возвращает путь к файлу в каталоге кеша."""
    return os.path.join("storage", "cache", name)
