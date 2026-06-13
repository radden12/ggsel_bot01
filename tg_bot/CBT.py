"""
Callback Texts — константы данных inline-кнопок Telegram-панели.

Хранение строк callback_data в одном месте упрощает поддержку и исключает опечатки.
"""
from __future__ import annotations

#: Главное меню.
MAIN = "main"
#: Экран статуса.
STATUS = "status"
#: Список плагинов.
PLUGINS = "plugins"
#: Переключение конкретного плагина (формат ``plugin_toggle:<uuid>``).
PLUGIN_TOGGLE = "plugin_toggle"
#: Переключение автоответчика.
TOGGLE_AR = "toggle_ar"
#: Переключение автовыдачи.
TOGGLE_AD = "toggle_ad"
#: Закрыть меню.
CLOSE = "close"
