"""Сторінка «Наукові роботи студентів» (apd.ipt.kpi.ua/nauka/stud_sci_works/) з data.yaml.

Запуск: python sitepages/run.py stud_sci_works generate|diff|upload (див. sitepages/common.py).
Запис у data.yaml: authors (необов'язково), title, source, note; запасний варіант — вільний `text`; `links: [{url, label}]` — кнопки-посилання (DOI, Посилання).
Лише ASCII/прямі символи в CSS: escape-коди (\25B8) WordPress ламає.
"""
from html import escape

from sitepages.common import minify_css, wrap, year_css

CSS = """
.sw .sw-list{list-style:none!important;margin:0!important;padding:0!important;counter-reset:sw}
.sw .sw-item{list-style:none!important;margin:0!important;counter-increment:sw;position:relative;padding:12px 16px 12px 52px;border-bottom:1px solid #eef0f5;line-height:1.45;color:var(--c-text);font-size:15px}
.sw-item:last-child{border-bottom:0}
.sw-item:nth-child(even){background:#fafbfd}
.sw-item::before{content:counter(sw);position:absolute;left:12px;top:12px;width:28px;height:28px;border-radius:50%;background:var(--c-acc-bg);color:var(--c-acc);font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center}
.sw-au{display:block;font-style:italic;color:#555;font-size:14px}
.sw-ti{display:block;font-weight:700;color:var(--c-acc);margin:2px 0}
.sw-so{display:block;color:#555;font-size:14px}
.sw-no{color:var(--c-mute);font-style:italic}
.sw-lk{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.sw .sw-lk a{display:inline-block;padding:3px 12px;line-height:1.5;height:auto;overflow:visible;border-radius:999px;border:1px solid var(--c-acc);border-bottom:1px solid var(--c-acc)!important;color:var(--c-acc)!important;font-size:12px;font-weight:600}
.sw .sw-lk a:hover{background:var(--c-acc);color:#fff!important}
@media(max-width:700px){.sw-item{padding-left:44px}.sw-item::before{left:8px}}
"""


def item(it: dict) -> str:
    if it.get("text"):
        body = f'<span class="sw-so">{escape(it["text"])}</span>'
    else:
        body = (
            (f'<span class="sw-au">{escape(it["authors"])}</span>' if it.get("authors") else "")
            + f'<span class="sw-ti">{escape(it["title"])}</span>'
            + (f'<span class="sw-so">{escape(it.get("source", ""))}'
               + (f' <span class="sw-no">{escape(it["note"])}</span>' if it.get("note") else "")
               + "</span>" if it.get("source") else ""))
    links = "".join(
        f'<a href="{escape(l["url"], quote=True)}" target="_blank" rel="noopener">↗ {escape(l["label"])}</a>'
        for l in it.get("links", []))
    if links:
        body += f'<span class="sw-lk">{links}</span>'
    return f'<li class="sw-item">{body}</li>'


def build(data: dict) -> str:
    years = sorted(data["years"], key=lambda y: -y["year"])
    parts = [f"<style>{year_css('sw')}{minify_css(CSS)}</style>", '<div class="sw">']
    parts.append('<nav class="sw-nav">' + "".join(
        f'<a href="#sw-{y["year"]}">{y["year"]}</a>' for y in years) + "</nav>")
    for i, y in enumerate(years):
        parts.append(
            f'<details class="sw-year" id="sw-{y["year"]}"{" open" if i == 0 else ""}>'
            f'<summary>{y["year"]} рік <span class="cnt">публікацій: {len(y["items"])}</span></summary>'
            '<ol class="sw-list">' + "".join(item(it) for it in y["items"]) + "</ol></details>")
    parts.append("</div>")
    return wrap("".join(parts))
