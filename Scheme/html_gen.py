# -*- coding: utf-8 -*-
"""
Генерація HTML сторінки з пре- та постреквізитами з JSON, який готує
prereq_extract.py.

Використання: python html_gen.py [year] [lang]
Приклад: python html_gen.py 2026 ua
Без аргументів - береться найновіший рік, для якого є data<рік>.py.
"""

import json
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from data_registry import discover_years

SCRIPT_DIR = Path(__file__).resolve().parent  # шляхи нижче рахуються
                                                 # від розташування самого
                                                 # скрипта, а не від того,
                                                 # звідки його запустили -
                                                 # інакше "python html_gen.py"
                                                 # з іншої теки або з IDE
                                                 # тихо не знаходить ані
                                                 # templates/, ані JSON

DEFAULT_LANG = "ua"
TEMPLATE_DIR = SCRIPT_DIR / "templates"
TEMPLATE_FILE = "template.html"
# CSS і JS раніше жили і тут, і всередині template.html одночасно
# (inline) - тепер лише тут; template.html підключає їх через
# <link>/<script src>, а generate_html() копіює обидва поруч з готовим
# HTML, у ту саму підпапку assets/, куди веде відносний шлях у шаблоні
STYLESHEET_FILE = SCRIPT_DIR / "styles2026.css"
SCRIPT_ASSET_FILE = SCRIPT_DIR / "rel-arrows.js"

UI_STRINGS = {
    "ua": {
        "page_title": "Пре- та постреквізити дисциплін",
        "semester_label": "Семестр",
        "prereq_label": "Пререквізити",
        "postreq_label": "Постреквізити",
        "none_label": "немає",
        "generated_note_template": "згенеровано з data{year}.py",
    },
    "en": {
        "page_title": "Course Prerequisites & Postrequisites",
        "semester_label": "Semester",
        "prereq_label": "Prerequisites",
        "postreq_label": "Postrequisites",
        "none_label": "none",
        "generated_note_template": "generated from data{year}.py",
    },
}


def generate_html(json_filename: Path, output_html: Path, lang: str, year: int,
                   template_dir: Path = TEMPLATE_DIR) -> None:
    with open(json_filename, "r", encoding="utf-8") as f:
        courses = json.load(f)

    courses_by_semester = {}
    for course in courses.values():
        courses_by_semester.setdefault(course["semester"], []).append(course)
    for sem in courses_by_semester:
        courses_by_semester[sem].sort(key=lambda c: c["name"])
    semesters = sorted(courses_by_semester.keys())

    strings = dict(UI_STRINGS.get(lang, UI_STRINGS[DEFAULT_LANG]))
    strings["generated_note"] = strings.pop("generated_note_template").format(year=year)

    env = Environment(loader=FileSystemLoader(str(template_dir)))
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

    # HTML посилається на "./assets/styles2026.css" і "./assets/rel-arrows.js"
    # відносними шляхами - копіюємо обидва саме в docs/assets/, а не в
    # корінь docs/, інакше посилання в браузері ведуть у нікуди
    assets_dir = output_html.parent / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    for asset in (STYLESHEET_FILE, SCRIPT_ASSET_FILE):
        if asset.exists():
            shutil.copy(asset, assets_dir / asset.name)

    print(f"[OK] HTML сторінка створена: {output_html}")
    print(f"[INFO] Всього дисциплін: {len(courses)}")


def default_year():
    years = discover_years()
    if not years:
        raise SystemExit("У поточній папці не знайдено жодного data<рік>.py")
    return years[-1]  # найновіший - а не захардкоджене число, яке з часом застаріє


def main() -> None:
    year = default_year()
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

    json_file = SCRIPT_DIR / f"prerequisites_{year}_{lang}.json"
    docs_dir = SCRIPT_DIR.parent / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    html_file = docs_dir / f"requisites_bachelor_{year}_{lang}.html"

    if not json_file.exists():
        print(f"Error: File '{json_file}' not found!")
        print(f"Спершу згенеруйте його: python prereq_extract.py {year} {lang}")
        sys.exit(1)

    if not TEMPLATE_DIR.exists():
        print(f"Error: Template directory '{TEMPLATE_DIR}' not found!")
        sys.exit(1)
    if not (TEMPLATE_DIR / TEMPLATE_FILE).exists():
        print(f"Error: Template file '{TEMPLATE_FILE}' not found in '{TEMPLATE_DIR}'!")
        sys.exit(1)


    generate_html(json_file, html_file, lang, year)
    print(f"Year: {year}, Language: {lang}")


if __name__ == "__main__":
    main()
