"""
Logging configuration and utilities for Conformity.

This module provides a centralized logging setup with support
for file and console output.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class ConformityLogger:
    """Centralized logger for the Conformity application."""

    _instance: Optional['ConformityLogger'] = None
    _initialized: bool = False

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the logger (only once)."""
        if not ConformityLogger._initialized:
            self._loggers = {}
            ConformityLogger._initialized = True

    def setup_logging(
        self,
        log_level: str = "INFO",
        log_dir: Optional[Path] = None,
        console_output: bool = True,
        file_output: bool = True
    ) -> None:
        """
        Configure the logging system.

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory for log files
            console_output: Enable console output
            file_output: Enable file output
        """
        # Convert log level string to logging constant
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)

        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        simple_formatter = logging.Formatter(
            '%(levelname)s - %(name)s - %(message)s'
        )

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)

        # Clear existing handlers
        root_logger.handlers.clear()

        # Add console handler if requested
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(numeric_level)
            console_handler.setFormatter(simple_formatter)
            root_logger.addHandler(console_handler)

        # Add file handler if requested
        if file_output and log_dir:
            log_dir = Path(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)

            # Create timestamped log file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"conformity_{timestamp}.log"

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(file_handler)

            root_logger.info(f"Logging to file: {log_file}")

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance for a specific module.

        Args:
            name: Name of the logger (typically __name__)

        Returns:
            Logger instance
        """
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        return self._loggers[name]


# Global logger instance
_logger_instance: Optional[ConformityLogger] = None


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get a logger instance for the calling module.

    Args:
        name: Name of the logger (defaults to caller's __name__)

    Returns:
        Logger instance
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ConformityLogger()
    return _logger_instance.get_logger(name)


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    console_output: bool = True,
    file_output: bool = True
) -> None:
    """
    Setup the logging system.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        console_output: Enable console output
        file_output: Enable file output
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ConformityLogger()
    _logger_instance.setup_logging(log_level, log_dir, console_output, file_output)
