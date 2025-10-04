# core/wordpress_pages.py
import requests
from requests.auth import HTTPBasicAuth

from core.config import WordPressConfig

config = WordPressConfig()


class WordPressClient:
    """Низькорівневий клієнт для WordPress REST API"""

    def __init__(self, api_url: str, auth: HTTPBasicAuth, timeout: int = 30):
        self.api_url = api_url
        self.auth = auth
        self.timeout = timeout

    def _request(
        self, method: str, endpoint: str, **kwargs
    ) -> requests.Response:
        """Виконує HTTP запит"""
        url = f"{self.api_url}/{endpoint}"
        kwargs.setdefault("auth", self.auth)
        kwargs.setdefault("timeout", self.timeout)
        return requests.request(method, url, **kwargs)

    def get_page(self, page_id: int) -> dict | None:
        """Отримує сторінку за ID"""
        response = self._request("GET", f"pages/{page_id}")
        return response.json() if response.status_code == 200 else None

    def get_page_by_slug(self, slug: str) -> dict | None:
        """Отримує сторінку за slug"""
        # response = requests('GET', self.api_url, params={"slug": slug}, auth=self.auth, timeout=30)
        response = self._request("GET", "pages", params={"slug": slug})
        pages = response.json()
        return pages[0] if pages and response.status_code == 200 else None

    def create_page(self, data: dict) -> dict | None:
        """Створює нову сторінку"""
        response = self._request("POST", "pages", json=data)
        return response.json() if response.status_code == 201 else None

    def update_page(self, page_id: int, data: dict) -> dict | None:
        """Оновлює сторінку за ID"""
        response = self._request("POST", f"pages/{page_id}", json=data)
        return response.json() if response.status_code == 200 else None
