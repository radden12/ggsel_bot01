"""
Runner — цикл опроса площадки.

Работает как генератор: на каждой итерации запрашивает чаты и заказы, сравнивает
с предыдущим состоянием и отдаёт разницу в виде событий. Ядро просто итерируется
по этому генератору.

Такой подход (diff по снимкам) повторяет логику «обновлений» классических ботов
для бирж цифровых товаров.
"""
from __future__ import annotations

import logging
import time
from typing import Dict, Iterator, List

from GGSelAPI.account import Account
from GGSelAPI.common.enums import EventType, OrderStatus
from GGSelAPI.common.exceptions import GGSelApiError
from GGSelAPI.types import Chat, Order
from GGSelAPI.updater.events import (
    BaseEvent,
    ChatsChangedEvent,
    InitialChatsEvent,
    InitialOrdersEvent,
    NewMessageEvent,
    NewOrderEvent,
    OrderStatusChangedEvent,
)

logger = logging.getLogger("Runner")


class Runner:
    """Генерирует события на основе изменений на площадке."""

    def __init__(self, account: Account, poll_interval: float = 4.0) -> None:
        self.account = account
        self.poll_interval = max(1.0, poll_interval)
        self.running = False

        self._known_last_message: Dict[str, str] = {}
        self._known_order_status: Dict[str, OrderStatus] = {}
        self._bootstrapped = False

    def stop(self) -> None:
        self.running = False

    def listen(self) -> Iterator[BaseEvent]:
        """Бесконечный генератор событий. Останавливается через :meth:`stop`."""
        self.running = True
        while self.running:
            try:
                yield from self._poll_once()
            except GGSelApiError as exc:
                logger.error("Ошибка опроса площадки: %s", exc)
            except Exception:
                logger.exception("Неожиданная ошибка в цикле опроса.")
            time.sleep(self.poll_interval)

    # ------------------------------------------------------------------ #
    def _poll_once(self) -> Iterator[BaseEvent]:
        chats = self.account.get_chats()
        orders = self.account.get_orders()

        if not self._bootstrapped:
            for chat in chats:
                self._known_last_message[chat.id] = chat.last_message_id
            for order in orders:
                self._known_order_status[order.id] = order.status
            self._bootstrapped = True
            yield InitialChatsEvent(type=EventType.INITIAL_CHATS, chats=chats)
            yield InitialOrdersEvent(type=EventType.INITIAL_ORDERS, orders=orders)
            return

        yield from self._diff_chats(chats)
        yield from self._diff_orders(orders)

    def _diff_chats(self, chats: List[Chat]) -> Iterator[BaseEvent]:
        changed = False
        for chat in chats:
            previous = self._known_last_message.get(chat.id)
            if chat.last_message_id and chat.last_message_id != previous:
                changed = True
                self._known_last_message[chat.id] = chat.last_message_id
                # Добираем последнее сообщение и проверяем, что оно от покупателя.
                try:
                    messages = self.account.get_chat_messages(chat.id, limit=1)
                except GGSelApiError:
                    messages = []
                if messages and messages[-1].is_from_buyer:
                    yield NewMessageEvent(
                        type=EventType.NEW_MESSAGE, chat=chat, message=messages[-1]
                    )
        if changed:
            yield ChatsChangedEvent(type=EventType.CHATS_CHANGED, chats=chats)

    def _diff_orders(self, orders: List[Order]) -> Iterator[BaseEvent]:
        for order in orders:
            previous = self._known_order_status.get(order.id)
            if previous is None:
                self._known_order_status[order.id] = order.status
                yield NewOrderEvent(type=EventType.NEW_ORDER, order=order)
            elif previous != order.status:
                self._known_order_status[order.id] = order.status
                yield OrderStatusChangedEvent(
                    type=EventType.ORDER_STATUS_CHANGED,
                    order=order,
                    old_status=previous,
                    new_status=order.status,
                )
