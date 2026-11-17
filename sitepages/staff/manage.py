#!/usr/bin/env python3
"""
sitepages/staff/manage.py — профілі викладачів і сторінка співробітників (/kafedra/stuff/).
Креденшіали — спільні з усім проєктом (.env у корені, core/config.py).

Команди:
    generate          Генерує HTML-профілі викладачів
    generate-staff    Генерує сторінку співробітників
    push              Пушить профілі на WordPress
    run-all           Генерує все + пушить все

Приклади:
    python manage.py generate
    python manage.py generate --id ponomarenko_sm
    python manage.py generate --output ./profiles
    python manage.py generate-staff
    python manage.py push
    python manage.py push --id ponomarenko_sm
    python manage.py push --staff
    python manage.py push --all
    python manage.py run-all
"""

import argparse
import re
import sys
from pathlib import Path

import requests
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
from core.config import WordPressConfig  # noqa: E402

# ── Константи ────────────────────────────────────────────────────────────────

WP_URL        = "https://apd.ipt.kpi.ua"
STAFF_PAGE_ID = 181

CATEGORIES = [
    ("head",            "👨‍🏫 Завідувач кафедри"),
    ("professor",       "👩‍🔬 Професори"),
    ("docent",          "👨‍🏫 Доценти"),
    ("senior_lecturer", "👩‍🏫 Старші викладачі"),
    ("assistant",       "👩‍🏫 Асистенти"),
    ("staff",           "🧑‍💼 Навчально-допоміжний персонал"),
]

UA_ALPHA = "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"
UA_ORDER = {ch: i for i, ch in enumerate(UA_ALPHA)}


# ── Спільні утиліти ───────────────────────────────────────────────────────────

def load_teachers(yaml_path: Path) -> list[dict]:
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("teachers", [])


def ua_sort_key(name: str) -> list:
    surname = name.split()[0].upper()
    return [UA_ORDER.get(ch, 999) for ch in surname]


def slugify(teacher_id: str) -> str:
    return teacher_id.rsplit("_", 1)[0].replace("_", "-")


def profile_url(teacher: dict) -> str:
    return f"https://apd.ipt.kpi.ua/kafedra/stuff/{slugify(teacher['id'])}/"


def wp_auth():
    return WordPressConfig().auth


def wp_push_page(page_id: int, html: str, label: str) -> bool:
    url = f"{WP_URL}/wp-json/wp/v2/pages/{page_id}"
    r = requests.post(url, auth=wp_auth(), json={"content": html})
    if r.ok:
        print(f"  ✓ {label} → {r.json().get('link')}")
        return True
    print(f"  ✗ {label} → HTTP {r.status_code}: {r.text[:200]}", file=sys.stderr)
    return False


# ── Генерація профілів ────────────────────────────────────────────────────────

def cmd_generate(args):
    yaml_path     = Path(args.yaml)
    template_path = Path(args.template)
    output_dir    = Path(args.output)

    for p, label in [(yaml_path, "YAML-файл"), (template_path, "Шаблон")]:
        if not p.exists():
            print(f"[ERROR] {label} не знайдено: {p}", file=sys.stderr)
            sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template(template_path.name)

    teachers = load_teachers(yaml_path)
    if not teachers:
        print("[WARNING] У YAML-файлі не знайдено жодного викладача.")
        return

    if args.id:
        teachers = [t for t in teachers if t.get("id") == args.id]
        if not teachers:
            print(f"[ERROR] Викладача з id='{args.id}' не знайдено.", file=sys.stderr)
            sys.exit(1)

    print(f"Генерація профілів у папку: {output_dir.resolve()}\n")
    for teacher in teachers:
        html = template.render(teacher=teacher)
        html = re.sub(r"\n{3,}", "\n\n", html)
        html = re.sub(r"^\s+$", "", html, flags=re.MULTILINE)
        out = output_dir / f"{teacher['id']}.html"
        out.write_text(html, encoding="utf-8")
        print(f"  ✓ {teacher['name']} → {out}")

    print(f"\nГотово! Згенеровано профілів: {len(teachers)}")


# ── Генерація сторінки співробітників ────────────────────────────────────────

def cmd_generate_staff(args):
    yaml_path     = Path(args.yaml)
    template_path = Path(args.staff_template)
    output_path   = Path(args.staff_output)

    for p in (yaml_path, template_path):
        if not p.exists():
            print(f"[ERROR] {p} не знайдено", file=sys.stderr)
            sys.exit(1)

    teachers = load_teachers(yaml_path)

    titles = dict(CATEGORIES)
    groups = {cat: [] for cat in titles}
    for t in teachers:
        cat = t.get("category", "staff")
        if cat in groups:
            groups[cat].append(t)
        else:
            print(f"[WARNING] невідома категорія '{cat}' для {t['id']}", file=sys.stderr)

    for cat in groups:
        groups[cat].sort(key=lambda t: ua_sort_key(t["name"]))

    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        autoescape=select_autoescape(["html"]),
    )
    env.globals["profile_url"] = profile_url
    template = env.get_template(template_path.name)

    html = template.render(groups=groups, titles=titles)
    output_path.write_text(html, encoding="utf-8")

    print(f"Done → {output_path}")
    for cat, title in CATEGORIES:
        print(f"  {title}: {len(groups[cat])}")


# ── Push на WordPress ─────────────────────────────────────────────────────────

def push_profiles(yaml_path: Path, profiles_dir: Path, teacher_id: str = None):
    teachers = load_teachers(yaml_path)
    if teacher_id:
        teachers = [t for t in teachers if t.get("id") == teacher_id]
        if not teachers:
            print(f"[ERROR] id='{teacher_id}' не знайдено в YAML", file=sys.stderr)
            sys.exit(1)

    ok = skip = fail = 0
    for t in teachers:
        tid     = t.get("id", "?")
        page_id = t.get("page_id")
        if not page_id:
            print(f"  — пропущено {tid} (немає page_id)")
            skip += 1
            continue

        html_path = profiles_dir / f"{tid}.html"
        if not html_path.exists():
            print(f"  — пропущено {tid} (немає {html_path})")
            skip += 1
            continue

        if wp_push_page(page_id, html_path.read_text(encoding="utf-8"), t.get("name", tid)):
            ok += 1
        else:
            fail += 1

    print(f"\nПрофілі: ✓{ok}  пропущено:{skip}  ✗{fail}")


def push_staff_page(staff_html: Path):
    if not staff_html.exists():
        print(f"[ERROR] {staff_html} не знайдено", file=sys.stderr)
        sys.exit(1)
    print(f"Пушу сторінку співробітників (id={STAFF_PAGE_ID})...")
    wp_push_page(STAFF_PAGE_ID, staff_html.read_text(encoding="utf-8"), "Співробітники")


def cmd_push(args):
    yaml_path    = Path(args.yaml)
    profiles_dir = Path(args.profiles_dir)
    staff_html   = Path(args.staff_output)

    if args.all:
        print("=== Профілі ===")
        push_profiles(yaml_path, profiles_dir)
        print("\n=== Сторінка співробітників ===")
        push_staff_page(staff_html)
    elif args.staff:
        push_staff_page(staff_html)
    elif args.id:
        print(f"=== Профіль: {args.id} ===")
        push_profiles(yaml_path, profiles_dir, args.id)
    else:
        print("=== Профілі ===")
        push_profiles(yaml_path, profiles_dir)


# ── run-all ───────────────────────────────────────────────────────────────────

def cmd_run_all(args):
    print("=== [1/3] Генерація профілів ===")
    cmd_generate(args)
    print("\n=== [2/3] Генерація сторінки співробітників ===")
    cmd_generate_staff(args)
    print("\n=== [3/3] Push на WordPress ===")
    args.all   = True
    args.staff = False
    args.id    = None
    cmd_push(args)


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    # Спільні аргументи для перевикористання
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--yaml",          default=str(HERE / "teachers.yaml"),
                        help="YAML-файл з базою даних (default: teachers.yaml)")
    shared.add_argument("--output",        default=str(HERE / "profiles"),
                        help="Папка для HTML-профілів (default: ./profiles)")
    shared.add_argument("--template",      default=str(HERE / "profile_template.html.j2"),
                        help="Jinja2-шаблон профілю (default: profile_template.html.j2)")
    shared.add_argument("--staff-template", default=str(HERE / "staff_page.html.j2"),
                        help="Jinja2-шаблон сторінки співробітників")
    shared.add_argument("--staff-output",  default=str(HERE / "staff_page.html"),
                        help="Вихідний HTML сторінки співробітників (default: staff_page.html)")
    shared.add_argument("--profiles-dir",  default=str(HERE / "profiles"),
                        help="Папка з HTML-профілями для push (default: ./profiles)")

    root = argparse.ArgumentParser(
        description="Інструмент керування сайтом кафедри",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = root.add_subparsers(dest="command", required=True)

    # generate
    p_gen = sub.add_parser("generate", parents=[shared],
                           help="Генерує HTML-профілі викладачів")
    p_gen.add_argument("--id", dest="id", default=None,
                       help="Генерувати лише профіль з вказаним id")
    p_gen.set_defaults(func=cmd_generate)

    # generate-staff
    p_gs = sub.add_parser("generate-staff", parents=[shared],
                          help="Генерує сторінку співробітників")
    p_gs.set_defaults(func=cmd_generate_staff)

    # push
    p_push = sub.add_parser("push", parents=[shared],
                             help="Пушить на WordPress")
    p_push.add_argument("--id", dest="id", default=None,
                        help="Пушити лише профіль з вказаним id")
    p_push.add_argument("--staff", action="store_true",
                        help="Пушити лише сторінку співробітників")
    p_push.add_argument("--all", action="store_true",
                        help="Пушити профілі + сторінку співробітників")
    p_push.set_defaults(func=cmd_push)

    # run-all
    p_all = sub.add_parser("run-all", parents=[shared],
                            help="Генерує все + пушить усе")
    p_all.set_defaults(func=cmd_run_all)

    return root


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
