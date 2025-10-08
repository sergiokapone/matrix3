from pathlib import Path

import pandas as pd

from core.file_utils import load_yaml_data
from core.logging_config import get_logger

logger = get_logger(__name__)


def generate_excel_report(
    yaml_file: str, output_file: str | Path = "matrices.xlsx"
) -> None:
    """
    Генерує Excel файл з матрицями компетенцій та програмних результатів на основі YAML конфігу
    """

    # Завантажуємо YAML
    config = load_yaml_data(yaml_file)

    disciplines = config["disciplines"]
    competencies = config["competencies"]
    program_results = config["program_results"]
    mappings = config["mappings"]

    # === МАТРИЦЯ КОМПЕТЕНЦІЙ ===
    comp_df = pd.DataFrame(
        "", index=list(competencies.keys()), columns=list(disciplines.keys())
    )

    # === МАТРИЦЯ ПРОГРАМНИХ РЕЗУЛЬТАТІВ ===
    prog_df = pd.DataFrame(
        "", index=list(program_results.keys()), columns=list(disciplines.keys())
    )

    # Заповнюємо матриці на основі mappings
    for discipline_code, mapping in mappings.items():
        if discipline_code in disciplines:
            # Компетенції
            for comp_code in mapping.get("competencies", []):
                if comp_code in comp_df.index:
                    comp_df.at[comp_code, discipline_code] = "+"

            # Програмні результати
            for prog_code in mapping.get("program_results", []):
                if prog_code in prog_df.index:
                    prog_df.at[prog_code, discipline_code] = "+"

    # Створюємо багаторівневі заголовки колонок
    # 🔧 ВИПРАВЛЕННЯ: отримуємо назву дисципліни
    comp_columns = pd.MultiIndex.from_tuples(
        [
            (
                disciplines[code].get("name", code)
                if isinstance(disciplines[code], dict)
                else disciplines[code],
                code,
            )
            for code in comp_df.columns
        ],
        names=["Дисципліна", "Код"],
    )

    prog_columns = pd.MultiIndex.from_tuples(
        [
            (
                disciplines[code].get("name", code)
                if isinstance(disciplines[code], dict)
                else disciplines[code],
                code,
            )
            for code in prog_df.columns
        ],
        names=["Дисципліна", "Код"],
    )

    comp_df.columns = comp_columns
    prog_df.columns = prog_columns

    # Зберігаємо в один Excel файл з трьома листами
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        comp_df.to_excel(writer, sheet_name="Компетентності")
        prog_df.to_excel(writer, sheet_name="Програмні результати")

        # === ЗВЕДЕНА ТАБЛИЦЯ ===
        summary_data = []
        for disc_code, disc_info in disciplines.items():
            # 🔧 ВИПРАВЛЕННЯ: обробка словника або рядка
            disc_name = (
                disc_info.get("name", disc_code)
                if isinstance(disc_info, dict)
                else disc_info
            )
            mapping = mappings.get(disc_code, {})
            comps = mapping.get("competencies", [])
            progs = mapping.get("program_results", [])

            summary_data.append(
                {
                    "Код": disc_code,
                    "Дисципліна": disc_name,
                    "Компетенції": ", ".join(comps) if comps else "",
                    "Програмні результати": ", ".join(progs) if progs else "",
                    "Кількість компетенцій": len(comps),
                    "Кількість ПРН": len(progs),
                }
            )

        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name="Зведена таблиця", index=False)

        # Налаштовуємо ширину колонок для зведеної таблиці
        worksheet = writer.sheets["Зведена таблиця"]
        worksheet.column_dimensions["A"].width = 10  # Код
        worksheet.column_dimensions["B"].width = 50  # Дисципліна
        worksheet.column_dimensions["C"].width = 40  # Компетенції
        worksheet.column_dimensions["D"].width = 40  # Програмні результати
        worksheet.column_dimensions["E"].width = 15  # Кількість компетенцій
        worksheet.column_dimensions["F"].width = 15  # Кількість ПРН

    logger.info(f"✅ Матриці згенеровано: {output_file}")
    logger.info(f"📊 Компетенції: {len(competencies)} x {len(disciplines)}")
    logger.info(f"📊 Програмні результати: {len(program_results)} x {len(disciplines)}")
    logger.info(f"📋 Зведена таблиця: {len(disciplines)} дисциплін")
