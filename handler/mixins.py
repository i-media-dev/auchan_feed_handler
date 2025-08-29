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

    def _get_filenames_list(self, feeds_list: str) -> list[str]:
        """Защищенный метод, возвращает список названий фидов."""
        feed_names = [feed.split('/')[-1] for feed in feeds_list]
        if len(feed_names) < len(feeds_list):
            logging.error('Список имен пуст или не полон.')
            raise EmptyFeedsListError('Список имен пуст или не полон.')
        return feed_names

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
