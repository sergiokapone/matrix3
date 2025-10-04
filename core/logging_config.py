import logging
from pathlib import Path

# Цветовые коды ANSI
RESET = "\033[0m"
COLORS = {
    "DEBUG": "\033[36m",     # Cyan
    "INFO": "\033[32m",      # Green
    "WARNING": "\033[33m",   # Yellow
    "ERROR": "\033[31m",     # Red
    "CRITICAL": "\033[41m",  # Red background
}

class ColorFormatter(logging.Formatter):
    def format(self, record):
        color = COLORS.get(record.levelname, RESET)
        emoji = {
            "DEBUG": "🐛",
            "INFO": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "💥"
        }.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{RESET}"
        record.msg = f"{emoji} {record.msg}"
        return super().format(record)

def setup_logging(level: str = "INFO"):
    logger = logging.getLogger("disciplines")
    logger.setLevel(getattr(logging, level.upper()))
    
    handler = logging.StreamHandler()
    formatter = ColorFormatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    
    if not logger.hasHandlers():
        logger.addHandler(handler)
    
    return logger

logger = setup_logging()
