import logging
import os
import re

from dotenv import load_dotenv

import requests
import xml.etree.ElementTree as ET
from handler.constants import FEEDS_FOLDER
from handler.decorators import time_of_function, retry_on_network_error
from handler.exceptions import (
    EmptyFeedsListError,
    EmptyXMLError,
    InvalidXMLError
)
from handler.feeds import FEEDS
from handler.mixins import FileMixin
from handler.logging_config import setup_logging

setup_logging()


class XMLSaver(FileMixin):
    """
    Класс, предоставляющий интерфейс для скачивания,
    валидации и сохранения фида в xml-файл.
    """
    load_dotenv()

    def __init__(
        self,
        feeds_list: list[str] = FEEDS,
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
                response.content
                return response

            if response.status_code == requests.codes.unauthorized:
                username = os.getenv('XML_FEED_USERNAME')
                password = os.getenv('XML_FEED_PASSWORD')
                auth_response = requests.get(
                    feed,
                    auth=(username, password),
                    stream=True,
                    timeout=(10, 60)
                )

                if auth_response.status_code == requests.codes.ok:
                    auth_response.content
                    return auth_response
                else:
                    logging.error(
                        f'Ошибка авторизации: {auth_response.status_code}')
                    return None
        except requests.RequestException as e:
            logging.error(f'Ошибка при загрузке {feed}: {e}')
            return None

    def _get_filename(self, feed: str) -> str:
        """Защищенный метод, формирующий имя xml-файлу."""
        return feed.split('/')[-1]

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
        except Exception as e:
            logging.warning(
                f'Не удалось определить кодировку из декларации: {e}')
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
        except ET.ParseError as e:
            raise InvalidXMLError(f'XML содержит синтаксические ошибки: {e}')
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
                logging.warning(f'XML-файл {file_name} не получен.')
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
                logging.info(f'Файл {file_name} успешно сохранен')
            except (EmptyXMLError, InvalidXMLError) as e:
                logging.error(f'Ошибка валидации XML {file_name}: {e}')
                continue
            except Exception as e:
                logging.error(f'Ошибка обработки файла {file_name}: {e}')
                continue
        logging.info(
            f'Успешно записано {saved_files} файлов из {total_files}.')
