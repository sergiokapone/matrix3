"""Сторінка «Освіта» (page 16): картки рівнів + сертифікати акредитації з розкриттям на весь екран."""
import sys
sys.path.insert(0, ".")
import requests
from core.config import WordPressConfig

UP = "https://apd.ipt.kpi.ua/wp-content/uploads/2026/11/"
OLD = "https://osvita.kpi.ua/sites/default/files/opfiles/"
LEVELS = [
    dict(id="cert-b", title="Бакалавр", kind="Освітньо-професійна програма", color="#2980b9",
         link="https://osvita.kpi.ua/105_OPPB_PF", pdf=UP + "105_OPPB_PF_Certificate_2026_no21622.pdf",
         num="№ 21622 від 27.05.2026", until="01.07.2031", year="2026", ok=True),
    dict(id="cert-m", title="Магістр", kind="Освітньо-наукова програма", color="#16a085",
         link="https://osvita.kpi.ua/105_ONPM_PF", pdf=UP + "105_ONPM_PF_Certificate_2026_no20757.pdf",
         num="№ 20757 від 22.04.2026", until="01.07.2031", year="2026", ok=True),
    dict(id="cert-d", title="Доктор філософії", kind="Освітньо-наукова програма", color="#8e44ad",
         link="https://osvita.kpi.ua/105_ONPD_PF", pdf=OLD + "105_ONPD_PF_Certificate_01-07-2027.pdf",
         num="акредитація 2021 року", until="01.07.2027", year="2021", ok=True),
]

CSS = """<style>
.osv-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:22px;margin:24px 0}
.osv-card{background:#fff;border:1px solid #e1e5ea;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.06);display:flex;flex-direction:column}
.osv-head{padding:18px 20px;color:#fff}
.osv-head h3{margin:0;color:#fff;font-size:22px}
.osv-head span{opacity:.9;font-size:14px}
.osv-body{padding:16px 20px 20px;display:flex;flex-direction:column;gap:12px;flex:1}
.osv-badge{display:inline-block;background:#e8f6ee;color:#1e8449;border-radius:20px;padding:4px 12px;font-size:14px;font-weight:bold;align-self:flex-start}
.osv-meta{color:#555;font-size:14px;line-height:1.5}
.osv-prev{position:relative;border:1px solid #e1e5ea;border-radius:8px;overflow:hidden;background:#f4f6f8}
.osv-prev iframe{display:block;width:100%;height:230px;border:none;pointer-events:none}
.osv-prev a{position:absolute;top:0;left:0;right:0;bottom:0;display:flex;align-items:flex-end;justify-content:center;padding-bottom:10px;text-decoration:none}
.osv-prev a span{background:rgba(44,62,80,.88);color:#fff;border-radius:20px;padding:5px 14px;font-size:14px}
.osv-prev a:hover span{background:#3498db}
.osv-btn{display:block;text-align:center;padding:10px 14px;border-radius:6px;text-decoration:none;font-weight:bold;color:#fff}
.osv-btn:hover{opacity:.88;color:#fff}
.osv-more{margin-top:26px;text-align:center}
.osv-more a{display:inline-block;padding:12px 24px;border:2px solid #3498db;border-radius:6px;color:#3498db;text-decoration:none;font-weight:bold}
.osv-more a:hover{background:#3498db;color:#fff}
.cert-full{display:none;position:fixed;top:0;left:0;right:0;bottom:0;z-index:99999;background:rgba(0,0,0,.85);padding:20px;box-sizing:border-box}
.cert-full:target{display:block}
.cert-full iframe{width:100%;height:100%;border:none;background:#fff;border-radius:6px}
.cert-close{position:absolute;top:6px;right:14px;z-index:2;font-size:28px;line-height:1;color:#fff;text-decoration:none;background:#c0392b;border-radius:50%;width:38px;height:38px;text-align:center;padding-top:5px;box-sizing:border-box}
</style>
"""

def card(l):
    return f"""<div class="osv-card">
<div class="osv-head" style="background:{l['color']}"><h3>{l['title']}</h3><span>{l['kind']}</span></div>
<div class="osv-body">
<span class="osv-badge">✔ Акредитовано до {l['until']}</span>
<div class="osv-meta">Сертифікат НАЗЯВО: {l['num']}</div>
<div class="osv-prev"><iframe src="{l['pdf']}#toolbar=0&amp;navpanes=0" scrolling="no" loading="lazy"></iframe><a href="#{l['id']}"><span>⤢ Розгорнути на весь екран</span></a></div>
<a class="osv-btn" style="background:{l['color']}" href="{l['link']}">Сторінка програми →</a>
</div></div>"""

def overlay(l):
    return (f'<div class="cert-full" id="{l["id"]}"><a class="cert-close" href="#cert-top" title="Закрити">✕</a>'
            f'<iframe src="{l["pdf"]}" loading="lazy"></iframe></div>')

def build():
    return (CSS + '<span id="cert-top"></span>\n'
        '<p style="color:#2c3e50;font-size:18px;line-height:1.6">Кафедра прикладної фізики запрошує отримати якісну вищу освіту за спеціальністю '
        '<strong>E6 «Прикладна фізика та наноматеріали»</strong> за трьома рівнями. Освітні програми акредитовані Національним агентством із забезпечення якості вищої освіти.</p>\n'
        '<div class="osv-grid">\n' + "\n".join(card(l) for l in LEVELS) + '\n</div>\n'
        '<div class="osv-more"><a href="https://apd.ipt.kpi.ua/nauka/lab/matherial_stuff/">Матеріально-технічне забезпечення освітніх програм</a></div>\n'
        + "\n".join(overlay(l) for l in LEVELS))

if __name__ == "__main__":
    c = WordPressConfig()
    r = requests.post(c.api_url + "/pages/16", json={"content": build()}, auth=c.auth)
    print(r.status_code)
