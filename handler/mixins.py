import logging
from pathlib import Path
import xml.etree.ElementTree as ET

from handler.exceptions import (
    DirectoryCreationError,
    EmptyFeedsListError,
    GetTreeError
)
from handler.logging_config import setup_logging

setup_logging()


class FileMixin:
    """
    Миксин для работы с файловой системой и XML.
    Содержиит универсальные методы:
    - _get_filenames_list - Получение имен для XML-файлов списком.
    - _make_dir - Создает директорию и возвращает путь до нее.
    - _get_tree - Получает дерево XML-файла.
    """

    def _get_filenames_list(self, folder_name: str) -> list[str]:
        """Защищенный метод, возвращает список названий фидов."""
        folder_path = Path(__file__).parent.parent / folder_name
        if not folder_path.exists():
            logging.error(f'Папка {folder_name} не существует')
            raise DirectoryCreationError(f'Папка {folder_name} не найдена')
        feeds_name = [
            feed.name for feed in folder_path.glob('*.xml') if feed.is_file()
        ]
        if not feeds_name:
            logging.error('В папке нет xml-файлов')
            raise EmptyFeedsListError('Нет скачанных xml-файлов')
        logging.debug(f'Найдены файлы: {feeds_name}')
        return feeds_name

    def _make_dir(self, folder_name: Path) -> Path:
        """Защищенный метод, создает директорию."""
        try:
            file_path = Path(__file__).parent.parent / folder_name
            logging.debug(f'Путь к файлу: {file_path}')
            file_path.mkdir(parents=True, exist_ok=True)
            return file_path
        except Exception as e:
            logging.error(f'Не удалось создать директорию по причине {e}')
            raise DirectoryCreationError('Ошибка создания директории.')

    def _get_tree(self, file_name: str, folder_name: Path) -> ET.ElementTree:
        """Защищенный метод, создает экземпляр класса ElementTree."""
        try:
            file_path = (
                Path(__file__).parent.parent / folder_name / file_name
            )
            logging.debug(f'Путь к файлу: {file_path}')
            return ET.parse(file_path)
        except Exception as e:
            logging.error(f'Не удалось получить дерево фида по причине {e}')
            raise GetTreeError('Ошибка получения дерева фида.')
