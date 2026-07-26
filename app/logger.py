import os
import logging
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")

_logger: logging.Logger | None = None


def get_logger() -> logging.Logger:
    global _logger
    if _logger is None:
        _setup_logging()
    return _logger


def _setup_logging(level: int = logging.DEBUG) -> logging.Logger:
    global _logger
    os.makedirs(LOG_DIR, exist_ok=True)

    _logger = logging.getLogger("farmtree")
    _logger.setLevel(level)

    if _logger.handlers:
        return _logger

    fh = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(level)
    fh.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    _logger.addHandler(fh)
    return _logger


def read_logs(num_lines: int = 200) -> list[str]:
    try:
        if not os.path.exists(LOG_FILE):
            return ["[No logs yet]"]
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return lines[-num_lines:]
    except Exception:
        return ["[Error reading log file]"]
