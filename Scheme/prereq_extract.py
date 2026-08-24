# -*- coding: utf-8 -*-
"""
Витягування пре- та постреквізитів напряму з data2026.py.

Стара версія (prepost_extract.py) спершу генерувала Graphviz .gv файл
(gen_gv.py), а тоді парсила його назад regex'ом, щоб дістати список
курсів і зв'язків. Це зайва й крихка ланка: .gv - лише текстове
представлення для картинки, і regex-парсер легко ламається на
екранованих символах, зміні формату fillcolor тощо. Ми вже маємо
структуровані дані в data2026.py (ті самі, що використовує
build_matplotlib.py для діаграми) - беремо їх напряму.

ВАЖЛИВО: тут НЕМАЄ логіки злиття дисциплін у розтягнуті блоки
(merge.py) - для таблиці пре/постреквізитів кожна дисципліна кожного
семестру лишається окремим записом зі своїми власними зв'язками.
Злиття - суто відображувальна річ для діаграми; тут вона би тільки
губила інформацію (саме тому одну дисципліну першого семестру, що є
пререквізитом для розтягнутої дисципліни другого семестру, тут видно
явно, а на діаграмі це лінія, намальована пунктиром).

Використання: python prereq_extract.py [year] [lang]
Приклад: python prereq_extract.py 2026 ua
"""
import json
import sys
from collections import defaultdict

import config as cfg
from data2026 import DISCIPLINES, EDGES

DEFAULT_YEAR = 2026
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

    for a, b in edges:
        # a - пререквізит для b; b - постреквізит для a
        result[b]["prerequisites"].append({"id": a, "name": result[a]["name"]})
        result[a]["postrequisites"].append({"id": b, "name": result[b]["name"]})

    for cid in result:
        result[cid]["prerequisites"].sort(key=lambda c: c["name"])
        result[cid]["postrequisites"].sort(key=lambda c: c["name"])

    return result


def main():
    year = DEFAULT_YEAR
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

    prerequisite_dict = build_prerequisite_dict(DISCIPLINES, EDGES, lang)

    print(f"Завантажено {len(DISCIPLINES)} курсів та {len(EDGES)} зв'язків\n")
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

    output_file = f"prerequisites_{year}_{lang}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(prerequisite_dict, f, ensure_ascii=False, indent=2)

    print(f"[OK] Результат збережено в {output_file}")
    print(f"Year: {year}, Language: {lang}")


if __name__ == "__main__":
    main()
