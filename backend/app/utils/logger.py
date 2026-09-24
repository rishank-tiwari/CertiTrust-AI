"""
CertiTrust AI - Loguru Logging Module with Fallback.
Configures structured, production-grade logging using Loguru or standard logging fallback.
"""

import sys
import logging
from pathlib import Path

try:
    from loguru import logger as _loguru_logger

    # Remove default loguru handler
    _loguru_logger.remove()

    # Configure stdout logging handler
    _loguru_logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG",
        colorize=True,
    )

    # Create logs directory
    LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Configure file rotation handler
    _loguru_logger.add(
        LOGS_DIR / "certitrust_ai.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}",
    )

    logger = _loguru_logger

except ImportError:
    # Fallback to standard logging if loguru is not installed yet
    standard_logger = logging.getLogger("certitrust_ai")
    if not standard_logger.handlers:
        standard_logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s")
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        standard_logger.addHandler(handler)
    logger = standard_logger

__all__ = ["logger"]
