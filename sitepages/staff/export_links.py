"""Оновлює sitepages/people.yaml — персональні сторінки викладачів (для посилань на ПІБ).

    python sitepages/staff/export_links.py

Бере з WordPress лише опубліковані підсторінки /kafedra/stuff/ (page 181) і пише
`short` («Загородній В.В.»), `name` (повне ПІБ) та `url`. Приватні, чернетки й pending пропускає.
Файл можна правити вручну (наприклад, додати зовнішнього консультанта з власним URL).
"""
import html
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def short(name: str) -> str:
    parts = name.split()
    return parts[0] + " " + "".join(p[0] + "." for p in parts[1:3])


def main() -> None:
    import requests
    from core.config import WordPressConfig

    cfg = WordPressConfig()
    pages, n = [], 1
    while True:
        r = requests.get(f"{cfg.api_url}/pages", auth=cfg.auth, timeout=60,
                         params={"parent": 181, "status": "publish", "per_page": 100, "page": n,
                                 "_fields": "id,link,title"})
        if r.status_code != 200 or not r.json():
            break
        pages += r.json()
        n += 1
    people = []
    for p in pages:
        name = html.unescape(p["title"]["rendered"]).strip()
        if not name or name.isascii():  # англомовні дублі
            continue
        people.append({"short": short(name), "name": name, "url": p["link"]})
    people.sort(key=lambda x: x["name"])
    out = ROOT / "sitepages" / "people.yaml"
    out.write_text(yaml.safe_dump({"people": people}, allow_unicode=True, sort_keys=False, width=160),
                   encoding="utf-8")
    print(f"{len(people)} people -> {out}")


if __name__ == "__main__":
    main()
