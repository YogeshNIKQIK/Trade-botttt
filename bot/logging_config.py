"""
Logging configuration for the trading bot.
Logs API requests, responses, and errors to a file and optionally to console.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(log_dir: str = "logs", log_level: int = logging.INFO) -> logging.Logger:
    """
    Configure structured logging for the trading bot.

    Args:
        log_dir: Directory for log files
        log_level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Create main logger
    logger = logging.getLogger("trading_bot")
    logger.setLevel(log_level)

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # File handler - detailed logs
    log_filename = f"trading_bot_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_path / log_filename, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_format)

    # Console handler - important messages only
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "trading_bot") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
