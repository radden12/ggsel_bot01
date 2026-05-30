"""
GGSelCardinal — точка входа.

Отвечает за подготовку окружения (каталоги, конфиги, логирование), запуск мастера
первичной настройки при первом старте и передачу управления ядру :class:`core.GGSelCardinal`.

Философия: ``main`` ничего не знает о бизнес-логике. Его задача — собрать окружение и
корректно стартовать/остановить ядро.
"""
from __future__ import annotations

import os
import sys
import logging
import logging.config

from Utils import logger as logger_cfg
from Utils import core_tools

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
   ____  ____           _  ____              _ _             _
  / ___|/ ___| ___  ___| |/ ___|__ _ _ __ __| (_)_ __   __ _| |
 | |  _| |  _ / __|/ _ \ | |   / _` | '__/ _` | | '_ \ / _` | |
 | |_| | |_| |\__ \  __/ | |__| (_| | | | (_| | | | | | (_| | |
  \____|\____||___/\___|_|\____\__,_|_|  \__,_|_|_| |_|\__,_|_|
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
        raise SystemExit("GGSelCardinal requires Python 3.10 or newer.")

    bootstrap_directories()
    configure_logging()
    core_tools.set_console_title(f"GGSelCardinal v{VERSION}")
    print(core_tools.colorize(BANNER, "cyan"))
    print(core_tools.colorize(f"  GGSelCardinal v{VERSION}\n", "yellow"))

    # Ленивая загрузка: импортируем тяжёлые модули только после настройки логов.
    if not os.path.exists(MAIN_CONFIG_PATH):
        from first_setup import run_first_setup
        LOGGER.info("Основной конфиг не найден — запускаю мастер первичной настройки.")
        run_first_setup(MAIN_CONFIG_PATH)

    from core import GGSelCardinal

    instance = GGSelCardinal(version=VERSION)
    try:
        instance.init()
        instance.run()
    except KeyboardInterrupt:
        LOGGER.warning("Получен сигнал остановки (Ctrl+C). Завершаю работу...")
        instance.shutdown()
    except Exception:
        LOGGER.critical("Необработанное исключение в главном потоке.", exc_info=True)
        raise


if __name__ == "__main__":
    main()
