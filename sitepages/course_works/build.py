"""Сторінка «Теми курсових робіт» (apd.ipt.kpi.ua/nauka/course-works/) з data.yaml.

Запуск: python sitepages/run.py course_works generate|diff|upload (див. sitepages/common.py).
Роки — розгортні блоки <details> (найновіший відкритий), навігація-«пілюлі», на вузькому екрані рядки стають картками.
"""
from html import escape

from sitepages.common import minify_css, wrap, year_css

CSS = """
.cw-intro{color:var(--c-mute);margin:0 0 1em}
.cw-table{width:100%;border-collapse:collapse;margin:0;border:0;font-size:15px}
.cw-table th{text-align:left;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--c-mute);padding:8px 16px;border:0;border-bottom:1px solid var(--c-line);background:#fff}
.cw-table td{padding:10px 16px;vertical-align:top;border:0;border-bottom:1px solid #eef0f5;line-height:1.4;color:var(--c-text)}
.cw-table tr:last-child td{border-bottom:0}
.cw-table tbody tr:nth-child(even){background:#fafbfd}
.cw-table .st{width:22%;font-weight:600}
.cw-table .ad{width:24%}
.cw-chip{display:inline-block;margin:0 6px 4px 0;padding:2px 9px;border-radius:999px;background:var(--c-acc-bg);color:var(--c-acc);font-size:13px;white-space:nowrap}
@media(max-width:700px){
.cw-table thead{display:none}
.cw-table,.cw-table tbody,.cw-table tr,.cw-table td{display:block;width:100%!important}
.cw-table tr{padding:10px 14px;border-bottom:1px solid var(--c-line)}
.cw-table td{padding:2px 0;border:0}
.cw-table .st{font-size:13px;color:var(--c-mute);font-weight:600}
}
"""


def row(w: dict) -> str:
    chips = "".join(f'<span class="cw-chip">{escape(a)}</span>' for a in w["advisors"])
    return (f'<tr><td class="st">{escape(w["student"])}</td><td>{escape(w["title"])}</td>'
            f'<td class="ad">{chips}</td></tr>')


def build(data: dict) -> str:
    years = sorted(data["years"], key=lambda y: -y["year"])
    parts = [f"<style>{year_css("cw")}{minify_css(CSS)}</style>", '<div class="cw">']
    if data.get("intro"):
        parts.append(f'<p class="cw-intro">{escape(data["intro"])}</p>')
    parts.append('<nav class="cw-nav">' + "".join(
        f'<a href="#cw-{y["year"]}">{y["year"]}</a>' for y in years) + "</nav>")
    for i, y in enumerate(years):
        n = len(y["works"])
        rows = "".join(row(w) for w in sorted(y["works"], key=lambda w: w["student"]))
        parts.append(
            f'<details class="cw-year" id="cw-{y["year"]}"{" open" if i == 0 else ""}>'
            f'<summary>Теми за {y["year"]} рік <span class="cnt">робіт: {n}</span></summary>'
            '<table class="cw-table"><thead><tr><th>ПІБ студента</th><th>Тема курсової роботи</th>'
            f'<th>Науковий керівник</th></tr></thead><tbody>{rows}</tbody></table></details>')
    parts.append("</div>")
    return wrap("".join(parts))
