"""
Модели данных GGSelAPI.

Это простые dataclass-структуры, которыми оперируют ядро, обработчики и плагины.
Каждая модель умеет конструироваться из «сырого» словаря ответа площадки через
класс-метод ``from_raw`` — это держит парсинг рядом со схемой.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from GGSelAPI.common.enums import MessageAuthor, OrderStatus
from GGSelAPI.common import utils


@dataclass
class AccountProfile:
    """Профиль авторизованного продавца."""

    seller_id: str
    username: str
    balance: float = 0.0
    currency: str = "RUB"
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, data: Dict[str, Any]) -> "AccountProfile":
        return cls(
            seller_id=utils.as_str(data.get("seller_id") or data.get("id")),
            username=utils.as_str(data.get("username") or data.get("name"), "unknown"),
            balance=utils.as_float(data.get("balance")),
            currency=utils.as_str(data.get("currency"), "RUB"),
            raw=data,
        )


@dataclass
class Message:
    """Сообщение в диалоге с покупателем."""

    id: str
    chat_id: str
    author: MessageAuthor
    text: str
    author_name: str = ""
    created_at: Optional[datetime] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_from_buyer(self) -> bool:
        return self.author is MessageAuthor.BUYER

    @classmethod
    def from_raw(cls, chat_id: str, data: Dict[str, Any]) -> "Message":
        raw_author = utils.as_str(data.get("author") or data.get("sender"), "buyer").lower()
        try:
            author = MessageAuthor(raw_author)
        except ValueError:
            author = MessageAuthor.SYSTEM
        return cls(
            id=utils.as_str(data.get("id") or data.get("message_id")),
            chat_id=chat_id,
            author=author,
            text=utils.as_str(data.get("text") or data.get("message")),
            author_name=utils.as_str(data.get("author_name") or data.get("sender_name")),
            created_at=utils.parse_timestamp(data.get("created_at") or data.get("date")),
            raw=data,
        )


@dataclass
class Chat:
    """Диалог продавца с покупателем."""

    id: str
    buyer_id: str
    buyer_name: str
    last_message_text: str = ""
    last_message_id: str = ""
    unread: bool = False
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, data: Dict[str, Any]) -> "Chat":
        return cls(
            id=utils.as_str(data.get("id") or data.get("chat_id")),
            buyer_id=utils.as_str(data.get("buyer_id") or data.get("user_id")),
            buyer_name=utils.as_str(data.get("buyer_name") or data.get("username"), "buyer"),
            last_message_text=utils.as_str(data.get("last_message") or data.get("preview")),
            last_message_id=utils.as_str(data.get("last_message_id")),
            unread=bool(data.get("unread", False)),
            raw=data,
        )


@dataclass
class Order:
    """Заказ на площадке."""

    id: str
    buyer_id: str
    buyer_name: str
    lot_title: str
    amount: float
    currency: str
    status: OrderStatus
    chat_id: str = ""
    quantity: int = 1
    created_at: Optional[datetime] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, data: Dict[str, Any]) -> "Order":
        return cls(
            id=utils.as_str(data.get("id") or data.get("order_id")),
            buyer_id=utils.as_str(data.get("buyer_id") or data.get("user_id")),
            buyer_name=utils.as_str(data.get("buyer_name") or data.get("username"), "buyer"),
            lot_title=utils.as_str(data.get("lot_title") or data.get("product") or data.get("title")),
            amount=utils.as_float(data.get("amount") or data.get("price")),
            currency=utils.as_str(data.get("currency"), "RUB"),
            status=OrderStatus.from_raw(utils.as_str(data.get("status"), "pending")),
            chat_id=utils.as_str(data.get("chat_id")),
            quantity=utils.as_int(data.get("quantity"), 1),
            created_at=utils.parse_timestamp(data.get("created_at") or data.get("date")),
            raw=data,
        )


@dataclass
class LotShortcut:
    """Краткая карточка товара (лота) продавца."""

    id: str
    title: str
    price: float
    currency: str = "RUB"
    active: bool = True
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, data: Dict[str, Any]) -> "LotShortcut":
        return cls(
            id=utils.as_str(data.get("id") or data.get("lot_id")),
            title=utils.as_str(data.get("title") or data.get("name")),
            price=utils.as_float(data.get("price")),
            currency=utils.as_str(data.get("currency"), "RUB"),
            active=bool(data.get("active", True)),
            raw=data,
        )
