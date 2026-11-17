#!/usr/bin/env python3
"""
generate_profiles.py
Генерує HTML-сторінки профілів викладачів з YAML-бази за допомогою Jinja2.

Використання:
    python generate_profiles.py                         # генерує всі профілі
    python generate_profiles.py --id ponomarenko_sm    # один профіль за id
    python generate_profiles.py --output ./profiles    # вказати вихідну папку
"""

import argparse
import re
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape


def load_teachers(yaml_path: Path) -> list[dict]:
    """Завантажує список викладачів з YAML-файлу."""
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("teachers", [])


def generate_profile(teacher: dict, template, output_dir: Path) -> Path:
    """Рендерить профіль одного викладача і зберігає HTML-файл."""
    html = template.render(teacher=teacher)
    html = re.sub(r'\n{3,}', '\n\n', html)       # більше 2 порожніх рядків → 1
    html = re.sub(r'^\s+$', '', html, flags=re.MULTILINE)  # рядки лише з пробілами → порожні
    filename = f"{teacher['id']}.html"
    output_path = output_dir / filename
    output_path.write_text(html, encoding="utf-8")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Генератор HTML-профілів викладачів з YAML + Jinja2"
    )
    parser.add_argument(
        "--yaml",
        default="teachers.yaml",
        help="Шлях до YAML-файлу з базою даних (default: teachers.yaml)",
    )
    parser.add_argument(
        "--template",
        default="profile_template.html.j2",
        help="Шлях до Jinja2-шаблону (default: profile_template.html.j2)",
    )
    parser.add_argument(
        "--output",
        default="profiles",
        help="Вихідна папка для HTML-файлів (default: ./profiles)",
    )
    parser.add_argument(
        "--id",
        dest="teacher_id",
        default=None,
        help="Генерувати лише профіль з вказаним id",
    )
    args = parser.parse_args()

    yaml_path = Path(args.yaml)
    template_path = Path(args.template)
    output_dir = Path(args.output)

    # Перевірка файлів
    if not yaml_path.exists():
        print(f"[ERROR] YAML-файл не знайдено: {yaml_path}", file=sys.stderr)
        sys.exit(1)
    if not template_path.exists():
        print(f"[ERROR] Шаблон не знайдено: {template_path}", file=sys.stderr)
        sys.exit(1)

    # Створення вихідної папки
    output_dir.mkdir(parents=True, exist_ok=True)

    # Завантаження Jinja2-середовища
    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template(template_path.name)

    # Завантаження викладачів
    teachers = load_teachers(yaml_path)
    if not teachers:
        print("[WARNING] У YAML-файлі не знайдено жодного викладача.")
        sys.exit(0)

    # Фільтрація за --id
    if args.teacher_id:
        teachers = [t for t in teachers if t.get("id") == args.teacher_id]
        if not teachers:
            print(f"[ERROR] Викладача з id='{args.teacher_id}' не знайдено.", file=sys.stderr)
            sys.exit(1)

    # Генерація профілів
    print(f"Генерація профілів у папку: {output_dir.resolve()}\n")
    for teacher in teachers:
        out_path = generate_profile(teacher, template, output_dir)
        print(f"  ✓ {teacher['name']} → {out_path}")

    print(f"\nГотово! Згенеровано профілів: {len(teachers)}")


if __name__ == "__main__":
    main()
