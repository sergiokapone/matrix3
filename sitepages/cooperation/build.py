"""Сторінка «Міжнародне наукове співробітництво» (apd.ipt.kpi.ua/international/cooperation/) з data.yaml.

Запуск: python sitepages/run.py cooperation generate|diff|upload (див. sitepages/common.py).
Партнери — картки в сітці: назва (посилання на сайт партнера), країна-бейдж, список заходів;
пункт може мати `url` (інакше простий текст). Один акцентний колір замість різнобарвних смуг
(жовтий текст був нечитабельним). Без CSS-escape кодів (WordPress їх ламає).
"""
from html import escape

from sitepages.common import minify_css, wrap

CSS = """
.co{--c-line:#d6dbe5;--c-text:#1d2433;--c-mute:#7a8396;--c-acc:#1f5fbf;--c-acc-bg:#eaf1fc;margin:0 0 2em;color:var(--c-text);line-height:1.5}
.co *{box-sizing:border-box}
.co a,.co a:hover{text-decoration:none!important;border-bottom:0!important}
.co a{color:var(--c-acc)}
.co-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}
.co-card{display:flex;flex-direction:column;padding:16px 18px;border:1px solid var(--c-line);border-top:4px solid var(--c-acc);border-radius:10px;background:#fff;box-shadow:0 1px 2px rgba(20,30,50,.05)}
.co-cn{align-self:flex-start;margin:0 0 8px;padding:2px 10px;border-radius:999px;background:var(--c-acc-bg);color:var(--c-acc);font-size:12px;font-weight:700;letter-spacing:.03em}
.co-nm{margin:0 0 10px;font-size:18px;font-weight:700;line-height:1.3}
.co-nm a:hover{text-decoration:underline!important}
.co-card ul{list-style:none!important;margin:0!important;padding:0!important}
.co-card li{list-style:none!important;position:relative;margin:0 0 8px!important;padding:0 0 0 18px;font-size:15px}
.co-card li:last-child{margin-bottom:0!important}
.co-card li::before{content:"";position:absolute;left:3px;top:8px;width:6px;height:6px;border-radius:50%;background:var(--c-acc)}
.co .co-lk{border-bottom:1px solid var(--c-acc)!important}
.co .co-lk:hover{background:var(--c-acc-bg)}
@media(max-width:400px){.co-grid{grid-template-columns:minmax(0,1fr)}}
"""


def item(it: dict) -> str:
    t = escape(it["text"])
    if it.get("url"):
        t = f'<a class="co-lk" href="{escape(it["url"], quote=True)}" target="_blank" rel="noopener">{t}</a>'
    return f"<li>{t}</li>"


def card(p: dict) -> str:
    name = escape(p["name"])
    if p.get("url"):
        name = f'<a href="{escape(p["url"], quote=True)}" target="_blank" rel="noopener">{name}</a>'
    return (f'<div class="co-card"><span class="co-cn">{escape(p["country"])}</span>'
            f'<h4 class="co-nm">{name}</h4><ul>{"".join(item(i) for i in p["items"])}</ul></div>')


def build(data: dict) -> str:
    return wrap(f"<style>{minify_css(CSS)}</style>"
                '<div class="co"><div class="co-grid">' + "".join(card(p) for p in data["partners"]) + "</div></div>")
