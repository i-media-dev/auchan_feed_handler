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

    def _save_xml(self, elem, file_folder, filename) -> None:
        """Защищенный метод, сохраняет отформатированные файлы."""
        root = elem
        self._indent(root)
        formatted_xml = ET.tostring(root, encoding='windows-1251')
        file_path = self._make_dir(file_folder)
        with open(
            file_path / filename,
            'wb'
        ) as f:
            f.write(formatted_xml)

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

    def _get_files_list(self, folder_name: str) -> list[str]:
        """Защищенный метод, возвращает список названий фидов."""
        folder_path = Path(__file__).parent.parent / folder_name
        if not folder_path.exists():
            logging.error(f'Папка {folder_name} не существует')
            raise DirectoryCreationError(f'Папка {folder_name} не найдена')
        filenames = [
            file.name for file in folder_path.iterdir() if file.is_file()
        ]
        if not filenames:
            logging.error('В папке нет файлов')
            raise EmptyFeedsListError('Нет скачанных файлов')
        logging.debug('Найдены файлы: %s', filenames)
        return filenames

    def _get_files_dict(self, folder_name: str) -> dict:
        """
        Защищенный метод, возвращает словарь
        '{offer_id}: {filename}' названий файлов в переданной директории.
        """
        folder_path = Path(__file__).parent.parent / folder_name
        if not folder_path.exists():
            logging.error(f'Папка {folder_name} не существует')
            raise DirectoryCreationError(f'Папка {folder_name} не найдена')
        files_dict = {
            file.name.split('.')[0]: file.name for file
            in folder_path.iterdir() if file.is_file()
        }
        if not files_dict:
            logging.error('В папке нет файлов')
            raise EmptyFeedsListError('Нет скачанных файлов')
        logging.debug(f'Найдены файлы: {files_dict}')
        return files_dict

    def _build_set(self, folder: str, target_set: set):
        """Защищенный метод, строит множество всех существующих офферов."""
        try:
            filenames_list = self._get_files_list(folder)
            for file_name in filenames_list:
                offer_image = file_name.split('.')[0]
                if offer_image:
                    target_set.add(offer_image)

            logging.info(
                'Построен кэш для %s файлов',
                len(target_set)
            )
        except EmptyFeedsListError:
            raise
        except DirectoryCreationError:
            raise
        except Exception as error:
            logging.error(
                'Неожиданная ошибка при сборе множества '
                'скачанных изображений: %s',
                error
            )
            raise

    def _make_dir(self, folder_name: str) -> Path:
        """Защищенный метод, создает директорию."""
        try:
            file_path = Path(__file__).parent.parent / folder_name
            logging.debug('Путь к файлу: %s', file_path)
            file_path.mkdir(parents=True, exist_ok=True)
            return file_path
        except Exception as error:
            logging.error('Не удалось создать директорию по причине %s', error)
            raise DirectoryCreationError('Ошибка создания директории.')

    def _get_root(self, file_name: str, folder_name: str) -> ET.Element:
        """Защищенный метод, создает экземпляр класса Element."""
        try:
            file_path = (
                Path(__file__).parent.parent / folder_name / file_name
            )
            logging.debug(f'Путь к файлу: {file_path}')
            tree = ET.parse(file_path)
            return tree.getroot()
        except Exception as error:
            logging.error(
                'Не удалось получить дерево фида по причине %s',
                error
            )
            raise GetTreeError('Ошибка получения дерева фида.')
