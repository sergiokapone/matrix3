# tests/test_wordpress_client.py
import sys
import os
import pytest
import responses
from requests.auth import HTTPBasicAuth

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.wordpress_client import WordPressClient
from core.config import WordPressConfig


class TestWordPressConfig:
    """Тести для WordPressConfig"""

    def test_config_creation(self):
        """Тест створення конфігурації"""
        config = WordPressConfig()
        assert config.base_url == "https://apd.ipt.kpi.ua"
        assert config.api_path == "/wp-json/wp/v2/pages"

    def test_api_url_property(self):
        """Тест властивості api_url"""
        config = WordPressConfig()
        assert config.api_url == "https://apd.ipt.kpi.ua/wp-json/wp/v2/pages"

    def test_auth_property(self):
        """Тест властивості auth"""
        with pytest.MonkeyPatch().context() as mp:
            mp.setenv("WP_USER", "testuser")
            mp.setenv("WP_PASSWORD", "testpass")
            config = WordPressConfig()
            auth = config.auth
            assert auth.username == "testuser"
            assert auth.password == "testpass"

    def test_missing_credentials(self):
        """Тест відсутності credentials"""
        with pytest.MonkeyPatch().context() as mp:
            mp.delenv("WP_USER", raising=False)
            mp.delenv("WP_PASSWORD", raising=False)
            with pytest.raises(
                ValueError, match="WP_USER або WP_PASSWORD не встановлені"
            ):
                WordPressConfig()


class TestWordPressClient:
    """Тести для WordPressClient"""

    @pytest.fixture
    def mock_auth(self):
        return HTTPBasicAuth("testuser", "testpass")

    @pytest.fixture
    def wp_client(self, mock_auth):
        return WordPressClient("https://example.com", mock_auth)

    @pytest.fixture
    def mock_page_data(self):
        return {
            "id": 123,
            "title": {"rendered": "Test Page"},
            "content": {"rendered": "<p>Test content</p>"},
            "slug": "test-page",
            "status": "publish",
        }

    # GET Page tests
    @responses.activate
    def test_get_page_success(self, wp_client, mock_page_data):
        """Тест успішного отримання сторінки за ID"""
        responses.add(
            responses.GET,
            "https://example.com/pages/123",
            json=mock_page_data,
            status=200,
        )

        result = wp_client.get_page(123)
        assert result == mock_page_data

    @responses.activate
    def test_get_page_not_found(self, wp_client):
        """Тест отримання неіснуючої сторінки"""
        responses.add(
            responses.GET,
            "https://example.com/pages/999",
            json={"error": "Not found"},
            status=404,
        )

        result = wp_client.get_page(999)
        assert result is None

    # Find Page ID tests
    @responses.activate
    def test_find_page_id_by_slug_success(self, wp_client):
        """Тест успішного пошуку ID за slug"""
        responses.add(
            responses.GET,
            "https://example.com/pages",
            json=[{"id": 123, "slug": "test-page"}],
            status=200,
        )

        result = wp_client.find_page_id_by_slug("test-page")
        assert result == 123

    @responses.activate
    def test_find_page_id_by_slug_not_found(self, wp_client):
        """Тест пошуку неіснуючого slug"""
        responses.add(responses.GET, "https://example.com/pages", json=[], status=200)

        result = wp_client.find_page_id_by_slug("non-existent")
        assert result is None

    @responses.activate
    def test_find_page_id_empty_response(self, wp_client):
        """Тест пошуку з пустою відповіддю"""
        responses.add(responses.GET, "https://example.com/pages", json=[], status=200)

        result = wp_client.find_page_id_by_slug("empty")
        assert result is None

    # Create Page tests
    @responses.activate
    def test_create_page_success(self, wp_client, mock_page_data):
        """Тест успішного створення сторінки"""
        responses.add(
            responses.POST, "https://example.com/pages", json=mock_page_data, status=201
        )

        page_data = {"title": "New Page", "content": "Content"}
        result = wp_client.create_page(page_data)
        assert result == mock_page_data

    @responses.activate
    def test_create_page_failure(self, wp_client):
        """Тест невдалого створення сторінки"""
        responses.add(
            responses.POST,
            "https://example.com/pages",
            json={"error": "Bad request"},
            status=400,
        )

        result = wp_client.create_page({})
        assert result is None

    # Update Page tests
    @responses.activate
    def test_update_page_success(self, wp_client, mock_page_data):
        """Тест успішного оновлення сторінки"""
        responses.add(
            responses.POST,
            "https://example.com/pages/123",
            json=mock_page_data,
            status=200,
        )

        result = wp_client.update_page(123, {"title": "Updated"})
        assert result == mock_page_data

    @responses.activate
    def test_update_page_not_found(self, wp_client):
        """Тест оновлення неіснуючої сторінки"""
        responses.add(
            responses.POST,
            "https://example.com/pages/999",
            json={"error": "Not found"},
            status=404,
        )

        result = wp_client.update_page(999, {"title": "Updated"})
        assert result is None


# Додаткові тести для різних сценаріїв
class TestWordPressClientEdgeCases:
    """Тести для крайніх випадків"""

    @pytest.fixture
    def wp_client(self):
        auth = HTTPBasicAuth("user", "pass")
        return WordPressClient("https://test.com", auth, timeout=10)

    @responses.activate
    def test_client_with_custom_timeout(self, wp_client):
        """Тест клієнта з кастомним таймаутом"""
        responses.add(
            responses.GET, "https://test.com/pages/1", json={"id": 1}, status=200
        )

        result = wp_client.get_page(1)
        assert result is not None

    @responses.activate
    def test_multiple_pages_found(self, wp_client):
        """Тест, коли знайдено кілька сторінок"""
        responses.add(
            responses.GET,
            "https://test.com/pages",
            json=[{"id": 1, "slug": "test"}, {"id": 2, "slug": "test"}],
            status=200,
        )

        # Має повернути ID першої знайденої сторінки
        result = wp_client.find_page_id_by_slug("тест")
        assert result == 1
