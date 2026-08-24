# -*- coding: utf-8 -*-
"""
Пошук дисциплін, що повторюються в кількох семестрах ПІДРЯД (напр.
"Математичний аналіз" у 1-2-3 семестрах), і згортання їх в один
"розтягнутий" блок — замість кількох однакових блоків, з'єднаних
непотрібною стрілкою "сам у себе".

Критерій злиття двох вузлів a (семестр n) і b (семестр n+1):
  1. однаковий "type";
  2. однаковий текст "ua" і "en" (після нормалізації пробілів/\\n);
  3. існує ребро a -> b у EDGES (тобто це справді "продовження",
     а не випадковий збіг назви);
  4. жоден з вузлів ланцюжка не входить у never_merge (config.NEVER_MERGE) -
     явний виняток, коли розтягування небажане навіть за виконання
     умов 1-3 (напр. якщо хочеться бачити Алгебру окремим блоком у
     кожному семестрі). Досить вказати ОДИН id з ланцюжка - виняток
     стосується всього ланцюжка цілком, не розриває його посередині.

Ланцюжки такого виду можуть бути довільної довжини (наприклад,
3 семестри підряд) — вони згортаються в ОДИН блок, що охоплює весь
діапазон від першого до останнього семестру.

Результат — уніфікований опис вузлів (як "звичайних", так і
"розтягнутих") з полями semester_start/semester_end, та список ребер,
де посилання на злиті вузли замінені на id об'єднаного блоку.
Далі з цим працює layout.py, не знаючи взагалі, що якісь вузли
колись були кількома окремими записами.
"""
from collections import defaultdict


def _normalize(text):
    return " ".join(text.split())


def build_merged_graph(disciplines, edges, never_merge=frozenset()):
    # ---- 1) знайти ребра-"продовження" (a у семестрі n -> b у n+1,
    #         однакові тип і текст) ----
    cont_next = {}   # src -> dst
    cont_prev = {}   # dst -> src
    for a, b in edges:
        da, db = disciplines[a], disciplines[b]
        if (da["type"] == db["type"]
                and _normalize(da["ua"]) == _normalize(db["ua"])
                and _normalize(da["en"]) == _normalize(db["en"])
                and db["semester"] == da["semester"] + 1):
            cont_next[a] = b
            cont_prev[b] = a

    # ---- 2) зібрати ланцюжки: починаємо з вузлів, які самі не є
    #         "продовженням" когось іншого, і йдемо вперед ----
    chains = []
    for nid in disciplines:
        if nid in cont_prev:
            continue
        if nid in cont_next:
            chain = [nid]
            cur = nid
            while cur in cont_next:
                cur = cont_next[cur]
                chain.append(cur)
            chains.append(chain)

    # виняток: якщо хоч один id ланцюжка позначений як "ніколи не
    # зливати" - весь ланцюжок лишається розсипаним на окремі вузли
    chains = [chain for chain in chains if not (never_merge & set(chain))]

    # ---- 3) побудувати уніфіковані вузли ----
    merge_map = {}   # оригінальний id -> id об'єднаного блоку
    node_info = {}
    consumed_edges = set()  # ребра-"продовження", які більше не малюємо

    for chain in chains:
        merged_id = "MERGE_" + chain[0]
        first, last = disciplines[chain[0]], disciplines[chain[-1]]
        node_info[merged_id] = {
            "semester_start": first["semester"],
            "semester_end": last["semester"],
            "type": first["type"],
            "ua": _normalize(first["ua"]),
            "en": _normalize(first["en"]),
            "orig_ids": chain,
        }
        for nid in chain:
            merge_map[nid] = merged_id
        for i in range(len(chain) - 1):
            consumed_edges.add((chain[i], chain[i + 1]))

    for nid, info in disciplines.items():
        if nid in merge_map:
            continue
        node_info[nid] = {
            "semester_start": info["semester"],
            "semester_end": info["semester"],
            "type": info["type"],
            "ua": _normalize(info["ua"]),
            "en": _normalize(info["en"]),
            "orig_ids": [nid],
        }

    # ---- 4) перебудувати ребра: пропустити "продовження", інші -
    #         перенаправити на об'єднані id, прибрати дублікати й
    #         самопетлі (якщо обидва кінці звелись до одного блоку) ----
    new_edges = []
    seen = set()
    for a, b in edges:
        if (a, b) in consumed_edges:
            continue
        na, nb = merge_map.get(a, a), merge_map.get(b, b)
        if na == nb:
            continue
        if (na, nb) in seen:
            continue
        seen.add((na, nb))
        new_edges.append((na, nb))

    return node_info, new_edges
