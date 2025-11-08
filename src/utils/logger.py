"""
Logging Utility
Provides structured logging for the application
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import json

try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "text",
    log_dir: Optional[Path] = None
) -> None:
    """
    Setup application-wide logging

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ("text" or "json")
        log_dir: Directory for log files
    """
    # Get numeric log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create formatters
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        if HAS_COLORLOG:
            # Colored console output
            formatter = colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
        else:
            # Standard text format
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if log directory specified)
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        # Application log file
        app_log_file = log_dir / f"ehpa_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(app_log_file)
        file_handler.setLevel(numeric_level)

        # Use JSON format for file logs if requested
        if log_format == "json":
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))

        root_logger.addHandler(file_handler)

        # Separate error log file
        error_log_file = log_dir / f"ehpa_errors_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.FileHandler(error_log_file)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(pathname)s:%(lineno)d\n'
        ))
        root_logger.addHandler(error_handler)

    # Suppress verbose third-party loggers
    logging.getLogger('anthropic').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    root_logger.info(f"Logging initialized: level={log_level}, format={log_format}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Initialize logging on import (with default settings)
# This can be overridden by calling setup_logging() explicitly
try:
    from ..core.config import config
    setup_logging(
        log_level=config.settings.log_level,
        log_format=config.settings.log_format,
        log_dir=Path(config.settings.logs_dir)
    )
except:
    # Fallback to basic logging if config not available
    setup_logging()
