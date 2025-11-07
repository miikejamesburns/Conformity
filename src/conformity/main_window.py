"""
Main application window for Conformity.

This module provides the main Qt window and application structure.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QStatusBar, QFileDialog,
    QMessageBox, QTabWidget, QLabel, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from pathlib import Path
from typing import Optional

from .core.config import get_config
from .core.logger import get_logger, setup_logging
from .conform_engine.timeline_manager import TimelineManager
from .color_manager.ocio_manager import OCIOManager
from .color_manager.color_pipeline import ColorPipeline
from .asset_tracker.asset_manager import AssetManager
from .ui_components.timeline_widget import TimelineWidget
from .ui_components.asset_browser import AssetBrowserWidget
from .ui_components.conform_panel import ConformPanel

logger = get_logger(__name__)


class ConformityMainWindow(QMainWindow):
    """Main application window for Conformity."""

    def __init__(self):
        """Initialize the main window."""
        super().__init__()

        # Initialize core components
        self._config = get_config()
        self._timeline_manager = TimelineManager()
        self._ocio_manager = OCIOManager()
        self._color_pipeline = ColorPipeline(self._ocio_manager)
        self._asset_manager = AssetManager()

        # Setup UI
        self._setup_window()
        self._setup_menu_bar()
        self._setup_central_widget()
        self._setup_status_bar()

        logger.info("Conformity main window initialized")

    def _setup_window(self):
        """Configure the main window properties."""
        self.setWindowTitle(f"{self._config.app_name} v{self._config.version}")
        self.setGeometry(100, 100, self._config.window_width, self._config.window_height)

        # Apply theme
        if self._config.theme == "dark":
            self._apply_dark_theme()

    def _apply_dark_theme(self):
        """Apply dark theme to the application."""
        dark_stylesheet = """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QGroupBox {
            border: 1px solid #555555;
            border-radius: 5px;
            margin-top: 10px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        QPushButton {
            background-color: #3d3d3d;
            border: 1px solid #555555;
            padding: 5px 15px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #4d4d4d;
        }
        QPushButton:pressed {
            background-color: #2d2d2d;
        }
        QListWidget {
            background-color: #1e1e1e;
            border: 1px solid #555555;
        }
        QTabWidget::pane {
            border: 1px solid #555555;
        }
        QTabBar::tab {
            background-color: #3d3d3d;
            padding: 5px 15px;
            border: 1px solid #555555;
        }
        QTabBar::tab:selected {
            background-color: #2b2b2b;
        }
        QMenuBar {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QMenuBar::item:selected {
            background-color: #3d3d3d;
        }
        QMenu {
            background-color: #2b2b2b;
            color: #ffffff;
            border: 1px solid #555555;
        }
        QMenu::item:selected {
            background-color: #3d3d3d;
        }
        QStatusBar {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        """
        self.setStyleSheet(dark_stylesheet)

    def _setup_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        open_timeline_action = QAction("Open Timeline...", self)
        open_timeline_action.setShortcut("Ctrl+O")
        open_timeline_action.triggered.connect(self._on_open_timeline)
        file_menu.addAction(open_timeline_action)

        save_timeline_action = QAction("Save Timeline...", self)
        save_timeline_action.setShortcut("Ctrl+S")
        save_timeline_action.triggered.connect(self._on_save_timeline)
        file_menu.addAction(save_timeline_action)

        file_menu.addSeparator()

        new_timeline_action = QAction("New Timeline", self)
        new_timeline_action.setShortcut("Ctrl+N")
        new_timeline_action.triggered.connect(self._on_new_timeline)
        file_menu.addAction(new_timeline_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Color menu
        color_menu = menubar.addMenu("Color")

        load_ocio_action = QAction("Load OCIO Config...", self)
        load_ocio_action.triggered.connect(self._on_load_ocio_config)
        color_menu.addAction(load_ocio_action)

        show_color_spaces_action = QAction("Show Color Spaces", self)
        show_color_spaces_action.triggered.connect(self._on_show_color_spaces)
        color_menu.addAction(show_color_spaces_action)

        # Assets menu
        assets_menu = menubar.addMenu("Assets")

        scan_assets_action = QAction("Scan Directory...", self)
        scan_assets_action.triggered.connect(self._on_scan_assets)
        assets_menu.addAction(scan_assets_action)

        verify_assets_action = QAction("Verify Assets", self)
        verify_assets_action.triggered.connect(self._on_verify_assets)
        assets_menu.addAction(verify_assets_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _setup_central_widget(self):
        """Create the central widget layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Create tab widget
        self._tab_widget = QTabWidget()

        # Conform tab (import/export)
        self._conform_panel = ConformPanel()
        self._conform_panel.timeline_imported.connect(self._on_timeline_imported)
        self._tab_widget.addTab(self._conform_panel, "Conform")

        # Timeline tab
        self._timeline_widget = TimelineWidget()
        self._tab_widget.addTab(self._timeline_widget, "Timeline")

        # Assets tab
        self._asset_browser = AssetBrowserWidget(self._asset_manager)
        self._tab_widget.addTab(self._asset_browser, "Assets")

        # Color Management tab
        color_widget = QWidget()
        color_layout = QVBoxLayout(color_widget)
        self._color_info_label = QLabel("No OCIO config loaded")
        self._color_info_label.setWordWrap(True)
        color_layout.addWidget(self._color_info_label)
        color_layout.addStretch()
        self._tab_widget.addTab(color_widget, "Color Management")

        layout.addWidget(self._tab_widget)

    def _setup_status_bar(self):
        """Create the status bar."""
        self.statusBar().showMessage("Ready")

    # Menu action handlers
    def _on_open_timeline(self):
        """Handle open timeline action."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Timeline",
            str(Path.home()),
            "OTIO Files (*.otio);;All Files (*)"
        )

        if file_path:
            try:
                timeline = self._timeline_manager.load_timeline(Path(file_path))
                self._timeline_widget.set_timeline(timeline)
                self.statusBar().showMessage(f"Loaded timeline: {timeline.name}")
                logger.info(f"Timeline loaded from: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load timeline: {e}")
                logger.error(f"Failed to load timeline: {e}")

    def _on_save_timeline(self):
        """Handle save timeline action."""
        timeline = self._timeline_manager.get_current_timeline()
        if not timeline:
            QMessageBox.warning(self, "Warning", "No timeline to save")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Timeline",
            str(Path.home() / f"{timeline.name}.otio"),
            "OTIO Files (*.otio)"
        )

        if file_path:
            try:
                self._timeline_manager.save_timeline(timeline, Path(file_path))
                self.statusBar().showMessage(f"Saved timeline: {file_path}")
                logger.info(f"Timeline saved to: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save timeline: {e}")
                logger.error(f"Failed to save timeline: {e}")

    def _on_new_timeline(self):
        """Handle new timeline action."""
        timeline = self._timeline_manager.create_timeline(
            "New Timeline",
            self._config.default_fps
        )
        self._timeline_widget.set_timeline(timeline)
        self.statusBar().showMessage("Created new timeline")

    def _on_load_ocio_config(self):
        """Handle load OCIO config action."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open OCIO Config",
            str(Path.home()),
            "OCIO Config (*.ocio config.yaml);;All Files (*)"
        )

        if file_path:
            try:
                self._ocio_manager.load_config(Path(file_path))
                self._update_color_info()
                self.statusBar().showMessage(f"Loaded OCIO config: {file_path}")
                logger.info(f"OCIO config loaded from: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load OCIO config: {e}")
                logger.error(f"Failed to load OCIO config: {e}")

    def _on_show_color_spaces(self):
        """Handle show color spaces action."""
        color_spaces = self._ocio_manager.get_color_spaces()
        if color_spaces:
            message = "Available Color Spaces:\n\n" + "\n".join(f"• {cs}" for cs in color_spaces)
            QMessageBox.information(self, "Color Spaces", message)
        else:
            QMessageBox.warning(self, "Warning", "No OCIO config loaded")

    def _on_scan_assets(self):
        """Handle scan assets action."""
        # Switch to assets tab and let the widget handle it
        self._tab_widget.setCurrentWidget(self._asset_browser)
        self._asset_browser._on_scan_clicked()

    def _on_verify_assets(self):
        """Handle verify assets action."""
        # Switch to assets tab and let the widget handle it
        self._tab_widget.setCurrentWidget(self._asset_browser)
        self._asset_browser._on_verify_clicked()

    def _on_about(self):
        """Handle about action."""
        about_text = f"""
        <h2>{self._config.app_name}</h2>
        <p>Version {self._config.version}</p>
        <p>A post-production pipeline management system</p>
        <p>Built with:</p>
        <ul>
            <li>OpenTimelineIO (OTIO)</li>
            <li>OpenColorIO (OCIO)</li>
            <li>PyQt6</li>
        </ul>
        """
        QMessageBox.about(self, "About Conformity", about_text)

    def _on_timeline_imported(self, timeline, timeline_info):
        """
        Handle timeline imported from conform panel.

        Args:
            timeline: Imported OTIO timeline
            timeline_info: Parsed timeline information
        """
        # Update timeline manager
        self._timeline_manager.set_current_timeline(timeline)

        # Update timeline widget
        self._timeline_widget.set_timeline(timeline)

        # Update status
        self.statusBar().showMessage(
            f"Imported timeline: {timeline.name} "
            f"({timeline_info.num_clips} clips, {timeline_info.num_tracks} tracks)"
        )

        logger.info(f"Timeline imported via conform panel: {timeline.name}")

    def _update_color_info(self):
        """Update color management information display."""
        config = self._ocio_manager.get_config()
        if config:
            info = [
                f"<b>OCIO Configuration</b>",
                f"<b>Description:</b> {config.getDescription()}",
                f"<b>Color Spaces:</b> {len(self._ocio_manager.get_color_spaces())}",
                f"<b>Displays:</b> {len(self._ocio_manager.get_displays())}",
            ]
            self._color_info_label.setText("<br>".join(info))
        else:
            self._color_info_label.setText("No OCIO config loaded")
