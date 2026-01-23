"""
Генерація HTML таблиці з пререквізитами
Використання: python html_gen.py [year]
Приклад: python html_gen.py 2025
"""

import json
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# ===== НАЛАШТУВАННЯ ЗА ЗАМОВЧУВАННЯМ =====
DEFAULT_YEAR = 2025
TEMPLATE_DIR = "templates"
TEMPLATE_FILE = "template.html"


def generate_html_table(
    json_filename: Path, output_html: str, template_dir: str = TEMPLATE_DIR
) -> None:
    """Генерація HTML таблиці з JSON файлу з пререквізитами"""

    # Читання JSON
    with open(json_filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Налаштування Jinja2
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(TEMPLATE_FILE)

    # Підготовка даних для шаблону
    context = {"courses": data, "total_courses": len(data)}

    # Рендеринг HTML
    html_content = template.render(context)

    # Збереження HTML
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[OK] HTML таблиця створена: {output_html}")
    print(f"[INFO] Всього дисциплін: {len(data)}")


def main() -> None:
    """Головна функція"""
    year = DEFAULT_YEAR

    if len(sys.argv) > 1:
        try:
            year = int(sys.argv[1])
        except ValueError:
            print("Error: Year must be a number")
            print("Usage: python html_gen.py [year]")
            print("Example: python html_gen.py 2025")
            sys.exit(1)

    # Формуємо імена файлів на основі року
    json_file = Path(f"prerequisites_{year}.json")

    # Вихід на один рівень вгору та збереження в папку docs
    docs_dir = Path("..") / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)  # Створюємо папку якщо не існує
    html_file = docs_dir / f"requisites_bachelor_{year}.html"

    # Перевіряємо чи існує JSON файл
    if not json_file.exists():
        print(f"Error: File '{json_file}' not found!")
        print(f"Make sure you have a prerequisites file for year {year}")
        sys.exit(1)

    # Перевіряємо чи існує директорія з шаблонами
    template_path = Path(TEMPLATE_DIR)
    if not template_path.exists():
        print(f"Error: Template directory '{TEMPLATE_DIR}' not found!")
        print("Creating template directory...")
        template_path.mkdir(parents=True)
        print(f"Please place '{TEMPLATE_FILE}' in the '{TEMPLATE_DIR}' directory")
        sys.exit(1)

    template_file_path = template_path / TEMPLATE_FILE
    if not template_file_path.exists():
        print(f"Error: Template file '{template_file_path}' not found!")
        print(f"Please place '{TEMPLATE_FILE}' in the '{TEMPLATE_DIR}' directory")
        sys.exit(1)

    # Генеруємо HTML
    generate_html_table(json_file, html_file)
    print(f"Year: {year}")


if __name__ == "__main__":
    main()
