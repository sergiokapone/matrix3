from jinja2 import Environment, FileSystemLoader

from core.config import AppConfig
from core.exceptions import TemplateRenderError

config = AppConfig()


def get_jinja_environment() -> Environment:
    """Створює налаштоване Jinja2 Environment"""
    templates_dir = config.template_dir
    if not templates_dir.exists():
        raise TemplateRenderError(f"Templates directory not found: {templates_dir}")

    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
