# exceptions.py
class DisciplineGeneratorError(Exception):
    """Базовое исключение для генератора дисциплин"""

    pass


class DisciplineNotFoundError(DisciplineGeneratorError):
    """Дисциплина не найдена"""

    pass


class TemplateRenderError(DisciplineGeneratorError):
    """Ошибка рендеринга шаблона"""

    pass


class WordPressUploadError(DisciplineGeneratorError):
    """Ошибка загрузки в WordPress"""

    pass


class YAMLValidationError(DisciplineGeneratorError):
    """Ошибка валидации YAML"""

    pass


class ParrentIdError(Exception):
    """Не существует parrent id"""

    pass
