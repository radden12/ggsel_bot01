# Плагины GGSelCardinal

Плагин — это обычный Python-файл (`*.py`) в каталоге `plugins/`. При старте ядро
сканирует каталог, импортирует каждый файл и подписывает объявленные в нём функции
на события.

> Файлы, имя которых начинается с `_` (например, `_template.py`), **игнорируются**.
> Удобно для шаблонов и временно отключённых плагинов.

## Метаданные

В начале файла можно объявить метаданные плагина (все необязательны, но желательны):

| Переменная      | Назначение                                  |
|-----------------|---------------------------------------------|
| `NAME`          | Человекочитаемое имя плагина                 |
| `VERSION`       | Версия                                       |
| `DESCRIPTION`   | Краткое описание                             |
| `CREDITS`       | Автор (например, `@username`)                |
| `UUID`          | Уникальный идентификатор (используется панелью)|
| `SETTINGS_PAGE` | Зарезервировано на будущее                   |

## Точки привязки (`BIND_TO_*`)

Каждая переменная — это функция или список функций с сигнатурой `(core, event)`.

| Переменная                     | Когда вызывается                                   | `event`                     |
|--------------------------------|----------------------------------------------------|-----------------------------|
| `BIND_TO_PRE_INIT`             | до инициализации компонентов ядра                  | `None`                      |
| `BIND_TO_POST_INIT`            | после инициализации (account/runner/telegram готовы)| `None`                      |
| `BIND_TO_NEW_MESSAGE`          | новое сообщение от покупателя                       | `NewMessageEvent`           |
| `BIND_TO_NEW_ORDER`            | появился новый заказ                                | `NewOrderEvent`             |
| `BIND_TO_ORDER_STATUS_CHANGED` | статус заказа изменился                             | `OrderStatusChangedEvent`   |
| `BIND_TO_DELETE`               | плагин выгружается                                  | `None`                      |

Через `core` доступны: `core.account` (клиент GGSEL), `core.config` (настройки),
`core.auto_response` / `core.auto_delivery` (правила), `core.send_telegram(text)`
(уведомление админам) и `core._(key, *args)` (локализация).

## Минимальный пример

```python
NAME = "My Plugin"
VERSION = "1.0.0"
DESCRIPTION = "Что делает плагин"
CREDITS = "@username"
UUID = "00000000-0000-0000-0000-000000000000"
SETTINGS_PAGE = False


def handle_new_message(core, event):
    if event.message.text.strip().lower() == "ping":
        core.account.send_message(event.chat.id, "pong")


BIND_TO_NEW_MESSAGE = [handle_new_message]
BIND_TO_DELETE = None
```

Готовые примеры в этом каталоге:

- `example_clock.py` — отвечает покупателю временем сервера на команды `!время` / `!time`;
- `_template.py` — заготовка со всеми точками привязки (отключена, т.к. начинается с `_`).
