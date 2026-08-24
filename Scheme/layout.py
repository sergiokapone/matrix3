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


def compute_layout(node_info, edges, cfg):
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
        return idx * cfg.XSTEP

    def row_y(r):
        return -r * cfg.YSTEP

    # ---- розподіл розтягнутих вузлів по "смугах" (band-rows) ----
    # Інтервали (start_idx, end_idx), відсортовані за початком; кожному
    # інтервалу — найнижчий вільний рядок, чий останній зайнятий кінець
    # менший за початок поточного (класичне жадібне розфарбування
    # інтервального графа).
    intervals = []
    for nid in wide_ids:
        info = node_info[nid]
        s_idx = col_of_sem[info["semester_start"]]
        e_idx = col_of_sem[info["semester_end"]]
        intervals.append((s_idx, e_idx, nid))
    intervals.sort(key=lambda t: (t[0], t[1]))

    band_row_of = {}
    band_last_end = []  # band_last_end[i] = останній end_idx, зайнятий у смузі i
    for s_idx, e_idx, nid in intervals:
        placed = False
        for band_i, last_end in enumerate(band_last_end):
            if last_end < s_idx:
                band_row_of[nid] = band_i
                band_last_end[band_i] = e_idx
                placed = True
                break
        if not placed:
            band_row_of[nid] = len(band_last_end)
            band_last_end.append(e_idx)
    band_rows_count = len(band_last_end)  # 0, якщо розтягнутих вузлів немає

    # ---- локальний відступ ЗВЕРХУ для кожної колонки окремо ----
    # Глобальний band_rows_count - це відступ, потрібний лише в колонках,
    # де смуги дійсно накопичуються (напр. семестри 1-2, де перетинаються
    # Алгебра/Англійська/Матаналіз). Колонка, крізь яку не проходить
    # жоден розтягнутий блок (або проходить лише один), не повинна мати
    # такий самий великий відступ - інакше звичайні дисципліни в ній
    # висітимуть з порожнім місцем зверху. Тому для кожної колонки
    # рахуємо ОКРЕМО, скільки смуг реально перетинають саме її.
    col_band_offset = defaultdict(int)
    for s_idx, e_idx, nid in intervals:
        top = band_row_of[nid] + 1
        for idx in range(s_idx, e_idx + 1):
            if top > col_band_offset[idx]:
                col_band_offset[idx] = top

    # ---- звичайні вузли: групування по колонках, з відступом під смуги ----
    by_sem = defaultdict(list)
    for nid in normal_ids:
        by_sem[node_info[nid]["semester_start"]].append(nid)

    pos = {}            # nid -> (x, y, w, h)
    col_extent = {}      # idx -> (x, y_top, y_bottom)
    col_x_of_idx = {}
    for s in semesters:
        idx = col_of_sem[s]
        x = col_x(idx)
        col_x_of_idx[idx] = x
        nodes = by_sem.get(s, [])
        offset = col_band_offset[idx]
        for i, nid in enumerate(nodes):
            pos[nid] = (x, row_y(i + offset), cfg.BOX_W, cfg.BOX_H)
        y_top = row_y(offset) + cfg.BOX_H / 2
        if nodes:
            y_bottom = row_y(len(nodes) - 1 + offset) - cfg.BOX_H / 2
        else:
            y_bottom = y_top - cfg.BOX_H  # порожня колонка - мінімальна заглушка
        col_extent[idx] = (x, y_top, y_bottom)

    # ---- розтягнуті вузли: широкий блок у своїй смузі ----
    for nid in wide_ids:
        info = node_info[nid]
        s_idx = col_of_sem[info["semester_start"]]
        e_idx = col_of_sem[info["semester_end"]]
        x = (col_x(s_idx) + col_x(e_idx)) / 2
        y = row_y(band_row_of[nid])
        w = (col_x(e_idx) - col_x(s_idx)) + cfg.BOX_W
        pos[nid] = (x, y, w, cfg.BOX_H)

    # ---- індекс колонки для кожного вузла (для маршрутизації: скільки
    #      коридорів перестрибує ребро) - для звичайного вузла старт=кінець,
    #      для розтягнутого - діапазон його семестрів ----
    node_col_start = {}
    node_col_end = {}
    for s in semesters:
        idx = col_of_sem[s]
        for nid in by_sem.get(s, []):
            node_col_start[nid] = idx
            node_col_end[nid] = idx
    for nid in wide_ids:
        info = node_info[nid]
        node_col_start[nid] = col_of_sem[info["semester_start"]]
        node_col_end[nid] = col_of_sem[info["semester_end"]]

    # ---- перешкоди (усі блоки, звичайні й розтягнуті, трохи "роздуті") ----
    obstacles = {}
    for nid, (x, y, w, h) in pos.items():
        obstacles[nid] = (x - w / 2 - cfg.OBST_PAD, x + w / 2 + cfg.OBST_PAD,
                           y - h / 2 - cfg.OBST_PAD, y + h / 2 + cfg.OBST_PAD)

    # ---- координати коридорів (між колонками) і каналів (між рядками) ----
    corridors = sorted(col_x_of_idx[i] + cfg.XSTEP / 2 for i in range(max_idx))
    max_rows = max((len(v) for v in by_sem.values()), default=0) + band_rows_count
    channels = sorted(row_y(k) + cfg.YSTEP / 2 for k in range(-1, max_rows + 2))

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

    def grid_fallback_route(x1, y1, x2, y2, exclude):
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
                res.append(((nix, niy, kind), dist + bend + cong, gkey))
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
        cx = (ov_lo + ov_hi) / 2 if ov_hi > ov_lo else (sx + dx) / 2
        if sy > dy:
            y1, y2 = sy - sh / 2, dy + dh / 2   # src знизу -> dst зверху
        else:
            y1, y2 = sy + sh / 2, dy - dh / 2   # src зверху -> dst знизу
        exclude = {src, dst}
        chosen_x = cx
        for cand_x in make_x_candidates(cx):
            if seg_free(('v', cand_x, y1, y2), exclude):
                chosen_x = cand_x
                break
        endpoints_cache[e] = (chosen_x, y1, chosen_x, y2)
        edge_paths[e] = [(chosen_x, y1), (chosen_x, y2)]

    for e in edges:
        src, dst = e
        exclude = {src, dst}
        if not path_free(edge_paths[e], exclude):
            x1, y1, x2, y2 = endpoints_cache[e]
            fb = grid_fallback_route(x1, y1, x2, y2, exclude)
            if fb is not None:
                edge_paths[e] = fb

    return {
        "pos": pos,                     # nid -> (x, y, w, h)
        "col_extent": col_extent,         # idx -> (x, y_top, y_bottom)
        "col_x_of_idx": col_x_of_idx,     # idx -> x
        "semesters": semesters,           # відсортований список номерів семестрів
        "col_of_sem": col_of_sem,         # semester -> idx
        "max_col_idx": max_idx,
        "band_rows_count": band_rows_count,
        "edge_paths": edge_paths,         # edge -> [(x,y), ...]
    }
