import functools
import logging
import time
from datetime import datetime as dt
from http.client import IncompleteRead

import requests

import mysql.connector
from handler.db_config import config
from handler.exceptions import (
    DirectoryCreationError,
    EmptyFeedsListError,
    GetTreeError,
    StructureXMLError
)
from handler.logging_config import setup_logging

setup_logging()


def time_of_script(func):
    """Декортаор для измерения времени работы всего приложения."""
    @functools.wraps(func)
    def wrapper():
        date_str = dt.now().strftime('%Y-%m-%d')
        time_str = dt.now().strftime('%H:%M:%S')
        run_id = str(int(time.time()))
        print(f'Функция main начала работу {date_str} в {time_str}')
        start_time = time.time()
        try:
            result = func()
            execution_time = round(time.time() - start_time, 3)
            print(
                'Функция main завершила '
                f'работу в {dt.now().strftime("%H:%M:%S")}.'
                f' Время выполнения - {execution_time} сек. '
                f'или {round(execution_time / 60, 2)} мин.'
            )
            logging.info('SCRIPT_FINISHED_STATUS=SUCCESS')
            logging.info(f'DATE={date_str}')
            logging.info(f'EXECUTION_TIME={execution_time} сек')
            logging.info(f'FUNCTION_NAME={func.__name__}')
            logging.info(f'RUN_ID={run_id}')
            logging.info('ENDLOGGING=1')
            return result
        except Exception as e:
            execution_time = round(time.time() - start_time, 3)
            print(
                'Функция main завершилась '
                f'с ошибкой в {dt.now().strftime("%H:%M:%S")}. '
                f'Время выполнения - {execution_time} сек. '
                f'Ошибка: {e}'
            )
            logging.info('SCRIPT_FINISHED_STATUS=ERROR')
            logging.info(f'DATE={date_str}')
            logging.info(f'EXECUTION_TIME={execution_time} сек')
            logging.info(f'ERROR_TYPE={type(e).__name__}')
            logging.info(f'ERROR_MESSAGE={str(e)}')
            logging.info(f'FUNCTION_NAME={func.__name__}')
            logging.info(f'RUN_ID={run_id}')
            logging.info('ENDLOGGING=1')
            raise
    return wrapper


def time_of_function(func):
    """
    Декоратор для измерения времени выполнения функции.

    Замеряет время выполнения декорируемой функции и логирует результат
    в секундах и минутах. Время округляется до 3 знаков после запятой
    для секунд и до 2 знаков для минут.

    Args:
        func (callable): Декорируемая функция, время выполнения которой
        нужно измерить.

    Returns:
        callable: Обёрнутая функция с добавленной функциональностью
        замера времени.
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = round(time.time() - start_time, 3)
        logging.info(
            f'Функция {func.__name__} завершила работу. '
            f'Время выполнения - {execution_time} сек. '
            f'или {round(execution_time / 60, 2)} мин.'
        )
        return result
    return wrapper


def connection_db(func):
    """
    Декоратор для подключения к базе данных.

    Подключается к базе данных, обрабатывает ошибки в процессе подключения,
    логирует все успешные/неуспешные действия, вызывает функцию, выполняющую
    действия в базе данных и закрывает подключение.

    Args:
        func (callable): Декорируемая функция, которая выполняет
        действия с базой данных.

    Returns:
        callable: Обёрнутая функция с добавленной функциональностью
        подключения к базе данных и логирования.
    """
    def wrapper(*args, **kwargs):
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        try:
            kwargs['cursor'] = cursor
            result = func(*args, **kwargs)
            connection.commit()
            return result
        except Exception as e:
            connection.rollback()
            logging.error(f'Ошибка в {func.__name__}: {str(e)}', exc_info=True)
            raise
        finally:
            cursor.close()
            connection.close()
    return wrapper


def retry_on_network_error(max_attempts=3, delays=(2, 5, 10)):
    """Декоратор для повторных попыток скачивания при сетевых ошибках."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            last_exception = None

            while attempt < max_attempts:
                attempt += 1
                try:
                    return func(*args, **kwargs)
                except (
                    IncompleteRead,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.ChunkedEncodingError,
                    requests.exceptions.ReadTimeout
                ) as e:
                    last_exception = e
                    if attempt < max_attempts:
                        delay = delays[attempt - 1] if attempt - \
                            1 < len(delays) else delays[-1]
                        logging.warning(
                            f'Попытка {attempt}/{max_attempts} неудачна, '
                            f'повтор через {delay}сек: {e}')
                        time.sleep(delay)
                    else:
                        logging.error(f'Все {max_attempts} попыток неудачны')
                        raise last_exception
            return None
        return wrapper
    return decorator


def try_except(func):
    """Декоратор для обработки исключений."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except StructureXMLError:
            logging.warning(
                'Тег пуст или структура фида не соответствует ожидаемой.')
            if func.__annotations__.get('return') == bool:
                return False
            raise
        except (EmptyFeedsListError, GetTreeError, DirectoryCreationError):
            logging.error(f'Критическая ошибка в методе {func.__name__}')
            raise
        except Exception as e:
            logging.error(f'Возникла ошибка в методе {func.__name__}: {e}')
            if func.__annotations__.get('return') == bool:
                return False
            raise
    return wrapper
