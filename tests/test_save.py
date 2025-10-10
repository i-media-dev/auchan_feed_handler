from unittest.mock import Mock, patch

import pytest
import requests

from handler.exceptions import (EmptyFeedsListError, EmptyXMLError,
                                InvalidXMLError)
from handler.feeds_save import XMLSaver


def test_init_with_empty_feeds_list():
    """Тест инициализации с пустым списком фидов."""
    with pytest.raises(EmptyFeedsListError):
        XMLSaver(feeds_list=[])


def test_init_with_valid_feeds_list(sample_feeds, tmp_path):
    """Тест инициализации с валидным списком фидов."""
    saver = XMLSaver(feeds_list=sample_feeds, feeds_folder=str(tmp_path))
    assert saver.feeds_list == sample_feeds
    assert saver.feeds_folder == str(tmp_path)


def test_make_dir_creates_directory(sample_feeds, tmp_path):
    """Тест создания директории."""
    saver = XMLSaver(feeds_list=sample_feeds, feeds_folder=str(tmp_path))
    folder_path = saver._make_dir(str(tmp_path))
    assert folder_path.exists()
    assert folder_path == tmp_path


def test_get_filename_from_url(sample_feeds):
    """Тест извлечения имени файла из URL."""
    saver = XMLSaver(feeds_list=sample_feeds)
    filename = saver._get_filename('https://example.com/test_feed.xml')
    assert filename == 'test_feed.xml'


@patch('handler.feeds_save.requests.get')
def test_get_file_success(mock_get, sample_feeds, mock_response):
    """Тест успешного получения файла."""
    mock_get.return_value = mock_response
    saver = XMLSaver(feeds_list=sample_feeds)
    response = saver._get_file('https://example.com/feed.xml')

    assert response == mock_response
    mock_get.assert_called_once_with(
        'https://example.com/feed.xml', stream=True, timeout=(10, 60)
    )


@patch('handler.feeds_save.requests.get')
def test_get_file_unauthorized_then_success(mock_get, sample_feeds):
    """Тест получения файла с авторизацией."""
    mock_response_401 = Mock()
    mock_response_401.status_code = 401
    mock_response_200 = Mock()
    mock_response_200.status_code = 200
    mock_response_200.content = b'<root>test</root>'

    mock_get.side_effect = [mock_response_401, mock_response_200]

    with patch.dict('os.environ', {
        'XML_FEED_USERNAME': 'test_user',
        'XML_FEED_PASSWORD': 'test_pass'
    }):
        saver = XMLSaver(feeds_list=sample_feeds)
        response = saver._get_file('https://example.com/feed.xml')

    assert response == mock_response_200
    assert mock_get.call_count == 2


def test_validate_xml_valid_content(sample_feeds, sample_xml_content):
    """Тест валидации корректного XML."""
    saver = XMLSaver(feeds_list=sample_feeds)
    decoded_content, encoding = saver._validate_xml(sample_xml_content)

    assert 'root' in decoded_content
    assert encoding == 'utf-8'


def test_validate_xml_empty_content(sample_feeds):
    """Тест валидации пустого XML."""
    saver = XMLSaver(feeds_list=sample_feeds)
    with pytest.raises(EmptyXMLError):
        saver._validate_xml(b'')


def test_validate_xml_invalid_content(sample_feeds):
    """Тест валидации некорректного XML."""
    saver = XMLSaver(feeds_list=sample_feeds)
    with pytest.raises(InvalidXMLError):
        saver._validate_xml(b'<invalid><xml>')


@patch('handler.feeds_save.requests.get')
@patch('handler.feeds_save.XMLSaver._validate_xml')
def test_save_xml_success(
    mock_validate,
    mock_get,
    sample_feeds,
    tmp_path,
    sample_xml_content
):
    """Тест успешного сохранения XML файлов."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = sample_xml_content
    mock_get.return_value = mock_response
    mock_validate.return_value = ('<root>test</root>', 'utf-8')
    saver = XMLSaver(feeds_list=sample_feeds, feeds_folder=str(tmp_path))
    saver.save_xml()
    files = list(tmp_path.glob('*.xml'))

    assert len(files) == 2
    assert any(file.name == 'feed1.xml' for file in files)
    assert any(file.name == 'feed2.xml' for file in files)


@patch('handler.feeds_save.requests.get')
def test_save_xml_failed_download(mock_get, sample_feeds, tmp_path):
    """Тест обработки ошибки загрузки файла."""
    mock_get.side_effect = requests.RequestException("Connection error")
    saver = XMLSaver(feeds_list=sample_feeds, feeds_folder=str(tmp_path))
    saver.save_xml()
    files = list(tmp_path.glob('*.xml'))

    assert len(files) == 0


@patch('handler.feeds_save.requests.get')
@patch('handler.feeds_save.XMLSaver._validate_xml')
def test_save_xml_invalid_xml(
    mock_validate,
    mock_get,
    sample_feeds,
    tmp_path,
    sample_xml_content
):
    """Тест обработки невалидного XML."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = sample_xml_content
    mock_get.return_value = mock_response
    mock_validate.side_effect = InvalidXMLError('Invalid XML')
    saver = XMLSaver(feeds_list=sample_feeds, feeds_folder=str(tmp_path))
    saver.save_xml()
    files = list(tmp_path.glob('*.xml'))

    assert len(files) == 0


@patch('handler.feeds_save.requests.get')
def test_save_xml_encoding_detection(mock_get, tmp_path):
    """Тест определения кодировки XML."""
    xml_content_win1251 = b'''<?xml version="1.0" encoding="windows-1251"?>
    <root><item>Test</item></root>'''
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = xml_content_win1251
    mock_get.return_value = mock_response
    saver = XMLSaver(
        feeds_list=[
            'https://example.com/feed1.xml'
        ], feeds_folder=str(tmp_path))
    saver.save_xml()
    files = list(tmp_path.glob('*.xml'))
    assert len(files) == 1


def test_save_xml_with_custom_folder(sample_feeds, tmp_path):
    """Тест работы с пользовательской папкой."""
    custom_folder = tmp_path / 'custom_feeds'
    saver = XMLSaver(feeds_list=sample_feeds, feeds_folder=str(custom_folder))
    folder_path = saver._make_dir(str(custom_folder))

    assert folder_path == custom_folder
    assert custom_folder.exists()
