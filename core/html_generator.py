from pathlib import Path

from core.data_manipulation import (
    get_mapped_competencies,
    get_mapped_program_results,
    load_discipline_data,
    prepare_disciplines_with_totals,
)
from core.file_utils import get_safe_filename, load_yaml_data, save_html_file
from core.logging_config import get_logger
from core.render_html import render_template
from core.validators import validate_yaml_schema

logger = get_logger(__name__)


def generate_discipline_page(
    yaml_file: str,
    discipline_code: str,
    output_filename: str | None = None,
    template_filename: str = "discipline_template.html",
) -> bool:
    """Генерує HTML-сторінку для конкретної дисципліни з використанням конфігурації"""

    # Використовуємо load_discipline_data для завантаження даних
    data, discipline = load_discipline_data(yaml_file, discipline_code)

    if data is None or discipline is None:
        logger.debug("Failed to load discipline data")
        return False

    # Отримуємо метадані з завантажених даних
    metadata = data.get("metadata", {})

    # Отримуємо компетентності та результати навчальної програми
    general_comps, professional_comps = get_mapped_competencies(
        discipline_code, data.get("mappings", {}), data.get("competencies", {})
    )
    program_results = get_mapped_program_results(
        discipline_code,
        data.get("mappings", {}),
        data.get("program_results", {}),
    )

    # Формуємо контекст для шаблону
    context = {
        "discipline_code": discipline_code,
        "discipline": discipline,
        "metadata": metadata,
        "general_competencies": general_comps,
        "professional_competencies": professional_comps,
        "mapped_program_results": program_results,
    }

    # Генеруємо HTML контент
    html_content = render_template(template_filename, context)

    # Зберігаємо HTML файл
    output_filename = get_safe_filename(output_filename)
    save_html_file(html_content, output_filename)

    logger.debug("Discipline page created")
    return True


def generate_index_page(
    yaml_file: str | Path, output_file: str | Path = "index.html"
) -> bool:
    """Генерує індексну сторінку зі списком всіх дисциплін"""
    try:
        data = load_yaml_data(yaml_file)
        validate_yaml_schema(data)

        metadata = data.get("metadata", {})
        disciplines = data.get("disciplines", {}) | data.get(
            "elevative_disciplines", {}
        )

        disciplines = prepare_disciplines_with_totals(disciplines)

        context = {"metadata": metadata, "disciplines": disciplines}

        html_content = render_template("index_template.html", context)
        save_html_file(html_content, output_file)

        logger.debug("Index page created: %s", str(output_file))
        return True  # Успіх

    except Exception as e:
        logger.debug("Failed to generate index page: %s", str(e))
        return False  # Не успіх
