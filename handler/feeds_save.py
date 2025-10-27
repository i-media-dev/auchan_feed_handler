import logging
import re
import xml.etree.ElementTree as ET

import requests
from dotenv import load_dotenv

from handler.constants import FEEDS_FOLDER
from handler.decorators import retry_on_network_error, time_of_function
from handler.exceptions import (EmptyFeedsListError, EmptyXMLError,
                                InvalidXMLError)
from handler.feeds import FEEDS
from handler.logging_config import setup_logging
from handler.mixins import FileMixin

setup_logging()


class XMLSaver(FileMixin):
    """
    Класс, предоставляющий интерфейс для скачивания,
    валидации и сохранения фида в xml-файл.
    """
    load_dotenv()

    def __init__(
        self,
        feeds_list: tuple[str, ...] = FEEDS,
        feeds_folder: str = FEEDS_FOLDER
    ) -> None:
        if not feeds_list:
            logging.error('Не передан список фидов.')
            raise EmptyFeedsListError('Список фидов пуст.')

        self.feeds_list = feeds_list
        self.feeds_folder = feeds_folder

    @retry_on_network_error(max_attempts=3, delays=(2, 5, 10))
    def _get_file(self, feed: str):
        """Защищенный метод, получает фид по ссылке."""
        try:
            response = requests.get(feed, stream=True, timeout=(10, 60))

            if response.status_code == requests.codes.ok:
                return response
            else:
                logging.error(
                    'HTTP ошибка %s при загрузке %s',
                    response.status_code,
                    feed
                )
                return None

        except requests.RequestException as error:
            logging.error('Ошибка при загрузке %s: %s', feed, error)
            return None

    def _get_filename(self, feed: str) -> str:
        """Защищенный метод, формирующий имя xml-файлу."""
        return feed.split('/')[-1]

    def _validate_xml(self, xml_content: bytes):
        """
        Валидирует XML.
        Возвращает декодированное содержимое и кодировку.
        """
        if not xml_content.strip():
            raise EmptyXMLError('XML пуст')
        encoding = 'utf-8'
        try:
            declaration = xml_content[:100].decode('ascii', errors='ignore')
            if 'encoding=' in declaration:
                match = re.search(r'encoding=[\'"]([^\'"]+)[\'"]', declaration)
                if match:
                    encoding = match.group(1).lower()
        except Exception as error:
            logging.warning(
                'Не удалось определить кодировку из декларации: %s',
                error
            )
        try:
            decoded_content = xml_content.decode(encoding)
        except UnicodeDecodeError:
            try:
                decoded_content = xml_content.decode('utf-8')
                encoding = 'utf-8'
            except UnicodeDecodeError:
                raise InvalidXMLError('Не удалось декодировать XML')
        try:
            ET.fromstring(decoded_content)
        except ET.ParseError as error:
            raise InvalidXMLError(
                'XML содержит синтаксические ошибки: %s',
                error
            )
        return decoded_content, encoding

    @time_of_function
    def save_xml(self) -> None:
        """Метод, сохраняющий фиды в xml-файлы"""
        total_files: int = len(self.feeds_list)
        saved_files = 0
        folder_path = self._make_dir(self.feeds_folder)
        for feed in self.feeds_list:
            file_name = self._get_filename(feed)
            file_path = folder_path / file_name
            response = self._get_file(feed)
            if response is None:
                logging.warning('XML-файл %s не получен.', file_name)
                continue
            try:
                xml_content = response.content
                decoded_content, encoding = self._validate_xml(xml_content)
                xml_tree = ET.fromstring(decoded_content)
                self._indent(xml_tree)
                tree = ET.ElementTree(xml_tree)
                with open(file_path, 'wb') as file:
                    tree.write(file, encoding=encoding, xml_declaration=True)
                saved_files += 1
                logging.info('Файл %s успешно сохранен', file_name)
            except (EmptyXMLError, InvalidXMLError) as error:
                logging.error('Ошибка валидации XML %s: %s', file_name, error)
                continue
            except Exception as error:
                logging.error(
                    'Ошибка обработки файла %s: %s',
                    file_name,
                    error
                )
                raise
        logging.info(
            'Успешно записано %s файлов из %s.',
            saved_files,
            total_files
        )
