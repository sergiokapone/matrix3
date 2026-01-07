import re
import json

def parse_graphviz_file(filename):
    """Парсинг Graphviz файлу для витягування курсів та їх зв'язків"""

    courses = {}
    edges = []

    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Парсинг визначень вузлів (курсів)
    node_pattern = r'(\w+)\s*\[label="([^"]+)"[^\]]*fillcolor="([^"]+)"'
    for match in re.finditer(node_pattern, content):
        node_id = match.group(1)
        label = match.group(2).replace('\\n', ' ')
        color = match.group(3)
        courses[node_id] = {
            'name': label,
            'color': color
        }

    # Парсинг ребер (пререквізитів)
    edge_pattern = r'(\w+)\s*->\s*(\w+)'
    for match in re.finditer(edge_pattern, content):
        from_node = match.group(1)
        to_node = match.group(2)
        if from_node in courses and to_node in courses:
            edges.append((from_node, to_node))

    return courses, edges


def build_prerequisite_dict(courses, edges):
    """Побудова словника з пререквізитами та пострерквізитами для кожного курсу"""

    result = {}

    # Ініціалізація для всіх курсів
    for course_id, course_info in courses.items():
        result[course_id] = {
            'name': course_info['name'],
            'prerequisites': [],  # курси, які потрібні перед цим
            'postrequisites': []  # курси, для яких потрібен цей
        }

    # Заповнення зв'язків
    for from_node, to_node in edges:
        # from_node є пререквізитом для to_node
        result[to_node]['prerequisites'].append(courses[from_node]['name'])
        # to_node є пострерквізитом для from_node
        result[from_node]['postrequisites'].append(courses[to_node]['name'])

    # Сортування для зручності
    for course_id in result:
        result[course_id]['prerequisites'].sort()
        result[course_id]['postrequisites'].sort()

    return result


# Головна функція
if __name__ == "__main__":
    filename = "diagramm_bak_2024.gv"

    try:
        # Парсинг файлу
        courses, edges = parse_graphviz_file(filename)

        # Побудова словника
        prerequisite_dict = build_prerequisite_dict(courses, edges)

        # Виведення результату
        print(f"Завантажено {len(courses)} курсів та {len(edges)} зв'язків\n")

        # Виведення у зручному форматі
        for course_id in sorted(prerequisite_dict.keys()):
            info = prerequisite_dict[course_id]
            print(f"{course_id}:")
            print(f"  Назва: {info['name']}")
            print(f"  Пререквізити ({len(info['prerequisites'])}): {info['prerequisites']}")
            print(f"  Пострерквізити ({len(info['postrequisites'])}): {info['postrequisites']}")
            print()

        # Збереження в JSON (опціонально)
        with open('prerequisites.json', 'w', encoding='utf-8') as f:
            json.dump(prerequisite_dict, f, ensure_ascii=False, indent=2)

        print("✅ Результат збережено в prerequisites.json")

        # Також повертаємо словник для використання в коді
        # prerequisite_dict доступний для подальшого використання

    except FileNotFoundError:
        print(f"❌ Файл '{filename}' не знайдено!")
    except Exception as e:
        print(f"❌ Помилка: {e}")

