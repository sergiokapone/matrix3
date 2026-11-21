"""Сторінка «Контакти» (apd.ipt.kpi.ua/main/contacts/) з data.yaml.

Запуск: python sitepages/run.py contacts generate|diff|upload (див. sitepages/common.py).
Картки зв'язку (телефон, пошта, адреса), плитки соцмереж, карта Google. Іконки — вбудований SVG
(без Font Awesome з CDN); логотипи соцмереж — Font Awesome Free 6.5.2 (CC BY 4.0), файли в icons/. Без CSS-escape кодів.
"""
import re
from html import escape
from pathlib import Path

from sitepages.common import minify_css, wrap

CSS = """
.ct{--c-line:#d6dbe5;--c-text:#1d2433;--c-mute:#7a8396;--c-acc:#1f5fbf;--c-acc-bg:#eaf1fc;margin:0 0 2em;color:var(--c-text);line-height:1.5}
.ct *{box-sizing:border-box}
.ct a,.ct a:hover{text-decoration:none!important;border-bottom:0!important}
.ct h3{margin:30px 0 14px!important;padding:0 0 8px;border-bottom:2px solid var(--c-acc-bg);font-size:1.3em}
.ct h3:first-child{margin-top:0!important}
.ct-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}
.ct a.ct-card{border-bottom:1px solid var(--c-line)!important}
.ct a.ct-card:hover{border-bottom-color:var(--c-acc)!important}
.ct .ct-card{display:flex;gap:14px;align-items:center;padding:16px 18px;border:1px solid var(--c-line);border-radius:12px;background:#fff;color:var(--c-text)!important;box-shadow:0 1px 2px rgba(20,30,50,.05)}
.ct a.ct-card:hover{border-color:var(--c-acc);box-shadow:0 3px 10px rgba(31,95,191,.18);transform:translateY(-1px)}
.ct-ic{flex:none;width:46px;height:46px;border-radius:12px;background:var(--c-acc-bg);color:var(--c-acc);display:flex;align-items:center;justify-content:center}
.ct-ic svg{width:22px;height:22px;display:block}
.ct-lb{display:block;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--c-mute);font-weight:700}
.ct-v{display:block;font-size:17px;font-weight:700;line-height:1.3;word-break:break-word}
.ct-tag{flex:none;width:46px;height:46px;border-radius:12px;color:#fff;display:flex;align-items:center;justify-content:center}
.ct-tag svg{width:22px;height:22px;display:block}
.ct-h{display:block;font-size:14px;color:var(--c-mute)}
.ct-soc{display:flex;flex-wrap:wrap;gap:14px}
.ct-soc .ct-card{flex:1 1 280px}
.ct-map{overflow:hidden;border:1px solid var(--c-line);border-radius:12px;box-shadow:0 1px 2px rgba(20,30,50,.05)}
.ct-map iframe{display:block;width:100%;height:420px;border:0}
@media(max-width:600px){.ct-map iframe{height:320px}}
"""

PHONE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>'
MAIL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><polyline points="22,6 12,13 2,6"/></svg>'
PIN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>'


def brand(name: str) -> str:
    """SVG логотипу з icons/<name>.svg (без службового коментаря), заливка — колір тексту."""
    svg = (Path(__file__).parent / "icons" / f"{name}.svg").read_text(encoding="utf-8")
    svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S)
    return svg.replace("<svg ", '<svg fill="currentColor" ', 1)


def contact(icon: str, label: str, value: str, href: str | None = None) -> str:
    inner = (f'<span class="ct-ic">{icon}</span><span><span class="ct-lb">{label}</span>'
             f'<span class="ct-v">{escape(value)}</span></span>')
    if href:
        return f'<a class="ct-card" href="{escape(href, quote=True)}">{inner}</a>'
    return f'<div class="ct-card">{inner}</div>'


def social(s: dict) -> str:
    return (f'<a class="ct-card" href="{escape(s["url"], quote=True)}" target="_blank" rel="noopener">'
            f'<span class="ct-tag" style="background:{s["color"]}">{brand(s["icon"])}</span>'
            f'<span><span class="ct-v">{escape(s["name"])}</span><span class="ct-h">{escape(s["handle"])}</span></span></a>')


def build(data: dict) -> str:
    p = [f"<style>{minify_css(CSS)}</style>", '<div class="ct"><h3>Наші контакти</h3><div class="ct-grid">',
         contact(PHONE, "Телефон", data["phone"], "tel:" + data["phone_href"]),
         contact(MAIL, "Електронна пошта", data["email"], "mailto:" + data["email"]),
         contact(PIN, "Адреса", data["address"]),
         '</div><h3>Ми в соцмережах</h3><div class="ct-soc">',
         "".join(social(s) for s in data["social"]),
         '</div><h3>Ми на карті</h3>',
         f'<div class="ct-map"><iframe src="{escape(data["map"], quote=True)}" allowfullscreen loading="lazy" '
         'referrerpolicy="no-referrer-when-downgrade" title="Карта"></iframe></div></div>']
    return wrap("".join(p))
