# -*- coding: utf-8 -*-
"""
Логіка розкладки й маршрутизації ребер — без matplotlib, без даних
навчального плану, без мовних підписів.

Приймає уніфікований опис вузлів node_info (id -> {"semester_start",
"semester_end", "type", "ua", "en", ...}, див. merge.py) та edges
(список пар (src_id, dst_id)), повертає геометрію, готову для рендеру.

Розкладка:
  * колонка = семестр, у порядку зростання;
  * "звичайний" вузол (semester_start == semester_end) займає один
    рядок у своїй колонці, у порядку появи в node_info;
  * "розтягнутий" вузол (semester_start < semester_end, тобто
    дисципліна, що триває кілька семестрів підряд — див. merge.py)
    малюється як одна широка смуга зверху, над звичайною сіткою, і
    займає всі колонки свого діапазону. Якщо таких смуг кілька і
    їхні діапазони семестрів перетинаються, вони автоматично
    розкладаються по різних рівнях (band-rows) методом розфарбування
    інтервалів (interval graph coloring) — це узагальнення старого
    підходу з фіксованими BAND_ROWS=2 на довільну кількість і
    довжину розтягнутих блоків.

Маршрутизація ребер (щоб лінії не ховались за чужими блоками і не
розповзались хаотично) — за мотивами того, як реально працює Graphviz
(`dot`): не пошук найкоротшого шляху для кожного ребра окремо, а
СПІЛЬНЕ пакування споріднених ребер у сусідні "смуги", щоб вони йшли
одним тугим джгутом і розходились лише біля самої цілі. Механізм:

  * ребра, що перестрибують ≥2 колонки, отримують один спільний
    горизонтальний рівень ("стовбур") на весь проміжний шлях;
  * ребра, що з'єднують сусідні колонки (і самі "заходи"/"виходи"
    стовбурних ребер у межах одного коридору), отримують вертикальний
    "перетин" — конкретну x-позицію всередині коридору;
  * в обох випадках позиція обирається ОДНІЄЮ й тією самою функцією
    pack_lanes: ребра сортуються за barycenter (середньою координатою
    їхніх кінців), і кожне отримує найближчу вільну смугу, причому
    смуга може бути перевикористана іншим ребром, якщо їхні діапазони
    (по колонках - для стовбура, по y - для перетину) не перетинаються.
    Це і дає ефект "спорідненi ребра йдуть поруч".

Якщо для якогось ребра (рідкісний край) не вдається підібрати вільну
смугу geometрично - є аварійний резерв: повний пошук шляху (Дейкстра)
по сітці коридор×канал, як було раніше, але тепер лише як fallback.
"""
from collections import defaultdict
import heapq
import numpy as np


def compute_layout(node_info, edges, cfg, forced_bands=None):
    # ---- орієнтація визначається ЗАЗДАЛЕГІДЬ: блок завжди фізично
    #      BOX_W x BOX_H (не обертається), тому крок сітки вздовж
    #      "осі семестрів" (u) і "осі елементів у семестрі" (v) мають
    #      спиратись на ту сторону блоку, яка після повороту (у кінці
    #      функції) стане відповідною фізичною віссю:
    #      vertical:   u -> x (потрібна ширина блоку BOX_W), v -> y (BOX_H)
    #      horizontal: u -> y (потрібна ширина блоку по y це BOX_H),
    #                  v -> x (потрібна ширина блоку по x це BOX_W)
    orientation = getattr(cfg, "ORIENTATION", "vertical")
    if orientation == "horizontal":
        U_SIZE, V_SIZE = cfg.BOX_H, cfg.BOX_W
    else:
        U_SIZE, V_SIZE = cfg.BOX_W, cfg.BOX_H
    U_STEP = U_SIZE + cfg.COL_GAP
    V_STEP = V_SIZE + cfg.ROW_GAP

    normal_ids = [nid for nid, info in node_info.items()
                  if info["semester_start"] == info["semester_end"]]
    wide_ids = [nid for nid, info in node_info.items()
                if info["semester_start"] != info["semester_end"]]

    # ---- індекс колонок за номерами семестрів ----
    all_sems = set()
    for info in node_info.values():
        all_sems.add(info["semester_start"])
        all_sems.add(info["semester_end"])
    semesters = sorted(all_sems)
    col_of_sem = {s: i for i, s in enumerate(semesters)}
    max_idx = len(semesters) - 1

    def col_x(idx):
        return idx * U_STEP

    def row_y(r):
        return -r * V_STEP

    # ---- єдине розміщення по рядках: розтягнутий вузол - це просто
    #      один рядок, як і звичайний, тільки той самий номер рядка
    #      резервується в усіх колонках, які він охоплює. Порядок
    #      визначається порядком появи в data2026.py (через node_info,
    #      який успадковує цей порядок від merge.py) - ніякого окремого
    #      "поверху зверху для розтягнутих": хочеш іншого порядку -
    #      перестав рядки в даних, або постав config.FORCE_BAND.
    rank_of = {nid: i for i, nid in enumerate(node_info)}
    home_col = {}       # nid -> індекс колонки, де вузол "вперше" з'являється
    span_end_col = {}    # nid -> індекс колонки, де вузол востаннє видно
    for nid, info in node_info.items():
        home_col[nid] = col_of_sem[info["semester_start"]]
        span_end_col[nid] = col_of_sem[info["semester_end"]]

    forced_rows = forced_bands or {}

    home_in_col = defaultdict(list)
    for nid in node_info:
        home_in_col[home_col[nid]].append(nid)
    for idx in home_in_col:
        home_in_col[idx].sort(key=lambda n: rank_of[n])

    row_of = {}
    occupied = defaultdict(set)  # idx -> зайняті рядки ("проїзні" розтягнуті блоки)
    for idx in range(max_idx + 1):
        for nid in home_in_col.get(idx, []):
            if nid in forced_rows:
                r = forced_rows[nid]
            else:
                r = 0
                while r in occupied[idx]:
                    r += 1
            row_of[nid] = r
            occupied[idx].add(r)
            for future_idx in range(idx + 1, span_end_col[nid] + 1):
                occupied[future_idx].add(r)

    # ---- координати ----
    pos = {}            # nid -> (x, y, w, h)
    col_extent = {}       # idx -> (x, y_top, y_bottom)
    col_x_of_idx = {}
    visible_in_col = defaultdict(list)  # idx -> [nid, ...] (домашні + "проїзні")
    for nid in node_info:
        for idx in range(home_col[nid], span_end_col[nid] + 1):
            visible_in_col[idx].append(nid)

    for idx in range(max_idx + 1):
        x = col_x(idx)
        col_x_of_idx[idx] = x
        rows_here = [row_of[nid] for nid in visible_in_col.get(idx, [])]
        if rows_here:
            y_top = row_y(min(rows_here)) + V_SIZE / 2
            y_bottom = row_y(max(rows_here)) - V_SIZE / 2
        else:
            y_top = V_SIZE / 2
            y_bottom = y_top - V_SIZE
        col_extent[idx] = (x, y_top, y_bottom)

    for nid, info in node_info.items():
        s_idx, e_idx = home_col[nid], span_end_col[nid]
        y = row_y(row_of[nid])
        if s_idx == e_idx:
            pos[nid] = (col_x(s_idx), y, U_SIZE, V_SIZE)
        else:
            x = (col_x(s_idx) + col_x(e_idx)) / 2
            w = (col_x(e_idx) - col_x(s_idx)) + U_SIZE
            pos[nid] = (x, y, w, V_SIZE)

    # ---- індекс колонки для кожного вузла (для маршрутизації: скільки
    #      коридорів перестрибує ребро) ----
    node_col_start = home_col
    node_col_end = span_end_col

    # ---- перешкоди (усі блоки, звичайні й розтягнуті, трохи "роздуті") ----
    obstacles = {}
    for nid, (x, y, w, h) in pos.items():
        obstacles[nid] = (x - w / 2 - cfg.OBST_PAD, x + w / 2 + cfg.OBST_PAD,
                           y - h / 2 - cfg.OBST_PAD, y + h / 2 + cfg.OBST_PAD)

    # ---- координати коридорів (між колонками) і каналів (між рядками) ----
    corridors = sorted(col_x_of_idx[i] + U_STEP / 2 for i in range(max_idx))
    # найбільший зайнятий номер рядка по всіх колонках (row_of уже враховує
    # і звичайні, і розтягнуті блоки, і forced_bands - рахований вище)
    max_rows = max(row_of.values(), default=0)
    band_rows_count = max_rows + 1
    channels = sorted(row_y(k) + V_STEP / 2 for k in range(-1, max_rows + 2))

    def corridor_after(x):
        cands = [c for c in corridors if c > x + cfg.EPS]
        return min(cands) if cands else None

    def corridor_before(x):
        cands = [c for c in corridors if c < x - cfg.EPS]
        return max(cands) if cands else None

    def nearest_channels(y_target, y_lo=None, y_hi=None):
        """Канали, відсортовані за близькістю до y_target. Якщо задано
        y_lo/y_hi - спершу канали в цьому діапазоні, потім решта."""
        if y_lo is not None and y_hi is not None:
            inside = [c for c in channels if y_lo - cfg.EPS <= c <= y_hi + cfg.EPS]
            outside = [c for c in channels if c not in inside]
            inside.sort(key=lambda c: abs(c - y_target))
            outside.sort(key=lambda c: abs(c - y_target))
            return inside + outside
        return sorted(channels, key=lambda c: abs(c - y_target))

    def seg_free(seg, exclude):
        kind = seg[0]
        for node, (xmn, xmx, ymn, ymx) in obstacles.items():
            if node in exclude:
                continue
            if kind == 'h':
                _, y, xa, xb = seg
                lo, hi = min(xa, xb), max(xa, xb)
                if ymn < y < ymx and hi > xmn and lo < xmx:
                    return False
            else:
                _, x, ya, yb = seg
                lo, hi = min(ya, yb), max(ya, yb)
                if xmn < x < xmx and hi > ymn and lo < ymx:
                    return False
        return True

    # ---- "вертикальні" ребра: рідкісний крайовий випадок, коли ціль -
    #      розтягнутий блок, що починається РАНІШЕ або в тій самій
    #      колонці, де закінчується джерело (напр. Алгебра лежить прямо
    #      НАД Матаналізом, з тим самим діапазоном колонок, а не
    #      ліворуч) - тут природний порт не лівий/правий, а верх/низ ----
    vertical_edges, horiz_edges = [], []
    for e in edges:
        src, dst = e
        (vertical_edges if node_col_end[src] >= node_col_start[dst] else horiz_edges).append(e)

    # ---- порти: зсув по y для кожного ГОРИЗОНТАЛЬНОГО ребра на стороні
    #      джерела/приймача (вертикальні ребра портів не потребують -
    #      вони йдуть з верху/низу блоку, див. нижче) ----
    out_edges = defaultdict(list)
    in_edges = defaultdict(list)
    for e in horiz_edges:
        src, dst = e
        out_edges[src].append(e)
        in_edges[dst].append(e)

    def spread_offsets(n):
        if n == 1:
            return [0.0]
        return [-cfg.PORT_SPREAD / 2 + cfg.PORT_SPREAD * i / (n - 1) for i in range(n)]

    port_y_out = {}
    for node, es in out_edges.items():
        _, y, _, h = pos[node]
        es_sorted = sorted(es, key=lambda e: pos[e[1]][1])
        for e, off in zip(es_sorted, spread_offsets(len(es_sorted))):
            port_y_out[e] = y + off * h

    port_y_in = {}
    for node, es in in_edges.items():
        _, y, _, h = pos[node]
        es_sorted = sorted(es, key=lambda e: pos[e[0]][1])
        for e, off in zip(es_sorted, spread_offsets(len(es_sorted))):
            port_y_in[e] = y + off * h

    def edge_endpoints(e):
        src, dst = e
        x1, _y1, w1, _h1 = pos[src]
        x2, _y2, w2, _h2 = pos[dst]
        return (x1 + w1 / 2, port_y_out[e]), (x2 - w2 / 2, port_y_in[e])

    endpoints_cache = {}
    for e in horiz_edges:
        (x1, y1), (x2, y2) = edge_endpoints(e)
        endpoints_cache[e] = (x1, y1, x2, y2)

    # =====================================================================
    # МАРШРУТИЗАЦІЯ (у стилі Graphviz: спільні смуги замість незалежного
    # пошуку шляху для кожного ребра окремо)
    # =====================================================================

    def pack_lanes(items, key_fn, interval_fn, candidates_fn, is_free_fn):
        """Універсальне пакування "смуг": кожному item призначається
        lane-значення (число - або y-рівень стовбура, або x-зсув
        перетину, залежно від виклику). Items обробляються в порядку
        key_fn (barycenter) - тому спорідненi ребра, з близькими
        ключами, природно отримують сусідні/однакові смуги. Смуга
        може бути ПЕРЕВИКОРИСТАНА іншим items, якщо їхні інтервали
        (interval_fn) не перетинаються; інакше - новий кандидат зі
        списку candidates_fn, перший, що проходить перевірку is_free_fn
        (геометричну - чи не перетинає перешкоду)."""
        order = sorted(items, key=key_fn)
        active = []  # [[lane_value, interval_end], ...]
        assigned = {}
        for it in order:
            lo, hi = interval_fn(it)
            chosen = None
            reusable = sorted((a for a in active if a[1] < lo),
                               key=lambda a: abs(a[0] - key_fn(it)))
            for a in reusable:
                if is_free_fn(it, a[0]):
                    chosen = a
                    break
            if chosen is None:
                for cand in candidates_fn(it):
                    conflict = any(abs(a[0] - cand) < cfg.EPS and a[1] >= lo for a in active)
                    if conflict:
                        continue
                    if is_free_fn(it, cand):
                        chosen = [cand, lo]
                        active.append(chosen)
                        break
            if chosen is None:
                cands = candidates_fn(it)
                cand = cands[0] if cands else key_fn(it)
                chosen = [cand, lo]
                active.append(chosen)
            chosen[1] = max(chosen[1], hi)
            assigned[it] = chosen[0]
        return assigned

    def barycenter(e):
        x1, y1, x2, y2 = endpoints_cache[e]
        return (y1 + y2) / 2.0

    # ---- класифікація: сусідні колонки (один коридор) чи "стовбурні" ----
    adjacent_edges, multi_edges = [], []
    for e in horiz_edges:
        src, dst = e
        gap_start = node_col_end[src]
        gap_end = node_col_start[dst] - 1
        (adjacent_edges if gap_end <= gap_start else multi_edges).append(e)

    # ---- крок А: спільний Y-рівень ("стовбур") для стовбурних ребер ----
    def trunk_interval(e):
        src, dst = e
        return (node_col_end[src], node_col_start[dst] - 1)

    def trunk_candidates(e):
        x1, y1, x2, y2 = endpoints_cache[e]
        return nearest_channels(barycenter(e), min(y1, y2), max(y1, y2))

    def trunk_is_free(e, y):
        src, dst = e
        gap_start, gap_end = trunk_interval(e)
        return seg_free(('h', y, corridors[gap_start], corridors[gap_end]), {src, dst})

    trunk_y = pack_lanes(multi_edges, barycenter, trunk_interval, trunk_candidates, trunk_is_free)


    # ---- крок Б: вертикальні "перетини" всередині кожного коридору ----
    # ключ items: ('adj', e) для сусідніх ребер, ('in', e)/('out', e) для
    # входу/виходу стовбурних ребер у межах їхнього першого/останнього
    # коридору
    crossing_requests = defaultdict(list)  # gap_idx -> [(item, y_a, y_b), ...]
    for e in adjacent_edges:
        x1, y1, x2, y2 = endpoints_cache[e]
        crossing_requests[node_col_end[e[0]]].append((('adj', e), y1, y2))
    for e in multi_edges:
        x1, y1, x2, y2 = endpoints_cache[e]
        ty = trunk_y[e]
        gap_start, gap_end = trunk_interval(e)
        crossing_requests[gap_start].append((('in', e), y1, ty))
        crossing_requests[gap_end].append((('out', e), ty, y2))

    def make_x_candidates(center):
        seq = [center]
        for k in range(1, cfg.MAX_LANE_STEPS + 1):
            seq.append(center + k * cfg.LANE_STEP)
            seq.append(center - k * cfg.LANE_STEP)
        return seq

    crossing_x = {}
    for gap_idx, reqs in crossing_requests.items():
        corridor_x = corridors[gap_idx]
        items = [r[0] for r in reqs]
        y_lo = {r[0]: min(r[1], r[2]) for r in reqs}
        y_hi = {r[0]: max(r[1], r[2]) for r in reqs}
        mid = {r[0]: (r[1] + r[2]) / 2.0 for r in reqs}
        excl = {r[0]: set(r[0][1]) for r in reqs}
        cand_list = make_x_candidates(corridor_x)

        assigned = pack_lanes(
            items,
            key_fn=lambda it: mid[it],
            interval_fn=lambda it: (y_lo[it], y_hi[it]),
            candidates_fn=lambda it: cand_list,
            is_free_fn=lambda it, x: seg_free(('v', x, y_lo[it], y_hi[it]), excl[it]),
        )
        crossing_x.update(assigned)

    # ---- складання фінального шляху кожного ребра ----
    def simplify(pts):
        out = [pts[0]]
        for p in pts[1:]:
            if len(out) >= 2:
                x0, y0 = out[-2]
                xp, yp = out[-1]
                xq, yq = p
                if (xp - x0) * (yq - yp) == (yp - y0) * (xq - xp):
                    out[-1] = p
                    continue
            out.append(p)
        return out

    def path_free(points, exclude):
        for (px, py), (qx, qy) in zip(points, points[1:]):
            seg = ('h', py, px, qx) if abs(qy - py) < cfg.EPS else ('v', px, py, qy)
            if not seg_free(seg, exclude):
                return False
        return True

    # ---- аварійний резерв: повний пошук шляху (Дейкстра), якщо
    #      призначена смуга виявилась заблокованою (рідкісний край) ----
    fallback_usage = defaultdict(int)

    def grid_fallback_route(x1, y1, x2, y2, exclude, final_kind):
        wx = sorted(set(corridors) | {x1, x2})
        wy = sorted(set(channels) | {y1, y2})
        xi = {v: i for i, v in enumerate(wx)}
        yi = {v: i for i, v in enumerate(wy)}
        start = (xi[x1], yi[y1], None)
        goal_xy = (xi[x2], yi[y2])

        def seg_key(p, q):
            return (p, q) if p <= q else (q, p)

        def neighbors(state):
            ix, iy, d = state
            x, y = wx[ix], wy[iy]
            steps = []
            if ix + 1 < len(wx):
                steps.append(((ix + 1, iy), 'h', wx[ix + 1] - x))
            if ix - 1 >= 0:
                steps.append(((ix - 1, iy), 'h', x - wx[ix - 1]))
            if iy + 1 < len(wy):
                steps.append(((ix, iy + 1), 'v', wy[iy + 1] - y))
            if iy - 1 >= 0:
                steps.append(((ix, iy - 1), 'v', y - wy[iy - 1]))
            res = []
            for (nix, niy), kind, dist in steps:
                nx, ny = wx[nix], wy[niy]
                seg = ('h', y, x, nx) if kind == 'h' else ('v', x, y, ny)
                if not seg_free(seg, exclude):
                    continue
                bend = 0.0 if (d is None or d == kind) else cfg.BEND_PENALTY
                gkey = seg_key((ix, iy), (nix, niy))
                cong = cfg.CONGESTION_WEIGHT * fallback_usage.get(gkey, 0)
                # штраф за проїзд УЗДОВЖ власної грані блоку (x=x2 або
                # y=y2) - ці лінії додані в сітку (wx/wy нижче) лише щоб
                # гарантувати, що ціль ВЗАГАЛІ досяжна, а не як звичайний
                # наскрізний коридор. Без штрафу Дейкстра іноді знаходить
                # "дешевшим" виїхати на грань блоку заздалегідь і потім
                # довго ковзати вздовж неї до порту, замість короткого
                # перпендикулярного заходу в останній момент - саме це і
                # виглядає як "стрілка входить по дотичній". Штраф не
                # діє на сам фінальний крок до цілі.
                # штраф за НЕПРАВИЛЬНИЙ НАПРЯМОК фінального кроку в ціль:
                # порт на лівій/правій грані блоку (LR) вимагає, щоб
                # ОСТАННІЙ відрізок шляху був ГОРИЗОНТАЛЬНИМ (заходимо
                # збоку, впритул); порт на верхній/нижній грані (TB) -
                # ВЕРТИКАЛЬНИМ. Якщо фінальний крок не того типу, шлях
                # спершу виїжджає точно на лінію x2 (чи y2) ЗАЗДАЛЕГІДЬ,
                # а потім ковзає вздовж неї до порту - лінія тоді
                # буквально збігається з гранню блоку замість
                # перпендикулярного заходу в останній момент.
                hug = 0.0
                if (nix, niy) == goal_xy and kind != final_kind:
                    hug += 10000.0
                res.append(((nix, niy, kind), dist + bend + cong + hug, gkey))
            return res

        dist_map, prev, pq, visited = {start: 0.0}, {}, [(0.0, start)], set()
        goal_state = None
        while pq:
            d, state = heapq.heappop(pq)
            if state in visited:
                continue
            visited.add(state)
            if (state[0], state[1]) == goal_xy:
                goal_state = state
                break
            for nstate, cost, gkey in neighbors(state):
                nd = d + cost
                if nstate not in dist_map or nd < dist_map[nstate]:
                    dist_map[nstate] = nd
                    prev[nstate] = (state, gkey)
                    heapq.heappush(pq, (nd, nstate))
        if goal_state is None:
            return None

        pts_idx, gkeys, cur = [(goal_state[0], goal_state[1])], [], goal_state
        while cur in prev:
            pstate, gkey = prev[cur]
            gkeys.append(gkey)
            pts_idx.append((pstate[0], pstate[1]))
            cur = pstate
        pts_idx.reverse()
        for gk in gkeys:
            fallback_usage[gk] += 1
        return simplify([(wx[ix], wy[iy]) for ix, iy in pts_idx])

    edge_paths = {}
    for e in adjacent_edges:
        src, dst = e
        x1, y1, x2, y2 = endpoints_cache[e]
        x = crossing_x[('adj', e)]
        edge_paths[e] = simplify([(x1, y1), (x, y1), (x, y2), (x2, y2)])
    for e in multi_edges:
        src, dst = e
        x1, y1, x2, y2 = endpoints_cache[e]
        ty = trunk_y[e]
        xin, xout = crossing_x[('in', e)], crossing_x[('out', e)]
        edge_paths[e] = simplify(
            [(x1, y1), (xin, y1), (xin, ty), (xout, ty), (xout, y2), (x2, y2)])

    # ---- вертикальні ребра: порти зверху/знизу блоку, а не зліва/справа ----
    for e in vertical_edges:
        src, dst = e
        sx, sy, sw, sh = pos[src]
        dx, dy, dw, dh = pos[dst]
        ov_lo = max(sx - sw / 2, dx - dw / 2)
        ov_hi = min(sx + sw / 2, dx + dw / 2)
        if sy > dy:
            y1, y2 = sy - sh / 2, dy + dh / 2   # src знизу -> dst зверху
        else:
            y1, y2 = sy + sh / 2, dy - dh / 2   # src зверху -> dst знизу
        exclude = {src, dst}

        if ov_hi > ov_lo:
            # блоки перетинаються по X - є спільна смуга, де ОДНА пряма
            # вертикальна лінія влучає в обидва блоки по нормалі
            cx = (ov_lo + ov_hi) / 2
            chosen_x = cx
            for cand_x in make_x_candidates(cx):
                if seg_free(('v', cand_x, y1, y2), exclude):
                    chosen_x = cand_x
                    break
            endpoints_cache[e] = (chosen_x, y1, chosen_x, y2)
            edge_paths[e] = [(chosen_x, y1), (chosen_x, y2)]
        else:
            # перетину немає - пряма вертикаль на "середині" (sx+dx)/2
            # фізично промахується повз ширину цільового (а часто й
            # вихідного) блоку - лінія б впиралась збоку, а не по
            # нормалі в грань. Замість цього: вертикальний вихід рівно
            # з ЦЕНТРУ джерела, горизонтальна перемичка на проміжному
            # рівні, і вертикальний вхід рівно в ЦЕНТР цілі - обидва
            # порти гарантовано в межах "своїх" блоків.
            mid_y = (y1 + y2) / 2
            endpoints_cache[e] = (sx, y1, dx, y2)
            edge_paths[e] = simplify(
                [(sx, y1), (sx, mid_y), (dx, mid_y), (dx, y2)])

    vertical_edges_set = set(vertical_edges)
    for e in edges:
        src, dst = e
        exclude = {src, dst}
        if not path_free(edge_paths[e], exclude):
            x1, y1, x2, y2 = endpoints_cache[e]
            final_kind = 'v' if e in vertical_edges_set else 'h'
            fb = grid_fallback_route(x1, y1, x2, y2, exclude, final_kind)
            if fb is not None:
                edge_paths[e] = fb

    # =====================================================================
    # ОРІЄНТАЦІЯ: усе вище рахувалось у "логічних" осях (u = вісь семестрів,
    # v = вісь порядку в семестрі), а розміри блоків (U_SIZE/V_SIZE) вже
    # ЗАЗДАЛЕГІДЬ підібрані так, щоб після повороту фізичний блок лишався
    # BOX_W x BOX_H в обох орієнтаціях (сам блок не обертається - лише
    # координати). "vertical" (за замовчуванням): u йде вправо (x), v -
    # вниз (y), як і було завжди. "horizontal": u йде вниз (y), v -
    # вправо (x), тобто дисципліни одного семестру йдуть в один рядок
    # ліворуч->праворуч, а самі семестри - зверху вниз.
    #
    # Це поворот на 90° - (x, y) -> (-y, -x) - застосований ПОСТФАКТУМ до
    # вже готової геометрії: сам алгоритм пакування смуг і маршрутизації
    # вище рахує все як завжди і не знає про орієнтацію.
    # =====================================================================
    if orientation == "horizontal":
        # (x, y) -> (-y, -x): один numpy-оператор на всі координати одразу -
        # rotate() нижче і є тим самим місцем, де "легко робиться інверсія":
        # для дзеркальної/іншої трансформації досить переписати саме цю
        # функцію, решта коду (алгоритм пакування смуг вище, build_diagramm.py
        # нижче) її не знає.
        def rotate(points):
            arr = np.asarray(points, dtype=float).reshape(-1, 2)
            return (arr[:, ::-1] * -1.0)

        pos_ids = list(pos.keys())
        xy = rotate([(x, y) for x, y, _w, _h in pos.values()])
        # розміри теж міняються місцями (без знаку!) - "довга" вздовж
        # старої u-осі сторона розтягнутого блоку (w) стає його висотою
        # (h) після повороту, і навпаки. Це НЕЗАЛЕЖНО від U_SIZE/V_SIZE
        # вище: той свап відповідав за те, ЯКЕ число піде в w/h ще ДО
        # повороту (щоб після свапу вийшло рівно BOX_W x BOX_H для
        # звичайного блоку), а цей swap - за те, на яку вісь це число
        # ляже на полотні.
        pos = {nid: (xy[i, 0], xy[i, 1], pos[nid][3], pos[nid][2])
               for i, nid in enumerate(pos_ids)}

        ext_ids = list(col_extent.keys())
        # три числа на колонку - це НЕ одна точка (x,y), а перпендикулярна
        # координата + два кінці екстенту; трансформуємо як три незалежні
        # "x"-значення через ту саму rotate(), підставляючи фіктивний 0
        ext_arr = np.array([col_extent[i] for i in ext_ids], dtype=float)  # (N, 3)
        ext_new = -ext_arr
        col_extent = {ext_ids[i]: tuple(ext_new[i]) for i in range(len(ext_ids))}

        idx_ids = list(col_x_of_idx.keys())
        idx_vals = -np.array([col_x_of_idx[i] for i in idx_ids], dtype=float)
        col_x_of_idx = {idx_ids[i]: idx_vals[i] for i in range(len(idx_ids))}

        for e in list(edge_paths.keys()):
            pts = rotate(edge_paths[e])
            edge_paths[e] = [tuple(p) for p in pts]

    return {
        "pos": pos,                     # nid -> (x, y, w, h)
        "col_extent": col_extent,         # idx -> (перп.координата, екстент_a, екстент_b)
        "col_x_of_idx": col_x_of_idx,     # idx -> координата колонки на її "власній" осі
        "semesters": semesters,           # відсортований список номерів семестрів
        "col_of_sem": col_of_sem,         # semester -> idx
        "max_col_idx": max_idx,
        "band_rows_count": band_rows_count,
        "edge_paths": edge_paths,         # edge -> [(x,y), ...]
        "orientation": orientation,       # "vertical" | "horizontal" - для build_diagramm.py
        "col_axis_box_size": U_SIZE,      # фізичний розмір блоку вздовж осі семестрів
        "row_axis_box_size": V_SIZE,      # фізичний розмір блоку вздовж осі елементів семестру
        "row_axis_step": V_STEP,          # крок сітки вздовж осі елементів семестру
    }
