import os
import sys
from unittest.mock import MagicMock, Mock

import pytest

from handler.reports_db import ReportDataBase

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Фикстура подмены переменных окружения."""
    monkeypatch.setenv('XML_FEED_USERNAME', 'test_user')
    monkeypatch.setenv('XML_FEED_PASSWORD', 'test_pass')


@pytest.fixture
def sample_feeds():
    """Фикстура с тестовыми фидами."""
    return [
        'https://example.com/feed1.xml',
        'https://example.com/feed2.xml'
    ]


@pytest.fixture
def sample_xml_content():
    """Фикстура с валидным XML контентом."""
    return b'''<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <item>Test</item>
    </root>'''


@pytest.fixture
def mock_response(sample_xml_content):
    """Фикстура с моком ответа requests."""
    mock = Mock()
    mock.status_code = 200
    mock.content = sample_xml_content
    return mock


@pytest.fixture
def mock_db_connection():
    """Фикстура для мока подключения к базе данных"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


@pytest.fixture
def xml_db_client():
    """Фикстура для создания экземпляра XMLDataBase с моками"""
    client = ReportDataBase(shop_name='test_shop')
    yield client


@pytest.fixture
def sample_catalog_data():
    """Тестовые данные для каталога"""
    return [
        {'category_id': 1, 'category_name': 'Category 1'},
        {'category_id': 2, 'category_name': 'Category 2'}
    ]


@pytest.fixture
def sample_reports_data():
    """Тестовые данные для отчетов"""
    return [
        {
            'date': '2023-01-01',
            'feed_name': 'feed1',
            'category_id': 1,
            'parent_id': 0,
            'count_offers': 10,
            'min_price': 100.0,
            'clear_min_price': 90.0,
            'max_price': 200.0,
            'clear_max_price': 180.0,
            'avg_price': 150.0,
            'clear_avg_price': 135.0,
            'median_price': 145.0,
            'clear_median_price': 130.0
        }
    ]
