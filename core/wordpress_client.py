# core/wordpress_pages.py
import requests
from requests.auth import HTTPBasicAuth

from core.config import WordPressConfig

config = WordPressConfig()


class WordPressClient:
    """Низькорівневий клієнт для WordPress REST API"""

    def __init__(self, api_url: str, auth: HTTPBasicAuth, timeout: int = 30) -> None:
        self.api_url = api_url
        self.auth = auth
        self.timeout = timeout

    def _request(self, method: str, endpoint: str, **kwargs: dict) -> requests.Response:
        """Виконує HTTP запит"""
        url = f"{self.api_url}/{endpoint}"
        kwargs.setdefault("auth", self.auth)
        kwargs.setdefault("timeout", self.timeout)
        return requests.request(method, url, **kwargs)

    def get_page(self, page_id: int) -> dict | None:
        """Отримує сторінку за ID"""
        response = self._request("GET", f"pages/{page_id}")
        return response.json() if response.status_code == 200 else None

    # def get_page_by_slug(self, slug: str) -> dict | None:
    #     """Отримує сторінку за slug"""
    #     response = self._request("GET", "pages", params={"slug": slug})
    #     pages = response.json()
    #     return pages[0] if pages and response.status_code == 200 else None

    def get_page_by_slug(
        self,
        slug: str,
        parent_id: int | None = None,
        status: str = "publish",
        pick_latest: bool = True,
    ) -> dict | None:
        """
        Отримує сторінку за slug, інтелігентно обираючи при дублікатах.

        Args:
            slug (str): slug сторінки
            parent_id (int | None): якщо вказано, фільтруємо по батьківській сторінці
            status (str): статус сторінки ("publish", "draft" і т.д.)
            pick_latest (bool): якщо True, беремо найновішу сторінку; інакше найстарішу

        Returns:
            dict | None: знайдена сторінка або None
        """
        response = self._request(
            "GET", "pages", params={"slug": slug, "status": status}
        )
        if response.status_code != 200:
            return None

        pages = response.json()

        # Фільтруємо по батьківській сторінці
        if parent_id is not None:
            pages = [p for p in pages if p.get("parent") == parent_id]

        if not pages:
            return None

        # Сортуємо по даті публікації
        pages.sort(key=lambda p: p.get("date"), reverse=pick_latest)

        return pages[0]

    def create_page(self, data: dict) -> dict | None:
        """Створює нову сторінку"""
        response = self._request("POST", "pages", json=data)
        return response.json() if response.status_code == 201 else None

    def update_page(self, page_id: int, data: dict) -> dict | None:
        """Оновлює сторінку за ID"""
        response = self._request("POST", f"pages/{page_id}", json=data)
        return response.json() if response.status_code == 200 else None
