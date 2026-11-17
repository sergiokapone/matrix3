#!/usr/bin/env python3
"""
migrate_teachers.py
Нормалізує teachers.yaml:
  - contacts: лишає тільки id, прибирає дублі *_id/*_label/*_url
  - прибирає порожні списки/dict там де поле опціональне
  - перейменовує research_id -> wos
"""

import re
import sys
from pathlib import Path

import yaml


# ── helpers ───────────────────────────────────────────────────────────────────

def extract_orcid(val: str) -> str:
    """https://orcid.org/0000-0002-9851-7109  ->  0000-0002-9851-7109"""
    return val.rstrip("/").split("/")[-1] if "/" in val else val

def extract_scopus(val: str) -> str:
    """...?authorId=7005144109  ->  7005144109"""
    m = re.search(r"authorId=(\d+)", val)
    return m.group(1) if m else val

def extract_wos(val: str) -> str:
    """.../record/I-3896-2018  or  .../rid/I-4513-2018  ->  I-3896-2018"""
    m = re.search(r"/(?:record|rid)/([A-Z0-9\-]+)", val)
    return m.group(1) if m else val

def extract_scholar(val: str) -> str:
    """...?user=lyOREZEAAAAJ&...  ->  lyOREZEAAAAJ"""
    m = re.search(r"[?&]user=([^&]+)", val)
    return m.group(1) if m else val

def extract_github(val: str) -> str:
    """https://github.com/sergiokapone  ->  sergiokapone"""
    return val.rstrip("/").split("/")[-1] if "/" in val else val

def extract_linkedin(val: str) -> str:
    """https://www.linkedin.com/in/sergiokapone/  ->  sergiokapone"""
    m = re.search(r"/in/([^/]+)", val)
    return m.group(1).rstrip("/") if m else val

def extract_intellect(val: str) -> str:
    """https://intellect.kpi.ua/profile/psm37  ->  psm37"""
    return val.rstrip("/").split("/")[-1] if "/" in val else val


# ── contacts normalizer ───────────────────────────────────────────────────────

OPTIONAL_CONTACT_KEYS = {
    "orcid", "scopus", "wos", "google_scholar",
    "github", "linkedin", "intellect",
    "email", "schedule",
    "main_workplace_label", "main_workplace_url",
    "nas_page", "position_label", "ela_archive",
}

def normalize_contacts(c: dict) -> dict:
    out = {}

    # email
    if c.get("email"):
        out["email"] = c["email"]

    # orcid: може бути повний URL або вже id
    if c.get("orcid"):
        out["orcid"] = extract_orcid(c["orcid"])
    # прибираємо orcid_id

    # github
    if c.get("github"):
        out["github"] = extract_github(c["github"])
    # прибираємо github_label

    # linkedin
    if c.get("linkedin"):
        out["linkedin"] = extract_linkedin(c["linkedin"])
    # прибираємо linkedin_label

    # wos (було research_id)
    wos_val = c.get("research_id") or c.get("wos")
    if wos_val:
        out["wos"] = extract_wos(wos_val)
    # прибираємо research_id_label

    # scopus
    if c.get("scopus"):
        out["scopus"] = extract_scopus(c["scopus"])
    # прибираємо scopus_id

    # google_scholar
    if c.get("google_scholar"):
        out["google_scholar"] = extract_scholar(c["google_scholar"])
    # прибираємо google_scholar_label

    # intellect
    if c.get("intellect"):
        out["intellect"] = extract_intellect(c["intellect"])

    # schedule — лишаємо як є (довгий токен, не виводиться з id)
    if c.get("schedule"):
        out["schedule"] = c["schedule"]

    # main_workplace
    if c.get("main_workplace_label"):
        out["main_workplace_label"] = c["main_workplace_label"]
    if c.get("main_workplace_url"):
        out["main_workplace_url"] = c["main_workplace_url"]

    # nas_page
    if c.get("nas_page"):
        out["nas_page"] = c["nas_page"]

    # position_label
    if c.get("position_label"):
        out["position_label"] = c["position_label"]

    # ela_archive
    if c.get("ela_archive"):
        out["ela_archive"] = c["ela_archive"]

    return out


# ── strip empty ───────────────────────────────────────────────────────────────

OPTIONAL_LIST_KEYS = {
    "research_interests", "duties", "certificates",
    "methodical_materials", "publications", "conferences",
    "achievements", "international_projects", "national_projects",
}

OPTIONAL_STUDENT_KEYS = {"bachelor", "master", "phd", "phd_current", "contest_winners"}


def strip_empty(teacher: dict) -> dict:
    """Прибирає порожні списки/рядки для опціональних полів."""
    for key in OPTIONAL_LIST_KEYS:
        if key in teacher and not teacher[key]:
            del teacher[key]

    # students — прибираємо порожні підсписки, і весь блок якщо він порожній
    if "students" in teacher:
        s = teacher["students"]
        for k in list(s.keys()):
            if k in OPTIONAL_STUDENT_KEYS and not s[k]:
                del s[k]
        if not s:
            del teacher["students"]

    # courses — прибираємо порожні рівні
    if "courses" in teacher:
        c = teacher["courses"]
        for level in ("bachelor", "master", "phd"):
            if level in c and not c[level]:
                del c[level]

    # biography — порожній рядок
    if "biography" in teacher and not teacher["biography"].strip():
        del teacher["biography"]

    # position — порожній рядок
    if "position" in teacher and not teacher["position"].strip():
        del teacher["position"]

    return teacher


# ── main ──────────────────────────────────────────────────────────────────────

def migrate(src: Path, dst: Path):
    with open(src, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    teachers = data.get("teachers", [])
    print(f"Завантажено {len(teachers)} викладачів")

    for t in teachers:
        # contacts
        if "contacts" in t:
            t["contacts"] = normalize_contacts(t["contacts"])
        else:
            t["contacts"] = {}

        # strip empty optional fields
        strip_empty(t)

    # dump — зберігаємо unicode, без сортування ключів
    with open(dst, "w", encoding="utf-8") as f:
        yaml.dump(
            {"teachers": teachers},
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
            width=120,
        )

    print(f"Записано: {dst}")


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("teachers.yaml")
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("teachers_normalized.yaml")
    migrate(src, dst)
