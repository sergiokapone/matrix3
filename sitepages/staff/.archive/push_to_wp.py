#!/usr/bin/env python3
"""
push_to_wp.py
Пушить згенеровані HTML-профілі викладачів та/або сторінку співробітників
на сайт кафедри через WP REST API.

Використання:
    python push_to_wp.py                        # пушить всі профілі з ./profiles/
    python push_to_wp.py --id ponomarenko_sm    # один профіль
    python push_to_wp.py --staff                # тільки сторінку співробітників (id=181)
    python push_to_wp.py --all                  # профілі + сторінка співробітників
"""

import argparse
import os
import sys
from pathlib import Path

import requests
import yaml
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

WP_URL      = "https://apd.ipt.kpi.ua"
WP_USER     = os.getenv("WP_USER")
WP_PASS     = os.getenv("WP_PASS")
STAFF_PAGE_ID = 181
STAFF_HTML  = Path("staff_page.html")
PROFILES_DIR = Path("profiles")
YAML_FILE   = Path("teachers.yaml")


def auth():
    if not WP_USER or not WP_PASS:
        print("[ERROR] WP_USER або WP_PASS не задані в .env", file=sys.stderr)
        sys.exit(1)
    return HTTPBasicAuth(WP_USER, WP_PASS)


def push_page(page_id: int, html: str, label: str) -> bool:
    url = f"{WP_URL}/wp-json/wp/v2/pages/{page_id}"
    r = requests.post(url, auth=auth(), json={"content": html})
    if r.ok:
        print(f"  ✓ {label} → {r.json().get('link')}")
        return True
    else:
        print(f"  ✗ {label} → HTTP {r.status_code}: {r.text[:200]}", file=sys.stderr)
        return False


def load_teachers() -> list[dict]:
    if not YAML_FILE.exists():
        print(f"[ERROR] {YAML_FILE} не знайдено", file=sys.stderr)
        sys.exit(1)
    with open(YAML_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f).get("teachers", [])


def push_profiles(teacher_id: str = None):
    teachers = load_teachers()
    if teacher_id:
        teachers = [t for t in teachers if t.get("id") == teacher_id]
        if not teachers:
            print(f"[ERROR] id='{teacher_id}' не знайдено в YAML", file=sys.stderr)
            sys.exit(1)

    ok = skip = fail = 0
    for t in teachers:
        tid = t.get("id", "?")
        page_id = t.get("page_id")
        if not page_id:
            print(f"  — пропущено {tid} (немає page_id)")
            skip += 1
            continue

        html_path = PROFILES_DIR / f"{tid}.html"
        if not html_path.exists():
            print(f"  — пропущено {tid} (немає {html_path})")
            skip += 1
            continue

        html = html_path.read_text(encoding="utf-8")
        if push_page(page_id, html, t.get("name", tid)):
            ok += 1
        else:
            fail += 1

    print(f"\nПрофілі: ✓{ok}  пропущено:{skip}  ✗{fail}")


def push_staff():
    if not STAFF_HTML.exists():
        print(f"[ERROR] {STAFF_HTML} не знайдено", file=sys.stderr)
        sys.exit(1)
    html = STAFF_HTML.read_text(encoding="utf-8")
    print(f"Пушу сторінку співробітників (id={STAFF_PAGE_ID})...")
    push_page(STAFF_PAGE_ID, html, "Співробітники")


def main():
    parser = argparse.ArgumentParser(description="WP pusher для сайту кафедри")
    parser.add_argument("--id", dest="teacher_id", default=None,
                        help="Пушити лише профіль з вказаним id")
    parser.add_argument("--staff", action="store_true",
                        help="Пушити сторінку співробітників (id=181)")
    parser.add_argument("--all", action="store_true",
                        help="Пушити профілі + сторінку співробітників")
    parser.add_argument("--profiles-dir", default="profiles",
                        help="Папка з HTML-профілями (default: ./profiles)")
    args = parser.parse_args()

    global PROFILES_DIR
    PROFILES_DIR = Path(args.profiles_dir)

    if args.all:
        print("=== Профілі ===")
        push_profiles()
        print("\n=== Сторінка співробітників ===")
        push_staff()
    elif args.staff:
        push_staff()
    elif args.teacher_id:
        print(f"=== Профіль: {args.teacher_id} ===")
        push_profiles(args.teacher_id)
    else:
        # За замовчуванням — всі профілі
        print("=== Профілі ===")
        push_profiles()


if __name__ == "__main__":
    main()
