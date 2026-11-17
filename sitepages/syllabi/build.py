"""Сторінка «Силабуси» (apd.ipt.kpi.ua/for_stud/syllab_potoch/) з data.yaml.

Запуск: python sitepages/run.py syllabi generate|diff|upload (див. sitepages/common.py).
Курс без `url` показується як неактивна картка «Незабаром».
"""
from html import escape
from urllib.parse import urlparse

KINDS = {  # ключ -> (мітка на бейджі, підпис)
    "pdf": ("PDF", "PDF"),
    "drive": ("DR", "Google Drive"),
    "gdoc": ("DOC", "Google Doc"),
    "osvita": ("KPI", "osvita.kpi.ua"),
    "web": ("WEB", "Сайт"),
    "none": ("···", "Незабаром"),
}


def kind(url: str | None) -> str:
    if not url:
        return "none"
    u = urlparse(url)
    host, path = u.netloc, u.path.lower()
    if "docs.google.com" in host:
        return "gdoc"
    if "drive.google.com" in host:
        return "drive"
    if path.endswith(".pdf"):
        return "pdf"
    if "osvita.kpi.ua" in host:
        return "osvita"
    return "web"


CSS = """
.syl{--c-bg:#fff;--c-line:#d6dbe5;--c-text:#1d2433;--c-mute:#7a8396;--c-acc:#1f5fbf;--c-acc-bg:#eaf1fc;margin:0 0 2em}
.syl *{box-sizing:border-box}
.syl-nav{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 1.6em}
.syl-nav a{padding:6px 14px;border-radius:999px;background:var(--c-acc-bg);color:var(--c-acc)!important;font-weight:600;font-size:14px;text-decoration:none;border:1px solid transparent}
.syl a,.syl a:hover,.syl a:focus{text-decoration:none!important;border-bottom:0!important}
.syl-nav a:hover{border-color:var(--c-acc)}
.syl-nav .m{background:#f3ecfb;color:#6b3fa0!important}
.syl-group{margin:2em 0 .6em;display:flex;align-items:baseline;flex-wrap:wrap;gap:10px;padding-bottom:6px;border-bottom:2px solid var(--c-acc)}
.syl-group h3{margin:0;font-size:1.35em}
.syl-group .cnt{color:var(--c-mute);font-size:14px}
.syl-sub{margin:1.1em 0 .5em;font-size:13px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--c-mute)}
.syl-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.syl-card{display:flex;gap:12px;align-items:flex-start;padding:12px 14px;background:var(--c-bg);border:1px solid var(--c-line);border-radius:10px;color:var(--c-text);text-decoration:none;box-shadow:0 1px 2px rgba(20,30,50,.05);transition:transform .12s,box-shadow .12s,border-color .12s}
a.syl-card:hover{transform:translateY(-2px);box-shadow:0 6px 16px rgba(20,30,50,.12);border-color:var(--c-acc);color:var(--c-text)}
.syl-badge{flex:none;width:42px;height:42px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:#fff;background:#1f5fbf}
.syl-pdf .syl-badge{background:#d33a2c}
.syl-drive .syl-badge{background:#1a9460}
.syl-gdoc .syl-badge{background:#2f6fe0}
.syl-osvita .syl-badge{background:#c77d0a}
.syl-web .syl-badge{background:#6b3fa0}
.syl-none{background:#f6f7f9;border-style:dashed;box-shadow:none;color:var(--c-mute)}
.syl-none .syl-badge{background:#c9ceda}
.syl-txt{display:flex;flex-direction:column;gap:3px;min-width:0}
.syl .syl-name{color:var(--c-text)!important;font-weight:600;line-height:1.3;font-size:15px;overflow-wrap:anywhere}
.syl .syl-src{font-size:12px;color:var(--c-mute)}
"""


def card(c: dict) -> str:
    url = c.get("url")
    k = kind(url)
    badge, src = KINDS[k]
    body = (
        f'<span class="syl-badge">{badge}</span><span class="syl-txt">'
        f'<span class="syl-name">{escape(c["name"])}</span>'
        f'<span class="syl-src">{src}</span></span>'
    )
    if url:
        return (f'<a class="syl-card syl-{k}" href="{escape(url, quote=True)}" '
                f'target="_blank" rel="noopener">{body}</a>')
    return f'<div class="syl-card syl-none">{body}</div>'


def count(items: list) -> tuple[int, int]:
    return sum(1 for c in items if c.get("url")), len(items)


def build(data: dict) -> str:
    groups = data["groups"]
    parts = [f"<style>{CSS.strip().replace(chr(10), '')}</style>", '<div class="syl">']
    nav = "".join(
        f'<a class="{"m" if g.get("level") == "master" else ""}" href="#syl-{i}">{escape(g["group"])}</a>'
        for i, g in enumerate(groups)
    )
    parts.append(f'<nav class="syl-nav">{nav}</nav>')
    for i, g in enumerate(groups):
        allc = g["courses"] + g.get("electives", [])
        have, tot = count(allc)
        parts.append(
            f'<div class="syl-group" id="syl-{i}"><h3>Група {escape(g["group"])}</h3>'
            f'<span class="cnt">силабусів: {have} з {tot}</span></div>'
        )
        parts.append('<div class="syl-grid">' + "".join(card(c) for c in g["courses"]) + "</div>")
        if g.get("electives"):
            parts.append('<div class="syl-sub">Вибіркові дисципліни</div>')
            parts.append('<div class="syl-grid">' + "".join(card(c) for c in g["electives"]) + "</div>")
    parts.append("</div>")
    return "<!-- wp:html -->" + "".join(parts) + "<!-- /wp:html -->"
