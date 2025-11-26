import logging
import os
from datetime import datetime as dt
from logging.handlers import RotatingFileHandler

INFO_BOT = 25

logging.addLevelName(INFO_BOT, 'INFO_BOT')


class CustomLogger(logging.Logger):
    def bot_event(self, message, *args, **kws):
        if self.isEnabledFor(INFO_BOT):
            self._log(INFO_BOT, message, args, **kws, stacklevel=2)


logging.setLoggerClass(CustomLogger)


def setup_logging():
    """
    Настройка логирования приложения.

    Создает директорию для логов (если не существует) и настраивает:
    - Ротацию логов (макс. 50MB на файл, хранит до 3 бэкапов).
    - UTF-8 кодировку логов.
    - Формат записей: время, имя файла, функция, уровень,
    сообщение, имя логгера.
    - Кастомный уровень логирования INFO_BOT (помечать им сообщения,
    которые хотим видеть в деталях сообщений по отработке скриптов)
    - Уровень логирования: INFO.

    Логи сохраняются в папку 'logs' с именем файла в формате ГГГГ-ММ-ДД.log.
    Автоматически создает папку логов, если она не существует.
    """
    date_dir = dt.now().strftime('%Y-%m-%d')
    log_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'logs', date_dir)
    )
    os.makedirs(log_dir, exist_ok=True)
    log_id = dt.now().strftime('%Y%m%d%H%M')
    log_filename = f'{log_id}.log'
    log_filepath = os.path.join(log_dir, log_filename)

    handler = RotatingFileHandler(
        log_filepath,
        maxBytes=50000000,
        backupCount=3,
        encoding='utf-8'
    )

    handler.setLevel(logging.INFO)

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
