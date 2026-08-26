# -*- coding: utf-8 -*-
"""
Пошук дисциплін, що повторюються в кількох семестрах ПІДРЯД (напр.
"Математичний аналіз" у 1-2-3 семестрах), і згортання їх в один
"розтягнутий" блок — замість кількох однакових блоків, з'єднаних
непотрібною стрілкою "сам у себе".

Критерій злиття двох вузлів a (семестр n) і b (семестр n+1):
  1. однаковий "type";
  2. однаковий текст "ua" і "en" (після нормалізації пробілів/\\n);
  3. (ОПЦІОНАЛЬНО) існує ребро a -> b у EDGES (як підтвердження,
     що це справді "продовження");
  4. жоден з вузлів ланцюжка не входить у never_merge (config.NEVER_MERGE) -
     явний виняток, коли розтягування небажане навіть за виконання
     умов 1-2.

Якщо умову 3 вимкнути (через REQUIRE_EDGE_FOR_MERGE = False),
то зливаються ВСІ однакові дисципліни в сусідніх семестрах,
навіть без ребра-продовження.
"""
from collections import defaultdict

# ---- НАЛАШТУВАННЯ ----
REQUIRE_EDGE_FOR_MERGE = False  # True - потрібне ребро, False - зливати за назвою


def _normalize(text):
    return " ".join(text.split())


def build_merged_graph(disciplines, edges, never_merge=frozenset()):
    # ---- 1) знайти ребра-"продовження" (a у семестрі n -> b у n+1,
    #         однакові тип і текст) ----
    cont_next = {}   # src -> dst
    cont_prev = {}   # dst -> src

    edge_set = set(edges)

    for nid, info in disciplines.items():
        # Шукаємо кандидатів у наступному семестрі
        for other_id, other_info in disciplines.items():
            if (other_info["semester"] == info["semester"] + 1
                    and info["type"] == other_info["type"]
                    and _normalize(info["ua"]) == _normalize(other_info["ua"])
                    and _normalize(info["en"]) == _normalize(other_info["en"])):

                # Перевіряємо умову наявності ребра (якщо ввімкнено)
                if REQUIRE_EDGE_FOR_MERGE and (nid, other_id) not in edge_set:
                    continue

                cont_next[nid] = other_id
                cont_prev[other_id] = nid

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

    return node_info, new_edges, merge_map
