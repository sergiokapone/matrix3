# -*- coding: utf-8 -*-
"""
Генерація HTML сторінки з пре- та постреквізитами з JSON, який готує
prereq_extract.py.

Використання: python html_gen.py [year] [lang]
Приклад: python html_gen.py 2026 ua
"""

import json
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

DEFAULT_YEAR = 2026
DEFAULT_LANG = "ua"
TEMPLATE_DIR = "templates"
TEMPLATE_FILE = "template.html"

UI_STRINGS = {
    "ua": {
        "page_title": "Пре- та постреквізити дисциплін",
        "semester_label": "Семестр",
        "prereq_label": "Пререквізити",
        "postreq_label": "Постреквізити",
        "none_label": "немає",
        "generated_note": "згенеровано з data2026.py",
    },
    "en": {
        "page_title": "Course Prerequisites & Postrequisites",
        "semester_label": "Semester",
        "prereq_label": "Prerequisites",
        "postreq_label": "Postrequisites",
        "none_label": "none",
        "generated_note": "generated from data2026.py",
    },
}


def generate_html(json_filename: Path, output_html: Path, lang: str,
                   template_dir: str = TEMPLATE_DIR) -> None:
    with open(json_filename, "r", encoding="utf-8") as f:
        courses = json.load(f)

    courses_by_semester = {}
    for course in courses.values():
        courses_by_semester.setdefault(course["semester"], []).append(course)
    for sem in courses_by_semester:
        courses_by_semester[sem].sort(key=lambda c: c["name"])
    semesters = sorted(courses_by_semester.keys())

    strings = UI_STRINGS.get(lang, UI_STRINGS[DEFAULT_LANG])

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(TEMPLATE_FILE)

    context = {
        "lang": lang,
        "total_courses": len(courses),
        "semesters": semesters,
        "courses_by_semester": courses_by_semester,
        **strings,
    }

    html_content = template.render(context)
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[OK] HTML сторінка створена: {output_html}")
    print(f"[INFO] Всього дисциплін: {len(courses)}")


def main() -> None:
    year = DEFAULT_YEAR
    lang = DEFAULT_LANG

    if len(sys.argv) > 1:
        try:
            year = int(sys.argv[1])
        except ValueError:
            print("Error: Year must be a number")
            print("Usage: python html_gen.py [year] [lang]")
            print("Example: python html_gen.py 2026 ua")
            sys.exit(1)

    if len(sys.argv) > 2:
        lang = sys.argv[2].lower()
        if lang not in UI_STRINGS:
            print(f"Error: Language must be one of {list(UI_STRINGS)}")
            sys.exit(1)

    json_file = Path(f"prerequisites_{year}_{lang}.json")
    docs_dir = Path("..") / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    html_file = docs_dir / f"requisites_bachelor_{year}_{lang}.html"

    if not json_file.exists():
        print(f"Error: File '{json_file}' not found!")
        print(f"Спершу згенеруйте його: python prereq_extract.py {year} {lang}")
        sys.exit(1)

    template_path = Path(TEMPLATE_DIR)
    if not template_path.exists():
        print(f"Error: Template directory '{TEMPLATE_DIR}' not found!")
        sys.exit(1)
    if not (template_path / TEMPLATE_FILE).exists():
        print(f"Error: Template file '{TEMPLATE_FILE}' not found in '{TEMPLATE_DIR}'!")
        sys.exit(1)

    generate_html(json_file, html_file, lang)
    print(f"Year: {year}, Language: {lang}")


if __name__ == "__main__":
    main()
