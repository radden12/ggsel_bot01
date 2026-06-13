"""
Inline-клавиатуры Telegram-панели.

Функции возвращают :class:`telebot.types.InlineKeyboardMarkup`. Тексты берутся через
локализатор ``_`` (``core._``), поэтому панель отображается на выбранном языке.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from telebot import types

from tg_bot import CBT

if TYPE_CHECKING:
    from core import GGSelCardinal


def _state(flag: bool, _: Callable) -> str:
    return _("state_on") if flag else _("state_off")


def main_menu(core: "GGSelCardinal", _: Callable) -> types.InlineKeyboardMarkup:
    """Главное меню панели."""
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(_("btn_status"), callback_data=CBT.STATUS))
    kb.add(types.InlineKeyboardButton(_("btn_plugins"), callback_data=CBT.PLUGINS))
    kb.add(
        types.InlineKeyboardButton(
            f"{_('btn_autoresponse')}: {_state(core.config.autoresponse_enabled, _)}",
            callback_data=CBT.TOGGLE_AR,
        )
    )
    kb.add(
        types.InlineKeyboardButton(
            f"{_('btn_autodelivery')}: {_state(core.config.autodelivery_enabled, _)}",
            callback_data=CBT.TOGGLE_AD,
        )
    )
    kb.add(types.InlineKeyboardButton(_("btn_close"), callback_data=CBT.CLOSE))
    return kb


def back_menu(_: Callable) -> types.InlineKeyboardMarkup:
    """Клавиатура с единственной кнопкой «Назад»."""
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(_("btn_back"), callback_data=CBT.MAIN))
    return kb


def plugins_menu(core: "GGSelCardinal", _: Callable) -> types.InlineKeyboardMarkup:
    """Список плагинов с индикатором состояния."""
    kb = types.InlineKeyboardMarkup(row_width=1)
    if not core.plugins:
        kb.add(types.InlineKeyboardButton(_("tg_plugins_empty"), callback_data=CBT.MAIN))
        kb.add(types.InlineKeyboardButton(_("btn_back"), callback_data=CBT.MAIN))
        return kb
    for plugin in core.plugins.values():
        mark = "🟢" if plugin.enabled else "🔴"
        kb.add(
            types.InlineKeyboardButton(
                f"{mark} {plugin.name} v{plugin.version}",
                callback_data=f"{CBT.PLUGIN_TOGGLE}:{plugin.uuid}",
            )
        )
    kb.add(types.InlineKeyboardButton(_("btn_back"), callback_data=CBT.MAIN))
    return kb
