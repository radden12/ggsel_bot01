"""
Встроенные обработчики событий GGSelCardinal.

Реализуют базовую бизнес-логику: автоответчик, автовыдачу и уведомления.
Подключаются через :func:`register`, которую вызывает ядро на этапе init().

Встроенные обработчики намеренно имеют ту же сигнатуру, что и плагины: ``(core, event)``.
"""
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from GGSelAPI.common.enums import EventType, OrderStatus
from GGSelAPI.updater.events import NewMessageEvent, NewOrderEvent, OrderStatusChangedEvent
from Utils import core_tools

if TYPE_CHECKING:
    from core import GGSelCardinal

logger = logging.getLogger("Handlers")


def register(core: "GGSelCardinal") -> None:
    """Подписывает встроенные обработчики на события ядра."""
    core.add_handler(EventType.NEW_MESSAGE, handle_new_message)
    core.add_handler(EventType.NEW_ORDER, handle_new_order)
    core.add_handler(EventType.ORDER_STATUS_CHANGED, handle_order_status_changed)
    logger.info("Встроенные обработчики подключены.")


def handle_new_message(core: "GGSelCardinal", event: NewMessageEvent) -> None:
    """Автоответчик: реагирует на команды/ключевые фразы покупателей."""
    if not core.config.autoresponse_enabled:
        return

    text = event.message.text.strip().lower()
    if not text:
        return

    entry = core.auto_response.get(text)
    if entry is None:
        return

    variables = {
        "buyer_name": event.chat.buyer_name,
        "chat_id": event.chat.id,
        "seller": core.account.profile.username if core.account and core.account.profile else "",
    }
    response = core_tools.render_template(entry.response, variables)

    assert core.account is not None
    core.account.send_message(event.chat.id, response)
    logger.info("Автоответ на команду '%s' в чате %s", text, event.chat.id)

    if entry.telegram_notify:
        core.send_telegram(
            core._("notify_autoresponse", event.chat.buyer_name, core_tools.shorten(event.message.text))
        )


def handle_new_order(core: "GGSelCardinal", event: NewOrderEvent) -> None:
    """Уведомляет об оплаченном заказе и запускает автовыдачу."""
    order = event.order
    logger.info("Новый заказ #%s: %s (%.2f %s)", order.id, order.lot_title, order.amount, order.currency)

    core.send_telegram(
        core._("notify_new_order", order.id, order.lot_title, order.amount, order.currency, order.buyer_name)
    )

    if order.status in (OrderStatus.PAID, OrderStatus.DELIVERED):
        _deliver(core, event)


def handle_order_status_changed(core: "GGSelCardinal", event: OrderStatusChangedEvent) -> None:
    """Реагирует на смену статуса заказа: выдаёт товар при оплате, уведомляет о спорах."""
    order = event.order
    logger.info("Заказ #%s: %s -> %s", order.id, event.old_status.value, event.new_status.value)

    if event.new_status is OrderStatus.PAID:
        _deliver(core, event)
    elif event.new_status is OrderStatus.DISPUTE:
        core.send_telegram(core._("notify_dispute", order.id, order.buyer_name))
    elif event.new_status is OrderStatus.REFUNDED:
        core.send_telegram(core._("notify_refund", order.id))


def _deliver(core: "GGSelCardinal", event) -> None:
    """Выполняет автовыдачу товара по заказу, если для лота настроено правило."""
    if not core.config.autodelivery_enabled:
        return

    order = event.order
    entry = core.auto_delivery.get(order.lot_title.strip().lower())
    if entry is None or not entry.enabled:
        return

    payload = entry.message
    secret = _pop_product(entry.products_file)
    variables = {
        "buyer_name": order.buyer_name,
        "order_id": order.id,
        "lot": order.lot_title,
        "product": secret or "",
    }
    message = core_tools.render_template(payload, variables)

    if not order.chat_id:
        logger.warning("У заказа #%s нет chat_id — автовыдача невозможна.", order.id)
        return

    assert core.account is not None
    core.account.send_message(order.chat_id, message)
    logger.info("Автовыдача по заказу #%s выполнена.", order.id)
    core.send_telegram(core._("notify_delivered", order.id, order.lot_title))


def _pop_product(products_file: str) -> str:
    """
    Берёт одну строку-товар из файла товаров и удаляет её (FIFO).

    Файлы товаров лежат в ``storage/products``. Если файл не задан или пуст —
    возвращается пустая строка.
    """
    if not products_file:
        return ""
    path = os.path.join("storage", "products", products_file)
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as fh:
        lines = [line.rstrip("\n") for line in fh if line.strip()]
    if not lines:
        return ""
    product, rest = lines[0], lines[1:]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(rest) + ("\n" if rest else ""))
    return product
