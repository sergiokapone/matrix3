"""Сторінка «Академічна мобільність» (apd.ipt.kpi.ua/international/mobility/) з data.yaml.

Запуск: python sitepages/run.py mobility generate|diff|upload (див. sitepages/common.py).
Блоки: банер + вступ, послуги (нумеровані картки), студенти (картки: фото, ім'я, період, місця, документи),
викладачі, координатор. Нова мобільність = новий запис у students (найновіші зверху).
Поле intro — готовий html (посилання). Без CSS-escape кодів (WordPress їх ламає).
"""
from html import escape

from sitepages.common import minify_css, wrap

CSS = """
.mb{--c-line:#d6dbe5;--c-text:#1d2433;--c-mute:#7a8396;--c-acc:#1f5fbf;--c-acc-bg:#eaf1fc;margin:0 0 2em;color:var(--c-text);line-height:1.5}
.mb *{box-sizing:border-box}
.mb a,.mb a:hover{text-decoration:none!important;border-bottom:0!important}
.mb a{color:var(--c-acc)}
.mb h3{margin:30px 0 14px!important;padding:0 0 8px;border-bottom:2px solid var(--c-acc-bg);font-size:1.25em}
.mb-hero{display:block;width:100%;height:190px;object-fit:cover;border-radius:12px;margin:0 0 16px}
.mb-intro{margin:0;padding:16px 20px;border:1px solid var(--c-line);border-left:5px solid var(--c-acc);border-radius:10px;background:#f6f8fc;font-size:15.5px}
.mb-intro a{border-bottom:1px solid var(--c-acc)!important}
.mb-srv{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;list-style:none!important;margin:0!important;padding:0!important;counter-reset:s}
.mb-srv li{list-style:none!important;margin:0!important;counter-increment:s;position:relative;padding:14px 16px 14px 56px;border:1px solid var(--c-line);border-radius:10px;background:#fff;font-size:15px;box-shadow:0 1px 2px rgba(20,30,50,.05)}
.mb-srv li::before{content:counter(s);position:absolute;left:14px;top:14px;width:28px;height:28px;border-radius:50%;background:var(--c-acc);color:#fff;font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center}
.mb-st{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:14px}
.mb-card{display:flex;gap:16px;padding:14px 16px;border:1px solid var(--c-line);border-radius:12px;background:#fff;box-shadow:0 1px 2px rgba(20,30,50,.05)}
.mb-ph{flex:none;width:84px;height:106px;border-radius:8px;overflow:hidden;background:var(--c-acc-bg);display:flex;align-items:center;justify-content:center;color:var(--c-acc);font-size:30px;font-weight:700}
.mb-ph img{display:block;width:100%;height:100%;object-fit:cover;object-position:center top}
.mb-bd{min-width:0}
.mb-nm{margin:0 0 4px;font-size:17px;font-weight:700;line-height:1.3}
.mb-pr{display:inline-block;margin:0 0 8px;padding:2px 10px;border-radius:999px;background:var(--c-acc-bg);color:var(--c-acc);font-size:13px;font-weight:700}
.mb-pr.plan{background:#fff4d6;color:#8a5a00}
.mb-pl{margin:0 0 6px;font-size:14.5px}
.mb-pl a{border-bottom:1px solid var(--c-acc)!important}
.mb-dc{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.mb .mb-dc a,.mb .mb-dc span{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12.5px;font-weight:600}
.mb .mb-dc a{border:1px solid var(--c-acc);border-bottom:1px solid var(--c-acc)!important;color:var(--c-acc)}
.mb .mb-dc a:hover{background:var(--c-acc);color:#fff}
.mb .mb-dc span{background:#f1f3f8;color:var(--c-mute)}
.mb-tc{display:grid;gap:12px;list-style:none!important;margin:0!important;padding:0!important}
.mb-tc li{list-style:none!important;margin:0!important;display:flex;gap:16px;align-items:center;padding:14px 18px;border:1px solid var(--c-line);border-left:5px solid var(--c-acc);border-radius:10px;background:#fff;font-size:15px}
.mb-tc .mb-ph{width:76px;height:96px}
.mb-tc .mb-dc{margin-top:8px}
.mb-co{display:flex;gap:16px;align-items:center;margin:26px 0 0;padding:14px 20px;border-radius:10px;background:var(--c-acc-bg);font-size:16px}
.mb-co .mb-ph{background:#fff;width:76px;height:96px}
.mb-co p{margin:0}
.mb-co a{font-weight:700}
@media(max-width:520px){.mb-st{grid-template-columns:minmax(0,1fr)}.mb-hero{height:130px}}
"""


def initials(name: str) -> str:
    return escape(name[:1])


def links(items: list, note: str | None = None) -> str:
    parts = [f'<a href="{escape(d["url"], quote=True)}" target="_blank" rel="noopener">{escape(d["text"])}</a>' for d in items]
    if note:
        parts.append(f"<span>{escape(note)}</span>")
    return f'<div class="mb-dc">{"".join(parts)}</div>' if parts else ""


def student(s: dict) -> str:
    ph = (f'<img src="{escape(s["photo"], quote=True)}" alt="{escape(s["name"], quote=True)}" loading="lazy">'
          if s.get("photo") else initials(s["name"]))
    places = "".join(f'<p class="mb-pl"><a href="{escape(x["url"], quote=True)}" target="_blank" rel="noopener">{escape(x["text"])}</a></p>'
                     for x in s["places"])
    cls = "mb-pr plan" if s.get("planned") else "mb-pr"
    return (f'<div class="mb-card"><div class="mb-ph">{ph}</div><div class="mb-bd"><p class="mb-nm">{escape(s["name"])}</p>'
            f'<span class="{cls}">{escape(s["period"])}</span>{places}{links(s["docs"], s.get("docs_note"))}</div></div>')


def teacher(t: dict) -> str:
    ph = (f'<a class="mb-ph" href="{escape(t["url"], quote=True)}"><img src="{escape(t["photo"], quote=True)}" '
          f'alt="{escape(t["name"], quote=True)}" loading="lazy"></a>') if t.get("photo") else ""
    return (f'<li>{ph}<div class="mb-bd"><a href="{escape(t["url"], quote=True)}"><strong>{escape(t["name"])}</strong></a> — '
            f'{escape(t["text"])}{links(t["links"])}</div></li>')


def build(data: dict) -> str:
    p = [f"<style>{minify_css(CSS)}</style>", '<div class="mb">']
    if data.get("hero"):
        p.append(f'<img class="mb-hero" src="{escape(data["hero"], quote=True)}" alt="Академічна мобільність">')
    p.append(f'<p class="mb-intro">{data["intro"]}</p>')
    p.append(f'<h3>{escape(data["services_title"])}</h3><ol class="mb-srv">' + "".join(f"<li>{escape(x)}</li>" for x in data["services"]) + "</ol>")
    p.append(f'<h3>{escape(data["students_title"])}</h3><div class="mb-st">' + "".join(student(s) for s in data["students"]) + "</div>")
    p.append(f'<h3>{escape(data["teachers_title"])}</h3><ul class="mb-tc">' + "".join(teacher(t) for t in data["teachers"]) + "</ul>")
    u = escape(data["coordinator_url"], quote=True)
    cph = (f'<a class="mb-ph" href="{u}"><img src="{escape(data["coordinator_photo"], quote=True)}" '
           f'alt="{escape(data["coordinator_name"], quote=True)}" loading="lazy"></a>') if data.get("coordinator_photo") else ""
    p.append(f'<div class="mb-co">{cph}<p>{escape(data["coordinator"])}: <a href="{u}"><strong>{escape(data["coordinator_name"])}</strong></a></p></div>')
    p.append("</div>")
    return wrap("".join(p))
