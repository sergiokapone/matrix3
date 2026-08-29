# -*- coding: utf-8 -*-
"""
Пошук і завантаження файлів даних навчального плану (data2026.py,
data2027.py, ...) за номером року - щоб build_diagramm.py/validate_data.py
не мали "зашитого" імені конкретного файлу, і додавання нового року
зводилось до "покласти новий data<рік>.py в цю ж папку", без правок коду.

Кожен data<рік>.py повинен визначати:
  DISCIPLINES, EDGES          - обов'язково
  NEVER_MERGE, FORCE_BAND      - опціонально (за замовчуванням set()/{});
                                 навмисно лежать У САМОМУ файлі даних, а не
                                 в config.py, бо посилаються на id, які є
                                 лише в ЦЬОМУ конкретному наборі даних (id
                                 не збігаються між роками, напр. "S1_Alg1"
                                 у 2024 проти "S1_Alg" у 2025-2026 -
                                 спільний global-словник в config.py для
                                 всіх років одразу був би пасткою: тихо
                                 "не спрацьовував" би для будь-якого року,
                                 крім того, під який його востаннє писали).
"""
import re
import importlib
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent
_PATTERN = re.compile(r"^data(\d{4})\.py$")


def discover_years():
    """Усі роки, для яких у цій папці лежить data<рік>.py, за зростанням."""
    years = []
    for p in _DATA_DIR.glob("data*.py"):
        m = _PATTERN.match(p.name)
        if m:
            years.append(int(m.group(1)))
    return sorted(years)


def load_year(year):
    """Імпортувати data<рік>.py й повернути (DISCIPLINES, EDGES,
    NEVER_MERGE, FORCE_BAND) - останні два з дефолтом, якщо файл їх не
    визначає."""
    modname = f"data{year}"
    try:
        mod = importlib.import_module(modname)
    except ModuleNotFoundError:
        available = discover_years()
        raise SystemExit(
            f"Немає файлу {modname}.py в {_DATA_DIR}. "
            f"Доступні роки: {available if available else '(жодного)'}"
        )
    disciplines = mod.DISCIPLINES
    edges = mod.EDGES
    never_merge = getattr(mod, "NEVER_MERGE", set())
    force_band = getattr(mod, "FORCE_BAND", {})
    return disciplines, edges, never_merge, force_band


def resolve_requested_years(argv_years):
    """argv_years - список рядків з командного рядка (може бути порожній,
    містити конкретні роки, або "all"). Повертає список int-років, які
    треба побудувати."""
    available = discover_years()
    if not argv_years or argv_years == ["all"]:
        if not available:
            raise SystemExit(f"У {_DATA_DIR} не знайдено жодного data<рік>.py")
        return available
    years = []
    for token in argv_years:
        try:
            years.append(int(token))
        except ValueError:
            raise SystemExit(f"Не число: {token!r} (очікую рік, напр. 2026, або 'all')")
    return years
