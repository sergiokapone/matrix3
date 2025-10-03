from pathlib import Path
from venv import logger

from core import config
from core.data_manipulation import get_mapped_competencies, get_mapped_program_results, load_discipline_data, prepare_disciplines_with_totals
from core.file_utils import get_safe_filename, load_yaml_data, save_html_file
from core.render_html import render_template
from core.validators import validate_yaml_schema


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
        logger.error("Failed to load discipline data")
        return False

    # Отримуємо метадані з завантажених даних
    metadata = data.get("metadata", {})
    
    # Отримуємо компетентності та результати навчальної програми
    general_comps, professional_comps = get_mapped_competencies(
        discipline_code, data.get("mappings", {}), data.get("competencies", {})
    )
    program_results = get_mapped_program_results(
        discipline_code, data.get("mappings", {}), data.get("program_results", {})
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
    
    logger.info("Discipline page created")
    return True


def generate_all_disciplines(
    yaml_file: str | Path,
    output_dir: str | Path = None,
    template_filename: str = "discipline_template.html"
) -> dict[str, bool]:
    """Генерує HTML-сторінки для всіх дисциплін з використанням тієї ж логіки"""
    
    # Використовуємо load_discipline_data для отримання даних (як у generate_discipline_page)
    data, _ = load_discipline_data(yaml_file, "dummy_code")
    
    if data is None:
        logger.error("Failed to load YAML data")
        return {}
    
    # Отримуємо метадані (як у generate_discipline_page)
    metadata = data.get("metadata", {})
    
    # Отримуємо всі дисципліни (як у load_discipline_data)
    all_disciplines = data.get("disciplines", {}).copy()
    if "elevative_disciplines" in data:
        all_disciplines.update(data.get("elevative_disciplines", {}))
    
    results = {}
    output_dir = Path(output_dir) if output_dir else config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for discipline_code in all_disciplines.keys():
        # Використовуємо ту саму логіку, що й в generate_discipline_page
        general_comps, professional_comps = get_mapped_competencies(
            discipline_code, data.get("mappings", {}), data.get("competencies", {})
        )
        program_results = get_mapped_program_results(
            discipline_code, data.get("mappings", {}), data.get("program_results", {})
        )

        context = {
            "discipline_code": discipline_code,
            "discipline": all_disciplines.get(discipline_code),
            "metadata": metadata,
            "general_competencies": general_comps,
            "professional_competencies": professional_comps,
            "mapped_program_results": program_results,
        }

        html_content = render_template(template_filename, context)

        output_filename = output_dir / f"{discipline_code}.html"
        output_filename = get_safe_filename(str(output_filename))
        
        success = save_html_file(html_content, output_filename)
        results[discipline_code] = success
        
        if success:
            logger.info(f"Discipline page created: {discipline_code}")
            print(f"✅ {discipline_code}")
        else:
            logger.error(f"Failed to create discipline page: {discipline_code}")
            print(f"❌ {discipline_code}")
    
    return results


def generate_index_page(
    yaml_file: str | Path,
    output_file: str | Path = "index.html"
) -> bool:  # Змінюємо на bool
    """Генерує індексну сторінку зі списком всіх дисциплін"""
    try:
        data = load_yaml_data(yaml_file)
        validate_yaml_schema(data)

        metadata = data.get("metadata", {})
        disciplines = data.get("disciplines", {}) | data.get("elevative_disciplines", {})

        disciplines = prepare_disciplines_with_totals(disciplines)

        context = {
            "metadata": metadata,
            "disciplines": disciplines
        }

        html_content = render_template("index_template.html", context)
        save_html_file(html_content, output_file)

        logger.info("Index page created: %s", str(output_file))
        return True  # Успіх

    except Exception as e:
        logger.error("Failed to generate index page: %s", str(e))
        return False  # Не успіх
