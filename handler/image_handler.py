import logging
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

from handler.constants import (DEFAULT_IMAGE_SIZE, FEEDS_FOLDER, FRAME_FOLDER,
                               IMAGE_FOLDER, NAME_OF_FRAME,
                               NAME_OF_FRAME_PROMO, NEW_IMAGE_FOLDER,
                               NUMBER_PIXELS_IMAGE, RGB_COLOR_SETTINGS,
                               VERTICAL_OFFSET)
from handler.decorators import time_of_function
from handler.exceptions import DirectoryCreationError, EmptyFeedsListError
from handler.feeds import FEEDS
from handler.logging_config import setup_logging
from handler.mixins import FileMixin

setup_logging()


class XMLImage(FileMixin):
    """
    Класс, предоставляющий интерфейс
    для работы с изображениями.
    """

    def __init__(
        self,
        feeds_folder: str = FEEDS_FOLDER,
        frame_folder: str = FRAME_FOLDER,
        image_folder: str = IMAGE_FOLDER,
        new_image_folder: str = NEW_IMAGE_FOLDER,
        feeds_list: tuple[str, ...] = FEEDS,
        number_pixels_image: int = NUMBER_PIXELS_IMAGE
    ) -> None:
        self.frame_folder = frame_folder
        self.feeds_folder = feeds_folder
        self.image_folder = image_folder
        self.new_image_folder = new_image_folder
        self.feeds_list = feeds_list
        self.number_pixels_image = number_pixels_image
        self._existing_image_offers = set()
        self._existing_framed_offers = set()

    def _get_image_data(self, url: str) -> tuple:
        """
        Защищенный метод, загружает данные изображения
        и возвращает (image_data, image_format).
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            image_format = image.format.lower() if image.format else None
            return response.content, image_format
        except Exception as e:
            logging.error(f'Ошибка при загрузке изображения {url}: {e}')
            return None, None

    def _get_image_filename(
        self,
        offer_id: str,
        image_data: bytes,
        image_format: str
    ) -> str:
        """Защищенный метод, создает имя файла с изображением."""
        if not image_data or not image_format:
            return ''
        return f'{offer_id}.{image_format}'

    def _build_offers_set(self, folder: str, target_set: set):
        """Защищенный метод, строит множество всех существующих офферов."""
        try:
            for file_name in self._get_filenames_list(folder):
                offer_image = file_name.split('.')[0]
                if offer_image:
                    target_set.add(offer_image)

            logging.info(
                f'Построен кэш для {len(target_set)} файлов'
            )
        except EmptyFeedsListError:
            raise
        except DirectoryCreationError:
            raise
        except Exception as e:
            logging.error(
                'Неожиданная ошибка при сборе множества '
                f'скачанных изображений: {e}'
            )
            raise

    def _save_image(
        self,
        image_data: bytes,
        folder_path: Path,
        image_filename: str
    ):
        """Защищенный метод, сохраняет изображение по указанному пути."""
        try:
            with Image.open(BytesIO(image_data)) as img:
                file_path = folder_path / image_filename
                img.load()
                img.save(file_path)
        except Exception as e:
            logging.error(f'Ошибка при сохранении {image_filename}: {e}')

    @time_of_function
    def get_images(self):
        """Метод получения и сохранения изображений из xml-файла."""
        total_offers_processed = 0
        offers_with_images = 0
        images_downloaded = 0
        offers_skipped_existing = 0

        try:
            self._build_offers_set(
                self.image_folder,
                self._existing_image_offers
            )
        except (DirectoryCreationError, EmptyFeedsListError):
            logging.warning(
                'Директория с изображениями отсутствует. Первый запуск'
            )
        try:
            file_name_list = self._get_filenames_list(self.feeds_folder)
            for file_name in file_name_list:
                tree = self._get_tree(file_name, self.feeds_folder)
                root = tree.getroot()
                for offer in root.findall('.//offer'):
                    offer_id = offer.get('id')
                    total_offers_processed += 1

                    picture = offer.find('picture')
                    if picture is None:
                        continue

                    offer_image = picture.text
                    if not offer_image:
                        continue

                    offers_with_images += 1

                    if str(offer_id) in self._existing_image_offers:
                        offers_skipped_existing += 1
                        continue

                    image_data, image_format = self._get_image_data(
                        offer_image
                    )
                    image_filename = self._get_image_filename(
                        offer_id,
                        image_data,
                        image_format
                    )
                    folder_path = self._make_dir(self.image_folder)
                    self._save_image(
                        image_data,
                        folder_path,
                        image_filename
                    )
                    images_downloaded += 1
            logging.info(
                f'\n Всего обработано фидов - {len(file_name_list)}\n'
                f'Всего обработано офферов - {total_offers_processed}\n'
                'Всего офферов с подходящими '
                f'изображениями - {offers_with_images}\n'
                f'Всего изображений скачано {images_downloaded}\n'
                'Пропущено офферов с уже скачанными '
                f'изображениями - {offers_skipped_existing}'
            )
        except Exception as e:
            logging.error(f'Неожиданная ошибка при получении изображений: {e}')

    @time_of_function
    def _add_frame(
        self,
        name_of_frame: str,
        images_names_list: list,
        file_path: Path,
        frame_path: Path,
        new_file_path: Path
    ):
        """Метод форматирует изображения и добавляет рамку."""
        total_framed_images = 0
        total_failed_images = 0
        skipped_images = 0

        try:
            for image_name in images_names_list:
                base_name = image_name.split('.')[0]

                if 'promo' in name_of_frame:
                    result_name = f'{base_name}_promo'
                else:
                    result_name = base_name

                if result_name in self._existing_framed_offers:
                    skipped_images += 1
                    continue

                with Image.open(file_path / image_name) as image:
                    image.load()
                    image_width, image_height = image.size

                with Image.open(frame_path / name_of_frame) as frame:
                    frame_resized = frame.resize(DEFAULT_IMAGE_SIZE)

                final_image = Image.new(
                    'RGB',
                    DEFAULT_IMAGE_SIZE,
                    RGB_COLOR_SETTINGS
                )

                canvas_width, canvas_height = DEFAULT_IMAGE_SIZE
                x_position = (canvas_width - image_width) // 2
                y_position = (
                    canvas_height - image_height
                ) // 2 + VERTICAL_OFFSET

                if image_width > canvas_width or image_height > canvas_height:
                    ratio = min(
                        canvas_width / image_width,
                        canvas_height / image_height
                    )
                    new_width = int(image_width * ratio)
                    new_height = int(image_height * ratio)
                    image = image.resize((new_width, new_height))
                    x_position = (canvas_width - new_width) // 2
                    y_position = (
                        canvas_height - new_height
                    ) // 2 + VERTICAL_OFFSET

                final_image.paste(image, (x_position, y_position))
                final_image.paste(frame_resized, (0, 0), frame_resized)
                filename = f'{result_name}.png'
                final_image.save(new_file_path / filename, 'PNG')
                total_framed_images += 1

            logging.info(
                '\nКоличество изображений, к которым добавлена '
                f'рамка {name_of_frame} - {total_framed_images}\n'
                f'Количество уже обрамленных изображений - {skipped_images}\n'
                'Количество изображений обрамленных '
                f'неудачно - {total_failed_images}'
            )
        except Exception as e:
            total_failed_images += 1
            logging.error(f'Неожиданная ошибка наложения рамки: {e}')

    def add_all_frame(self):
        """
        Метод форматирует изображения и добавляет
        все рамки ко всем изображениям.
        """
        try:
            file_path = self._make_dir(self.image_folder)
            frame_path = self._make_dir(self.frame_folder)
            new_file_path = self._make_dir(self.new_image_folder)
            images_names_list = self._get_filenames_list(self.image_folder)
            try:
                self._build_offers_set(
                    self.new_image_folder,
                    self._existing_framed_offers
                )
            except (DirectoryCreationError, EmptyFeedsListError):
                logging.warning(
                    'Директория с форматированными изображениями отсутствует. '
                    'Первый запуск'
                )

            for frame_name in (NAME_OF_FRAME, NAME_OF_FRAME_PROMO):
                self._add_frame(
                    frame_name,
                    images_names_list,
                    file_path,
                    frame_path,
                    new_file_path
                )
        except Exception as e:
            logging.error(f'Неожиданная ошибка: {e}')
