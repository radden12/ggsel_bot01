"""
Telegram-панель управления GGSelCardinal.

:class:`TGBot` — тонкая обёртка над :mod:`telebot` (pyTelegramBotAPI). Ядро создаёт
её в :meth:`core.GGSelCardinal.init` (если Telegram включён) и взаимодействует через
стабильный контракт:

* :meth:`setup` — регистрирует обработчики команд и колбэков;
* :meth:`notify_admins` — рассылает уведомление всем админам;
* :meth:`start_polling_async` — запускает поллинг в фоновом потоке;
* :meth:`stop` — мягко останавливает поллинг.

Доступ к панели ограничен списком админов из конфига (``Telegram.admins``).
"""
from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING, List, Optional

import telebot
from telebot import types

from tg_bot import CBT, keyboards

if TYPE_CHECKING:
    from core import GGSelCardinal

logger = logging.getLogger("TGBot")


class TGBot:
    """Telegram-панель управления и уведомлений."""

    def __init__(self, core: "GGSelCardinal") -> None:
        self.core = core
        self.config = core.config
        self.bot = telebot.TeleBot(self.config.telegram_token, parse_mode="HTML")
        self.admins: List[int] = list(self.config.telegram_admins)
        self._polling_thread: Optional[threading.Thread] = None
        self._ = core._

    # ------------------------------------------------------------------ #
    # Вспомогательное
    # ------------------------------------------------------------------ #
    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admins

    def _state(self, flag: bool) -> str:
        return self._("state_on") if flag else self._("state_off")

    def _status_text(self) -> str:
        profile = self.core.account.profile if self.core.account else None
        username = profile.username if profile else "—"
        return self._(
            "tg_status",
            username,
            len(self.core.plugins),
            self._state(self.core.config.autoresponse_enabled),
            self._state(self.core.config.autodelivery_enabled),
        )

    # ------------------------------------------------------------------ #
    # Настройка обработчиков
    # ------------------------------------------------------------------ #
    def setup(self) -> None:
        self._register_handlers()
        logger.info("Telegram-панель инициализирована (админов: %d).", len(self.admins))

    def _register_handlers(self) -> None:
        bot = self.bot

        @bot.message_handler(commands=["start", "menu"])
        def _on_start(message: types.Message) -> None:
            if not self.is_admin(message.from_user.id):
                bot.reply_to(message, self._("tg_access_denied"))
                return
            bot.send_message(
                message.chat.id,
                self._("tg_welcome", message.from_user.first_name or ""),
                reply_markup=keyboards.main_menu(self.core, self._),
            )

        @bot.callback_query_handler(func=lambda c: True)
        def _on_callback(call: types.CallbackQuery) -> None:
            if not self.is_admin(call.from_user.id):
                bot.answer_callback_query(call.id, self._("tg_access_denied"))
                return
            try:
                self._handle_callback(call)
            except Exception:
                logger.exception("Ошибка обработки callback '%s'.", call.data)
            finally:
                try:
                    bot.answer_callback_query(call.id)
                except Exception:
                    pass

    def _handle_callback(self, call: types.CallbackQuery) -> None:
        bot = self.bot
        data = call.data or ""
        chat_id = call.message.chat.id
        message_id = call.message.message_id

        if data == CBT.MAIN:
            bot.edit_message_text(
                self._("tg_menu_title"), chat_id, message_id,
                reply_markup=keyboards.main_menu(self.core, self._),
            )
        elif data == CBT.STATUS:
            bot.edit_message_text(
                self._status_text(), chat_id, message_id,
                reply_markup=keyboards.back_menu(self._),
            )
        elif data == CBT.TOGGLE_AR:
            self.core.config.autoresponse_enabled = not self.core.config.autoresponse_enabled
            bot.edit_message_reply_markup(
                chat_id, message_id, reply_markup=keyboards.main_menu(self.core, self._)
            )
        elif data == CBT.TOGGLE_AD:
            self.core.config.autodelivery_enabled = not self.core.config.autodelivery_enabled
            bot.edit_message_reply_markup(
                chat_id, message_id, reply_markup=keyboards.main_menu(self.core, self._)
            )
        elif data == CBT.PLUGINS:
            bot.edit_message_text(
                self._("tg_plugins_title"), chat_id, message_id,
                reply_markup=keyboards.plugins_menu(self.core, self._),
            )
        elif data.startswith(f"{CBT.PLUGIN_TOGGLE}:"):
            plugin_uuid = data.split(":", 1)[1]
            self.core.toggle_plugin(plugin_uuid)
            bot.edit_message_reply_markup(
                chat_id, message_id, reply_markup=keyboards.plugins_menu(self.core, self._)
            )
        elif data == CBT.CLOSE:
            try:
                bot.delete_message(chat_id, message_id)
            except Exception:
                bot.edit_message_text(self._("tg_closed"), chat_id, message_id)

    # ------------------------------------------------------------------ #
    # Среда выполнения
    # ------------------------------------------------------------------ #
    def notify_admins(self, text: str) -> None:
        """Рассылает текст всем администраторам."""
        for admin_id in self.admins:
            try:
                self.bot.send_message(admin_id, text)
            except Exception:
                logger.exception("Не удалось отправить уведомление админу %s.", admin_id)

    def start_polling_async(self) -> None:
        """Запускает поллинг в отдельном демоническом потоке."""
        if self._polling_thread and self._polling_thread.is_alive():
            return
        self._polling_thread = threading.Thread(
            target=self._poll, name="tg-bot-polling", daemon=True
        )
        self._polling_thread.start()
        logger.info("Telegram-поллинг запущен.")

    def _poll(self) -> None:
        try:
            self.bot.infinity_polling(skip_pending=True, timeout=30)
        except Exception:
            logger.exception("Ошибка Telegram-поллинга.")

    def stop(self) -> None:
        """Останавливает поллинг."""
        try:
            self.bot.stop_polling()
        except Exception:
            pass
        logger.info("Telegram-панель остановлена.")
