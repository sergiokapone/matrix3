"""Сторінка «Науковий семінар» (apd.ipt.kpi.ua/nauka/seminar/) з data.yaml.

Запуск: python sitepages/run.py seminar generate|diff|upload (див. sitepages/common.py).
Роки — розгортні блоки <details> (найновіший відкритий); кожен семінар — рядок (дата | тема і доповідач | мова),
що розгортається стрілкою: фото, анотація, посилання на відеозапис. Найновіший семінар розгорнуто.
Запис: date (YYYY-MM-DD), title, speaker, extra[], lang, photo?, annotation_label, annotation[{p|ul|ol}], links[].
Текст анотації — готовий html (<em>,<strong>,<sup>). Без CSS-escape кодів (WordPress їх ламає).
"""
from html import escape

from sitepages.common import minify_css, wrap, year_css

CSS = """
.sm-intro{margin:0 0 12px;font-size:15.5px;line-height:1.55}
.sm-yt{display:inline-block;margin:0 0 18px;padding:7px 16px;border-radius:999px;background:var(--c-acc);color:#fff!important;font-weight:600;font-size:14px}
.sm .sm-yt:hover{background:#174a96}
.sm-row{border-bottom:1px solid #eef0f5;color:var(--c-text)}
.sm-row:last-child{border-bottom:0}
.sm-row>summary{cursor:pointer;list-style:none;display:grid;grid-template-columns:96px minmax(0,1fr) 78px 32px;gap:0 14px;align-items:start;padding:12px 16px;text-align:left!important}
.sm-row>summary::-webkit-details-marker{display:none}
.sm-row>summary:hover{background:#f3f6fc}
.sm-row[open]>summary{background:#eef3fb}
.sm-dt{font-weight:700;color:var(--c-acc);font-size:14px;white-space:nowrap}
.sm-ti{font-weight:600;font-size:15.5px;line-height:1.4}
.sm-sp{display:block;margin-top:3px;font-weight:400;font-size:13.5px;color:#4a5368;line-height:1.4}
.sm-lg{justify-self:start;margin-top:2px;padding:1px 9px;border-radius:999px;background:var(--c-acc-bg);color:var(--c-acc);font-size:12px;font-weight:700}
.sm-arr{justify-self:end;align-self:center;width:24px;height:24px;border-radius:50%;background:var(--c-acc-bg);position:relative}
.sm-arr::after{content:"";position:absolute;left:9px;top:8px;border-style:solid;border-width:4px 0 4px 6px;border-color:transparent transparent transparent var(--c-acc);transition:transform .15s}
.sm-row[open] .sm-arr::after{transform:rotate(90deg);left:8px;top:8px}
.sm-body{display:flex;flex-wrap:wrap;gap:16px 22px;align-items:flex-start;padding:14px 16px 18px;background:#f6f8fc;border-top:1px solid var(--c-line);text-align:left}
.sm-photo{flex:0 0 190px;max-width:100%}
.sm-photo img{display:block;width:100%;height:auto;border-radius:8px;border:1px solid var(--c-line)}
.sm-txt{flex:1 1 360px;min-width:0;font-size:15px;line-height:1.55}
.sm-meta{margin:0 0 10px;font-size:14px;color:#4a5368}
.sm-h{margin:0 0 6px;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--c-mute);font-weight:700}
.sm-txt p{margin:0 0 9px}
.sm-txt ul,.sm-txt ol{margin:4px 0 10px;padding-left:22px}
.sm-txt li{margin:0 0 5px}
.sm-txt .sm-ref{font-size:13px;color:#4a5368;margin:0 0 3px}
.sm-lk{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.sm .sm-lk a{display:inline-block;padding:3px 14px;border-radius:999px;border:1px solid var(--c-acc);color:var(--c-acc)!important;font-size:13px;font-weight:600}
.sm .sm-lk a:hover{background:var(--c-acc);color:#fff!important}
@media(max-width:700px){
.sm-row>summary{grid-template-columns:minmax(0,1fr) 32px;padding:10px 14px}
.sm-dt,.sm-main{grid-column:1}
.sm-lg{grid-column:1;margin-top:6px}
.sm-arr{grid-column:2;grid-row:1/4}
.sm-photo{flex-basis:150px}
}
"""

MONTHS = ["", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]


def fmt_date(d: str) -> str:
    y, m, dd = d.split("-")
    return f"{dd}.{m}.{y}"


def blocks(items: list) -> str:
    out = []
    for b in items:
        if "p" in b:
            cls = ' class="sm-ref"' if b["p"].startswith("<em>[") else ""
            out.append(f"<p{cls}>{b['p']}</p>")
        else:
            kind = "ul" if "ul" in b else "ol"
            out.append(f"<{kind}>" + "".join(f"<li>{li}</li>" for li in b[kind]) + f"</{kind}>")
    return "".join(out)


def link_label(url: str) -> str:
    return "Відеозапис семінару на YouTube"


def row(s: dict, opened: bool) -> str:
    sp = f'<span class="sm-sp">{escape(s["speaker"])}</span>' if s.get("speaker") else ""
    lang = "UA" if s["lang"].startswith("укр") else "EN"
    summ = (f'<span class="sm-dt">{fmt_date(s["date"])}</span>'
            f'<span class="sm-main"><span class="sm-ti">{escape(s["title"])}</span>{sp}</span>'
            f'<span class="sm-lg" title="Мова семінару: {escape(s["lang"])}">{lang}</span><span class="sm-arr"></span>')
    photo = (f'<div class="sm-photo"><img src="{escape(s["photo"].replace("http://", "https://"), quote=True)}" '
             f'alt="{escape(s["speaker"][:80], quote=True)}" loading="lazy"></div>') if s.get("photo") else ""
    meta = "".join(f'<p class="sm-meta">{escape(x)}</p>' for x in s.get("extra", []))
    links = ""
    if s.get("links"):
        links = '<div class="sm-lk">' + "".join(
            f'<a href="{escape(u, quote=True)}" target="_blank" rel="noopener">{link_label(u)}</a>' for u in s["links"]) + "</div>"
    body = (f'<div class="sm-body">{photo}<div class="sm-txt">{meta}'
            f'<div class="sm-h">{escape(s["annotation_label"])}</div>{blocks(s["annotation"])}{links}</div></div>')
    return f'<details class="sm-row"{" open" if opened else ""}><summary title="Показати анотацію">{summ}</summary>{body}</details>'


def build(data: dict) -> str:
    years: dict = {}
    for s in data["seminars"]:
        years.setdefault(s["date"][:4], []).append(s)
    ys = sorted(years, reverse=True)
    newest = max(data["seminars"], key=lambda s: s["date"])["date"]
    p = [f"<style>{year_css('sm')}{minify_css(CSS)}</style>", '<div class="sm">']
    p.append(f'<p class="sm-intro">{escape(data["intro"])}</p>')
    p.append(f'<a class="sm-yt" href="{escape(data["youtube"], quote=True)}" target="_blank" rel="noopener">Відеозаписи семінарів на YouTube</a>')
    p.append('<nav class="sm-nav">' + "".join(f'<a href="#sm-{y}">{y}</a>' for y in ys) + "</nav>")
    for i, y in enumerate(ys):
        rows = "".join(row(s, s["date"] == newest) for s in sorted(years[y], key=lambda s: s["date"], reverse=True))
        p.append(f'<details class="sm-year" id="sm-{y}"{" open" if i == 0 else ""}>'
                 f'<summary>{y} <span class="cnt">семінарів: {len(years[y])}</span></summary>{rows}</details>')
    p.append("</div>")
    return wrap("".join(p))
