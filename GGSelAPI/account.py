"""
Клиент GGSEL: авторизация и типизированные HTTP-методы.

``Account`` — единственная точка, которая работает с сетью. Остальные модули получают
уже разобранные модели из :mod:`GGSelAPI.types`.

Эндпоинты вынесены в константы класса: при изменении API площадки достаточно
поправить их в одном месте.
"""
from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Optional

import requests

from GGSelAPI.common.exceptions import (
    RequestFailedError,
    UnauthorizedError,
    UnexpectedResponseError,
)
from GGSelAPI.types import AccountProfile, Chat, LotShortcut, Message, Order

logger = logging.getLogger("GGSelAPI")


class Account:
    """Авторизованный аккаунт продавца GGSEL."""

    BASE_URL = "https://api.ggsel.net/v1"

    # Эндпоинты площадки (относительно BASE_URL).
    EP_PROFILE = "/seller/profile"
    EP_CHATS = "/seller/chats"
    EP_CHAT_MESSAGES = "/seller/chats/{chat_id}/messages"
    EP_SEND_MESSAGE = "/seller/chats/{chat_id}/messages"
    EP_ORDERS = "/seller/orders"
    EP_ORDER = "/seller/orders/{order_id}"
    EP_LOTS = "/seller/lots"

    def __init__(
        self,
        token: str,
        seller_id: str = "",
        base_url: Optional[str] = None,
        request_timeout: float = 30.0,
        user_agent: str = "GGSelCardinal/0.1",
    ) -> None:
        self.token = token
        self.seller_id = seller_id
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.request_timeout = request_timeout
        self.user_agent = user_agent

        self.profile: Optional[AccountProfile] = None
        self._session = requests.Session()
        self._lock = threading.Lock()
        self._authorized = False

    # ------------------------------------------------------------------ #
    # Низкоуровневый транспорт
    # ------------------------------------------------------------------ #
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        }

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{endpoint}"
        with self._lock:
            try:
                response = self._session.request(
                    method,
                    url,
                    headers=self._headers(),
                    timeout=self.request_timeout,
                    **kwargs,
                )
            except requests.RequestException as exc:
                raise RequestFailedError(url, None, str(exc)) from exc

        if response.status_code in (401, 403):
            raise UnauthorizedError()
        if response.status_code >= 400:
            raise RequestFailedError(url, response.status_code, response.text)

        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError as exc:
            raise UnexpectedResponseError(f"Ответ {url} не является JSON.") from exc

    @staticmethod
    def _unwrap_list(payload: Any, *keys: str) -> List[Dict[str, Any]]:
        """Извлекает список из ответа, учитывая разные форматы обёртки."""
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in keys:
                value = payload.get(key)
                if isinstance(value, list):
                    return value
            data = payload.get("data")
            if isinstance(data, list):
                return data
        return []

    # ------------------------------------------------------------------ #
    # Высокоуровневые методы
    # ------------------------------------------------------------------ #
    def authorize(self) -> AccountProfile:
        """Проверяет ключ и загружает профиль продавца."""
        payload = self._request("GET", self.EP_PROFILE)
        data = payload.get("data", payload) if isinstance(payload, dict) else {}
        self.profile = AccountProfile.from_raw(data)
        if not self.seller_id:
            self.seller_id = self.profile.seller_id
        self._authorized = True
        logger.info("Авторизация успешна: %s (id=%s)", self.profile.username, self.profile.seller_id)
        return self.profile

    @property
    def is_authorized(self) -> bool:
        return self._authorized

    def get_chats(self) -> List[Chat]:
        """Возвращает список активных диалогов."""
        payload = self._request("GET", self.EP_CHATS)
        return [Chat.from_raw(item) for item in self._unwrap_list(payload, "chats", "items")]

    def get_chat_messages(self, chat_id: str, limit: int = 30) -> List[Message]:
        """Возвращает сообщения конкретного диалога (от старых к новым)."""
        endpoint = self.EP_CHAT_MESSAGES.format(chat_id=chat_id)
        payload = self._request("GET", endpoint, params={"limit": limit})
        messages = [
            Message.from_raw(chat_id, item)
            for item in self._unwrap_list(payload, "messages", "items")
        ]
        return messages

    def send_message(self, chat_id: str, text: str) -> Message:
        """Отправляет сообщение покупателю."""
        endpoint = self.EP_SEND_MESSAGE.format(chat_id=chat_id)
        payload = self._request("POST", endpoint, json={"text": text})
        data = payload.get("data", payload) if isinstance(payload, dict) else {}
        logger.debug("Отправлено сообщение в чат %s", chat_id)
        return Message.from_raw(chat_id, data or {"text": text, "author": "seller"})

    def get_orders(self, status: Optional[str] = None) -> List[Order]:
        """Возвращает список заказов, опционально фильтруя по статусу."""
        params = {"status": status} if status else None
        payload = self._request("GET", self.EP_ORDERS, params=params)
        return [Order.from_raw(item) for item in self._unwrap_list(payload, "orders", "items")]

    def get_order(self, order_id: str) -> Order:
        """Возвращает один заказ по идентификатору."""
        endpoint = self.EP_ORDER.format(order_id=order_id)
        payload = self._request("GET", endpoint)
        data = payload.get("data", payload) if isinstance(payload, dict) else {}
        return Order.from_raw(data)

    def get_lots(self) -> List[LotShortcut]:
        """Возвращает список лотов продавца."""
        payload = self._request("GET", self.EP_LOTS)
        return [LotShortcut.from_raw(item) for item in self._unwrap_list(payload, "lots", "items")]
