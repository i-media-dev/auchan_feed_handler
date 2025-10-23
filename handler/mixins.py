import logging
import xml.etree.ElementTree as ET
from pathlib import Path

from handler.exceptions import (DirectoryCreationError, EmptyFeedsListError,
                                GetTreeError)
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

    def _indent(self, elem, level=0) -> None:
        """Защищенный метод, расставляет правильные отступы в XML файлах."""
        i = '\n' + level * '  '
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + '  '
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent(child, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def _get_filenames_list(self, folder_name: str) -> list[str]:
        """Защищенный метод, возвращает список названий фидов."""
        folder_path = Path(__file__).parent.parent / folder_name
        if not folder_path.exists():
            logging.error(f'Папка {folder_name} не существует')
            raise DirectoryCreationError(f'Папка {folder_name} не найдена')
        files_names = [
            file.name for file in folder_path.iterdir() if file.is_file()
        ]
        if not files_names:
            logging.error('В папке нет файлов')
            raise EmptyFeedsListError('Нет скачанных файлов')
        logging.debug(f'Найдены файлы: {files_names}')
        return files_names

    def _make_dir(self, folder_name: str) -> Path:
        """Защищенный метод, создает директорию."""
        try:
            file_path = Path(__file__).parent.parent / folder_name
            logging.debug(f'Путь к файлу: {file_path}')
            file_path.mkdir(parents=True, exist_ok=True)
            return file_path
        except Exception as e:
            logging.error(f'Не удалось создать директорию по причине {e}')
            raise DirectoryCreationError('Ошибка создания директории.')

    def _get_tree(self, file_name: str, folder_name: str) -> ET.ElementTree:
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
