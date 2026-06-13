"""
Шаблон плагина GGSelCardinal.

Скопируйте этот файл, переименуйте так, чтобы имя НЕ начиналось с «_»
(например, ``my_plugin.py``), и реализуйте нужные обработчики. Файлы,
начинающиеся с «_», ядро намеренно не загружает — поэтому сам шаблон неактивен.

Сигнатура любого обработчика: ``(core, event)``.
"""
from __future__ import annotations

NAME = "Template Plugin"
VERSION = "0.1.0"
DESCRIPTION = "Краткое описание плагина."
CREDITS = "@your_username"
UUID = "00000000-0000-0000-0000-000000000000"
SETTINGS_PAGE = False


def pre_init(core, _event=None):
    """Вызывается до инициализации компонентов ядра."""


def post_init(core, _event=None):
    """Вызывается после инициализации (account/runner/telegram готовы)."""


def on_new_message(core, event):
    """event: GGSelAPI.updater.events.NewMessageEvent"""


def on_new_order(core, event):
    """event: GGSelAPI.updater.events.NewOrderEvent"""


def on_order_status_changed(core, event):
    """event: GGSelAPI.updater.events.OrderStatusChangedEvent"""


def on_delete(core, _event=None):
    """Вызывается при выгрузке плагина."""


BIND_TO_PRE_INIT = [pre_init]
BIND_TO_POST_INIT = [post_init]
BIND_TO_NEW_MESSAGE = [on_new_message]
BIND_TO_NEW_ORDER = [on_new_order]
BIND_TO_ORDER_STATUS_CHANGED = [on_order_status_changed]
BIND_TO_DELETE = on_delete
