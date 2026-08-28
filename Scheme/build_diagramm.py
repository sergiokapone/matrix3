# -*- coding: utf-8 -*-
"""
Рендер графа навчального плану через matplotlib.
Тільки малювання: дані беруться з data2026.py, дисципліни, що
повторюються в кількох семестрах підряд, згортаються в один блок
(merge.py), геометрія/кольори — з config.py, розкладка й
маршрутизація ребер — з layout.py.

Будує ОБИДВІ мовні версії (ua/en) з одних і тих самих даних —
відрізняється лише те, яке поле ("ua"/"en") береться як підпис
блоку та який шаблон використовується для заголовків колонок.
"""
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.path import Path
import matplotlib.patches as mpatches

import config as cfg
from data2026 import DISCIPLINES, EDGES
from merge import build_merged_graph
from layout import compute_layout


def fit_label(text, box_w, box_h):
    """Перенести текст під ширину блоку і підібрати розмір шрифту так,
    щоб він влазив по висоті. chars_per_line масштабується під фактичну
    ширину блоку - завдяки цьому широкий (розтягнутий на кілька
    семестрів) блок отримує пропорційно довші рядки, а не дробиться
    на купу коротких без потреби."""
    width_ratio = box_w / cfg.BOX_W
    raw = " ".join(text.split())
    candidates = [
        (cfg.LABEL_FONTSIZE, 16),
        (cfg.LABEL_FONTSIZE - 1, 18),
        (cfg.LABEL_FONTSIZE - 2, 20),
        (cfg.LABEL_FONTSIZE - 3, 23),
        (cfg.LABEL_FONTSIZE - 4, 27),
        (cfg.LABEL_FONTSIZE - 4.5, 32),
    ]
    wrapped, fontsize = raw, cfg.LABEL_FONTSIZE
    for fs, base_chars in candidates:
        chars_per_line = max(int(round(base_chars * width_ratio)), base_chars)
        wrapped = textwrap.fill(raw, width=chars_per_line)
        n_lines = wrapped.count("\n") + 1
        line_h_in = fs / 72.0 * 1.45
        fontsize = fs
        if n_lines * line_h_in <= box_h * 0.75:
            break
    return wrapped, fontsize


def render(lang, node_info, layout_result):
    pos = layout_result["pos"]
    col_extent = layout_result["col_extent"]
    col_x_of_idx = layout_result["col_x_of_idx"]
    semesters = layout_result["semesters"]
    max_idx = layout_result["max_col_idx"]
    edge_paths = layout_result["edge_paths"]

    xs = [x for x, _y, _w, _h in pos.values()]
    ys = [y for _x, y, _w, _h in pos.values()]
    # межі полотна мають враховувати НЕ ЛИШЕ позиції блоків, а й фактичні
    # координати всіх ліній - при пошуку вільної смуги (layout.py)
    # маршрут інколи відходить далі за звичайну область рядків (особливо
    # коли багато багатоколонкових ребер конкурують за Y-рівні); якщо
    # рахувати межі тільки з pos, такі лінії просто обрізаються по краю
    # полотна без жодного попередження
    for pts in edge_paths.values():
        for px, py in pts:
            xs.append(px)
            ys.append(py)
    fig_w = (max(xs) - min(xs)) / 1.6 + 4
    fig_h = (max(ys) - min(ys)) / 1.6 + 3
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    orientation = layout_result.get("orientation", "vertical")
    col_box_size = layout_result["col_axis_box_size"]   # розмір блоку вздовж осі семестрів
    row_box_size = layout_result["row_axis_box_size"]   # розмір блоку вздовж осі елементів семестру
    row_step = layout_result["row_axis_step"]

    # ---- фонові прямокутники семестрів (кластери) ----
    if orientation == "vertical":
        top_with_band = 0 + row_box_size / 2 + cfg.CLUSTER_PAD_Y  # рядок 0 однаковий для всіх колонок
        for _idx, (x, _y_top, y_bottom) in col_extent.items():
            rect = FancyBboxPatch(
                (x - col_box_size / 2 - cfg.CLUSTER_PAD_X, y_bottom - cfg.CLUSTER_PAD_Y),
                col_box_size + 2 * cfg.CLUSTER_PAD_X,
                (top_with_band - (y_bottom - cfg.CLUSTER_PAD_Y)),
                boxstyle="round,pad=0,rounding_size=0.12",
                linewidth=0, facecolor=cfg.CLUSTER_FACECOLOR, zorder=0)
            ax.add_patch(rect)
    else:
        # горизонтальна орієнтація: "колонка" (семестр) - тепер
        # горизонтальна смуга вздовж Y; ліва межа - дзеркальний відповідник
        # top_with_band (та сама формула, той самий сенс "перед елементом
        # №0"), права межа - за найдальшим елементом у рядку
        left_with_band = 0 - (row_box_size / 2 + cfg.CLUSTER_PAD_Y)
        for _idx, (y, ext_a, ext_b) in col_extent.items():
            x_far = max(ext_a, ext_b) + cfg.CLUSTER_PAD_Y
            rect = FancyBboxPatch(
                (left_with_band, y - col_box_size / 2 - cfg.CLUSTER_PAD_X),
                x_far - left_with_band,
                col_box_size + 2 * cfg.CLUSTER_PAD_X,
                boxstyle="round,pad=0,rounding_size=0.12",
                linewidth=0, facecolor=cfg.CLUSTER_FACECOLOR, zorder=0)
            ax.add_patch(rect)

    # ---- підписи колонок (семестрів) ----
    if orientation == "vertical":
        label_pos = 0 + row_step * 0.55
        for idx, x in col_x_of_idx.items():
            # if idx == max_idx and not cfg.LAST_COLUMN_HAS_LABEL:
            #     continue
            sem_num = semesters[idx]
            label = cfg.COLUMN_LABEL_TEMPLATE[lang].format(n=sem_num)
            ax.text(x, label_pos, label, ha="center", va="bottom",
                    fontsize=cfg.COL_LABEL_FONTSIZE, fontweight="bold",
                    color=cfg.COL_LABEL_COLOR)
    else:
        label_pos = -(row_step * 0.55)
        for idx, y in col_x_of_idx.items():
            # if idx == max_idx and not cfg.LAST_COLUMN_HAS_LABEL:
            #     continue
            sem_num = semesters[idx]
            label = cfg.COLUMN_LABEL_TEMPLATE[lang].format(n=sem_num)
            ax.text(label_pos, y, label, ha="right", va="center",
                    fontsize=cfg.COL_LABEL_FONTSIZE, fontweight="bold",
                    color=cfg.COL_LABEL_COLOR)

    # ---- ребра (лінії - під блоками, блоки малюємо пізніше зверху) ----
    for e in edge_paths:
        src, dst = e
        color = cfg.TYPE_EDGE_COLOR[node_info[src]["type"]]
        pts = edge_paths[e]
        codes = [Path.MOVETO] + [Path.LINETO] * (len(pts) - 1)
        path = Path(pts, codes)
        # ребро між двома РІЗНИМИ розтягнутими блоками - пунктиром, щоб
        # було видно, що це "далекий" зв'язок, а не звичайна сусідня
        # стрілка (дані для нього все одно лишаються повними - див.
        # prereq_extract.py, який працює з тими самими EDGES напряму)
        is_wide_to_wide = (node_info[src]["semester_start"] != node_info[src]["semester_end"]
                           and node_info[dst]["semester_start"] != node_info[dst]["semester_end"])
        linestyle = cfg.WIDE_TO_WIDE_DASH if is_wide_to_wide else "solid"
        alpha = cfg.WIDE_TO_WIDE_ALPHA if is_wide_to_wide else cfg.EDGE_ALPHA
        patch = mpatches.PathPatch(path, facecolor="none", edgecolor=color,
                                    linewidth=cfg.EDGE_LINEWIDTH, alpha=alpha,
                                    linestyle=linestyle,
                                    zorder=1, capstyle="round", joinstyle="round")
        ax.add_patch(patch)
        (x2, y2) = pts[-1]
        (xprev, yprev) = pts[-2]
        dx, dy = x2 - xprev, y2 - yprev
        if abs(dx) >= abs(dy):
            # останній відрізок горизонтальний - хвостик зсуваємо по x
            arrow_len = cfg.ARROW_LEN if dx > 0 else -cfg.ARROW_LEN
            xytext = (x2 - arrow_len, y2)
        else:
            # останній відрізок вертикальний (наші "верх/низ" ребра) -
            # хвостик має йти по y, інакше наконечник стирчить убік
            arrow_len = cfg.ARROW_LEN if dy > 0 else -cfg.ARROW_LEN
            xytext = (x2, y2 - arrow_len)
        ax.annotate("", xy=(x2, y2), xytext=xytext,
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=cfg.EDGE_LINEWIDTH,
                                    alpha=alpha, shrinkA=0, shrinkB=0), zorder=1)

    # ---- блоки (поверх ліній) ----
    for nid, (x, y, w, h) in pos.items():
        info = node_info[nid]
        color = cfg.TYPE_FILL_COLOR[info["type"]]
        label, fontsize = fit_label(info[lang], w, h)
        box = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                              boxstyle=f"round,pad=0,rounding_size={cfg.BOX_ROUNDING}",
                              linewidth=cfg.BOX_LINEWIDTH, edgecolor=cfg.BOX_EDGE_COLOR,
                              facecolor=color, zorder=3)
        ax.add_patch(box)
        ax.text(x, y, label, ha="center", va="center", fontsize=fontsize,
                fontweight="bold", color=cfg.LABEL_COLOR, zorder=4)

    ax.set_xlim(min(xs) - cfg.BOX_W, max(xs) + cfg.BOX_W)
    ax.set_ylim(min(ys) - cfg.BOX_H, max(ys) + cfg.BOX_H * 2)
    ax.axis("off")
    ax.set_aspect("equal")
    plt.tight_layout()

    out_pdf = f"{cfg.OUTPUT_BASENAME}_{lang}.pdf"
    out_png = f"{cfg.OUTPUT_BASENAME}_{lang}.png"
    plt.savefig(out_pdf, bbox_inches="tight")
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"saved {out_png}, {out_pdf}")


if __name__ == "__main__":
    import validate_data
    if validate_data.main() != 0:
        raise SystemExit("Дані не пройшли валідацію (validate_data.py) - виправте помилки вище.")

    # злиття дисциплін, що йдуть кілька семестрів підряд, і побудова
    # розкладки - від мови не залежать, рахуємо один раз
    node_info, merged_edges, merge_map = build_merged_graph(DISCIPLINES, EDGES, cfg.NEVER_MERGE)
    # config.FORCE_BAND заданий в ОРИГІНАЛЬНИХ id (як і NEVER_MERGE) -
    # переводимо їх у id об'єднаного блоку, яким реально оперує layout.py
    forced_bands = {merge_map.get(nid, nid): band for nid, band in cfg.FORCE_BAND.items()}
    layout_result = compute_layout(node_info, merged_edges, cfg, forced_bands)
    for lang in cfg.LANGUAGES:
        render(lang, node_info, layout_result)
