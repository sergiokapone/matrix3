"""Сторінка «Лабораторія ФіНоТех» (apd.ipt.kpi.ua/nauka/lab/) з data.yaml.

Запуск: python sitepages/run.py lab generate|diff|upload (див. sitepages/common.py).
Блоки: вступ + паспорт, картки керівництва, напрями (сітка), завдання/функції (нумеровані картки з фото),
матеріально-технічне забезпечення (сітка карток з двома фото). Без CSS-escape кодів (WordPress їх ламає).
Поля intro, tasks[], functions[].text можуть містити готовий html (<strong>, <a>); решта екранується.
"""
from html import escape

from sitepages.common import minify_css, wrap

CSS = """
.lb{--c-line:#d6dbe5;--c-text:#1d2433;--c-mute:#7a8396;--c-acc:#1f5fbf;--c-acc-bg:#eaf1fc;margin:0 0 2em;color:var(--c-text);line-height:1.5}
.lb *{box-sizing:border-box}
.lb a,.lb a:hover{text-decoration:none!important;border-bottom:0!important}
.lb a{color:var(--c-acc)}
.lb-intro{display:flex;flex-wrap:wrap;gap:12px 20px;align-items:center;justify-content:space-between;padding:18px 20px;margin:0 0 20px;border:1px solid var(--c-line);border-left:5px solid var(--c-acc);border-radius:10px;background:#f6f8fc;font-size:16px}
.lb-intro p{margin:0;flex:1 1 380px}
.lb .lb-btn{display:inline-block;padding:8px 18px;border-radius:999px;background:var(--c-acc);color:#fff!important;font-weight:600;font-size:14px;white-space:nowrap}
.lb .lb-btn:hover{background:#174a96}
.lb-people{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;margin:0 0 28px}
.lb-person{display:flex;gap:16px;align-items:center;padding:14px 18px;border:1px solid var(--c-line);border-radius:10px;box-shadow:0 1px 2px rgba(20,30,50,.05)}
.lb-pph{flex:none;width:84px;height:106px;border-radius:8px;overflow:hidden;background:var(--c-acc-bg)}
.lb-pph img{display:block;width:100%;height:100%;object-fit:cover;object-position:center top}
.lb-role{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--c-mute);font-weight:700}
.lb-name{font-size:18px;font-weight:700;margin:2px 0}
.lb-post{font-size:14px;color:var(--c-mute)}
.lb h3{margin:30px 0 14px!important;padding:0 0 8px;border-bottom:2px solid var(--c-acc-bg);font-size:1.3em}
.lb-lead{margin:0 0 14px;font-size:16px}
.lb-dirs{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px;list-style:none!important;margin:0 0 8px!important;padding:0!important;counter-reset:d}
.lb-dirs li{list-style:none!important;margin:0!important;counter-increment:d;position:relative;padding:12px 14px 12px 54px;border:1px solid var(--c-line);border-radius:10px;background:#fff;font-size:14.5px}
.lb-dirs li::before{content:counter(d);position:absolute;left:14px;top:12px;width:28px;height:28px;border-radius:50%;background:var(--c-acc-bg);color:var(--c-acc);font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center}
.lb-cards{display:grid;gap:12px;list-style:none!important;margin:0!important;padding:0!important;counter-reset:t}
.lb-cards li{list-style:none!important;margin:0!important;counter-increment:t;position:relative;padding:14px 16px 14px 56px;border:1px solid var(--c-line);border-radius:10px;background:#fff;box-shadow:0 1px 2px rgba(20,30,50,.05)}
.lb-cards li::before{content:counter(t);position:absolute;left:14px;top:14px;width:28px;height:28px;border-radius:50%;background:var(--c-acc);color:#fff;font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center}
.lb-ct{font-weight:700;margin:0 0 4px}
.lb-cx{margin:0;color:#3a4358;font-size:15px}
.lb-demo{margin:14px 0 0;padding:14px 16px;border:1px solid var(--c-line);border-radius:10px;background:#f6f8fc}
.lb-demo-h{margin:0 0 10px;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--c-mute);font-weight:700}
.lb-demo .wp-video,.lb-demo video{max-width:100%!important;height:auto;margin:0 auto}
.lb-ph{display:flex;flex-wrap:wrap;gap:10px;margin:10px 0 0}
.lb-ph img{display:block;width:calc(50% - 5px);max-width:300px;height:auto;aspect-ratio:3/2;object-fit:cover;border-radius:8px;border:1px solid var(--c-line)}
.lb-eq{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.lb-eqc{padding:14px 16px;border:1px solid var(--c-line);border-radius:10px;background:#fff;box-shadow:0 1px 2px rgba(20,30,50,.05)}
.lb-eqc .lb-ct{margin:0}
@media(max-width:600px){.lb-ph img{width:100%;max-width:none}}
"""


def photos(urls: list | None, alt: str) -> str:
    if not urls:
        return ""
    return '<div class="lb-ph">' + "".join(
        f'<img src="{escape(u, quote=True)}" alt="{escape(alt, quote=True)}" loading="lazy">' for u in urls) + "</div>"


def person_photo(x: dict) -> str:
    if not x.get("photo"):
        return ""
    return (f'<a class="lb-pph" href="{escape(x["url"], quote=True)}"><img src="{escape(x["photo"], quote=True)}" '
            f'alt="{escape(x["name"], quote=True)}" loading="lazy"></a>')


def build(data: dict) -> str:
    p = [f"<style>{minify_css(CSS)}</style>", '<div class="lb">']
    p.append(f'<div class="lb-intro"><p>{data["intro"]}</p>'
             f'<a class="lb-btn" href="{escape(data["passport"], quote=True)}" target="_blank" rel="noopener">Паспорт лабораторії</a></div>')
    p.append('<div class="lb-people">' + "".join(
        f'<div class="lb-person">{person_photo(x)}<div><div class="lb-role">{escape(x["role"])}</div>'
        f'<div class="lb-name"><a href="{escape(x["url"], quote=True)}">{escape(x["name"])}</a></div>'
        f'<div class="lb-post">{escape(x["post"])}</div></div></div>' for x in data["people"]) + "</div>")
    p.append(f'<p class="lb-lead">{escape(data["mission"])}:</p>')
    p.append('<ul class="lb-dirs">' + "".join(f"<li>{escape(d)}</li>" for d in data["directions"]) + "</ul>")
    p.append("<h3>Основні завдання лабораторії</h3>")
    p.append('<ol class="lb-cards">' + "".join(f'<li><p class="lb-cx">{t}</p></li>' for t in data["tasks"]) + "</ol>")
    if data.get("video"):
        p.append(f'<div class="lb-demo"><div class="lb-demo-h">{escape(data.get("demo_caption", "Демонстрації"))}</div>{data["video"]}</div>')
    p.append("<h3>Функції лабораторії</h3>")
    p.append('<ol class="lb-cards">' + "".join(
        f'<li><p class="lb-ct">{escape(f["title"])}</p><p class="lb-cx">{f["text"]}</p>{photos(f.get("photos"), f["title"])}</li>'
        for f in data["functions"]) + "</ol>")
    p.append("<h3>Матеріально-технічне забезпечення</h3>")
    p.append(f'<p class="lb-lead">{escape(data["equipment_intro"])}:</p>')
    p.append('<div class="lb-eq">' + "".join(
        f'<div class="lb-eqc"><p class="lb-ct">{escape(e["title"])}</p>{photos(e["photos"], e["title"])}</div>'
        for e in data["equipment"]) + "</div>")
    p.append("</div>")
    return wrap("".join(p))
