"""Сторінка «Методичні розробки кафедри» (apd.ipt.kpi.ua/method_works/).

Банер (live_original.html, до першого </div>) і шорткод kpi_shelf_collection лишаються без змін;
між ними — блок «Онлайн-посібники» (картки з data.yaml `guides`, нові додавати туди).
"""
from html import escape
from pathlib import Path

from sitepages.common import minify_css, wrap

CSS = """
.mw{--c-line:#d6dbe5;--c-text:#1d2433;--c-mute:#7a8396;--c-acc:#1f5fbf;--c-acc-bg:#eaf1fc;margin:0 0 1em;color:var(--c-text);line-height:1.5}
.mw *{box-sizing:border-box}
.mw a,.mw a:hover{text-decoration:none!important;border-bottom:0!important}
.mw h3{margin:10px 0 8px!important;padding:0 0 8px;border-bottom:2px solid var(--c-acc-bg);font-size:1.25em}
.mw-note{margin:0 0 14px;font-size:15px;color:#4a5368}
.mw-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.mw a.mw-card{display:flex;gap:14px;align-items:flex-start;padding:14px 16px;border:1px solid var(--c-line);border-bottom:1px solid var(--c-line)!important;border-radius:10px;background:#fff;box-shadow:0 1px 2px rgba(20,30,50,.05);color:var(--c-text)}
.mw a.mw-card:hover{border-color:var(--c-acc);border-bottom-color:var(--c-acc)!important;box-shadow:0 2px 8px rgba(31,95,191,.15)}
.mw-pic{flex:none;width:64px;height:64px;display:flex;align-items:center;justify-content:center;border-radius:12px;background:var(--c-acc-bg);color:var(--c-acc);overflow:hidden}
.mw-pic img{width:100%;height:100%;object-fit:cover;display:block}
.mw-tx{min-width:0}
.mw-nm{margin:0 0 6px;font-size:16px;font-weight:700;color:var(--c-acc);line-height:1.3}
.mw-au{margin:0 0 6px;font-size:13.5px;font-weight:600;color:var(--c-mute)}
.mw-ds{margin:0 0 10px;font-size:14.5px;color:#4a5368}
.mw-go{display:inline-block;padding:2px 10px;border-radius:999px;background:var(--c-acc-bg);color:var(--c-acc);font-size:13px;font-weight:600}
.mw-h2{margin:26px 0 8px!important}
"""


ICONS = {  # inline SVG, stroke=currentColor
    "magnet": '<path d="M5 3v8a7 7 0 0 0 14 0V3h-4v8a3 3 0 0 1-6 0V3z"/><path d="M5 7h4M15 7h4"/>',
    "plasma": '<circle cx="12" cy="12" r="2"/><ellipse cx="12" cy="12" rx="10" ry="4"/><ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(60 12 12)"/><ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(120 12 12)"/>',
    "optics": '<path d="M12 3c4 3 4 15 0 18-4-3-4-15 0-18z"/><path d="M2 12h20M2 12l3-2M2 12l3 2M22 12l-3-2M22 12l-3 2"/>',
    "thermo": '<path d="M10 14V5a2 2 0 0 1 4 0v9a4 4 0 1 1-4 0z"/><path d="M12 9v7"/>',
    "field": '<path d="M3 12h4l2-6 4 12 2-6h6"/>',
    "bolt": '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
    "molecule": '<circle cx="6" cy="17" r="3"/><circle cx="18" cy="17" r="3"/><circle cx="12" cy="6" r="3"/><path d="M8 15l3-7M16 15l-3-7M9 17h6"/>',
    "book": '<path d="M4 4h6a2 2 0 0 1 2 2v14a2 2 0 0 0-2-2H4z"/><path d="M20 4h-6a2 2 0 0 0-2 2v14a2 2 0 0 1 2-2h6z"/>',
}


def pic(g: dict) -> str:
    if g.get("image"):
        return f'<span class="mw-pic"><img src="{escape(g["image"], quote=True)}" alt="" loading="lazy"></span>'
    svg = ICONS.get(g.get("icon", "book"), ICONS["book"])
    return (f'<span class="mw-pic"><svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor" '
            f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{svg}</svg></span>')


def build(data: dict) -> str:
    live = (Path(__file__).parent / "live_original.html").read_bytes().decode("utf-8")
    banner = live[: live.index("</div>\n</div>") + len("</div>\n</div>")] if "</div>\n</div>" in live else live[: live.rindex("</div>") + 6]
    banner = banner.replace("\r\n", "\n")
    cards = "".join(
        f'<a class="mw-card" href="{escape(g["url"], quote=True)}" target="_blank" rel="noopener">'
        f'{pic(g)}<span class="mw-tx"><p class="mw-nm">{escape(g["name"])}</p><p class="mw-au">{escape(g["authors"])}</p><p class="mw-ds">{escape(g["desc"])}</p>'
        f'<span class="mw-go">Відкрити →</span></span></a>' for g in data["guides"])
    block = (f"<style>{minify_css(CSS)}</style>"
             f'<div class="mw"><h3>{escape(data["online_title"])}</h3><p class="mw-note">{escape(data["online_note"])}</p>'
             f'<div class="mw-grid">{cards}</div><h3 class="mw-h2">Видання в електронній бібліотеці ela.kpi.ua</h3></div>')
    return wrap(banner) + wrap(block) + f'[kpi_shelf_collection scope="{data["shelf_scope"]}"]'
