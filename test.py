import requests
from core.config import WordPressConfig
from core.wordpress_client import WordPressClient
from requests.auth import HTTPBasicAuth
import os

# Використовуємо WordPressConfig після завантаження .env
config = WordPressConfig()
api_url = config.api_url
auth = HTTPBasicAuth(config.username, config.password)

# Створюємо клієнт з параметрами
client = WordPressClient(api_url=api_url, auth=auth)

if __name__ == "__main__":
    # Якщо передано page_id - одразу оновлюємо
  
    client.create_or_update_page(data, page_id)
