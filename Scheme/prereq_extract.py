# -*- coding: utf-8 -*-
"""
Витягування пре- та постреквізитів напряму з data<рік>.py.

Стара версія (prepost_extract.py) спершу генерувала Graphviz .gv файл
(gen_gv.py), а тоді парсила його назад regex'ом, щоб дістати список
курсів і зв'язків. Це зайва й крихка ланка: .gv - лише текстове
представлення для картинки, і regex-парсер легко ламається на
екранованих символах, зміні формату fillcolor тощо. Ми вже маємо
структуровані дані в data<рік>.py (ті самі, що використовує
build_diagramm.py для діаграми) - беремо їх напряму, через
data_registry.py (той самий механізм вибору року, що й у
build_diagramm.py - жодного захардкодженого "data2026" тут більше
немає).

ВАЖЛИВО: тут НЕМАЄ логіки злиття дисциплін у розтягнуті блоки
(merge.py) - для таблиці пре/постреквізитів кожна дисципліна кожного
семестру лишається окремим записом зі своїми власними зв'язками.
Злиття - суто відображувальна річ для діаграми; тут вона би тільки
губила інформацію (саме тому одну дисципліну першого семестру, що є
пререквізитом для розтягнутої дисципліни другого семестру, тут видно
явно, а на діаграмі це лінія, намальована пунктиром).

Використання: python prereq_extract.py [year] [lang]
Приклад: python prereq_extract.py 2026 ua
Без аргументів - береться найновіший рік, для якого є data<рік>.py.
"""
import json
import sys
from pathlib import Path

import config as cfg
from data_registry import discover_years, load_year
import validate_data

SCRIPT_DIR = Path(__file__).resolve().parent  # вихідний JSON завжди поруч
                                                 # зі скриптом, незалежно
                                                 # від того, звідки його
                                                 # запустили - html_gen.py
                                                 # шукає його саме тут
DEFAULT_LANG = "ua"


def normalize(text):
    return " ".join(text.split())


def build_prerequisite_dict(disciplines: dict, edges: list, lang: str) -> dict:
    """Для кожної дисципліни - її власна назва, семестр, тип/колір і
    списки пре- та постреквізитів (з id та назвою обраною мовою)."""
    result = {}
    for cid, info in disciplines.items():
        result[cid] = {
            "id": cid,
            "name": normalize(info[lang]),
            "semester": info["semester"],
            "type": info["type"],
            "color": cfg.TYPE_FILL_COLOR.get(info["type"], "#CCCCCC"),
            "prerequisites": [],
            "postrequisites": [],
        }

    # дублікати ребер (якщо раптом є) не повинні давати дубльований
    # запис у списку пре-/постреквізитів однієї дисципліни
    seen = set()
    for a, b in edges:
        if (a, b) in seen:
            continue
        seen.add((a, b))
        # a - пререквізит для b; b - постреквізит для a
        result[b]["prerequisites"].append({"id": a, "name": result[a]["name"]})
        result[a]["postrequisites"].append({"id": b, "name": result[b]["name"]})

    for cid in result:
        result[cid]["prerequisites"].sort(key=lambda c: c["name"])
        result[cid]["postrequisites"].sort(key=lambda c: c["name"])

    return result


def default_year():
    years = discover_years()
    if not years:
        raise SystemExit("У поточній папці не знайдено жодного data<рік>.py")
    return years[-1]  # найновіший - а не захардкоджене число, яке з часом застаріє


def main():
    year = default_year()
    lang = DEFAULT_LANG

    if len(sys.argv) > 1:
        try:
            year = int(sys.argv[1])
        except ValueError:
            print("Error: Year must be a number")
            print("Usage: python prereq_extract.py [year] [lang]")
            print("Example: python prereq_extract.py 2026 ua")
            sys.exit(1)

    if len(sys.argv) > 2:
        lang = sys.argv[2].lower()
        if lang not in cfg.LANGUAGES:
            print(f"Error: Language must be one of {cfg.LANGUAGES}")
            sys.exit(1)

    # рік підвантажується ТУТ, після розбору argv - на відміну від
    # попередньої версії, де `from data2026 import ...` виконувався на
    # рівні модуля ще до того, як рік узагалі був відомий, і аргумент
    # року впливав лише на ІМ'Я вихідного файлу, а не на те, які дані
    # в нього насправді потрапляли (мовчки писало дані 2026-го під
    # будь-якою назвою року)
    DISCIPLINES, EDGES, _never_merge, _force_band = load_year(year)

    if validate_data.main(DISCIPLINES, EDGES) != 0:
        raise SystemExit(
            f"Дані data{year}.py не пройшли валідацію (validate_data.py) - "
            f"виправте помилки вище."
        )

    prerequisite_dict = build_prerequisite_dict(DISCIPLINES, EDGES, lang)

    print(f"Завантажено {len(DISCIPLINES)} курсів та {len(EDGES)} зв'язків (data{year}.py)\n")
    for i, course_id in enumerate(sorted(prerequisite_dict.keys())):
        if i >= 3:
            print("...")
            break
        info = prerequisite_dict[course_id]
        print(f"{course_id}:")
        print(f"  Назва: {info['name']}")
        pre = [p['name'] for p in info['prerequisites']]
        post = [p['name'] for p in info['postrequisites']]
        print(f"  Пререквізити ({len(pre)}): {pre}")
        print(f"  Постреквізити ({len(post)}): {post}")
        print()

    output_file = SCRIPT_DIR / f"prerequisites_{year}_{lang}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(prerequisite_dict, f, ensure_ascii=False, indent=2)

    print(f"[OK] Результат збережено в {output_file}")
    print(f"Year: {year}, Language: {lang}")


if __name__ == "__main__":
    main()
