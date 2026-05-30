"""
GGSelAPI — самостоятельный клиент торговой площадки GGSEL.

Слой инкапсулирует HTTP-взаимодействие с площадкой и предоставляет ядру удобные
типизированные методы и модели. Ядро не должно работать с ``requests`` напрямую.
"""
from GGSelAPI.account import Account
from GGSelAPI import types
from GGSelAPI.common import enums, exceptions

__all__ = ["Account", "types", "enums", "exceptions"]
