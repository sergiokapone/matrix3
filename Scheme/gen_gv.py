"""
Генератор диаграммы учебного плана в формате Graphviz DOT
Використання: python gen_gv.py [ua|en] [year]
Приклад: python gen_gv.py ua 2025
"""

import sys
import importlib

# ===== НАЛАШТУВАННЯ ЗА ЗАМОВЧУВАННЯМ =====
DEFAULT_YEAR = 2025

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


def get_edge_color(source_id, disciplines):
    """Определяет цвет связи на основе типа исходной дисциплины"""
    return EDGE_COLORS.get(disciplines[source_id]["type"], "#666666")


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


def generate_semester_cluster(semester, lang, disciplines):
    """Генерирует кластер для одного семестра"""
    semester_label = f"Семестр {semester}" if lang == "ua" else f"Semester {semester}"

    # Получаем все дисциплины семестра
    semester_disciplines = {
        disc_id: disc_data
        for disc_id, disc_data in disciplines.items()
        if disc_data["semester"] == semester
    }

    if not semester_disciplines:
        return ""

    lines = [
        f'    subgraph cluster_{semester} {{',
        f'        style="filled";',
        f'        label="{semester_label}";',
        f'        color="#E8F4F8";',
        f'        rank="same";'
    ]

    # Добавляем дисциплины
    for disc_id, disc_data in sorted(semester_disciplines.items()):
        label = disc_data[lang]
        color = COLORS.get(disc_data["type"], "#CCCCCC")
        lines.append(f'        {disc_id} [label="{label}", fillcolor="{color}"];')

    lines.append('    }')
    return '\n'.join(lines)


def generate_final_cluster(lang, disciplines):
    """Генерирует финальный кластер для практики и диплома"""
    lines = [
        '    subgraph cluster_9 {',
        '        style="filled";',
        '        color="#E8F4F8";',
        '        rank="same";'
    ]

    # Добавляем переддипломную практику и дипломное проектирование
    practice_label = disciplines["S8_Practice"][lang]
    diploma_label = disciplines["S8_Diploma"][lang]

    lines.extend([
        f'        S8_Practice [label="{practice_label}", fillcolor="{COLORS["pract"]}"];',
        '        _dummy1 [label="", shape=point, width=0, height=0];',
        f'        S8_Diploma [label="{diploma_label}", fillcolor="{COLORS["pract"]}"];',
        '    }'
    ])

    return '\n'.join(lines)


def generate_edges(disciplines, edges):
    """Генерирует все связи между дисциплинами"""
    lines = []

    # Группируем связи по типам для удобства
    edges_by_type = {}
    for source, target in edges:
        edge_type = disciplines[source]["type"]
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
                color = get_edge_color(source, disciplines)
                lines.append(f'{source}     -> {target}        [color="{color}", penwidth=2];')
            lines.append('')

    return '\n'.join(lines)


def generate_diagram(lang, disciplines, edges):
    """Генерирует полную диаграмму"""
    if lang not in ["ua", "en"]:
        raise ValueError("Language must be 'ua' or 'en'")

    parts = [generate_header()]

    # Генерируем кластеры для семестров 1-8
    for semester in range(1, 9):
        cluster = generate_semester_cluster(semester, lang, disciplines)
        if cluster:
            parts.append(cluster)

    # Добавляем финальный кластер
    parts.append(generate_final_cluster(lang, disciplines))

    # Добавляем связи
    parts.append(generate_edges(disciplines, edges))

    # Закрываем диаграмму
    parts.append('}')

    return '\n'.join(parts)


def main():
    """Главная функция"""
    # Определяем язык из аргументов командной строки
    lang = "ua"
    year = DEFAULT_YEAR
    
    if len(sys.argv) > 1:
        lang = sys.argv[1].lower()
        if lang not in ["ua", "en"]:
            print("Error: Language must be 'ua' or 'en'")
            print("Usage: python gen_gv.py [ua|en] [year]")
            print("Example: python gen_gv.py ua 2025")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        try:
            year = int(sys.argv[2])
        except ValueError:
            print("Error: Year must be a number")
            print("Usage: python gen_gv.py [ua|en] [year]")
            print("Example: python gen_gv.py ua 2025")
            sys.exit(1)

    # Динамічний імпорт data модуля на основі року
    try:
        data_module = importlib.import_module(f"data{year}")
        disciplines = data_module.DISCIPLINES
        edges = data_module.EDGES
    except ImportError:
        print(f"Error: File 'data{year}.py' not found!")
        print(f"Make sure you have a data file for year {year}")
        sys.exit(1)
    except AttributeError:
        print(f"Error: 'data{year}.py' must contain DISCIPLINES and EDGES")
        sys.exit(1)

    # Генерируем диаграмму
    diagram = generate_diagram(lang, disciplines, edges)

    # Определяем имя выходного файла
    output_file = f"diagramm_bak_{year}_{lang}.gv"

    # Сохраняем в файл
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(diagram)

    print(f"Diagram generated successfully: {output_file}")
    print(f"Year: {year}")
    print(f"Language: {'Ukrainian' if lang == 'ua' else 'English'}")
    print(f"Total disciplines: {len(disciplines)}")
    print(f"Total edges: {len(edges)}")


if __name__ == "__main__":
    main()