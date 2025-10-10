import shutil
from pathlib import Path

from tabulate import tabulate

from core.excel_exporter import generate_excel_report
from core.file_utils import load_yaml_data, save_wp_links_yaml
from core.html_generator import (
    generate_discipline_page,
    generate_html_report,
    generate_index_page,
)
from core.logging_config import get_logger
from core.models import WordPressPage
from core.parse_index_links import parse_index_links
from core.wordpress_client import WordPressClient
from core.wordpress_uploader import (
    upload_all_pages,
    upload_discipline_page,
    upload_index,
)

logger = get_logger(__name__)

# ==================================================================================
# Утиліти
# ==================================================================================


def clean_output_directory(output_dir: Path | None = None) -> None:
    """
    Видаляє директорію з усім вмістом.
    """
    if output_dir is None:
        logger.warning("⚠️ Директорія не вказана — видалення пропущено")
        return

    path = Path(output_dir)

    if not path.exists():
        logger.debug(f"Директорія {path} не існує, нічого видаляти")
        return

    try:
        shutil.rmtree(path)
        logger.debug(f"Директорія {path} успішно видалена")
    except Exception as e:
        logger.error(f"Помилка при видаленні {path}: {e}")
        raise


def handle_dir_discipline(yaml_file: str | Path, max_len: int = 80) -> None:
    """
    Вводить таблицю з кодом дисципліни, її назвою, роком навчання та рівнем освіти.

    Args:
        yaml_file (str | Path): Шлях до YAML-файлу з даними про дисципліни.
        max_len (int, optional): Максимальна довжина назви дисципліни. Якщо назва перевищує
            цей ліміт, вона буде обрізана та доповнена трьома крапками. За замовчуванням 80.

    Returns:
        None: Функція нічого не повертає, лише виводить таблицю у консоль.
    """

    data = load_yaml_data(yaml_file)
    all_disciplines = data.get("disciplines", {}).copy()
    if "elevative_disciplines" in data:
        all_disciplines.update(data.get("elevative_disciplines", {}))

    table_data = []
    for discipline_code, info in all_disciplines.items():
        name = info.get("name", "")
        if len(name) > max_len:
            name = name[: max_len - 3] + "..."  # обрізаємо і додаємо три крапки
        table_data.append(
            [
                discipline_code,
                name,
                data.get("metadata").get("year"),
                data.get("metadata").get("degree"),
            ]
        )
    headers = ["Код ", "Назва", "Рік", "Рівень"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


# ==================================================================================
# Handlers для створення звіту
# ==================================================================================


def handle_generate_report(yaml_file: str | Path, output_filename: Path) -> bool:
    """CLI хендлер для генерації звітніх таблиць"""

    return generate_html_report(str(yaml_file), str(output_filename))


def handle_generate_excel(yaml_file: str | Path, output_filename: Path) -> bool:
    """CLI хендлер для генерації звітніх таблиць в excel"""

    return generate_excel_report(str(yaml_file), str(output_filename))


# ==================================================================================
# Handlers для створення сторінок
# ==================================================================================


def handle_generate_single_discipline(
    yaml_file: str | Path, output_filename: Path, discipline_code: str
) -> bool:
    """CLI хендлер для генерації однієї дисципліни"""
    # Преобразуем в Path и проверяем существование

    template_name = "discipline_template.html"

    return generate_discipline_page(
        str(yaml_file), discipline_code, str(output_filename), template_name
    )


def handle_generate_all_disciplines(yaml_file: Path, output_dir: Path) -> dict:
    """CLI handler for generating all disciplines with a progress bar."""

    data = load_yaml_data(yaml_file)

    # Get all disciplines
    all_disciplines = data.get("disciplines", {}).copy()
    if "elevative_disciplines" in data:
        all_disciplines.update(data.get("elevative_disciplines", {}))

    total = len(all_disciplines)
    logger.info(f"🎯 Generating {total} disciplines from {yaml_file.name}")

    results = {}
    successful = 0

    # Generate disciplines with progress
    for i, discipline_code in enumerate(all_disciplines.keys(), 1):
        output_filename = output_dir / f"{discipline_code}.html"
        logger.info(f"[{i}/{total}] Generating {discipline_code}...")
        success = generate_discipline_page(
            str(yaml_file), discipline_code, str(output_filename)
        )
        results[discipline_code] = success
        if success:
            successful += 1

    logger.info(f"Results: {successful}/{total} successful")
    return results


# ==================================================================================
# Handlers для завантаження сторінок
# ==================================================================================


def handle_upload_discipline(
    discipline_code: str, yaml_file: Path, client: WordPressClient
) -> bool:
    """CLI хендлер для завантаження сторінки дисципліни на WordPress"""

    try:
        # Завантажуємо дані з YAML
        yaml_data = load_yaml_data(yaml_file)

        # Отримуємо parent_id з метаданих
        wp_parent_id = yaml_data.get("metadata", {}).get("page_id")
        # Оттимуємо рік рограми
        programm_year = yaml_data.get("metadata", {}).get("year")

        if not wp_parent_id:
            logger.debug("page_id not found in YAML metadata")
            return False

        # Отримуємо всі дисципліни
        all_disciplines = {
            **yaml_data.get("disciplines", {}),
            **yaml_data.get("elevative_disciplines", {}),
        }

        # Перевіряємо чи існує дисципліна
        if discipline_code not in all_disciplines:
            logger.debug(f"Discipline '{discipline_code}' not found in YAML")
            logger.debug(f"Available disciplines: {list(all_disciplines.keys())}")
            return False

        # Завантажуємо сторінку
        page = upload_discipline_page(
            discipline_code=discipline_code,
            discipline_info=all_disciplines[discipline_code],
            programm_year=programm_year,
            parent_id=wp_parent_id,
            client=client,
        )
        if page:
            logger.debug(f"✅ Successfully uploaded: {discipline_code}")
            logger.debug(f"🔗 Link: {page.get(discipline_code)}")
            return True
        else:
            logger.debug(f"Failed to upload: {discipline_code}")
            return False

    except Exception as e:
        logger.debug(f"Error uploading {discipline_code}: {e}")
        return False


def handle_upload_all_disciplines(
    yaml_file: str | Path, wp_links_file: Path, client: WordPressClient
) -> bool:
    """
    Handler для завантаження всіх дисциплін на WordPress.

    Аргументи:
        yaml_file: шлях до YAML файлу з даними дисциплін
        parent_id: ID батьківської сторінки у WordPress
        client: інстанс WordPressClient

    Повертає:
        True якщо хоча б одна сторінка завантажена, False інакше
    """
    try:
        wp_data = upload_all_pages(yaml_file=yaml_file, client=client)
        if wp_data:
            logger.info(f"Успішно завантажено {len(wp_data)} сторінок")
            save_wp_links_yaml(wp_data, wp_links_file)
            return True
        else:
            logger.warning("Жодної сторінки не було завантажено")
            return False
    except Exception as e:
        logger.error(f"Помилка під час завантаження сторінок: {e}")
        return False


# ==================================================================================
# Handler для створення індексу
# ==================================================================================


def handle_generate_index(
    yaml_file: str | Path, output_file: str = "index.html"
) -> bool:
    """CLI хендлер для генерації індексної сторінки зі списком дисциплін"""

    logger.info(f"📄 Generating index page from: {yaml_file}")
    logger.info(f"📁 Output: {output_file}")

    try:
        # Генеруємо індексну сторінку
        generate_index_page(str(yaml_file), str(output_file))
        logger.debug("Index page generated successfully!")
        return True

    except Exception as e:
        logger.debug(f"Failed to generate index page: {e}")
        return False


def handle_parse_index_links(yaml_file: str | Path) -> bool:
    """CLI хендлер для заміни локальних посилань на WordPress посилання"""

    try:
        result = parse_index_links(str(yaml_file))
        return result
    except Exception as e:
        logger.error(f"Failed to parse links: {e}")
        return False


# ==================================================================================
# Handler для завантаження індексу
# ==================================================================================


def handle_upload_index(
    yaml_file: str | Path, client: WordPressClient
) -> WordPressPage | None:
    """
    Обработчик для CLI: загружает или обновляет индексную страницу на WordPress.

    Args:
        index_file (str | Path): Путь к HTML-файлу индекса.
        page_id (int): ID существующей страницы на WP для обновления.
        client (WordPressClient): Экземпляр клиента WP.

    Returns:
        WordPressPage | None: Загруженная/обновленная страница или None при ошибке.
    """
    page = upload_index(yaml_file, client)

    if page:
        logger.debug(
            f"Индексная страница успешно загружена: {page.title} (ID: {page.id})"
        )
    else:
        logger.error("Не удалось загрузить индексную страницу")

    return page
