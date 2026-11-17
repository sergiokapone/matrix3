#!/usr/bin/env python3
"""
migrate2_degree.py
Розбиває поле degree на degree + academic_title,
прибирає methodical_materials → замінює на ela_author.
"""

import re
import sys
from pathlib import Path
import yaml

# Порядок важливий: довші фрази раніше щоб не перекривались
ACADEMIC_TITLES = [
    'академік НАН України',
    'член-кореспондент НАН України',
    'старший науковий співробітник',
    'провідний науковий співробітник',
    'молодший науковий співробітник',
    'старший дослідник',
    'старший викладач',
    'професор',
    'доцент',
    'асистент',
]

# Посади які йдуть в degree якщо ступеня нема
POSITIONS_AS_DEGREE = [
    'Фахівець',
    'Завідувач',
    'Провідний інженер',
]

DEGREE_RE = re.compile(
    r'^(Доктор філософії[^(,]*(?:\([^)]*\))?'
    r'|Доктор [^,]+'
    r'|Кандидат [^,(]+(?:\([^)]*\))?)'
)


def split_degree(raw: str):
    """Повертає (degree, academic_title, extra)."""
    raw = raw.strip()

    # Спочатку витягуємо ступінь з початку рядка (може містити дужки)
    m = DEGREE_RE.match(raw)
    degree = m.group(1).strip() if m else None
    remainder = raw[m.end():].lstrip(', ') if m else raw

    # Решта — розбиваємо по комі
    parts = [p.strip() for p in remainder.split(',') if p.strip()]

    titles = []
    extra = []
    for part in parts:
        low = part.lower()
        matched = next((t for t in ACADEMIC_TITLES if t in low), None)
        if matched:
            titles.append(part)
        else:
            extra.append(part)

    # Якщо ступеня нема але є тільки звання — переносимо в degree
    if not degree and not extra and titles:
        degree = ', '.join(titles)
        titles = []

    # Якщо ступеня нема і є extra — кидаємо в degree
    if degree is None and extra:
        degree = ', '.join(extra)
        extra = []

    return degree, titles, extra


def migrate(src: Path, dst: Path):
    with open(src, encoding='utf-8') as f:
        data = yaml.safe_load(f)

    teachers = data['teachers']

    for t in teachers:
        raw = t.get('degree', '')
        degree, titles, extra = split_degree(raw)

        t['degree'] = degree or ''
        t['academic_title'] = titles  # список

        # extra — наприклад "завідувач кафедри" у Монастирського — лишаємо в position якщо position порожній
        if extra and not t.get('position'):
            t['position'] = ', '.join(extra)

        # methodical_materials → ela_author (ім'я для shortcode)
        if 'methodical_materials' in t:
            del t['methodical_materials']
        # ela_author = прізвище та ініціали для [kpi_author_works]
        # залишаємо повне ім'я — адмін підправить якщо треба інший формат
        t['ela_author'] = t['name']

    with open(dst, 'w', encoding='utf-8') as f:
        yaml.dump(
            {'teachers': teachers},
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
            width=120,
        )
    print(f'Записано: {dst}')


if __name__ == '__main__':
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('teachers_normalized.yaml')
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('teachers_normalized.yaml')
    migrate(src, dst)
