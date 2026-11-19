"""Спільне для всіх «верстальників» сторінок apd.ipt.kpi.ua.

Кожна сторінка — папка sitepages/<name>/ з файлами:
    data.yaml  — дані (+ `page_id` сторінки WordPress, `title`);
    build.py   — функція build(data) -> html (CSS вбудований у сторінку).
Запуск (з кореня проєкту):
    .venv/Scripts/python sitepages/run.py <name> generate|diff|upload
Нова сторінка = нова папка + рядок у PAGES в run.py.
"""
import sys
import time
from html import escape  # noqa: F401  (реекспорт для build.py)
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def load_yaml(folder: Path) -> dict:
    return yaml.safe_load((folder / "data.yaml").read_text(encoding="utf-8"))


def wrap(html: str) -> str:
    """Блок html Gutenberg: wpautop не чіпає розмітку."""
    return "<!-- wp:html -->" + html + "<!-- /wp:html -->"


def minify_css(css: str) -> str:
    return "".join(line.strip() for line in css.strip().splitlines())


def publish(folder: Path, data: dict, html: str, cmd: str) -> None:
    """generate: лише файл; diff: + резервна копія живої сторінки; upload: + POST і перевірка."""
    (folder / "page.html").write_text(html, encoding="utf-8", newline="")
    print(f"generated {folder.name}/page.html, {len(html)} chars")
    if cmd == "generate":
        return
    import requests
    from core.config import WordPressConfig

    cfg = WordPressConfig()
    url = f"{cfg.api_url}/pages/{data['page_id']}"
    live = requests.get(url, params={"context": "edit"}, auth=cfg.auth, timeout=60).json()
    raw = live["content"]["raw"]
    bak = folder / "bak"
    bak.mkdir(exist_ok=True)
    bf = bak / f"page{data['page_id']}_{time.strftime('%Y%m%d_%H%M%S')}.html"
    bf.write_bytes(raw.encode("utf-8"))  # бінарно: \r\n не подвоюється
    print(f"backup: {bf} ({len(raw)} chars)")
    if cmd == "diff":
        return
    assert cmd == "upload", cmd
    r = requests.post(url, json={"content": html}, auth=cfg.auth, timeout=60)
    r.raise_for_status()
    new = requests.get(url, params={"context": "edit"}, auth=cfg.auth, timeout=60).json()["content"]["raw"]
    print("posted:", r.status_code, "| \r\r\n count:", new.count("\r\r\n"), "| len:", len(new))
    print("public:", requests.get(live["link"], timeout=60).status_code, live["link"])


def year_css(p: str) -> str:
    """Спільний CSS «роки-розгортки»: змінні, навігація-пілюлі, <details class="{p}-year">.
    p — префікс класів сторінки (cw, sw, ...)."""
    return minify_css(f"""
.{p}{{--c-line:#d6dbe5;--c-text:#1d2433;--c-mute:#7a8396;--c-acc:#1f5fbf;--c-acc-bg:#eaf1fc;margin:0 0 2em}}
.{p} *{{box-sizing:border-box}}
.{p} a,.{p} a:hover{{text-decoration:none!important;border-bottom:0!important}}
.{p}-nav{{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 1.4em}}
.{p}-nav a{{padding:6px 14px;border-radius:999px;background:var(--c-acc-bg);color:var(--c-acc)!important;font-weight:600;font-size:14px;border:1px solid transparent;border-bottom:1px solid transparent!important}}
.{p}-nav a:hover{{border-color:var(--c-acc);border-bottom-color:var(--c-acc)!important}}
.{p}-year{{margin:0 0 14px;border:1px solid var(--c-line);border-radius:10px;overflow:hidden;box-shadow:0 1px 2px rgba(20,30,50,.05)}}
.{p}-year>summary{{cursor:pointer;list-style:none;padding:12px 16px;display:flex;align-items:baseline;gap:12px;background:#f6f8fc;font-weight:700;font-size:1.15em;color:var(--c-text)}}
.{p}-year>summary::-webkit-details-marker{{display:none}}
.{p}-year>summary::before{{content:"";flex:none;align-self:center;border-style:solid;border-width:5px 0 5px 8px;border-color:transparent transparent transparent var(--c-acc);transition:transform .15s}}
.{p}-year[open]>summary::before{{transform:rotate(90deg)}}
.{p}-year .cnt{{color:var(--c-mute);font-size:14px;font-weight:400}}
""")


_PEOPLE = None


def _pkey(name: str) -> str:
    import re
    parts = name.replace("\xa0", " ").split(None, 1)
    rest = parts[1] if len(parts) > 1 else ""
    return parts[0].lower() + " " + "".join(re.findall(r"[A-ZА-ЯІЇЄҐ]", rest)[:2]).lower()


def person_url(name: str) -> str | None:
    """Посилання на персональну сторінку викладача за «Прізвище І.П.» або повним ПІБ (people.yaml)."""
    global _PEOPLE
    if _PEOPLE is None:
        f = Path(__file__).parent / "people.yaml"
        rows = yaml.safe_load(f.read_text(encoding="utf-8"))["people"] if f.exists() else []
        _PEOPLE = {_pkey(p["short"]): p["url"] for p in rows}
    return _PEOPLE.get(_pkey(name))


_UA = "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"


def ua_key(s: str) -> list:
    """Ключ сортування за українським алфавітом (Python сортує є/і/ї за кодами Unicode — невірно)."""
    return [(_UA.index(c) if c in _UA else 100 + ord(c)) for c in s.lower()]
