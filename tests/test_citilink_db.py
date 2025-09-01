import pytest
from unittest.mock import patch

from handler.exceptions import TableNameError


def test_allowed_tables(xml_db_client, mock_db_connection):
    """Тест получения списка таблиц"""
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.fetchall.return_value = [('table1',), ('table2',)]
    with patch(
        'handler.decorators.mysql.connector.connect',
        return_value=mock_conn
    ):
        result = xml_db_client._allowed_tables()
        assert result == ['table1', 'table2']
        mock_cursor.execute.assert_called_once_with('SHOW TABLES')


def test_create_table_if_not_exists_new_table(
    xml_db_client,
    mock_db_connection
):
    """Тест создания новой таблицы"""
    mock_conn, mock_cursor = mock_db_connection

    with patch.object(
        xml_db_client,
        '_allowed_tables',
        return_value=[]
    ), patch('handler.decorators.logging.info') as mock_logging, patch(
        'handler.decorators.mysql.connector.connect',
        return_value=mock_conn
    ):
        table_name = xml_db_client._create_table_if_not_exists(
            'catalog_categories', 'CREATE TABLE {table_name} (id INT)'
        )
        expected_table_name = 'catalog_categories_test_shop'
        assert table_name == expected_table_name
        mock_cursor.execute.assert_called_once_with(
            'CREATE TABLE catalog_categories_test_shop (id INT)')
        mock_logging.assert_called_with(
            f'Таблица {expected_table_name} успешно создана')


def test_create_table_if_not_exists_existing_table(
    xml_db_client,
    mock_db_connection
):
    """Тест случая, когда таблица уже существует"""
    mock_conn, mock_cursor = mock_db_connection
    existing_table = 'catalog_categories_test_shop'

    with patch.object(
        xml_db_client,
        '_allowed_tables',
        return_value=[existing_table]
    ), patch('handler.decorators.logging.info') as mock_logging, patch(
        'handler.decorators.mysql.connector.connect',
        return_value=mock_conn
    ):
        table_name = xml_db_client._create_table_if_not_exists(
            'catalog_categories', 'CREATE TABLE {table_name} (id INT)'
        )
        assert table_name == existing_table
        mock_cursor.execute.assert_not_called()
        mock_logging.assert_called_with(
            f'Таблица {existing_table} найдена в базе')


def test_insert_catalog(xml_db_client, sample_catalog_data):
    """Тест формирования запроса для вставки каталога"""
    with patch.object(
        xml_db_client,
        '_create_table_if_not_exists',
        return_value='catalog_categories_test_shop'
    ):
        query, params = xml_db_client.insert_catalog(sample_catalog_data)
        assert 'catalog_categories_test_shop' in query
        assert len(params) == 2
        assert params[0] == (1, 'Category 1')
        assert params[1] == (2, 'Category 2')


def test_insert_reports(xml_db_client, sample_reports_data):
    """Тест формирования запроса для вставки отчетов"""
    with patch.object(
        xml_db_client,
        '_create_table_if_not_exists',
        return_value='reports_offers_test_shop'
    ):
        query, params = xml_db_client.insert_reports(sample_reports_data)
        assert 'reports_offers_test_shop' in query
        assert len(params) == 1
        expected_params = (
            '2023-01-01', 'feed1', 1, 0, 10,
            100.0, 90.0, 200.0, 180.0,
            150.0, 135.0, 145.0, 130.0
        )
        assert params[0] == expected_params


def test_save_to_database_params(xml_db_client, mock_db_connection):
    """Тест сохранения данных с множественными параметрами"""
    mock_conn, mock_cursor = mock_db_connection
    with patch(
        'handler.decorators.mysql.connector.connect',
        return_value=mock_conn
    ):
        query = "INSERT INTO table VALUES (%s, %s)"
        params = [('val1', 'val2'), ('val3', 'val4')]
        xml_db_client.save_to_database((query, params))
        mock_cursor.executemany.assert_called_once_with(query, params)


def test_clean_database_success(xml_db_client, mock_db_connection):
    """Тест успешной очистки базы данных"""
    mock_conn, mock_cursor = mock_db_connection

    with patch.object(
        xml_db_client,
        '_allowed_tables',
        return_value=['existing_table']
    ), patch('handler.decorators.logging.info') as mock_logging:

        with patch(
            'handler.decorators.mysql.connector.connect',
            return_value=mock_conn
        ):
            xml_db_client.clean_database(existing_table=True)

            mock_cursor.execute.assert_called_once_with(
                'DELETE FROM existing_table')
            mock_logging.assert_called_with('Таблица existing_table очищена')


def test_clean_database_table_not_exists(xml_db_client, mock_db_connection):
    """Тест очистки несуществующей таблицы"""
    mock_conn, mock_cursor = mock_db_connection

    with patch.object(
        xml_db_client,
        '_allowed_tables',
        return_value=[]
    ), patch('handler.decorators.logging.error') as mock_logging:
        with patch(
            'handler.decorators.mysql.connector.connect',
            return_value=mock_conn
        ):
            with pytest.raises(TableNameError):
                xml_db_client.clean_database(nonexistent_table=True)
            mock_logging.assert_called()
