"""
Генерація HTML таблиці з пререквізитами
Використання: python html_gen.py [year]
Приклад: python html_gen.py 2025
"""

import json
import sys
from pathlib import Path

# ===== НАЛАШТУВАННЯ ЗА ЗАМОВЧУВАННЯМ =====
DEFAULT_YEAR = 2025


def generate_html_table(json_filename: Path, output_html: str) -> None:
    """Генерація HTML таблиці з JSON файлу з пререквізитами"""

    # Читання JSON
    with open(json_filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Генерація HTML
    html = """<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Пререквізити навчального плану</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .search-container {
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }

        .search-box {
            width: 100%;
            padding: 15px 20px;
            font-size: 16px;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            transition: all 0.3s;
        }

        .search-box:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .stats {
            padding: 20px 30px;
            background: #f8f9fa;
            display: flex;
            gap: 30px;
            flex-wrap: wrap;
            justify-content: center;
            border-bottom: 2px solid #e9ecef;
        }

        .stat-item {
            text-align: center;
        }

        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }

        .stat-label {
            color: #6c757d;
            font-size: 0.9em;
            margin-top: 5px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            position: sticky;
            top: 0;
            z-index: 10;
        }

        th {
            padding: 18px 15px;
            text-align: left;
            font-weight: 600;
            font-size: 0.95em;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }

        tbody tr {
            border-bottom: 1px solid #e9ecef;
            transition: all 0.2s;
        }

        tbody tr:hover {
            background: #f8f9fa;
            transform: scale(1.01);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        tbody tr.hidden {
            display: none;
        }

        td {
            padding: 15px;
            vertical-align: top;
        }

        .course-name {
            font-weight: 600;
            color: #2c3e50;
            font-size: 1.05em;
            margin-bottom: 5px;
        }

        .course-id {
            color: #6c757d;
            font-size: 0.85em;
            font-family: 'Courier New', monospace;
            background: #e9ecef;
            padding: 2px 8px;
            border-radius: 4px;
            display: inline-block;
        }

        .list-items {
            list-style: none;
            padding: 0;
        }

        .list-items li {
            padding: 8px 12px;
            margin: 5px 0;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 3px solid #667eea;
            transition: all 0.2s;
        }

        .list-items li:hover {
            background: #e9ecef;
            border-left-color: #764ba2;
            transform: translateX(5px);
        }

        .empty-list {
            color: #adb5bd;
            font-style: italic;
            padding: 10px;
        }

        .count {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
            margin-left: 8px;
        }

        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8em;
            }

            table {
                font-size: 0.9em;
            }

            th, td {
                padding: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 Пререквізити навчального плану</h1>
            <p>Прикладна фізика та наноматеріали</p>
        </div>

        <div class="search-container">
            <input type="text" class="search-box" id="searchInput" placeholder="🔍 Пошук дисципліни...">
        </div>

        <div class="stats">
            <div class="stat-item">
                <div class="stat-number" id="totalCourses">0</div>
                <div class="stat-label">Всього дисциплін</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" id="visibleCourses">0</div>
                <div class="stat-label">Показано</div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th style="width: 25%;">Дисципліна</th>
                    <th style="width: 37.5%;">Пререквізити</th>
                    <th style="width: 37.5%;">Пострерквізити</th>
                </tr>
            </thead>
            <tbody id="tableBody">
"""

    # Додавання рядків таблиці
    for course_id in sorted(data.keys()):
        course = data[course_id]

        # Пререквізити
        prereq_html = ""
        if course["prerequisites"]:
            prereq_items = "".join([f"<li>{p}</li>" for p in course["prerequisites"]])
            prereq_html = f'<ul class="list-items">{prereq_items}</ul>'
        else:
            prereq_html = '<div class="empty-list">Немає пререквізитів</div>'

        # Пострерквізити
        postreq_html = ""
        if course["postrequisites"]:
            postreq_items = "".join([f"<li>{p}</li>" for p in course["postrequisites"]])
            postreq_html = f'<ul class="list-items">{postreq_items}</ul>'
        else:
            postreq_html = '<div class="empty-list">Немає пострерквізитів</div>'

        prereq_count = len(course["prerequisites"])
        postreq_count = len(course["postrequisites"])

        html += f"""
                <tr>
                    <td>
                        <div class="course-name">{course['name']}</div>
                        <span class="course-id">{course_id}</span>
                    </td>
                    <td>
                        {prereq_html}
                        <span class="count">{prereq_count}</span>
                    </td>
                    <td>
                        {postreq_html}
                        <span class="count">{postreq_count}</span>
                    </td>
                </tr>
"""

    # Закриття HTML
    html += """
            </tbody>
        </table>
    </div>

    <script>
        // Підрахунок статистики
        const totalRows = document.querySelectorAll('#tableBody tr').length;
        document.getElementById('totalCourses').textContent = totalRows;
        document.getElementById('visibleCourses').textContent = totalRows;

        // Пошук
        const searchInput = document.getElementById('searchInput');
        const tableBody = document.getElementById('tableBody');
        const rows = tableBody.querySelectorAll('tr');

        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            let visibleCount = 0;

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.classList.remove('hidden');
                    visibleCount++;
                } else {
                    row.classList.add('hidden');
                }
            });

            document.getElementById('visibleCourses').textContent = visibleCount;
        });
    </script>
</body>
</html>
"""

    # Збереження HTML
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ HTML таблиця створена: {output_html}")
    print(f"📊 Всього дисциплін: {len(data)}")


def main():
    """Головна функція"""
    year = DEFAULT_YEAR
    
    if len(sys.argv) > 1:
        try:
            year = int(sys.argv[1])
        except ValueError:
            print("Error: Year must be a number")
            print("Usage: python html_gen.py [year]")
            print("Example: python html_gen.py 2025")
            sys.exit(1)
    
    # Формуємо імена файлів на основі року
    json_file = Path(f"prerequisites_{year}.json")
    html_file = f"requisites_bachelor_{year}.html"
    
    # Перевіряємо чи існує JSON файл
    if not json_file.exists():
        print(f"Error: File '{json_file}' not found!")
        print(f"Make sure you have a prerequisites file for year {year}")
        sys.exit(1)
    
    # Генеруємо HTML
    generate_html_table(json_file, html_file)
    print(f"Year: {year}")


if __name__ == "__main__":
    main()