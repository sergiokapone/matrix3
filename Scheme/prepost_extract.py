"""
Парсинг Graphviz файлу для витягування пререквізитів та пострерквізитів
Використання: python prepost_extract.py [year] [lang]
Приклад: python prepost_extract.py 2025 ua
"""

import json
import re
import sys

# ===== НАЛАШТУВАННЯ ЗА ЗАМОВЧУВАННЯМ =====
DEFAULT_YEAR = 2025
DEFAULT_LANG = "ua"


def parse_graphviz_file(filename: str) -> tuple[dict, list]:
    """Парсинг Graphviz файлу для витягування курсів та їх зв'язків"""

    courses = {}
    edges = []

    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()

    # Парсинг визначень вузлів (курсів)
    node_pattern = r'(\w+)\s*\[label="([^"]+)"[^\]]*fillcolor="([^"]+)"'
    for match in re.finditer(node_pattern, content):
        node_id = match.group(1)
        label = match.group(2).replace("\\n", " ")
        color = match.group(3)
        courses[node_id] = {
            "name": label,
            "color": color
        }

    # Парсинг ребер (пререквізитів)
    edge_pattern = r"(\w+)\s*->\s*(\w+)"
    for match in re.finditer(edge_pattern, content):
        from_node = match.group(1)
        to_node = match.group(2)
        if from_node in courses and to_node in courses:
            edges.append((from_node, to_node))

    return courses, edges


def build_prerequisite_dict(courses: dict, edges: list) -> dict:
    """Побудова словника з пререквізитами та пострерквізитами для кожного курсу"""

    result = {}

    # Ініціалізація для всіх курсів
    for course_id, course_info in courses.items():
        result[course_id] = {
            "name": course_info["name"],
            "prerequisites": [],  # курси, які потрібні перед цим
            "postrequisites": []  # курси, для яких потрібен цей
        }

    # Заповнення зв'язків
    for from_node, to_node in edges:
        # from_node є пререквізитом для to_node
        result[to_node]["prerequisites"].append(courses[from_node]["name"])
        # to_node є пострерквізитом для from_node
        result[from_node]["postrequisites"].append(courses[to_node]["name"])

    # Сортування для зручності
    for course_id in result:
        result[course_id]["prerequisites"].sort()
        result[course_id]["postrequisites"].sort()

    return result


def main():
    """Головна функція"""
    year = DEFAULT_YEAR
    lang = DEFAULT_LANG
    
    # Парсинг аргументів
    if len(sys.argv) > 1:
        try:
            year = int(sys.argv[1])
        except ValueError:
            print("Error: Year must be a number")
            print("Usage: python prepost_extract.py [year] [lang]")
            print("Example: python prepost_extract.py 2025 ua")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        lang = sys.argv[2].lower()
        if lang not in ["ua", "en"]:
            print("Error: Language must be 'ua' or 'en'")
            print("Usage: python prepost_extract.py [year] [lang]")
            print("Example: python prepost_extract.py 2025 ua")
            sys.exit(1)
    
    # Формуємо імена файлів
    input_file = f"diagramm_bak_{year}_{lang}.gv"
    output_file = f"prerequisites_{year}.json"

    try:
        # Парсинг файлу
        courses, edges = parse_graphviz_file(input_file)

        # Побудова словника
        prerequisite_dict = build_prerequisite_dict(courses, edges)

        # Виведення результату
        print(f"Завантажено {len(courses)} курсів та {len(edges)} зв'язків\n")

        # Виведення у зручному форматі (перші 3 для прикладу)
        for i, course_id in enumerate(sorted(prerequisite_dict.keys())):
            if i >= 3:
                print("...")
                break
            info = prerequisite_dict[course_id]
            print(f"{course_id}:")
            print(f"  Назва: {info['name']}")
            print(f"  Пререквізити ({len(info['prerequisites'])}): {info['prerequisites']}")
            print(f"  Пострерквізити ({len(info['postrequisites'])}): {info['postrequisites']}")
            print()

        # Збереження в JSON
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(prerequisite_dict, f, ensure_ascii=False, indent=2)

        print(f"[OK] Результат збережено в {output_file}")
        print(f"Year: {year}, Language: {lang}")

    except FileNotFoundError:
        print(f"[ERROR] Файл '{input_file}' не знайдено!")
        print(f"Спершу згенеруйте діаграму: python gen_gv.py {lang} {year}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Помилка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()