"""Chair History (page 2523): оформлення + таймлайн + блок про акредитацію. Текст історії лежить у text.html (знято з живої сторінки)."""
import sys, re, pathlib
sys.path.insert(0, ".")
import requests
from core.config import WordPressConfig

HERE = pathlib.Path(__file__).parent

CSS = """<style>
.hist{max-width:900px;margin:0 auto;color:#2c3e50;font-size:17px;line-height:1.75}
.hist p{margin:0 0 1.1em}
.hist a{color:#2980b9}
.hist ul,.hist ol{margin:0 0 1.2em 1.2em}
.hist li{margin-bottom:.4em}
.hist img{max-width:100%;height:auto;border-radius:8px}
.hist .wp-caption{background:#f4f6f8;border:1px solid #e1e5ea;border-radius:8px;padding:8px;margin:0 0 12px 20px;font-size:14px;text-align:center}
.hist-h{margin:34px 0 16px;padding-bottom:8px;border-bottom:3px solid #3498db;color:#2c3e50;font-size:26px}
.tl{list-style:none;margin:0 0 30px;padding:0 0 0 22px;border-left:3px solid #3498db}
.tl li{position:relative;margin:0 0 14px;padding:10px 16px;background:#f4f6f8;border-radius:8px;line-height:1.5}
.tl li:before{content:"";position:absolute;left:-32px;top:16px;width:14px;height:14px;border-radius:50%;background:#3498db;border:3px solid #fff}
.tl b{color:#2980b9;margin-right:8px}
.acc{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px;margin:16px 0}
.acc div{border:1px solid #e1e5ea;border-radius:10px;overflow:hidden;background:#fff;box-shadow:0 2px 6px rgba(0,0,0,.06)}
.acc h4{margin:0;padding:12px 16px;color:#fff;font-size:18px}
.acc p{margin:0;padding:12px 16px;font-size:15px;line-height:1.5}
.acc-btn{display:inline-block;margin-top:6px;padding:11px 22px;border:2px solid #3498db;border-radius:6px;color:#3498db!important;text-decoration:none;font-weight:bold}
.acc-btn:hover{background:#3498db;color:#fff!important}
</style>
"""



TIMELINE_EN = """<ul class="tl">
<li><b>1997</b>Order No. 1-90 of July 18, 1997 on the creation of the Department of Applied Physics; it became the first department of the Physico-Technical Faculty (1998).</li>
<li><b>2001</b>First accreditation of the department in the direction of “Applied Physics”.</li>
<li><b>2003</b>Anatoliy Shpak becomes director of the Institute of Metal Physics; Dr. Sc. Serhiy Voronov is elected head of the department.</li>
<li><b>2011</b>On August 2, 2011, on the initiative of Boris Paton and Mykhailo Zgurovsky, the Department of Physics of Energy Systems (FES) is created at the Physico-Technical Institute, headed by Academician Artem Khalatov. It runs a parallel history: first Bachelor’s graduates in 2014/2015, first Master’s graduates in 2016/2017.</li>
<li><b>2021</b>Joint accreditation of the programme “Applied Physics” at all three levels by the two departments (Bachelor’s level with the “Exemplary” mark).</li>
<li><b>September 1, 2021</b>The Departments of Applied Physics and of Physics of Energy Systems merge into one — the Department of Applied Physics, headed by Dr. Sc., Assoc. Prof. Hennadii Monastyrskyi.</li>
<li><b>2026</b>Bachelor’s and Master’s programmes accredited again — certificates No. 21622 and No. 20757, valid until July 1, 2031.</li>
</ul>"""

TIMELINE_UK = """<ul class="tl">
<li><b>1997</b>Наказ №1-90 від 18 липня 1997 р. про створення кафедри прикладної фізики; перша кафедра фізико-технічного факультету (1998).</li>
<li><b>2001</b>Перша акредитація кафедри за напрямом «Прикладна фізика».</li>
<li><b>2003</b>А. П. Шпака призначено директором Інституту металофізики; завідувачем кафедри обрано д.т.н. Воронова С. О.</li>
<li><b>2011</b>2 серпня 2011 р. з ініціативи Б. Є. Патона і М. З. Згуровського на базі ФТІ створено кафедру фізики енергетичних систем (ФЕС) на чолі з академіком НАН України А. А. Халатовим. Її історія йшла паралельно: перший випуск бакалаврів — 2014/2015, магістрів — 2016/2017 н. р.</li>
<li><b>2021</b>Спільна акредитація кафедрами ФЕС і прикладної фізики програми «Прикладна фізика» за всіма трьома рівнями; бакалаврський рівень — з відзнакою «Зразкова».</li>
<li><b>1 вересня 2021</b>Кафедри ФЕС і прикладної фізики об’єднано в одну — кафедру прикладної фізики, яку очолив д.ф.-м.н., доц. Монастирський Г. Є.</li>
<li><b>2026</b>Повторна акредитація бакалаврської та магістерської програм Національним агентством із забезпечення якості вищої освіти — сертифікати № 21622 і № 20757, строк дії до 01.07.2031.</li>
</ul>"""

ACC_EN = """<h2 class="hist-h">Accreditation of educational programmes</h2>
<p>The educational programmes of specialty <strong>E6 “Applied Physics and Nanomaterials”</strong> are accredited by the National Agency for Higher Education Quality Assurance (NAQA).</p>
<div class="acc">
<div><h4 style="background:#2980b9">Bachelor</h4><p>Professional programme “Applied Physics”<br>Certificate No. 21622, issued May 27, 2026<br><strong>Valid until July 1, 2031</strong></p></div>
<div><h4 style="background:#16a085">Master</h4><p>Scientific programme “Applied Physics”<br>Certificate No. 20757, issued April 22, 2026<br><strong>Valid until July 1, 2031</strong></p></div>
<div><h4 style="background:#8e44ad">Doctor of Philosophy</h4><p>Scientific programme “Applied Physics”<br>Certificate No. 5433, issued July 6, 2023<br><strong>Valid until July 1, 2027</strong></p></div>
</div>
<p><a class="acc-btn" href="https://apd.ipt.kpi.ua/osvita/">Certificates and programmes →</a></p>"""


ACC_UK = """<h2 class="hist-h">Акредитація освітніх програм</h2>
<p>Освітні програми спеціальності <strong>E6 «Прикладна фізика та наноматеріали»</strong> акредитовані Національним агентством із забезпечення якості вищої освіти (НАЗЯВО).</p>
<div class="acc">
<div><h4 style="background:#2980b9">Бакалавр</h4><p>Освітньо-професійна програма «Прикладна фізика»<br>Сертифікат № 21622 від 27.05.2026<br><strong>Строк дії до 01.07.2031</strong></p></div>
<div><h4 style="background:#16a085">Магістр</h4><p>Освітньо-наукова програма «Прикладна фізика»<br>Сертифікат № 20757 від 22.04.2026<br><strong>Строк дії до 01.07.2031</strong></p></div>
<div><h4 style="background:#8e44ad">Доктор філософії</h4><p>Освітньо-наукова програма «Прикладна фізика»<br>Сертифікат № 5433 від 06.07.2023<br><strong>Строк дії до 01.07.2027</strong></p></div>
</div>
<p><a class="acc-btn" href="https://apd.ipt.kpi.ua/osvita/">Сертифікати та програми →</a></p>"""

PAGES = {
    "en": dict(id=2523, file="text.html", tl=TIMELINE_EN, acc=ACC_EN, h1="Key dates", h2="History of the department"),
    "uk": dict(id=754, file="text_uk.html", tl=TIMELINE_UK, acc=ACC_UK, h1="Ключові дати", h2="Історія кафедри"),
}

def clean(t):
    t = re.sub(r'<span style="color: #ff0000;">(.*?)</span>', r'\1', t, flags=re.S)
    t = t.replace(' style="color: #ff0000;"', '')
    t = re.sub(r'<figure>\s*</figure>', '', t)
    t = t.replace('<div class="article-article text-dark m-t-20 m-b-20">', '')
    t = re.sub(r'(?:\s*<div[^>]*>(?:&nbsp;|\s)*</div>)+\s*$', '', t.rstrip())
    t = re.sub(r'</div>\s*$', '', t.rstrip())
    return t.strip()

def build(text, cfg):
    return (CSS + '<div class="hist">\n<h2 class="hist-h">%s</h2>\n' % cfg["h1"] + cfg["tl"] +
            '\n<h2 class="hist-h">%s</h2>\n' % cfg["h2"] + clean(text) + '\n' + cfg["acc"] + '\n</div>')

if __name__ == "__main__":
    c = WordPressConfig()
    for lang in (sys.argv[1:] or PAGES):
        cfg = PAGES[lang]
        src = HERE / cfg["file"]
        if not src.exists():
            raw = requests.get(c.api_url + "/pages/%d" % cfg["id"], params={"context": "edit"}, auth=c.auth).json()["content"]["raw"]
            src.write_bytes(raw.encode())
        r = requests.post(c.api_url + "/pages/%d" % cfg["id"], json={"content": build(src.read_bytes().decode(), cfg)}, auth=c.auth)
        print(lang, r.status_code)
