"""
Module: utils/logger.py
Chức năng: Logging ra console VÀ file, có timestamp, có level.
"""
import logging
import os
import sys

# Import settings nhưng tránh circular import bằng cách lazy-load
def _get_log_file() -> str:
    try:
        from config.settings import LOG_DIR, LOG_FILE
        os.makedirs(LOG_DIR, exist_ok=True)
        return LOG_FILE
    except Exception:
        fallback = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "farmer.log")
        os.makedirs(os.path.dirname(fallback), exist_ok=True)
        return fallback


def _build_logger() -> logging.Logger:
    logger = logging.getLogger("farmer")
    if logger.handlers:          # Đã setup rồi, không tạo lại
        return logger

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File handler (ghi tất cả DEBUG trở lên)
    try:
        fh = logging.FileHandler(_get_log_file(), encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except Exception as e:
        logger.warning(f"Không thể ghi log ra file: {e}")

    return logger


_logger = _build_logger()


# ── Public API ────────────────────────────────────────
def log(msg: str, level: str = "info"):
    """
    Ghi log.
    level: 'debug' | 'info' | 'warning' | 'error'
    """
    getattr(_logger, level.lower(), _logger.info)(msg)


def debug(msg: str):   _logger.debug(msg)
def info(msg: str):    _logger.info(msg)
def warning(msg: str): _logger.warning(msg)
def error(msg: str):   _logger.error(msg)
