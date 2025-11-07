"""
Main entry point for the Conformity application.

This module initializes and starts the application.
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication

from .core.config import get_config
from .core.logger import setup_logging, get_logger
from .main_window import ConformityMainWindow


def main():
    """
    Main entry point for the application.
    """
    # Load configuration
    config = get_config()

    # Setup logging
    log_dir = config.project_root / "logs" if config.project_root else Path("logs")
    setup_logging(
        log_level=config.log_level,
        log_dir=log_dir,
        console_output=True,
        file_output=True
    )

    logger = get_logger(__name__)
    logger.info(f"Starting {config.app_name} v{config.version}")

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName(config.app_name)
    app.setApplicationVersion(config.version)

    # Create and show main window
    main_window = ConformityMainWindow()
    main_window.show()

    logger.info("Application started successfully")

    # Run application event loop
    exit_code = app.exec()

    logger.info(f"Application exited with code: {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
