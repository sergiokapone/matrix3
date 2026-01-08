"""
Генератор диаграммы учебного плана в формате Graphviz DOT
Использование: python generate_diagram.py [ua|en]
"""

import sys
from data import DISCIPLINES, EDGES

# Цвета для разных типов дисциплин
COLORS = {
    "math": "#4A90E2",      # Синий - математика
    "physics": "#E85D75",   # Красный - физика
    "comp": "#7ED321",      # Зеленый - программирование
    "elective": "#F5A623",  # Оранжевый - выборочные
    "pract": "#D4A5FF",     # Фиолетовый - практика
    "general": "#B8B8B8"    # Серый - общие дисциплины
}

# Цвета для связей (по типам)
EDGE_COLORS = {
    "math": "#4A90E2",
    "physics": "#E85D75",
    "comp": "#7ED321",
    "general": "#B8B8B8",
    "pract": "#9013FE"
}


def get_edge_color(source_id):
    """Определяет цвет связи на основе типа исходной дисциплины"""
    return EDGE_COLORS.get(DISCIPLINES[source_id]["type"], "#666666")


def generate_header():
    """Генерирует заголовок диаграммы"""
    return '''digraph Curriculum {
    rankdir="LR";
    splines="ortho";
    nodesep=0.5;
    ranksep=1.25;
    newrank="true";
    node [shape="box", style="rounded,filled", fontsize=14, width=3, height=1, fontname="Arial Bold"];
    edge [color="#666666", penwidth=1.5];
'''


def generate_semester_cluster(semester, lang):
    """Генерирует кластер для одного семестра"""
    semester_label = f"Семестр {semester}" if lang == "ua" else f"Semester {semester}"

    # Получаем все дисциплины семестра
    disciplines = {
        disc_id: disc_data
        for disc_id, disc_data in DISCIPLINES.items()
        if disc_data["semester"] == semester
    }

    if not disciplines:
        return ""

    lines = [
        f'    subgraph cluster_{semester} {{',
        f'        style="filled";',
        f'        label="{semester_label}";',
        f'        color="#E8F4F8";',
        f'        rank="same";'
    ]

    # Добавляем дисциплины
    for disc_id, disc_data in sorted(disciplines.items()):
        label = disc_data[lang]
        color = COLORS.get(disc_data["type"], "#CCCCCC")
        lines.append(f'        {disc_id} [label="{label}", fillcolor="{color}"];')

    lines.append('    }')
    return '\n'.join(lines)


def generate_final_cluster(lang):
    """Генерирует финальный кластер для практики и диплома"""
    lines = [
        '    subgraph cluster_9 {',
        '        style="filled";',
        '        color="#E8F4F8";',
        '        rank="same";'
    ]

    # Добавляем переддипломную практику и дипломное проектирование
    practice_label = DISCIPLINES["S8_Practice"][lang]
    diploma_label = DISCIPLINES["S8_Diploma"][lang]

    lines.extend([
        f'        S8_Practice [label="{practice_label}", fillcolor="{COLORS["pract"]}"];',
        '        _dummy1 [label="", shape=point, width=0, height=0];',
        f'        S8_Diploma [label="{diploma_label}", fillcolor="{COLORS["pract"]}"];',
        '    }'
    ])

    return '\n'.join(lines)


def generate_edges():
    """Генерирует все связи между дисциплинами"""
    lines = []

    # Группируем связи по типам для удобства
    edges_by_type = {}
    for source, target in EDGES:
        edge_type = DISCIPLINES[source]["type"]
        if edge_type not in edges_by_type:
            edges_by_type[edge_type] = []
        edges_by_type[edge_type].append((source, target))

    # Генерируем связи по группам
    type_comments = {
        "math": "ПРЕРЕКВІЗИТИ — Математика",
        "physics": "ПРЕРЕКВІЗИТИ — Фізика",
        "comp": "ПРЕРЕКВІЗИТИ — Програмування та обчислення",
        "general": "ПРЕРЕКВІЗИТИ — Іноземна мова",
        "pract": "ПРЕРЕКВІЗИТИ — Практика та дослідження"
    }

    for edge_type in ["math", "physics", "comp", "general", "pract"]:
        if edge_type in edges_by_type:
            lines.append(f' // {type_comments[edge_type]}')
            for source, target in edges_by_type[edge_type]:
                color = get_edge_color(source)
                lines.append(f'{source}     -> {target}        [color="{color}", penwidth=2];')
            lines.append('')

    return '\n'.join(lines)


def generate_diagram(lang="ua"):
    """Генерирует полную диаграмму"""
    if lang not in ["ua", "en"]:
        raise ValueError("Language must be 'ua' or 'en'")

    parts = [generate_header()]

    # Генерируем кластеры для семестров 1-8
    for semester in range(1, 9):
        cluster = generate_semester_cluster(semester, lang)
        if cluster:
            parts.append(cluster)

    # Добавляем финальный кластер
    parts.append(generate_final_cluster(lang))

    # Добавляем связи
    parts.append(generate_edges())

    # Закрываем диаграмму
    parts.append('}')

    return '\n'.join(parts)


def main():
    """Главная функция"""
    # Определяем язык из аргументов командной строки
    lang = "ua"
    if len(sys.argv) > 1:
        lang = sys.argv[1].lower()
        if lang not in ["ua", "en"]:
            print("Error: Language must be 'ua' or 'en'")
            print("Usage: python generate_diagram.py [ua|en]")
            sys.exit(1)

    # Генерируем диаграмму
    diagram = generate_diagram(lang)

    # Определяем имя выходного файла
    output_file = f"diagramm_bak_2024_{lang}.gv"

    # Сохраняем в файл
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(diagram)

    print(f"Diagram generated successfully: {output_file}")
    print(f"Language: {'Ukrainian' if lang == 'ua' else 'English'}")
    print(f"Total disciplines: {len(DISCIPLINES)}")
    print(f"Total edges: {len(EDGES)}")


if __name__ == "__main__":
    main()
