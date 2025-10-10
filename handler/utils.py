from handler.feeds_handler import XMLHandler
from handler.feeds_save import XMLSaver
from handler.image_handler import XMLImage
from handler.reports_db import XMLDataBase


def initialize_components() -> tuple:
    """
    Инициализирует и возвращает все необходимые
    компоненты для работы приложения.

    Выполняет следующие действия:
    1. Создает объект класса XMLSaver.
    2. Создает объект класса XMLHandler.
    3. Создает объект класса XMLDataBase.
    4 Создает объект класса XMLImage

    Returns:
        tuple: Кортеж с инициализированными компонентами.
    """
    saver = XMLSaver()
    handler = XMLHandler()
    db_client = XMLDataBase()
    image = XMLImage()
    return saver, handler, db_client, image


def save_to_database(
    db_client: XMLDataBase,
    data: list
) -> None:
    """
    Сохраняет данные в базу данных.
    Args:
        - db_client (XMLDataBase): Клиент для работы с базой данных.
        - data: Данные для сохранения
    """
    queries = [
        db_client.insert_reports(data),
        db_client.insert_catalog(data)
    ]
    for query in queries:
        db_client.save_to_database(query)
