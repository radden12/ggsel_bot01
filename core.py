"""
Ядро GGSelCardinal.

Связывает воеместе: клиент площадки (:class:`GGSelAPI.Account`), цикл событий
(:class:`GGSelAPI.updater.Runner`), Telegram-панель (:class:`tg_bot.bot.TGBot`),
встроенные обработчики (:mod:`handlers`) и внешние плагины.

Философия: ядро — это оркестратор. Оно держит списки обработчиков по типам
событий и последовательно вызывает их. Любая логика (встроенная или плагин) — это
просто функции, подписанные на события.
"""
from __future__ import annotations

import importlib.util
import logging
import os
import threading
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from GGSelAPI import Account
from GGSelAPI.common.enums import EventType
from GGSelAPI.updater import Runner
from GGSelAPI.updater.events import BaseEvent
from Utils import config_loader
from Utils.config_loader import AutoDeliveryEntry, AutoResponseEntry, MainConfig
from Utils.exceptions import PluginLoadError
from locales.localizer import Localizer

logger = logging.getLogger("GGSelCardinal")

Handler = Callable[["GGSelCardinal", Any], None]

# Имена точек привязки. Плагин объявляет переменную с таким именем —
# список функций, которые ядро вызовет на соответствующем этапе.
BIND_PRE_INIT = "BIND_TO_PRE_INIT"
BIND_POST_INIT = "BIND_TO_POST_INIT"
BIND_NEW_MESSAGE = "BIND_TO_NEW_MESSAGE"
BIND_NEW_ORDER = "BIND_TO_NEW_ORDER"
BIND_ORDER_STATUS_CHANGED = "BIND_TO_ORDER_STATUS_CHANGED"
BIND_DELETE = "BIND_TO_DELETE"


@dataclass
class Plugin:
    """Метаданные и состояние загруженного плагина."""

    uuid: str
    name: str
    version: str
    description: str
    credits: str
    path: str
    module: Any
    enabled: bool = True
    delete_handler: Optional[Handler] = None


class GGSelCardinal:
    """Центральный оркестратор приложения."""

    CONFIG_DIR = "configs"
    PLUGINS_DIR = "plugins"

    def __init__(self, version: str = "0.0.0") -> None:
        self.version = version

        # Конфиги.
        self.config: MainConfig = config_loader.load_main_config(
            os.path.join(self.CONFIG_DIR, "_main.cfg")
        )
        self.auto_response: Dict[str, AutoResponseEntry] = config_loader.load_auto_response_config(
            os.path.join(self.CONFIG_DIR, "auto_response.cfg")
        )
        self.auto_delivery: Dict[str, AutoDeliveryEntry] = config_loader.load_auto_delivery_config(
            os.path.join(self.CONFIG_DIR, "auto_delivery.cfg")
        )

        # Локализация.
        self.localizer = Localizer(self.config.language)
        self._ = self.localizer.translate

        # Компоненты (инициализируются в init()).
        self.account: Optional[Account] = None
        self.runner: Optional[Runner] = None
        self.telegram = None  # type: ignore[assignment]

        # Реестр обработчиков по типам событий.
        self.handlers: Dict[EventType, List[Handler]] = {event: [] for event in EventType}
        self.pre_init_handlers: List[Handler] = []
        self.post_init_handlers: List[Handler] = []

        # Плагины.
        self.plugins: Dict[str, Plugin] = {}

        self._stop_event = threading.Event()

    # ------------------------------------------------------------------ #
    # Публичный API для обработчиков и плагинов
    # ------------------------------------------------------------------ #
    def add_handler(self, event_type: EventType, handler: Handler) -> None:
        """Подписывает функцию на событие заданного типа."""
        self.handlers[event_type].append(handler)

    def run_handlers(self, event_type: EventType, event: BaseEvent) -> None:
        """Последовательно вызывает все обработчики события, изолируя ошибки."""
        for handler in self.handlers.get(event_type, []):
            try:
                handler(self, event)
            except Exception:
                logger.exception("Ошибка в обработчике события %s.", event_type.name)

    def send_telegram(self, text: str) -> None:
        """Удобный шорткат для уведомлений админам через Telegram."""
        if self.telegram is not None:
            self.telegram.notify_admins(text)

    # ------------------------------------------------------------------ #
    # Инициализация
    # ------------------------------------------------------------------ #
    def init(self) -> "GGSelCardinal":
        """Поднимает все компоненты и регистрирует обработчики."""
        logger.info(self._("init_start"))

        # 1. Клиент площадки.
        self.account = Account(self.config.ggsel_token, self.config.ggsel_seller_id)
        self.account.authorize()

        # 2. Цикл событий.
        self.runner = Runner(self.account, poll_interval=self.config.poll_interval)

        # 3. Telegram-панель (опционально).
        if self.config.telegram_enabled:
            from tg_bot.bot import TGBot
            self.telegram = TGBot(self)
            self.telegram.setup()

        # 4. Встроенные обработчики.
        import handlers
        handlers.register(self)

        # 5. Плагины.
        self._load_plugins()

        # 6. Этап post-init для плагинов.
        for handler in self.post_init_handlers:
            try:
                handler(self, None)
            except Exception:
                logger.exception("Ошибка в post-init обработчике.")

        logger.info(self._("init_done", len(self.plugins)))
        return self

    # ------------------------------------------------------------------ #
    # Система плагинов
    # ------------------------------------------------------------------ #
    def _load_plugins(self) -> None:
        if not os.path.isdir(self.PLUGINS_DIR):
            return
        for filename in sorted(os.listdir(self.PLUGINS_DIR)):
            if not filename.endswith(".py") or filename.startswith("_"):
                continue
            path = os.path.join(self.PLUGINS_DIR, filename)
            try:
                self._load_plugin_file(path)
            except PluginLoadError as exc:
                logger.error(str(exc))
            except Exception:
                logger.exception("Непредвиденная ошибка при загрузке плагина %s.", path)

    def _load_plugin_file(self, path: str) -> None:
        module_name = f"ggsel_plugin_{os.path.splitext(os.path.basename(path))[0]}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise PluginLoadError(path, "не удалось создать спецификацию модуля")
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as exc:  # noqa: BLE001
            raise PluginLoadError(path, f"ошибка импорта: {exc}") from exc

        plugin_uuid = str(getattr(module, "UUID", "") or uuid.uuid4())
        plugin = Plugin(
            uuid=plugin_uuid,
            name=str(getattr(module, "NAME", os.path.basename(path))),
            version=str(getattr(module, "VERSION", "0.0.0")),
            description=str(getattr(module, "DESCRIPTION", "")),
            credits=str(getattr(module, "CREDITS", "")),
            path=path,
            module=module,
            delete_handler=self._first_or_none(getattr(module, BIND_DELETE, None)),
        )
        self.plugins[plugin_uuid] = plugin
        self._bind_module_handlers(module)
        logger.info(self._("plugin_loaded", plugin.name, plugin.version))

    def _bind_module_handlers(self, module: Any) -> None:
        """Читает BIND_TO_* из модуля и регистрирует функции."""
        for func in self._as_list(getattr(module, BIND_PRE_INIT, None)):
            func(self, None)
        self.pre_init_handlers.extend(self._as_list(getattr(module, BIND_PRE_INIT, None)))
        self.post_init_handlers.extend(self._as_list(getattr(module, BIND_POST_INIT, None)))
        for func in self._as_list(getattr(module, BIND_NEW_MESSAGE, None)):
            self.add_handler(EventType.NEW_MESSAGE, func)
        for func in self._as_list(getattr(module, BIND_NEW_ORDER, None)):
            self.add_handler(EventType.NEW_ORDER, func)
        for func in self._as_list(getattr(module, BIND_ORDER_STATUS_CHANGED, None)):
            self.add_handler(EventType.ORDER_STATUS_CHANGED, func)

    @staticmethod
    def _as_list(value: Any) -> List[Handler]:
        if value is None:
            return []
        if callable(value):
            return [value]
        if isinstance(value, (list, tuple)):
            return [f for f in value if callable(f)]
        return []

    @classmethod
    def _first_or_none(cls, value: Any) -> Optional[Handler]:
        handlers = cls._as_list(value)
        return handlers[0] if handlers else None

    def toggle_plugin(self, plugin_uuid: str) -> None:
        """Включает/выключает плагин (флаг учитывается обработчиками)."""
        plugin = self.plugins.get(plugin_uuid)
        if plugin:
            plugin.enabled = not plugin.enabled

    # ------------------------------------------------------------------ #
    # Главный цикл
    # ------------------------------------------------------------------ #
    def run(self) -> None:
        """Запускает Telegram-панель и основной цикл обработки событий."""
        if self.telegram is not None:
            self.telegram.start_polling_async()

        assert self.runner is not None
        logger.info(self._("run_start"))
        for event in self.runner.listen():
            if self._stop_event.is_set():
                break
            self.run_handlers(event.type, event)

    def shutdown(self) -> None:
        """Мягко останавливает ядро."""
        self._stop_event.set()
        if self.runner is not None:
            self.runner.stop()
        if self.telegram is not None:
            self.telegram.stop()
        logger.info(self._("shutdown"))
