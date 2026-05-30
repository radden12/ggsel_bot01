"""
Пример плагина «Часы».

Отвечает покупателю текущим временем сервера, когда тот пишет ``!время`` или ``!time``.
Демонстрирует две точки привязки: ``BIND_TO_POST_INIT`` и ``BIND_TO_NEW_MESSAGE``.
"""
from __future__ import annotations

import logging
from datetime import datetime

logger = logging.getLogger("plugin.clock")

NAME = "Clock Example"
VERSION = "1.0.0"
DESCRIPTION = "Отвечает текущим временем сервера на команды !время / !time."
CREDITS = "GGSelCardinal"
UUID = "7b6f2c9e-1d34-4a5b-9c0e-1a2b3c4d5e6f"
SETTINGS_PAGE = False

TRIGGERS = ("!время", "!time")


def on_post_init(core, _event=None):
    """Сообщает в лог, что плагин готов к работе."""
    logger.info("Плагин «%s» v%s загружен.", NAME, VERSION)


def on_new_message(core, event):
    """Отправляет время сервера, если сообщение совпало с триггером."""
    text = (event.message.text or "").strip().lower()
    if text not in TRIGGERS:
        return
    if core.account is None:
        return
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    core.account.send_message(event.chat.id, f"🕒 Время сервера: {now}")
    logger.info("Отправлено время в чат %s.", event.chat.id)


BIND_TO_POST_INIT = [on_post_init]
BIND_TO_NEW_MESSAGE = [on_new_message]
BIND_TO_DELETE = None
