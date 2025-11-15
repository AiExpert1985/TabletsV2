"""
Structured logging configuration for the application.

Provides both console and file logging with rotation.
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from core.config import get_settings

settings = get_settings()


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"

        # Format the message
        formatted = super().format(record)

        # Reset levelname to original (for other handlers)
        record.levelname = levelname

        return formatted


def setup_logging():
    """
    Configure application-wide logging.

    Sets up:
    - Console handler with colored output
    - File handler with rotation (10MB max, 5 backups)
    - Structured log format with timestamp, level, module, message
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Define log format
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Console Handler (with colors)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    console_formatter = ColoredFormatter(log_format, datefmt=date_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File Handler (with rotation)
    log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    # Use INFO level in production to avoid excessive logging
    file_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    file_formatter = logging.Formatter(log_format, datefmt=date_format)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Error File Handler (errors only)
    error_log_file = log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
    error_file_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("watchfiles.main").setLevel(logging.WARNING)  # Prevent log file feedback loop

    # Log startup message
    root_logger.info("=" * 70)
    root_logger.info(f"Logging system initialized - {settings.APP_NAME}")
    root_logger.info(f"Log Level: {'DEBUG' if settings.DEBUG else 'INFO'}")
    root_logger.info(f"Log Directory: {log_dir.absolute()}")
    root_logger.info("=" * 70)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
