import re
from pathlib import Path

import yaml

from core.config import AppConfig
from core.logging_config import get_logger

logger = get_logger(__name__)

config = AppConfig()


def parse_index_links(data_yaml: str | Path) -> bool:
    """Заменяет локальные ссылки на дисциплины в index.html на WP ссылки."""

    # Пути к index.html и YAML с WP ссылками
    index_file = config.output_dir / "index.html"
    wp_links_file = Path("wp_links") / f"wp_links_{Path(data_yaml).stem}.yaml"

    # Проверка существования файлов
    if not index_file.exists() or not wp_links_file.exists():
        logger.error(
            f"Файл {'index.html' if not index_file.exists() else wp_links_file} не найден"
        )
        return False

    # Загружаем WP ссылки и основной YAML
    wp_data = yaml.safe_load(wp_links_file.read_text(encoding="utf-8"))
    meta_data = yaml.safe_load(Path(data_yaml).read_text(encoding="utf-8"))

    # Проверка совпадения метаданных (год и степень)
    if (wp_data.get("year"), wp_data.get("degree")) != (
        meta_data.get("metadata", {}).get("year"),
        meta_data.get("metadata", {}).get("degree"),
    ):
        logger.error(
            f"Метаданные не совпадают: WP ({wp_data.get('year')}/{wp_data.get('degree')}) "
            f"vs YAML ({meta_data.get('metadata', {}).get('year')}/{meta_data.get('metadata', {}).get('degree')})"
        )
        return False

    # Чтение HTML и поиск всех ссылок на дисциплины по шаблону
    html = index_file.read_text(encoding="utf-8")
    pattern = re.compile(r'href="((ЗО|ПО|ПВ|НК|ВК)[ _]\d{2}(?:\.\d+)?)\.html"')

    # Замена найденных href на соответствующие WP ссылки или "#" если нет соответствия
    html = pattern.sub(
        lambda m: f'href="{wp_data.get("links", {}).get(m.group(1).replace("_", " ").strip(), "#")}"',
        html,
    )

    # Сохраняем обновлённый HTML
    index_file.write_text(html, encoding="utf-8")

    logger.debug(f"href в {index_file} заменены на WP ссылки")
    return True
