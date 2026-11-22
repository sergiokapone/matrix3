"""Сторінка «Досягнення» (apd.ipt.kpi.ua/kafedra/achievements/) з data.yaml.

Запуск: python sitepages/run.py achievements generate|diff|upload (див. sitepages/common.py).
Розділ 1 «Досягнення викладачів»: картка на викладача (фото, ім'я-посилання, кількість записів), записи — рядки
з бейджами ECTS і годин (картки не розгортаються). Розділ 2 «Досягнення студентів»: роки-розгортки (спільний year_css), записи — картки
(заголовок-посилання + рядки). Усі посилання з рамкою мають власну нижню межу !important (див. скіл apd-site).
Без CSS-escape кодів (WordPress їх ламає).
"""
from html import escape

from sitepages.common import minify_css, person_url, wrap, year_css

CSS = """
.ac h3{margin:28px 0 14px!important;padding:0 0 8px;border-bottom:2px solid var(--c-acc-bg);font-size:1.3em}
.ac h3:first-child{margin-top:0!important}
.ac-nav{margin:0 0 14px}
.ac-year .ac-body{padding:6px 0}
.ac-it{padding:12px 16px;border-bottom:1px solid #eef0f5;color:var(--c-text);font-size:15px;line-height:1.5}
.ac-it:last-child{border-bottom:0}
.ac-t{margin:0;font-weight:700}
.ac-t a{color:var(--c-acc);border-bottom:1px solid var(--c-acc)!important}
.ac-t a:hover{background:var(--c-acc-bg)}
.ac-ls{list-style:none!important;margin:6px 0 0!important;padding:0!important}
.ac-ls li{list-style:none!important;position:relative;margin:0 0 4px!important;padding:0 0 0 16px;font-size:14.5px;color:#3a4358}
.ac-ls li::before{content:"";position:absolute;left:2px;top:9px;width:6px;height:6px;border-radius:50%;background:var(--c-acc)}
.ac-tt{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 8px}
.ac-tt .ac-t{flex:1 1 380px;font-weight:600}
.ac-b{display:inline-block;padding:1px 9px;border-radius:999px;font-size:12.5px;font-weight:700;white-space:nowrap}
.ac-e{background:var(--c-acc-bg);color:var(--c-acc)}
.ac-h{background:#f1f3f8;color:#4a5368}
.ac-n{font-size:13px;color:var(--c-mute);font-style:italic}
.ac-tgrid{display:grid;grid-template-columns:minmax(0,1fr);gap:14px}
.ac-card{border:1px solid var(--c-line);border-radius:12px;background:#fff;box-shadow:0 1px 2px rgba(20,30,50,.05);overflow:hidden}
.ac-hd{display:flex;gap:16px;align-items:center;padding:14px 16px;background:#f6f8fc;border-bottom:1px solid var(--c-line)}
.ac-ph{flex:none;width:76px;height:96px;border-radius:8px;overflow:hidden;background:var(--c-acc-bg);display:flex;align-items:center;justify-content:center;color:var(--c-acc);font-size:28px;font-weight:700}
.ac-ph img{display:block;width:100%;height:100%;object-fit:cover;object-position:center top}
.ac-nm{margin:0;font-size:18px;font-weight:700;line-height:1.3}
.ac-nm a{color:var(--c-text)!important}
.ac-nm a:hover{color:var(--c-acc)!important}
.ac-ct{display:inline-block;margin-top:6px;padding:1px 10px;border-radius:999px;background:var(--c-acc-bg);color:var(--c-acc);font-size:12.5px;font-weight:700}
"""


def teacher_item(i: dict) -> str:
    b = ""
    if i.get("e"):
        b += f'<span class="ac-b ac-e">{escape(str(i["e"]))} ECTS</span>'
    if i.get("h"):
        b += f'<span class="ac-b ac-h">{escape(str(i["h"]))} год.</span>'
    if i.get("n"):
        b += f'<span class="ac-n">{escape(i["n"])}</span>'
    return f'<div class="ac-it ac-tt"><p class="ac-t">{escape(i["t"])}</p>{b}</div>'


def teacher(t: dict) -> str:
    n = len(t["items"])
    url = person_url(t["name"])
    ph = f'<img src="{escape(t["photo"], quote=True)}" alt="{escape(t["name"], quote=True)}" loading="lazy">' if t.get("photo") else escape(t["name"][:1])
    if url:
        u = escape(url, quote=True)
        ph = f'<a class="ac-ph" href="{u}">{ph}</a>'
        name = f'<a href="{u}">{escape(t["name"])}</a>'
    else:
        ph = f'<span class="ac-ph">{ph}</span>'
        name = escape(t["name"])
    return (f'<div class="ac-card"><div class="ac-hd">{ph}<div><p class="ac-nm">{name}</p>'
            f'<span class="ac-ct">записів: {n}</span></div></div>'
            f'<div class="ac-body">{"".join(teacher_item(i) for i in t["items"])}</div></div>')


def student_item(i: dict) -> str:
    title = escape(i["text"])
    if i.get("url"):
        title = f'<a href="{escape(i["url"], quote=True)}" target="_blank" rel="noopener">{title}</a>'
    lines = ""
    if i.get("lines"):
        lines = '<ul class="ac-ls">' + "".join(f"<li>{escape(x)}</li>" for x in i["lines"]) + "</ul>"
    return f'<div class="ac-it"><p class="ac-t">{title}</p>{lines}</div>'


def build(data: dict) -> str:
    ys = sorted(data["students"], key=lambda y: -y["year"])
    p = [f"<style>{year_css('ac')}{minify_css(CSS)}</style>", '<div class="ac"><h3>Досягнення викладачів</h3>']
    p.append('<div class="ac-tgrid">' + "".join(teacher(t) for t in data["teachers"]) + "</div>")
    p.append("<h3>Досягнення студентів</h3>")
    p.append('<nav class="ac-nav">' + "".join(f'<a href="#ac-{y["year"]}">{y["year"]}</a>' for y in ys) + "</nav>")
    for k, y in enumerate(ys):
        p.append(f'<details class="ac-year" id="ac-{y["year"]}"{" open" if k == 0 else ""}><summary>{y["year"]} рік '
                 f'<span class="cnt">досягнень: {len(y["items"])}</span></summary><div class="ac-body">'
                 + "".join(student_item(i) for i in y["items"]) + "</div></details>")
    p.append("</div>")
    return wrap("".join(p))
