# logger.py
import logging
from pathlib import Path

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
    def format(self, record):
        levelname = record.levelname
        color = COLORS.get(levelname, RESET)
        emoji = EMOJIS.get(levelname, "")
        record.levelname = f"{color}{levelname}{RESET}"
        record.message = f"{emoji} {record.getMessage()}"
        return super().format(record)

def setup_logging(name: str = "wp pages", level: str = "INFO"):
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    handler = logging.StreamHandler()
    formatter = ColorFormatter(
        "%(levelname)s | %(name)s: %(lineno)d |  %(funcName)s() | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    if not logger.hasHandlers():
        logger.addHandler(handler)

    return logger


def get_logger(name: str = "wp pages"):
    """Отримати логер (автоматично налаштує, якщо ще не налаштований)"""
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        setup_logging(name)
    return logger