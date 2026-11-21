"""Сторінка «Партнери кафедри» (apd.ipt.kpi.ua/international/partners/) з data.yaml.

Запуск: python sitepages/run.py partners generate|diff|upload (див. sitepages/common.py).
Групи (установи НАН / підприємства) — картки в сітці: логотип у рамці однакового розміру (object-fit:contain),
назва (посилання на сайт), строк дії договору (посилання на скан договору). Без logo — літерна заглушка.
Логотипи лежать на самому сайті (wp-content/uploads), не на чужих серверах. Без CSS-escape кодів.
"""
from html import escape

from sitepages.common import minify_css, wrap

CSS = """
.pt{--c-line:#d6dbe5;--c-text:#1d2433;--c-mute:#7a8396;--c-acc:#1f5fbf;--c-acc-bg:#eaf1fc;margin:0 0 2em;color:var(--c-text);line-height:1.5}
.pt *{box-sizing:border-box}
.pt a,.pt a:hover{text-decoration:none!important;border-bottom:0!important}
.pt a{color:var(--c-acc)}
.pt-lead{margin:0 0 6px;font-size:16.5px;font-weight:600}
.pt-note{margin:0 0 14px;font-size:15px;color:#4a5368}
.pt-nav{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 6px}
.pt .pt-nav a{padding:6px 14px;border-radius:999px;background:var(--c-acc-bg);font-weight:600;font-size:14px;border:1px solid transparent}
.pt .pt-nav a:hover{border-color:var(--c-acc)}
.pt h3{margin:26px 0 14px!important;padding:0 0 8px;border-bottom:2px solid var(--c-acc-bg);font-size:1.25em}
.pt-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:14px}
.pt-card{display:flex;gap:14px;align-items:center;padding:12px 14px;border:1px solid var(--c-line);border-radius:10px;background:#fff;box-shadow:0 1px 2px rgba(20,30,50,.05)}
.pt-lg{flex:none;width:96px;height:72px;display:flex;align-items:center;justify-content:center;border-radius:8px;background:#fff;border:1px solid #eef0f5;overflow:hidden}
.pt-lg img{display:block;max-width:100%;max-height:100%;width:auto;height:auto;object-fit:contain}
.pt-lg span{font-size:22px;font-weight:700;color:var(--c-acc);background:var(--c-acc-bg);width:100%;height:100%;display:flex;align-items:center;justify-content:center}
.pt-tx{min-width:0}
.pt-nm{margin:0 0 6px;font-size:15.5px;font-weight:700;line-height:1.3}
.pt-nm a:hover{text-decoration:underline!important}
.pt .pt-dt{display:inline-block;padding:2px 10px;border-radius:999px;background:var(--c-acc-bg);font-size:13px;font-weight:600;white-space:nowrap}
.pt .pt-dt:hover{background:var(--c-acc);color:#fff}
@media(max-width:420px){.pt-grid{grid-template-columns:minmax(0,1fr)}}
"""


def card(p: dict) -> str:
    name = escape(p["name"])
    if p.get("url"):
        name = f'<a href="{escape(p["url"], quote=True)}" target="_blank" rel="noopener">{name}</a>'
    if p.get("logo"):
        logo = f'<img src="{escape(p["logo"], quote=True)}" alt="{escape(p["name"], quote=True)}" loading="lazy">'
    else:
        logo = f'<span>{escape(p["name"][0])}</span>'
    dt = (f'<a class="pt-dt" href="{escape(p["doc"], quote=True)}" target="_blank" rel="noopener" '
          f'title="Договір (скан)">Договір: {escape(p["dates"])}</a>')
    return f'<div class="pt-card"><div class="pt-lg">{logo}</div><div class="pt-tx"><p class="pt-nm">{name}</p>{dt}</div></div>'


def build(data: dict) -> str:
    p = [f"<style>{minify_css(CSS)}</style>", '<div class="pt">', f'<p class="pt-lead">{escape(data["lead"])}</p>',
         f'<p class="pt-note">{escape(data["note"])}</p>',
         '<nav class="pt-nav">' + "".join(
             f'<a href="{escape(x["url"], quote=True)}">{escape(x["label"])}</a>' for x in data["links"]) + "</nav>"]
    for g in data["groups"]:
        p.append(f'<h3>{escape(g["title"])}</h3><div class="pt-grid">' + "".join(card(x) for x in g["partners"]) + "</div>")
    p.append("</div>")
    return wrap("".join(p))
