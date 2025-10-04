from core.exceptions import TemplateRenderError
from core.junja_environment import get_jinja_environment


def render_template(template_file_name: str, context: dict) -> str:
    """Рендерить HTML-контент через Jinja2-шаблон"""
    try:
        env = get_jinja_environment()
        # FileSystemLoader уже знает про templates_dir,
        # поэтому передаем только имя файла шаблона
        template = env.get_template(template_file_name)
        return template.render(context)
    except Exception as e:
        raise TemplateRenderError(f"Error rendering template {template_file_name}: {e}")
