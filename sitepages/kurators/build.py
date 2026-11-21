"""Сторінка «Куратори студентських груп» (apd.ipt.kpi.ua/kurators/) з data.yaml.

Запуск: python sitepages/run.py kurators generate|diff|upload (див. sitepages/common.py).
Куратори — картки в сітці: фото (однаковий розмір, object-fit:cover), бейдж групи, ПІБ-посилання
на персональну сторінку. Розділи «Куратори бакалаврату» / «Куратори магістратури» — за суфіксом «мн» у назві групи; у розділі групи — від новіших (більша цифра = пізніший вступ) до старших. Без CSS-escape кодів.
"""
import re
from html import escape

from sitepages.common import minify_css, wrap

CSS = """
.ku{--c-line:#d6dbe5;--c-text:#1d2433;--c-mute:#7a8396;--c-acc:#1f5fbf;--c-acc-bg:#eaf1fc;margin:0 0 2em;color:var(--c-text);line-height:1.5}
.ku *{box-sizing:border-box}
.ku a,.ku a:hover{text-decoration:none!important;border-bottom:0!important}
.ku-intro{margin:0 0 22px;padding:16px 20px;border:1px solid var(--c-line);border-left:5px solid var(--c-acc);border-radius:10px;background:#f6f8fc;font-size:16px}
.ku h3{margin:26px 0 14px!important;padding:0 0 8px;border-bottom:2px solid var(--c-acc-bg);font-size:1.25em}
.ku-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.ku a.ku-card{border-bottom:1px solid var(--c-line)!important}
.ku a.ku-card:hover{border-bottom-color:var(--c-acc)!important}
.ku .ku-card{display:flex;gap:16px;align-items:center;padding:12px 14px;border:1px solid var(--c-line);border-radius:10px;background:#fff;color:var(--c-text)!important;box-shadow:0 1px 2px rgba(20,30,50,.05)}
.ku .ku-card:hover{border-color:var(--c-acc);box-shadow:0 2px 8px rgba(31,95,191,.18)}
.ku-ph{flex:none;width:76px;height:96px;border-radius:8px;overflow:hidden;background:var(--c-acc-bg)}
.ku-ph img{display:block;width:100%;height:100%;object-fit:cover;object-position:center top}
.ku-gr{display:inline-block;margin:0 0 6px;padding:2px 11px;border-radius:999px;background:var(--c-acc);color:#fff;font-size:13px;font-weight:700}
.ku-nm{display:block;font-size:16px;font-weight:700;line-height:1.3}
.ku-card:hover .ku-nm{color:var(--c-acc)}
@media(max-width:360px){.ku-grid{grid-template-columns:minmax(0,1fr)}}
"""


def card(k: dict) -> str:
    return (f'<a class="ku-card" href="{escape(k["url"], quote=True)}">'
            f'<span class="ku-ph"><img src="{escape(k["photo"], quote=True)}" alt="{escape(k["name"], quote=True)}" loading="lazy"></span>'
            f'<span><span class="ku-gr">{escape(k["group"])}</span><span class="ku-nm">{escape(k["name"])}</span></span></a>')


def build(data: dict) -> str:
    """Групи з «мн» наприкінці — магістратура, решта — бакалаврат."""
    def newest_first(rows):  # ФФ-61 — вступ 2026: новіші групи вгорі
        return sorted(rows, key=lambda k: -int(re.search(r"\d+", k["group"]).group()))

    mas = newest_first(k for k in data["kurators"] if k["group"].endswith("мн"))
    bach = newest_first(k for k in data["kurators"] if not k["group"].endswith("мн"))
    parts = [f"<style>{minify_css(CSS)}</style>", f'<div class="ku"><p class="ku-intro">{escape(data["intro"])}</p>']
    for title, rows in (("Куратори бакалаврату", bach), ("Куратори магістратури", mas)):
        if rows:
            parts.append(f'<h3>{title}</h3><div class="ku-grid">' + "".join(card(k) for k in rows) + "</div>")
    parts.append("</div>")
    return wrap("".join(parts))
