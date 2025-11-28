import os

from dotenv import load_dotenv

load_dotenv()

ATTEMPTION_LOAD_FEED = 3
"""Попытки для скачивания фида."""

PROTOCOL = 'https'
"""Протокол запроса."""

ADDRESS = 'projects/auchan/new_images'
"""Путь к файлу."""

DOMEN_FTP = 'feeds.i-media.ru'
"""Домен FTP-сервера."""

DEFAULT_IMAGE_SIZE = (1000, 1000)
"""
Оптимальный размер рамки и финального
изображения по умолчанию.
"""

VERTICAL_OFFSET = 0
"""
Сдвиг вниз по вертикали (опциональный параметр).
Если указать 0, изображение будет ровно по центру.
"""

RGB_COLOR_SETTINGS = (255, 255, 255)
"""Цвет RGB холста."""

RGBA_COLOR_SETTINGS = (0, 0, 0, 0)
"""Цвет RGBA холста."""

NUMBER_PIXELS_IMAGE = 250
"""
Количество пикселей для подгонки изображения.
Чем меньше число, тем больше размер картинки.
(в этом скрипте не используется)
"""

NAME_OF_FRAME = 'auchan.png'

NAME_OF_FRAME_PROMO = 'auchan_promo.png'

DATE_FORMAT = '%Y-%m-%d'
"""Формат даты по умолчанию."""

TIME_FORMAT = '%H:%M:%S'
"""Формат времени по умолчанию."""

TIME_DELAY = 5
"""Время повторного реконнекта к дб в секундах."""

MAX_RETRIES = 5
"""Максимальное количество переподключений к бд."""

NAME_OF_SHOP = 'auchan'
"""Константа названия магазина."""

FRAME_FOLDER = os.getenv('FRAME_FOLDER', 'frame')
"""Константа стокового названия директории c рамкой"""

JOIN_FEEDS_FOLDER = os.getenv('JOIN_FEEDS_FOLDER', 'join_feeds')
"""Константа стокового названия директории с объединенными фидами."""

FEEDS_FOLDER = os.getenv('FEEDS_FOLDER', 'temp_feeds')
"""Константа стокового названия директории с скачанными фидами."""

NEW_FEEDS_FOLDER = os.getenv('NEW_FEEDS_FOLDER', 'new_feeds')
"""Константа стокового названия директории с обработанными фидами."""

IMAGE_FOLDER = os.getenv('IMAGE_FOLDER', 'old_images')
"""Константа стокового названия директории с скачанными изображениями."""

NEW_IMAGE_FOLDER = os.getenv('NEW_IMAGE_FOLDER', 'new_images')
"""Константа стокового названия директории с обработанными изображениями."""

UPPER_OUTLIER_PERCENTILE = 0.75
"""Процентиль (0.75)."""
LOWER_OUTLIER_PERCENTILE = 0.25
"""Процентиль (0.25)."""

DECIMAL_ROUNDING = 2
"""Округление до указанного количества знаков после точки (2)."""

UNAVAILABLE_OFFER_ID_LIST = ['1621720', '1621704', '1621686']
"""Список id офферов для available=False."""

CUSTOM_LABEL = {'asia': {
    'name': ['Видеокарта', 'Роликовые'],
    'url': ['videokarta-biostar-pci-e-rx550-4gb-amd-rx550-4gb'],
    'id': ['2043409']
}, 'computer': {
    'name': ['IVIGO', 'Сетевые'],
    'url': [
        'product/ultrabuk-msi-summit-e13-flip-evo-a13mt-243us-i7-1360p-'
        '16gb-ssd1tb-13-4-2043424/?referrer=reattribution'
        '%3D1&amp;utm_term=split'
    ],
    'id': ['1860372']
}}
"""Данные для вставки в оффер."""

# запросы на создание таблиц.
CREATE_REPORTS_TABLE = '''
CREATE TABLE IF NOT EXISTS {table_name} (
    `id` INT NOT NULL AUTO_INCREMENT,
    `date` DATE NOT NULL,
    `feed_name` VARCHAR(255) NOT NULL,
    `category_id` BIGINT UNSIGNED NOT NULL,
    `parent_id` BIGINT UNSIGNED NULL,
    `count_offers` INT UNSIGNED NOT NULL,
    `min_price` FLOAT UNSIGNED NOT NULL,
    `clear_min_price` FLOAT UNSIGNED NOT NULL,
    `max_price` FLOAT UNSIGNED NOT NULL,
    `clear_max_price` FLOAT UNSIGNED NOT NULL,
    `avg_price` DECIMAL(20,2) UNSIGNED NOT NULL,
    `clear_avg_price` DECIMAL(20,2) UNSIGNED NOT NULL,
    `median_price` DECIMAL(20,2) UNSIGNED NOT NULL,
    `clear_median_price` DECIMAL(20,2) UNSIGNED NOT NULL,
PRIMARY KEY (`id`),
UNIQUE KEY `unique_{table_name}_combo` (
    `date`, `feed_name`, `category_id`
),
KEY `idx_date` (`date`),
KEY `idx_category` (`category_id`)
)
'''
"""SQL-запрос на создание таблицы reports_offers_<название магазина>"""

CREATE_CATALOG_TABLE = '''
CREATE TABLE IF NOT EXISTS {table_name} (
    `id` INT NOT NULL AUTO_INCREMENT,
    `category_id` BIGINT UNSIGNED NOT NULL,
    `category_name` VARCHAR(255) NULL,
PRIMARY KEY (`id`),
UNIQUE KEY `category_id` (`category_id`),
FULLTEXT KEY `category_name` (`category_name`)
)
'''
"""SQL-запрос на создание таблицы catalog_categories_<название магазина>"""

# запросы заполнения таблиц данными.
INSERT_REPORT = '''
INSERT INTO {table_name} (
    date,
    feed_name,
    category_id,
    parent_id,
    count_offers,
    min_price,
    clear_min_price,
    max_price,
    clear_max_price,
    avg_price,
    clear_avg_price,
    median_price,
    clear_median_price
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    count_offers = VALUES(count_offers),
    min_price = VALUES(min_price),
    clear_min_price = VALUES(clear_min_price),
    max_price = VALUES(max_price),
    clear_max_price = VALUES(clear_max_price),
    avg_price = VALUES(avg_price),
    clear_avg_price = VALUES(clear_avg_price),
    median_price = VALUES(median_price),
    clear_median_price = VALUES(clear_median_price)
'''
"""SQL-запрос на вставку данных в таблицу reports_offers_<название магазина>"""

INSERT_CATALOG = '''
INSERT INTO {table_name} (
    category_id,
    category_name
)
VALUES (%s, %s)
ON DUPLICATE KEY UPDATE
    category_name = VALUES(category_name)
'''
"""
SQL-запрос на вставку данных в таблицу
catalog_categories_<название магазина>
"""
