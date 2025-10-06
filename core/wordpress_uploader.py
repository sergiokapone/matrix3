# core/wordpress_uploader.py
from pathlib import Path

from slugify import slugify

from core.config import AppConfig
from core.file_utils import get_safe_filename, load_yaml_data
from core.logging_config import ColorFormatter, get_logger
from core.models import WordPressPage
from core.wordpress_client import WordPressClient

logger = get_logger(__name__)

link_logger = get_logger(
    __name__ + "_link",
    formatter=ColorFormatter("LINK: %(message)s", color="\033[32m"),
)

config = AppConfig()


def upload_discipline_page(
    discipline_code: str,
    discipline_info: dict,
    programm_year: str,
    parent_id: int,
    client: WordPressClient,
) -> WordPressPage | None:
    """Завантажує сторінку дисципліни на WordPress"""
    try:
        # Формуємо title та slug
        discipline_code_safe = get_safe_filename(discipline_code)
        title = f"{discipline_code}: {discipline_info['name']}"
        slug = slugify(f"{discipline_code_safe}: {discipline_info['name']}-{programm_year}")

        # Шлях до HTML файлу
        html_file = config.output_dir / f"{discipline_code_safe}.html"

        if not html_file.exists():
            logger.debug(f"❌ HTML file not found: {html_file}")
            return None

        # Читаємо HTML контент
        html_content = html_file.read_text(encoding="utf-8")

        # Готуємо дані для WordPress
        post_data = {
            "title": title,
            "content": html_content,
            "slug": slug,
            "status": "publish",
            "parent": parent_id,
        }

        # Шукаємо існуючу сторінку
        existing_page = client.get_page_by_slug(slug)

        if existing_page:
            # Оновлюємо існуючу сторінку
            page_id = existing_page.get("id")
            logger.info(f"♻️ Оновлюємо існуючу сторінку: {slug} (id={page_id})")
            result = client.update_page(page_id, post_data)
            action = "оновлено"
        else:
            # Створюємо нову сторінку
            logger.info(f"Створюємо нову сторінку: {slug}")
            result = client.create_page(post_data)
            action = "створено"

        if result:
            page = WordPressPage(
                id=result.get("id"),
                title=title,
                content=html_content,
                slug=slug,
                link=result.get("link"),
                parent=parent_id,
            )
            logger.debug(f"Сторінку {action}: {title} (ID: {page.id}) завантажено")
            return {discipline_code: page.link}
        else:
            logger.debug(f"Не вдалося завантажити сторінку: {title}")
            return None

    except Exception as e:
        logger.error(f"Помилка завантаження {discipline_code}: {e}")
        return None


def upload_all_pages(
    yaml_file: Path, client: WordPressClient
) -> list[WordPressPage] | None:
    """Завантажує всі HTML сторінки з директорії на WordPress використовуючи upload_discipline_page"""
    wp_links = {}

    # Завантажуємо дані з YAML
    yaml_data = load_yaml_data(yaml_file)

    # Отримуємо рік дисципліни для slug
    programm_year = yaml_data.get("metadata").get("year")

    if not yaml_data:
        logger.debug(f"❌ Failed to load YAML data from {yaml_file}")
        return None

    # Отримуємо всі дисципліни
    all_disciplines = {
        **yaml_data.get("disciplines", {}),
        **yaml_data.get("elevative_disciplines", {}),
    }

    if not all_disciplines:
        logger.error("❌ No disciplines found in YAML file")
        return None

    total = len(all_disciplines)
    logger.info(f"📤 Uploading {total} pages to WordPress...")

    for i, (discipline_code, discipline_info) in enumerate(
        all_disciplines.items(), start=1
    ):
        # Використовуємо upload_discipline_page для кожної дисципліни
        link = upload_discipline_page(
            discipline_code=discipline_code,
            discipline_info=discipline_info,
            parent_id=yaml_data["metadata"]["page_id"],
            programm_year=programm_year,
            client=client,
        )
        logger.info(f"[{i}/{total}] Generating {discipline_code}...")
        link_logger.info(link.get(discipline_code))
        if link:
            wp_links.update(link)

    logger.debug(f"Завантажено {len(wp_links)}/{len(all_disciplines)} сторінок")

    metadata = {
        "year": yaml_data.get("metadata", {}).get("year", ""),
        "degree": yaml_data.get("metadata", {}).get("degree", ""),
    }

    wp_data = {
        "year": metadata["year"],
        "degree": metadata["degree"],
        "links": wp_links,
    }

    return wp_data


def upload_index(yaml_file: Path, client: WordPressClient) -> WordPressPage | None:
    """Завантажує індексну сторінку на WordPress"""
    try:
        config = AppConfig()
        index_file = config.output_dir / "index.html"
        if not index_file.exists():
            logger.error(f"❌ Index file does not exist: {index_file}")
            return None

        # Отримуємо title з YAML
        yaml_data = load_yaml_data(yaml_file)
        page_id = yaml_data["metadata"]["page_id"]
        title = f"Освітні компоненти: {yaml_data['metadata'].get('degree', '')} {yaml_data['metadata'].get('year', '')}"

        html_content = index_file.read_text(encoding="utf-8")

        # Готуємо дані
        post_data = {
            "title": title,
            "content": html_content,
            "parent": 16,
            "status": "publish",
        }

        # Оновлюємо існуючу сторінку
        logger.debug(f"♻️ Оновлюємо індексну сторінку з id={page_id}")
        result = client.update_page(page_id, post_data)

        if result:
            page = WordPressPage(
                id=page_id,
                title=title,
                content=html_content,
                link=result.get("link"),
            )

            logger.debug(f"✅ Індексну сторінку оновлено: {title} (ID: {page.id})")
            return page
        else:
            logger.error("❌ Не вдалося оновити індексну сторінку")
            return None

    except Exception as e:
        logger.error(f"❌ Помилка завантаження індексної сторінки: {e}")
        return None
