"""
Мастер первичной настройки.

Запускается при отсутствии ``configs/_main.cfg``: в интерактивном режиме
спрашивает ключ GGSEL и настройки Telegram, затем сохраняет конфиг
и создаёт рабочие файлы автоответчика и автовыдачи на основе примеров.
"""
from __future__ import annotations

import os
import shutil


_MAIN_TEMPLATE = """\
; Основной конфиг GGSelCardinal.
[GGSel]
; Ключ API продавца GGSEL.
token = {token}
; Идентификатор продавца (необязательно, определится автоматически).
seller_id = {seller_id}

[Telegram]
; Включить Telegram-панель управления.
enabled = {tg_enabled}
token = {tg_token}
; Список ID админов через запятую.
admins = {tg_admins}

[Other]
language = {language}
poll_interval = 4
autoresponse = on
autodelivery = on
"""


def _ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def _ask_yes_no(prompt: str, default: bool = False) -> bool:
    default_label = "y" if default else "n"
    value = input(f"{prompt} (y/n) [{default_label}]: ").strip().lower()
    if not value:
        return default
    return value in ("y", "yes", "д", "да")


def _seed_example(config_dir: str, name: str) -> None:
    """Копирует ``<name>.example`` в рабочий ``<name>``, если его ещё нет."""
    target = os.path.join(config_dir, name)
    example = os.path.join(config_dir, f"{name}.example")
    if not os.path.exists(target) and os.path.exists(example):
        shutil.copyfile(example, target)


def run_first_setup(main_config_path: str) -> None:
    """Проводит интерактивную настройку и создаёт конфиги."""
    config_dir = os.path.dirname(main_config_path) or "configs"
    os.makedirs(config_dir, exist_ok=True)

    print("\n=== Первичная настройка GGSelCardinal ===\n")
    token = ""
    while not token:
        token = _ask("Введите API-ключ GGSEL")
        if not token:
            print("  Ключ обязателен.")

    seller_id = _ask("ID продавца (можно пропустить)")
    language = _ask("Язык интерфейса (ru/en)", "ru")

    tg_enabled = _ask_yes_no("Подключить Telegram-панель?", default=False)
    tg_token = ""
    tg_admins = ""
    if tg_enabled:
        tg_token = _ask("Токен Telegram-бота")
        tg_admins = _ask("ID админов через запятую")

    content = _MAIN_TEMPLATE.format(
        token=token,
        seller_id=seller_id,
        tg_enabled="on" if tg_enabled else "off",
        tg_token=tg_token,
        tg_admins=tg_admins,
        language=language or "ru",
    )
    with open(main_config_path, "w", encoding="utf-8") as fh:
        fh.write(content)

    _seed_example(config_dir, "auto_response.cfg")
    _seed_example(config_dir, "auto_delivery.cfg")

    print(f"\nКонфиг сохранён: {main_config_path}")
    print("Настройка завершена. Запускаю ядро...\n")
