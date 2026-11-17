#!/usr/bin/env python3
"""
Генератор сторінки співробітників кафедри (WP page id=181)
Читає teachers.yaml, рендерить через Jinja2-шаблон staff_page.html.j2
"""

import sys
import locale
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

# --- Налаштування ---
INPUT_YAML    = Path('teachers.yaml')
TEMPLATE_FILE = Path('staff_page.html.j2')
OUTPUT_HTML   = Path('staff_page.html')

CATEGORIES = [
    ('head',            '👨‍🏫 Завідувач кафедри'),
    ('professor',       '👩‍🔬 Професори'),
    ('docent',          '👨‍🏫 Доценти'),
    ('senior_lecturer', '👩‍🏫 Старші викладачі'),
    ('assistant',       '👩‍🏫 Асистенти'),
    ('staff',           '🧑‍💼 Навчально-допоміжний персонал'),
]

# Правильний алфавітний порядок для української мови
UA_ALPHA = 'АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ'
UA_ORDER = {ch: i for i, ch in enumerate(UA_ALPHA)}


def ua_sort_key(name: str) -> list:
    """Сортування за українським алфавітом по першому слову (прізвищу)."""
    surname = name.split()[0].upper()
    return [UA_ORDER.get(ch, 999) for ch in surname]


def slugify(teacher_id: str) -> str:
    """monastyrsky_ge -> monastyrsky"""
    return teacher_id.rsplit('_', 1)[0].replace('_', '-')


def profile_url(teacher: dict) -> str:
    return f'https://apd.ipt.kpi.ua/kafedra/stuff/{slugify(teacher["id"])}/'


def main():
    for path in (INPUT_YAML, TEMPLATE_FILE):
        if not path.exists():
            print(f'ERROR: {path} not found', file=sys.stderr)
            sys.exit(1)

    with open(INPUT_YAML, encoding='utf-8') as f:
        data = yaml.safe_load(f)

    teachers = data['teachers']

    # Групуємо по category
    titles = dict(CATEGORIES)
    groups = {cat: [] for cat in titles}
    for t in teachers:
        cat = t.get('category', 'staff')
        if cat in groups:
            groups[cat].append(t)
        else:
            print(f'WARNING: unknown category "{cat}" for {t["id"]}', file=sys.stderr)

    # Сортуємо за прізвищем по українському алфавіту
    for cat in groups:
        groups[cat].sort(key=lambda t: ua_sort_key(t['name']))

    # Jinja2
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_FILE.parent)),
        autoescape=select_autoescape(['html']),
    )
    env.globals['profile_url'] = profile_url
    template = env.get_template(TEMPLATE_FILE.name)

    html = template.render(groups=groups, titles=titles)

    OUTPUT_HTML.write_text(html, encoding='utf-8')
    print(f'Done -> {OUTPUT_HTML}')
    for cat, title in CATEGORIES:
        print(f'  {title}: {len(groups[cat])}')


if __name__ == '__main__':
    main()
