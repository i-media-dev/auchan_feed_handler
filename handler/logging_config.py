import logging
import os
from datetime import datetime as dt
from logging.handlers import RotatingFileHandler


def setup_logging():
    """
    Настройка логирования приложения.

    Создает директорию для логов (если не существует) и настраивает:
    - Ротацию логов (макс. 50MB на файл, хранит до 3 бэкапов).
    - UTF-8 кодировку логов.
    - Формат записей: время, имя файла, функция, уровень,
    сообщение, имя логгера.
    - Уровень логирования: INFO.

    Логи сохраняются в папку 'logs' с именем файла в формате ГГГГ-ММ-ДД.log.
    Автоматически создает папку логов, если она не существует.
    """
    log_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'logs')
    )
    os.makedirs(log_dir, exist_ok=True)

    log_filename = dt.now().strftime('%Y-%m-%d.log')
    log_filepath = os.path.join(log_dir, log_filename)

    handler = RotatingFileHandler(
        log_filepath,
        maxBytes=50000000,
        backupCount=3,
        encoding='utf-8'
    )

    logging.basicConfig(
        level=logging.INFO,
        format=(
            '%(asctime)s, '
            '%(filename)s, '
            '%(funcName)s, '
            '%(levelname)s, '
            '%(message)s, '
            '%(name)s'
        ),
        handlers=[handler]
    )
