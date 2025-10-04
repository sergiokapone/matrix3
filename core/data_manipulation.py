
from logging import config
from pathlib import Path

from core.config import AppConfig
from core.exceptions import DisciplineGeneratorError
from core.file_utils import load_yaml_data
from core.validators import validate_yaml_schema

from core.logging_config import get_logger
logger = get_logger(__name__)

config = AppConfig()

def get_mapped_competencies(
    discipline_code: str,
    mappings: dict,
    all_competencies: dict
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Отримує компетенції для конкретної дисципліни"""
    if discipline_code not in mappings:
        return [], []

    mapped_comps = mappings[discipline_code].get("competencies", [])
    general_competencies = []
    professional_competencies = []

    for comp_code in mapped_comps:
        if comp_code in all_competencies:
            comp_desc = all_competencies[comp_code]
            if comp_code.startswith("ЗК"):
                general_competencies.append((comp_code, comp_desc))
            elif comp_code.startswith("ФК"):
                professional_competencies.append((comp_code, comp_desc))

    return general_competencies, professional_competencies


def get_mapped_program_results(
    discipline_code: str,
    mappings: dict,
    all_program_results: dict
) -> list[tuple[str, str]]:
    """Отримує програмні результати навчання для дисципліни"""
    if discipline_code not in mappings:
        return []

    mapped_results = mappings[discipline_code].get("program_results", [])
    program_results = []

    for prn_code in mapped_results:
        if prn_code in all_program_results:
            program_results.append((prn_code, all_program_results[prn_code]))

    return program_results


def load_discipline_data(
    yaml_file: str | Path,
    discipline_code: str
) -> tuple[dict | None, dict | None]:
    """Завантажує дані дисципліни та інформацію про викладачів"""
    try:
        data = load_yaml_data(yaml_file)
        lecturers = load_yaml_data(config.lecturers_yaml)

        validate_yaml_schema(data)

        all_disciplines = data["disciplines"].copy()
        if "elevative_disciplines" in data:
            all_disciplines.update(data["elevative_disciplines"])

        if discipline_code not in all_disciplines:
            logger.warning("Discipline not found", discipline_code=discipline_code)
            return None, None

        discipline = all_disciplines[discipline_code]

        if "lecturer_id" in discipline:
            lecturer_id = discipline["lecturer_id"]
            if lecturer_id in lecturers:
                discipline["lecturer"] = lecturers[lecturer_id]
            else:
                logger.warning("Lecturer not found", lecturer_id=lecturer_id)

        return data, discipline

    except Exception as e:
        logger.error("Failed to load discipline data", error=str(e))
        raise DisciplineGeneratorError(f"Error loading discipline data: {e}")
    

def prepare_disciplines_with_totals(disciplines: dict) -> dict:
    """Додає розраховані підсумки до кожної дисципліни"""
    for _, discipline in disciplines.items():
        total_credits, all_controls = calculate_subdiscipline_totals(discipline)
        discipline["total_credits"] = total_credits
        discipline["all_controls"] = all_controls

    return disciplines

def calculate_subdiscipline_totals(discipline: dict) -> tuple[int, str]:
    """Розраховує загальні кредити та форми контролю для піддисциплін"""
    if "subdisciplines" not in discipline or not discipline["subdisciplines"]:
        return discipline.get("credits", 0), discipline.get("control", "")

    total_credits = sum(
        sub.get("credits", 0) for sub in discipline["subdisciplines"].values()
    )

    controls = list(
        {
            sub.get("control")
            for sub in discipline["subdisciplines"].values()
            if sub.get("control")
        }
    )

    return total_credits, ", ".join(controls)