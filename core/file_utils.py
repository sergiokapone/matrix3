import sys
from pathlib import Path

import yaml

from core.exceptions import ParrentIdError
from core.logging_config import get_logger

logger = get_logger(__name__)


def get_safe_filename(discipline_code: str) -> str:
    """Створює безпечне ім'я файлу з коду дисципліни"""
    return discipline_code.replace(" ", "_").replace("/", "_")


def save_html_file(content: str, output_file: str | Path) -> None:
    """Зберігає HTML-контент у файл з кодуванням UTF-8"""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.debug("HTML file saved")
    except Exception:
        logger.error("Failed to save HTML file")
        raise


def load_yaml_data(yaml_path: Path) -> dict | None:
    """Завантаження YAML файлу"""
    try:
        with open(yaml_path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Помилка читання YAML файлу: {e}")
        sys.exit(1)


def get_discipline_parent_id(yaml_data: dict) -> int:
    """Отримує ID батьківської сторінки для дисциплін з YAML-даних"""
    try:
        page_id = yaml_data["metadata"]["page_id"]
        logger.debug("Отримано parent_id з YAML", parent_id=page_id)
        return page_id
    except KeyError:
        logger.error("YAML missing 'page_id' in metadata")
        raise ParrentIdError("Missing 'page_id' in YAML metadata")


def save_wp_links_yaml(wp_data: dict, output_file: str = "wp_links.yaml") -> None:
    """
    Зберігає посилання WordPress та метадані у YAML-файл.

    Args:
        wp_data (dict): Структура з посиланнями та метаданими:
            {
                "year": "2024",
                "degree": "Бакалавр",
                "links": {"ПО 01": "https://..."}
            }
        output_file (str | Path, optional): Шлях до вихідного YAML-файлу.
            За замовчуванням "wp_links.yaml".

    Note:
        Автоматично створює батьківські директорії якщо їх не існує.
        Використовує кодування UTF-8 для підтримки кирилиці.
    """
    output_path = Path(output_file)

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(wp_data, f, allow_unicode=True)

    logger.info(f"📋 WP посилання збережені в {output_path}")
