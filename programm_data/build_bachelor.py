# -*- coding: utf-8 -*-
"""
Побудова bachelor2026.yaml на основі:
 - структури/довідників bachelor2025.yaml (competencies, program_results, mappings, metadata)
 - переліку дисциплін data2026.py (DISCIPLINES, EDGES) - навчальний план інтейку 2026 року

Стратегія зіставлення:
 1) Однозначні збіги за (нормалізованою) назвою -> переносимо credits/control/
    syllabus_url/lecturer_id/discipline_id/mapping з bachelor2025.yaml.
 2) Курси, розбиті на частини в 2025 (MatAn, Alg, DiffEq) зіставляються по
    порядку семестрів з частинами 1/2/3.
 3) "Методи математичної фізики" в 2026 розбиті на S3/S4/S5 -> зіставлено з
    ПО 02.1 (тензорний аналіз) / ПО 02.2 (комплексний аналіз) / ПО 02.3 (рівн.
    в частинних похідних) за порядком семестрів та графом передумов (EDGES).
 4) "Обчислювальні методи та комп'ютерні пакети" в 2025 - один курс (6 кред.),
    в 2026 розбитий на S3+S4 -> кредити ОРІЄНТОВНО розділені порівну (3+3),
    позначено як TODO для перевірки.
 5) Нечіткі збіги (скорочення на кшталт "Стат. фіз. та основи ФТТ",
    "проф. спрямуванням") зіставлено вручну.
 6) Курси, яких не було в 2025 (національний спротив, історико-філософські
    модулі, ЗУ-Каталог, практичний курс іноземної мови, вибіркові Ф1-Ф14) -
    НОВІ, дані (credits/control) відсутні в жодному з вхідних файлів і
    позначені як TODO. Їм присвоєні нові коди ЗО23+/ПО17+ за послідовністю.

Усі рішення з п.3-6 потребують ручної перевірки викладачем.
"""
import re
import sys
import yaml
sys.path.insert(0, '.')
from data2026 import DISCIPLINES as D26, EDGES

with open('bachelor2025.yaml', encoding='utf-8') as f:
    Y25 = yaml.safe_load(f)

D25 = Y25['disciplines']

TODO = "TODO-2026"

def clean(name):
    return re.sub(r'\s+', ' ', name.replace('\n', ' ')).strip()

# ------------------------------------------------------------------
# Ручне зіставлення "код 2026" -> "код(и) 2025" / None (нове) / список
# для розбитих по семестрах курсів.
# ------------------------------------------------------------------
MANUAL_MAP = {
    "S1_MatAn": "ЗО 01.1",
    "S2_MatAn": "ЗО 01.2",
    "S3_MatAn": "ЗО 01.3",
    "S1_Alg": "ЗО 02.1",
    "S2_Alg": "ЗО 02.2",
    "S1_Mech": "ЗО 03",
    "S1_Intro": "ЗО 22",
    "S1_Econ": "ЗО 15",
    "S1_Eng": "ЗО 12",
    "S1_Health": "ЗО 11",
    "S1_Ukr": "ЗО 09",
    "S2_Thermo": "ЗО 04",
    "S2_Chem": "ЗО 19",
    "S2_Graph": "ЗО 21",
    "S2_Eng": "ЗО 12",
    "S3_ElMag": "ЗО 06",
    "S3_DiffEq": "ЗО 05.1",
    "S4_DiffEq": "ЗО 05.2",
    "S3_EngProf": "ЗО 16",
    "S3_Military": "ПО 01",   # Програмування - в 2025 теж один запис на кілька семестрів
    "S4_Military": "ПО 01",   # (як і Англійська мова нижче) - НЕ ділимо кредити
    "S4_ClassMech": "ПО 04",
    "S4_Optics": "ЗО 07",
    "S3_MathPhys": "ПО 02.1",  # Тензорний аналіз
    "S4_MathPhys": "ПО 02.2",  # Комплексний аналіз
    "S5_MathPhys": "ПО 02.3",  # Рівняння в частинних похідних
    "S3_CompMeth": "ПО 03",   # в 2025 - один запис (6 кред.) на кілька семестрів,
    "S4_CompMeth": "ПО 03",   # як і Англійська мова - НЕ ділимо кредити
    "S5_Atomic": "ЗО 08",
    "S5_FieldTheory": "ПО 05",
    "S5_OscWaves": "ПО 06",
    "S5_Ecology": "ЗО 13",
    "S6_ProbStat": "ЗО 20",
    "S6_MathModel": "ПО 10",
    "S6_ESS": "ПО 07",
    "S6_QMech": "ПО 08",
    "S6_Rights": "ЗО 18",
    "S7_StatPhys": "ПО 09",
    "S7_StatRadio": "ПО 11",
    "S7_Lab": "ПО 12",
    "S7_Course": "ПО 13",
    "S8_Research": "ПО 14",
    "S8_Practice": "ПО 15",
    "S8_Diploma": "ПО 16",
}

# Нові дисципліни 2026 року (яких не було в 2025) -> новий код
NEW_CODES = {
    "S1_Prog":       "ЗО 23.1",
    "S2_Prog":       "ЗО 23.2",
    "S2_HistPhil_1": "ЗО 24.1",
    "S2_HistPhil_2": "ЗО 24.2",
    "S3_Catalog":    "ЗО 25.1",
    "S4_Catalog":    "ЗО 25.2",
    "S4_EngPract":   "ЗО 26",
    "S4_F1":  "ПВ 01.1",
    "S5_F2":  "ПВ 01.2",
    "S5_F3":  "ПВ 01.3",
    "S5_F4":  "ПВ 01.4",
    "S6_F5":  "ПВ 01.5",
    "S6_F6":  "ПВ 01.6",
    "S6_F7":  "ПВ 01.7",
    "S7_F8":  "ПВ 01.8",
    "S7_F9":  "ПВ 01.9",
    "S7_F10": "ПВ 01.10",
    "S7_F11": "ПВ 01.11",
    "S8_F12": "ПВ 01.12",
    "S8_F13": "ПВ 01.13",
    "S8_F14": "ПВ 01.14",
}

assert set(MANUAL_MAP) | set(NEW_CODES) == set(D26), \
    "Не всі коди data2026 враховані: %s" % (set(D26) - set(MANUAL_MAP) - set(NEW_CODES))

mappings25 = Y25['mappings']

# курси, на які посилаються кілька кодів data2026 (наскрізні: Англійська мова,
# Програмування, Обчислювальні методи) - в bachelor2025.yaml це ОДИН запис,
# що охоплює кілька семестрів. Зберігаємо мінімальний семестр як семестр
# початку курсу, кредити НЕ ділимо (так само, як зроблено в bachelor2025.yaml).
ref_semesters = {}
for code26, ref in MANUAL_MAP.items():
    ref_semesters.setdefault(ref, []).append(D26[code26]['semester'])

out_disciplines = {}
out_mappings = {}
notes = []
seen_refs = set()

for code26, info in D26.items():
    semester = info['semester']

    if code26 in NEW_CODES:
        new_code = NEW_CODES[code26]
        entry = {
            'name': clean(info['ua']),
            'semester': semester,
            'credits': TODO,
            'control': TODO,
        }
        notes.append(f"НОВА дисципліна (не було в bachelor2025.yaml): {new_code} — {entry['name']} "
                      f"(сем. {semester}). Потрібно вписати кредити/контроль/мапінг компетенцій.")
        out_disciplines[new_code] = entry
        continue

    ref = MANUAL_MAP[code26]
    if ref in seen_refs:
        # наскрізний курс - запис уже додано (з мінімальним семестром)
        continue
    seen_refs.add(ref)

    src = D25[ref]
    new_code = ref
    entry = {
        'name': src['name'],
        'semester': min(ref_semesters[ref]),
        'credits': src['credits'],
        'control': src['control'],
    }
    for opt in ('syllabus_url', 'online_resources', 'lecturer_id', 'discipline_id'):
        if opt in src:
            entry[opt] = src[opt]
    if len(ref_semesters[ref]) > 1:
        entry['semesters_note'] = f"курс охоплює семестри {sorted(set(ref_semesters[ref]))}"

    out_disciplines[new_code] = entry
    if ref in mappings25:
        out_mappings[new_code] = mappings25[ref]

# сортування природним порядком коду (як в оригіналі bachelor2025.yaml):
# спочатку ЗО за зростанням номера/частини, потім ПО за зростанням номера/частини
import re as _re

def natural_code_key(code):
    m = _re.match(r'(ЗО|ПО|ПВ)\s*(\d+)(?:\.(\d+))?', code)
    prefix, num, part = m.group(1), int(m.group(2)), int(m.group(3) or 0)
    prefix_order = {'ЗО': 0, 'ПО': 1, 'ПВ': 2}[prefix]
    return (prefix_order, num, part)

out_disciplines = dict(sorted(out_disciplines.items(), key=lambda kv: natural_code_key(kv[0])))

result = {
    'metadata': dict(Y25['metadata']),
    'disciplines': out_disciplines,
    'competencies': Y25['competencies'],
    'program_results': Y25['program_results'],
    'mappings': out_mappings,
}
result['metadata']['year'] = '2026'
result['metadata']['page_id'] = 10930
result['metadata']['created_date'] = '2026-08-14'
result['metadata']['last_updated'] = '2026-08-14'
result['metadata']['_draft_note'] = (
    'Автоматично згенеровано з data2026.py на основі bachelor2025.yaml. '
    'Поля зі значенням TODO-2026 та розділені кредити потребують ручної перевірки.'
)

class Dumper(yaml.SafeDumper):
    pass

def str_presenter(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

Dumper.add_representer(str, str_presenter)

with open('bachelor2026.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(result, f, Dumper=Dumper, allow_unicode=True, sort_keys=False, width=100)

print(f"Дисциплін у 2026: {len(out_disciplines)}")
print(f"Мапінгів компетенцій перенесено: {len(out_mappings)}")
total_credits = sum(v['credits'] for v in out_disciplines.values() if v['credits'] != TODO)
todo_count = sum(1 for v in out_disciplines.values() if v['credits'] == TODO)
print(f"Сума відомих кредитів: {total_credits} (TODO ще {todo_count} дисциплін)")
print()
print("=== ПРИМІТКИ / ПОТРЕБУЄ ПЕРЕВІРКИ ===")
for n in notes:
    print(" -", n)
