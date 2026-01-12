import json
import logging
import os
from collections import defaultdict
from datetime import datetime as dt

import numpy as np

from handler.calculation import clear_avg, clear_max, clear_median, clear_min
from handler.constants import (DATE_FORMAT, DECIMAL_ROUNDING, FEEDS_FOLDER,
                               JOIN_FEEDS_FOLDER, NEW_FEEDS_FOLDER)
from handler.decorators import time_of_function, try_except
from handler.exceptions import StructureXMLError
from handler.logging_config import setup_logging
from handler.mixins import FileMixin

setup_logging()


class FeedReport(FileMixin):

    def __init__(
        self,
        filenames: list,
        feeds_folder: str = FEEDS_FOLDER,
        new_feeds_folder: str = NEW_FEEDS_FOLDER,
        join_feeds_folder: str = JOIN_FEEDS_FOLDER
    ):
        self.filenames = filenames
        self.feeds_folder = feeds_folder
        self.new_feeds_folder = new_feeds_folder
        self.join_feeds_folder = join_feeds_folder
        self._cached_offers = None

    def __repr__(self):
        return (
            f"FeedReport(filenames='{self.filenames}', "
            f"feeds_folder='{self.feeds_folder}', "
            f"new_feeds_folder='{self.new_feeds_folder}'), "
        )

    def save_to_json(
        self,
        data: list[dict],
        prefix: str = 'offers_report',
        folder: str = 'data'
    ) -> None:
        """Отладочный метод сохраняет данные в файл формата json."""
        os.makedirs(folder, exist_ok=True)
        date_str = (dt.now()).strftime(DATE_FORMAT)
        filename = os.path.join(folder, f'{prefix}_{date_str}.json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f'✅ Данные сохранены в {filename}')
        logging.debug('Файл сохранен.')

    @time_of_function
    @try_except
    def get_offers_report(self) -> list[dict]:
        """Метод, формирующий отчет по офферам."""
        result = []
        date_str = (dt.now()).strftime(DATE_FORMAT)
        for filename in self.filenames:
            root = self._get_root(filename, self.feeds_folder)
            category_data = {}
            all_categories = {}

            for category in root.findall('.//category'):
                category_name = category.text
                category_id = category.get('id')
                parent_id = category.get('parentId')
                all_categories[category_id] = parent_id
                category_data[category_id] = {
                    'prices': [],
                    'category_name': category_name,
                    'offers_count': 0
                }

            for offer in root.findall('.//offer'):
                category_id = offer.findtext('categoryId')
                price = offer.findtext('price')
                if category_id and price:
                    if category_id not in category_data:
                        category_data[category_id] = {
                            'prices': [],
                            'category_name': '',
                            'offers_count': 0
                        }
                    category_data[category_id]['prices'].append(int(price))
                    category_data[category_id]['offers_count'] += 1

            def aggregate_data(category_id):
                prices = category_data[category_id]['prices'].copy()
                offers_count = category_data[category_id]['offers_count']

                for child_id, parent_id in all_categories.items():
                    if parent_id == category_id:
                        child_prices, child_count = aggregate_data(child_id)
                        prices.extend(child_prices)
                        offers_count += child_count
                category_data[category_id]['prices'] = prices
                category_data[category_id]['offers_count'] = offers_count
                return prices, offers_count

            root_categories = [
                cat_id for cat_id, parent_id in all_categories.items()
                if parent_id is None
            ]
            for root_id in root_categories:
                aggregate_data(root_id)

            for category_id, data in category_data.items():
                count_offers = data['offers_count']
                price_list = data['prices']
                parent_id = all_categories.get(category_id)
                category_name = data['category_name']

                result.append({
                    'date': date_str,
                    'feed_name': filename,
                    'category_name': category_name,
                    'category_id': category_id,
                    'parent_id': parent_id,
                    'count_offers': count_offers,
                    'min_price': min(price_list) if price_list else 0,
                    'clear_min_price': clear_min(price_list)
                    if price_list else 0,
                    'max_price': max(price_list) if price_list else 0,
                    'clear_max_price': clear_max(price_list)
                    if price_list else 0,
                    'avg_price': round(
                        sum(price_list) / len(price_list), DECIMAL_ROUNDING
                    ) if price_list else 0,
                    'clear_avg_price': clear_avg(price_list)
                    if price_list else 0,
                    'median_price': round(
                        np.median(price_list), DECIMAL_ROUNDING
                    ) if price_list else 0,
                    'clear_median_price': clear_median(price_list)
                    if price_list else 0
                })
        return result

    def _super_feed(self) -> tuple:
        """Защищенный метод, создает шаблон фида с пустыми offers."""
        root = self._get_root(self.filenames[0], self.new_feeds_folder)
        offers = root.find('.//offers')
        if offers is not None:
            offers.clear()
        else:
            raise StructureXMLError(
                'Тег пуст или структура фида не соответствует ожидаемой.'
            )
        return root, offers

    def _collect_all_offers(self) -> tuple[dict, dict]:
        """
        Защищенный метод, подсчитывает встречался ли оффер в том или ином фиде.
        """
        offer_counts: dict = defaultdict(int)
        all_offers = {}
        for filename in self.filenames:
            root = self._get_root(filename, self.new_feeds_folder)
            for offer in root.findall('.//offer'):
                offer_id = offer.get('id')
                if offer_id:
                    offer_counts[offer_id] += 1
                    all_offers[offer_id] = offer
        return offer_counts, all_offers

    @time_of_function
    @try_except
    def join_feeds(self, join_type: str = 'inner') -> bool:
        """
        Универсальный метод для объединения фидов.

        Args:
            join_type: 'inner' или 'full_outer'
        """
        if not self._cached_offers:
            self._cached_offers = self._collect_all_offers()

        offer_counts, all_offers = self._cached_offers
        root, offers = self._super_feed()
        if join_type == 'inner':
            for offer_id, count in offer_counts.items():
                if count == len(self.filenames):
                    offers.append(all_offers[offer_id])
            filename = 'inner_join_feed.xml'
        elif join_type == 'full_outer':
            for offer in all_offers.values():
                offers.append(offer)
            filename = 'full_outer_join_feed.xml'
        else:
            raise ValueError(f'Неизвестный тип join: {join_type}')

        self._save_xml(root, self.join_feeds_folder, filename)
        return True
