"""
GGSEL Cardinal — точка входа.

Отвечает за подготовку окружения (каталоги, логи), запуск мастера первичной
настройки при первом старте и передачу управления ядру :class:`core.GGSelCardinal`.

Философия: ``main`` ничего не знает о бизнес-логике. Его задача — собрать окружение и
корректно стартовать/остановить ядро.
"""
from __future__ import annotations

import logging
import logging.config
import os
import sys

from Utils import core_tools
from Utils import logger as logger_cfg

VERSION = "0.1.0"

LOGGER = logging.getLogger("GGSelCardinal")

# Каталоги, которые обязаны существовать до старта ядра.
REQUIRED_DIRECTORIES = (
    "configs",
    "logs",
    "plugins",
    "storage",
    "storage/cache",
    "storage/plugins",
    "storage/products",
)

MAIN_CONFIG_PATH = os.path.join("configs", "_main.cfg")


BANNER = r"""
   ____  ____ ____       _    ____               _ _             _
  / ___|/ ___/ ___|  ___| |  / ___|__ _ _ __ __| (_)_ __   __ _| |
 | |  _| |  _\___ \ / _ \ | | |   / _` | '__/ _` | | '_ \ / _` | |
 | |_| | |_| |___) |  __/ | | |__| (_| | | | (_| | | | | | (_| | |
  \____|\____|____/ \___|_|  \____\__,_|_|  \__,_|_|_| |_|\__,_|_|
"""


def bootstrap_directories() -> None:
    """Создаёт обязательные каталоги, если их ещё нет."""
    for directory in REQUIRED_DIRECTORIES:
        os.makedirs(directory, exist_ok=True)


def configure_logging() -> None:
    """Подключает конфигурацию логирования из :mod:`Utils.logger`."""
    logging.config.dictConfig(logger_cfg.LOGGING_CONFIG)


def main() -> None:
    if sys.version_info < (3, 10):
        raise SystemExit("GGSEL Cardinal requires Python 3.10 or newer.")

    bootstrap_directories()
    configure_logging()
    core_tools.set_console_title(f"GGSEL Cardinal v{VERSION}")
    print(core_tools.colorize(BANNER, "cyan"))
    print(core_tools.colorize(f"  GGSEL Cardinal v{VERSION} — ассистент продавца GGSEL\n", "yellow"))

    # Первый запуск: если конфига нет — запускаем мастер настройки.
    if not os.path.exists(MAIN_CONFIG_PATH):
        from first_setup import run_first_setup
        LOGGER.info("Основной конфиг не найден — запускаю мастер первичной настройки.")
        run_first_setup(MAIN_CONFIG_PATH)

    # Ленивая загрузка: тяжёлые модули импортируем после настройки логов.
    from core import GGSelCardinal

    instance = GGSelCardinal(version=VERSION)
    try:
        instance.init()
        instance.print_status()
        instance.run()
    except KeyboardInterrupt:
        LOGGER.warning("Получен сигнал остановки (Ctrl+C). Завершаю работу...")
        instance.shutdown()
    except Exception:
        LOGGER.critical("Необработанное исключение в главном потоке.", exc_info=True)
        raise


if __name__ == "__main__":
    main()
