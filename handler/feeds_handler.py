import logging
import xml.etree.ElementTree as ET

from handler.constants import (ADDRESS_FTP_IMAGES, FEEDS_FOLDER,
                               NEW_FEEDS_FOLDER, NEW_IMAGE_FOLDER)
from handler.decorators import time_of_function, try_except
from handler.feeds import FEEDS
from handler.logging_config import setup_logging
from handler.mixins import FileMixin

setup_logging()

logger = logging.getLogger(__name__)


class FeedHandler(FileMixin):
    """
    Класс, предоставляющий интерфейс
    для обработки xml-файлов.
    """

    def __init__(
        self,
        filename: str,
        feeds_folder: str = FEEDS_FOLDER,
        new_feeds_folder: str = NEW_FEEDS_FOLDER,
        new_image_folder: str = NEW_IMAGE_FOLDER,
        feeds_list: tuple[str, ...] = FEEDS
    ) -> None:
        self.filename = filename
        self.feeds_folder = feeds_folder
        self.new_feeds_folder = new_feeds_folder
        self.feeds_list = feeds_list
        self.new_image_folder = new_image_folder
        self._root = None
        self._is_modified = False

    @property
    def root(self):
        """Ленивая загрузка корневого элемента."""
        if self._root is None:
            self._root = self._get_root(self.filename, self.feeds_folder)
        return self._root

    @try_except
    def change_available(self, offers_id_list: list, flag: str):
        offers = self.root.findall('.//offer')

        if not offers:
            logging.error('В файле %s не найдено offers', self.filename)
            raise

        for offer in offers:
            offer_id = offer.get('id')
            if offer_id in offers_id_list:
                offer.set('available', flag)
                self._is_modified = True
        return self

    @time_of_function
    @try_except
    def add_custom_label(
        self,
        custom_label: dict[str, dict],
    ):
        """
        Метод, подставляющий в фиды данные
        из настраиваемого словаря CUSTOM_LABEL.
        """
        offers = self.root.findall('.//offer')

        if not offers:
            logging.error('В файле %s не найдено offers', self.filename)
            raise

        for offer in offers:
            offer_name_text = offer.findtext('name')
            offer_url_text = offer.findtext('url')
            offer_id = offer.get('id')
            if None in (
                offer_name_text,
                offer_url_text,
                offer_id
            ):
                continue
            existing_nums = set()
            for element in offer.findall('*'):
                if element.tag.startswith('custom_label_'):
                    try:
                        existing_nums.add(
                            int(element.tag.split('_')[-1]))
                    except ValueError:
                        continue
            for label_name, conditions in custom_label.items():
                name_match = any(
                    sub.lower() in offer_name_text.lower()
                    for sub in conditions.get('name', [])
                )
                url_match = any(
                    sub.lower() in offer_url_text.lower()
                    for sub in conditions.get('url', [])
                )
                id_match = offer_id in conditions.get('id', [])
                if name_match or url_match or id_match:
                    next_num = 0
                    while next_num in existing_nums:
                        next_num += 1
                    existing_nums.add(next_num)
                    ET.SubElement(
                        offer, f'custom_label_{next_num}'
                    ).text = label_name
                    self._is_modified = True
        return self

    @time_of_function
    def replace_images(self):
        """Метод, подставляющий в фиды новые изображения."""
        deleted_images = 0
        input_images = 0
        input_images_promo = 0
        try:
            image_dict = self._get_files_dict(self.new_image_folder)

            offers = list(self.root.findall('.//offer'))
            for offer in offers:
                offer_id = offer.get('id')
                oldprice_tag = offer.find('oldprice')

                if not offer_id:
                    continue

                pictures = offer.findall('picture')
                if oldprice_tag is not None:
                    if offer_id in image_dict:
                        pictures = offer.findall('picture')
                        for picture in pictures:
                            offer.remove(picture)
                        deleted_images += len(pictures)
                        picture_tag = ET.SubElement(offer, 'picture')
                        picture_tag.text = (
                            f'{ADDRESS_FTP_IMAGES}/{image_dict[offer_id]}'
                        )
                        input_images += 1
                        self._is_modified = True
                else:
                    image_key = f'{offer_id}_promo'
                    if image_key in image_dict:
                        picture_tag = ET.SubElement(offer, 'picture')
                        picture_tag.text = (
                            f'{ADDRESS_FTP_IMAGES}/{image_dict[image_key]}'
                        )
                        input_images_promo += 1
                        self._is_modified = True

            logger.bot_event(
                'Количество удаленных изображений - %s',
                deleted_images
            )
            logger.bot_event(
                'Количество добавленных изображений без промо - %s',
                input_images
            )
            logger.bot_event(
                'Количество добавленных изображений с промо - %s',
                input_images_promo
            )
            return self

        except Exception as error:
            logging.error('Ошибка в image_replacement: %s', error)
            raise

    def delete_offers(self, offers_ids: list[str]):
        removed = 0
        try:
            offers = list(self.root.findall('.//offer'))
            parent = self.root.find('.//offers') or self.root
            for offer in offers[:]:
                offer_id = str(offer.get('id'))
                if offer_id in offers_ids:
                    parent.remove(offer)
                    removed += 1
                    self._is_modified = True
            logging.info(
                'Удалено офферов с неподходящим id: %s (%s)',
                removed,
                self.filename
            )
            return self
        except Exception as error:
            logging.error(
                'Неизвестная ошибка при удалении оффера: %s',
                error
            )
            raise

    def save(self):
        """Метод сохраняет файл, если были изменения."""
        try:
            if not self._is_modified:
                self._save_xml(self.root, self.new_feeds_folder, self.filename)
                logger.info('Файл обновлен без изменений')
                return self

            self._save_xml(self.root, self.new_feeds_folder, self.filename)
            logger.info('Файл %s сохранён', self.filename)

            self._is_modified = False
            return self
        except Exception as error:
            logging.error(
                'Неожиданная ошибка при сохранении файла %s: %s',
                self.filename,
                error
            )
            raise
