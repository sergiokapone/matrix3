#!/usr/bin/env python3
"""
Повний пайплайн генерації діаграми навчального плану
Використання: python pipeline.py [lang] [year]
Приклад: python pipeline.py ua 2025
"""

import sys
import subprocess
import os
from pathlib import Path

# ===== НАЛАШТУВАННЯ ЗА ЗАМОВЧУВАННЯМ =====
DEFAULT_LANG = "ua"
DEFAULT_YEAR = 2025


def print_header(text):
    """Виводить красивий заголовок"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_step(step_num, total, text):
    """Виводить номер кроку"""
    print(f"\n[{step_num}/{total}] {text}...")


def run_command(cmd, description):
    """Запускає команду та перевіряє результат"""
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.stdout:
            print(result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Помилка при {description}!")
        if e.stderr:
            print(e.stderr)
        return False
    except FileNotFoundError:
        print(f"[ERROR] Команда не знайдена: {cmd[0]}")
        return False


def check_file_exists(filepath, description):
    """Перевіряє чи існує файл"""
    if not Path(filepath).exists():
        print(f"[ERROR] Файл {filepath} не знайдено!")
        print(f"   {description}")
        return False
    return True


def main():
    """Головна функція"""
    # Парсинг аргументів
    lang = DEFAULT_LANG
    year = DEFAULT_YEAR

    if len(sys.argv) > 1:
        lang = sys.argv[1].lower()
        if lang not in ["ua", "en"]:
            print("Error: Language must be 'ua' or 'en'")
            print("Usage: python pipeline.py [lang] [year]")
            print("Example: python pipeline.py ua 2025")
            sys.exit(1)

    if len(sys.argv) > 2:
        try:
            year = int(sys.argv[2])
        except ValueError:
            print("Error: Year must be a number")
            print("Usage: python pipeline.py [lang] [year]")
            print("Example: python pipeline.py ua 2025")
            sys.exit(1)

    # Виводимо інформацію
    print_header("Генерація навчального плану")
    print(f"Мова: {'Українська' if lang == 'ua' else 'English'}")
    print(f"Рік: {year}")

    # Імена файлів
    gv_file = f"diagramm_bak_{year}_{lang}.gv"
    pdf_file = f"diagramm_bak_{year}_{lang}.pdf"
    json_file = f"prerequisites_{year}.json"
    html_file = f"../docs/requisites_bachelor_{year}.html"

    # Перевіряємо наявність data файлу
    data_file = f"data{year}.py"
    if not check_file_exists(
        data_file, f"Створіть файл data{year}.py з даними навчального плану"
    ):
        sys.exit(1)

    total_steps = 4

    # ============================================================
    # Крок 1: Генерація Graphviz діаграми
    # ============================================================
    print_step(1, total_steps, "Генерація Graphviz діаграми")
    if not run_command(
        [sys.executable, "gen_gv.py", lang, str(year)], "генерації діаграми"
    ):
        sys.exit(1)

    if not check_file_exists(gv_file, "Щось пішло не так при генерації"):
        sys.exit(1)

    print(f"[OK] Діаграму згенеровано: {gv_file}")

    # ============================================================
    # Крок 2: Конвертація в PDF
    # ============================================================
    print_step(2, total_steps, "Конвертація в PDF")

    # Перевіряємо наявність Graphviz
    try:
        subprocess.run(["dot", "-V"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[WARNING] Graphviz не встановлено або не в PATH")
        print("   Завантажте з https://graphviz.org/download/")
        print("   Пропускаємо генерацію PDF...")
    else:
        if run_command(["dot", "-Tpdf", gv_file, "-o", pdf_file], "конвертації в PDF"):
            print(f"[OK] PDF створено: {pdf_file}")
        else:
            print("[WARNING] Помилка при створенні PDF, продовжуємо...")

    # ============================================================
    # Крок 3: Витягування пререквізитів
    # ============================================================
    print_step(3, total_steps, "Витягування пререквізитів")
    if not run_command(
        [sys.executable, "prepost_extract.py", str(year), lang],
        "витягування пререквізитів",
    ):
        sys.exit(1)

    if not check_file_exists(json_file, "Щось пішло не так при витягуванні"):
        sys.exit(1)

    print(f"[OK] Пререквізити збережено: {json_file}")

    # ============================================================
    # Крок 4: Генерація HTML таблиці
    # ============================================================
    print_step(4, total_steps, "Генерація HTML таблиці")
    if not run_command([sys.executable, "html_gen.py", str(year)], "генерації HTML"):
        sys.exit(1)

    if not check_file_exists(html_file, "Щось пішло не так при генерації HTML"):
        sys.exit(1)

    print(f"[OK] HTML таблиця створена: {html_file}")

    # ============================================================
    # Підсумок
    # ============================================================
    print_header("Пайплайн завершено успішно!")
    print("\n[RESULTS] Згенеровані файли:")
    print(f"   - {gv_file} - Graphviz діаграма")
    if Path(pdf_file).exists():
        print(f"   - {pdf_file} - PDF діаграма")
    print(f"   - {json_file} - JSON з пререквізитами")
    print(f"   - {html_file} - HTML таблиця")

    print("\n[INFO] Для перегляду HTML відкрийте файл у браузері")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
