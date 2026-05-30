"""Перечисления уровня API GGSEL."""
from __future__ import annotations

from enum import Enum, auto


class EventType(Enum):
    """Типы событий, которые порождает :class:`GGSelAPI.updater.runner.Runner`."""

    #: Первичная инициализация: получен стартовый снимок чатов.
    INITIAL_CHATS = auto()
    #: Список чатов изменился (появился новый чат или новое последнее сообщение).
    CHATS_CHANGED = auto()
    #: В существующем чате новое сообщение от покупателя.
    NEW_MESSAGE = auto()
    #: Первичная инициализация: получен стартовый снимок заказов.
    INITIAL_ORDERS = auto()
    #: Появился новый заказ.
    NEW_ORDER = auto()
    #: У заказа изменился статус.
    ORDER_STATUS_CHANGED = auto()


class OrderStatus(Enum):
    """Статусы заказа на GGSEL."""

    PENDING = "pending"      # ожидает оплаты
    PAID = "paid"            # оплачен
    DELIVERED = "delivered"  # товар выдан
    REFUNDED = "refunded"    # возврат
    DISPUTE = "dispute"      # открыт спор
    CLOSED = "closed"        # завершён

    @classmethod
    def from_raw(cls, value: str) -> "OrderStatus":
        try:
            return cls(str(value).lower())
        except ValueError:
            return cls.PENDING


class MessageAuthor(Enum):
    """Кто отправил сообщение в чате."""

    BUYER = "buyer"
    SELLER = "seller"
    SYSTEM = "system"
