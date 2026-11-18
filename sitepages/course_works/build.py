"""Сторінка «Теми курсових робіт» (apd.ipt.kpi.ua/nauka/course-works/) з data.yaml.

Запуск: python sitepages/run.py course_works generate|diff|upload (див. sitepages/common.py).
Роки — розгортні блоки <details> (найновіший відкритий). Кожна робота — рядок-сітка
(студент | тема | керівники); якщо є `annotation`, рядок розгортається стрілкою й показує анотацію.
Записи annotation: {label?, text?, items?[]}. Усе вирівняно по лівому краю.
Без CSS-escape кодів (\\25B8): WordPress їх ламає.
"""
from html import escape

from sitepages.common import minify_css, ua_key, wrap, year_css

CSS = """
.cw-head,.cw-row>summary,.cw-row.plain{display:grid;grid-template-columns:22% minmax(0,1fr) 24% 32px;gap:0 14px;align-items:start;text-align:left!important}
.cw-head{padding:8px 16px;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--c-mute);border-bottom:1px solid var(--c-line);background:#fff}
.cw-row{border-bottom:1px solid #eef0f5;color:var(--c-text);font-size:15px;line-height:1.4}
.cw-row:last-child{border-bottom:0}
.cw-row>summary,.cw-row.plain{padding:10px 16px}
.cw-row>summary{cursor:pointer;list-style:none}
.cw-row>summary::-webkit-details-marker{display:none}
.cw-row>summary:hover{background:#f3f6fc}
.cw-row[open]>summary{background:#eef3fb}
.cw-st{font-weight:600;text-align:left}
.cw-ti{text-align:left}
.cw-ad{text-align:left}
.cw-arr{justify-self:end;align-self:center;width:24px;height:24px;border-radius:50%;background:var(--c-acc-bg);position:relative}
.cw-arr::after{content:"";position:absolute;left:9px;top:8px;border-style:solid;border-width:4px 0 4px 6px;border-color:transparent transparent transparent var(--c-acc);transition:transform .15s}
.cw-row[open] .cw-arr::after{transform:rotate(90deg);left:8px;top:8px}
.cw-ann{padding:12px 16px 16px;margin:0;background:#f6f8fc;border-top:1px solid var(--c-line);text-align:left}
.cw-ann-h{margin:0 0 8px;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--c-mute);font-weight:700}
.cw-ann p{margin:0 0 8px;line-height:1.5}
.cw-ann b{color:var(--c-text)}
.cw-ann ol{margin:4px 0 8px;padding-left:22px}
.cw-ann li{margin:0 0 6px;line-height:1.5}
.cw-chip{display:inline-block;margin:0 6px 4px 0;padding:2px 9px;border-radius:999px;background:var(--c-acc-bg);color:var(--c-acc);font-size:13px;white-space:nowrap}
@media(max-width:700px){
.cw-head{display:none}
.cw-row>summary,.cw-row.plain{grid-template-columns:minmax(0,1fr) 32px;padding:10px 14px}
.cw-st{grid-column:1;font-size:13px;color:var(--c-mute)}
.cw-ti{grid-column:1}
.cw-ad{grid-column:1;margin-top:4px}
.cw-arr{grid-column:2;grid-row:1/4}
}
"""


def annotation(blocks: list) -> str:
    out = ['<div class="cw-ann"><div class="cw-ann-h">Анотація</div>']
    for b in blocks:
        if b.get("items"):
            if b.get("label"):
                out.append(f'<p><b>{escape(b["label"])}:</b></p>')
            out.append("<ol>" + "".join(f"<li>{escape(i)}</li>" for i in b["items"]) + "</ol>")
        else:
            lab = f'<b>{escape(b["label"])}.</b> ' if b.get("label") else ""
            out.append(f'<p>{lab}{escape(b["text"])}</p>')
    out.append("</div>")
    return "".join(out)


def row(w: dict) -> str:
    chips = "".join(f'<span class="cw-chip">{escape(a)}</span>' for a in w["advisors"])
    cells = (f'<span class="cw-st">{escape(w["student"])}</span>'
             f'<span class="cw-ti">{escape(w["title"])}</span>'
             f'<span class="cw-ad">{chips}</span>')
    if w.get("annotation"):
        return (f'<details class="cw-row"><summary title="Показати анотацію">{cells}'
                f'<span class="cw-arr"></span></summary>{annotation(w["annotation"])}</details>')
    return f'<div class="cw-row plain">{cells}<span></span></div>'


def build(data: dict) -> str:
    years = sorted(data["years"], key=lambda y: -y["year"])
    parts = [f"<style>{year_css('cw')}{minify_css(CSS)}</style>", '<div class="cw">']
    if data.get("intro"):
        parts.append(f'<p class="cw-intro">{escape(data["intro"])}</p>')
    parts.append('<nav class="cw-nav">' + "".join(
        f'<a href="#cw-{y["year"]}">{y["year"]}</a>' for y in years) + "</nav>")
    for i, y in enumerate(years):
        n = len(y["works"])
        rows = "".join(row(w) for w in sorted(y["works"], key=lambda w: ua_key(w["student"])))
        parts.append(
            f'<details class="cw-year" id="cw-{y["year"]}"{" open" if i == 0 else ""}>'
            f'<summary>Теми за {y["year"]} рік <span class="cnt">робіт: {n}</span></summary>'
            '<div class="cw-head"><span>ПІБ студента</span><span>Тема курсової роботи</span>'
            f'<span>Науковий керівник</span><span></span></div>{rows}</details>')
    parts.append("</div>")
    return wrap("".join(parts))
