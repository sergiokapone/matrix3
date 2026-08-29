# -*- coding: utf-8 -*-
"""
Валідатор data<рік>.py (за замовчуванням - усі знайдені, або конкретний
рік аргументом: python validate_data.py 2026). Ловить автоматично те, що
раніше доводилось шукати вручну по скріншотах:

  1. Побите посилання в EDGES (id, якого немає в DISCIPLINES).
  2. Дублікати ребер.
  3. "Мовчазний розрив ланцюжка": дві дисципліни з однаковим
     (type, ua, en) стоять у СУСІДНІХ семестрах, але ребра між ними
     немає — тому merge.py їх не зʼєднає, хоча текст натякає, що
     мало б.
  4. "Ребро перестрибує семестр": дві дисципліни з однаковим текстом
     зʼєднані ребром, але їхні семестри відрізняються більш ніж на 1
     (напр. n -> n+2) — ланцюжок злиття розірветься на цьому місці.
  5. Цикли в графі пререквізитів (граф має бути DAG - дисципліна не
     може бути передумовою сама для себе транзитивно).
  6. Ребра між двома вузлами, які злиються в "розтягнуті" блоки
     (wide-to-wide) - це НЕ помилка (такі ребра свідомо лишаються в
     даних для таблиці пре/постреквізитів), але варто показати
     список, щоб було видно, що саме буде намальовано пунктиром.

Запуск: python validate_data.py
Код виходу: 0 - лише попередження (або взагалі нічого), 1 - є
структурні помилки (biti посилання/дублікати/цикли), які ламають
подальшу побудову.
"""
import sys
from collections import defaultdict


def normalize(text):
    return " ".join(text.split())


def check_broken_refs(disciplines, edges):
    errors = []
    for a, b in edges:
        if a not in disciplines:
            errors.append(f"ребро {a!r} -> {b!r}: {a!r} немає в DISCIPLINES")
        if b not in disciplines:
            errors.append(f"ребро {a!r} -> {b!r}: {b!r} немає в DISCIPLINES")
    return errors


def check_duplicate_edges(edges):
    seen = set()
    dups = []
    for e in edges:
        if e in seen:
            dups.append(e)
        seen.add(e)
    return dups


def check_broken_chains(disciplines, edges):
    """Класи 3 і 4: групуємо дисципліни за (type, ua, en) і дивимось,
    чи всі сусідні за семестром пари з'єднані ребром n -> n+1."""
    edge_set = set(edges)
    groups = defaultdict(list)  # (type, ua, en) -> [id, ...]
    for nid, info in disciplines.items():
        key = (info["type"], normalize(info["ua"]), normalize(info["en"]))
        groups[key].append(nid)

    silent_gaps = []     # клас 3
    semester_skips = []  # клас 4

    for key, ids in groups.items():
        if len(ids) < 2:
            continue
        ids_sorted = sorted(ids, key=lambda i: disciplines[i]["semester"])
        for i in range(len(ids_sorted) - 1):
            a, b = ids_sorted[i], ids_sorted[i + 1]
            sa, sb = disciplines[a]["semester"], disciplines[b]["semester"]
            has_edge = (a, b) in edge_set
            if sb == sa + 1 and not has_edge:
                silent_gaps.append((a, b, key))
            elif sb > sa + 1 and has_edge:
                semester_skips.append((a, b, sa, sb, key))
            elif sb > sa + 1 and not has_edge:
                # не послідовні і без ребра - не ланцюжок, нормально
                pass
    return silent_gaps, semester_skips


def check_cycles(edges):
    """Пошук циклів у графі пререквізитів (має бути DAG)."""
    graph = defaultdict(list)
    for a, b in edges:
        graph[a].append(b)

    WHITE, GRAY, BLACK = 0, 1, 2
    color = defaultdict(int)
    cycles = []

    def dfs(u, path):
        color[u] = GRAY
        path.append(u)
        for v in graph[u]:
            if color[v] == GRAY:
                i = path.index(v)
                cycles.append(path[i:] + [v])
            elif color[v] == WHITE:
                dfs(v, path)
        path.pop()
        color[u] = BLACK

    for node in list(graph.keys()):
        if color[node] == WHITE:
            dfs(node, [])
    return cycles


def find_wide_to_wide(disciplines, edges):
    """Клас 6: інформаційний список, не помилка. Не враховує самі
    ребра-продовження (a -> наступний у тому самому ланцюжку) - вони
    "з'їдаються" при злитті і взагалі не малюються окремою лінією;
    цікаві саме ребра МІЖ РІЗНИМИ розтягнутими блоками."""
    edge_set = set(edges)
    groups = defaultdict(list)
    for nid, info in disciplines.items():
        key = (info["type"], normalize(info["ua"]), normalize(info["en"]))
        groups[key].append(nid)

    wide_members = set()
    internal_edges = set()  # самі ребра-продовження всередині ланцюжків
    for key, ids in groups.items():
        if len(ids) < 2:
            continue
        ids_sorted = sorted(ids, key=lambda i: disciplines[i]["semester"])
        sems = [disciplines[i]["semester"] for i in ids_sorted]
        chained = all(
            sems[i + 1] == sems[i] + 1 and (ids_sorted[i], ids_sorted[i + 1]) in edge_set
            for i in range(len(ids_sorted) - 1)
        )
        if chained:
            wide_members.update(ids_sorted)
            for i in range(len(ids_sorted) - 1):
                internal_edges.add((ids_sorted[i], ids_sorted[i + 1]))

    result = []
    for a, b in edges:
        if a in wide_members and b in wide_members and (a, b) not in internal_edges:
            result.append((a, b))
    return result


def main(disciplines=None, edges=None):
    """disciplines/edges не задані - для запуску як окремого скрипта
    (python3 validate_data.py [рік]) підвантажуємо через data_registry;
    коли викликається з build_diagramm.py - дані вже передані напряму,
    без жодного імпорту конкретного data<рік>.py тут."""
    if disciplines is None or edges is None:
        from data_registry import load_year, resolve_requested_years
        year = resolve_requested_years(sys.argv[1:])[0]
        disciplines, edges, _never_merge, _force_band = load_year(year)

    errors = []
    warnings = []

    errors += check_broken_refs(disciplines, edges)
    dups = check_duplicate_edges(edges)
    if dups:
        errors += [f"дублікат ребра: {e}" for e in dups]

    if not errors:
        silent_gaps, semester_skips = check_broken_chains(disciplines, edges)
        for a, b, key in silent_gaps:
            warnings.append(
                f"'{key[1]}' [{a}] (сем.{disciplines[a]['semester']}) і [{b}] "
                f"(сем.{disciplines[b]['semester']}) - однаковий текст, сусідні "
                f"семестри, але немає ребра {a}->{b}. Блок НЕ розтягнеться."
            )
        for a, b, sa, sb, key in semester_skips:
            warnings.append(
                f"'{key[1]}' ребро {a}(сем.{sa}) -> {b}(сем.{sb}) перестрибує "
                f"{sb - sa - 1} семестр(и). Ланцюжок злиття розірветься тут."
            )

        cycles = check_cycles(edges)
        for c in cycles:
            errors.append("цикл у пререквізитах: " + " -> ".join(c))

        wide_pairs = find_wide_to_wide(disciplines, edges)
        if wide_pairs:
            warnings.append(
                f"{len(wide_pairs)} ребро(а) з'єднують два розтягнутих блоки "
                f"(намальовані пунктиром): "
                + ", ".join(f"{a}->{b}" for a, b in wide_pairs)
            )

    if errors:
        print(f"ПОМИЛКИ ({len(errors)}):")
        for e in errors:
            print(f"  ✗ {e}")
    if warnings:
        print(f"\nПопередження ({len(warnings)}):")
        for w in warnings:
            print(f"  ⚠ {w}")
    if not errors and not warnings:
        print("Все чисто: жодних помилок чи попереджень.")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
