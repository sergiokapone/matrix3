"""Єдина точка входу: python sitepages/run.py <page> [generate|diff|upload]"""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sitepages.common import load_yaml, publish  # noqa: E402

PAGES = {  # ім'я папки -> опис (сторінка на сайті)
    "syllabi": "/for_stud/syllab_potoch/ — силабуси поточного року",
    "course_works": "/nauka/course-works/ — теми курсових робіт",
    "lab": "/nauka/lab/ — лабораторія «ФіНоТех»",
    "cooperation": "/international/cooperation/ — міжнародне співробітництво",
    "partners": "/international/partners/ — партнери кафедри",
    "kurators": "/kurators/ — куратори студентських груп",
    "contacts": "/main/contacts/ — контакти",
    "mobility": "/international/mobility/ — академічна мобільність",
    "seminar": "/nauka/seminar/ — науковий семінар",
    "stud_sci_works": "/nauka/stud_sci_works/ — наукові роботи студентів (публікації)",
}
# Окремо (багато сторінок): python sitepages/staff/manage.py generate|generate-staff|push|run-all
# — профілі викладачів /kafedra/stuff/<slug>/ і список співробітників (page 181), дані в staff/teachers.yaml


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in PAGES:
        print("Сторінки:\n" + "\n".join(f"  {k:14} {v}" for k, v in PAGES.items()))
        return
    name, cmd = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "generate")
    folder = Path(__file__).parent / name
    data = load_yaml(folder)
    mod = importlib.import_module(f"sitepages.{name}.build")
    publish(folder, data, mod.build(data), cmd)


if __name__ == "__main__":
    main()
