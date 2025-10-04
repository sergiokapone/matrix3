# logger.py
import logging

RESET = "\033[0m"
COLORS = {
    "DEBUG": "\033[36m",
    "INFO": "\033[32m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[41m",
}

EMOJIS = {
    "DEBUG": "🐛",
    "INFO": "✅",
    "WARNING": "⚠️",
    "ERROR": "❌",
    "CRITICAL": "💥"
}


class ColorFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, color: str | None = None):
        """
        color: якщо задано, весь текст повідомлення буде в цьому кольорі
        """
        super().__init__(fmt, datefmt)
        self.color = color  # None = стандартний режим (кольори рівнів)

    def format(self, record):
        if self.color:
            # весь текст повідомлення у заданому кольорі
            record.msg = f"{self.color}{record.getMessage()}{RESET}"
        else:
            # стандартний режим: кольори та емодзі для рівня логування
            color = COLORS.get(record.levelname, RESET)
            emoji = EMOJIS.get(record.levelname, "")
            record.msg = f"{emoji} {record.getMessage()}"
            record.levelname = f"{color}{record.levelname}{RESET}"
        return super().format(record)


def setup_logging(
    name: str = "wp pages",
    level: str = "INFO",
    formatter: logging.Formatter | None = None
):
    """Налаштувати логер з можливістю передати кастомний форматтер"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        if formatter is None:
            # стандартний логер: кольори рівня + емодзі
            formatter = ColorFormatter(
                "%(levelname)s | %(name)s: %(lineno)d | %(funcName)s() | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def get_logger(
    name: str = "wp pages",
    level: str = "INFO",
    formatter: logging.Formatter | None = None,
    color: str | None = None
):
    """
    Отримати логер:
      - color: якщо задано, весь текст повідомлення буде в цьому кольорі
      - formatter: можна передати свій кастомний форматтер
      - level: рівень логування по замовчуванню
    """
    if formatter is None and color:
        formatter = ColorFormatter("%(levelname)s | %(name)s | %(message)s", color=color)

    return setup_logging(name=name, level=level, formatter=formatter)
