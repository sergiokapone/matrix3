import logging
from pathlib import Path

import logging

def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(levelname)s: %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger("disciplines")

logger = setup_logging()