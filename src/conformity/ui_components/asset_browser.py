"""
Asset browser widget for viewing and managing assets.

This module provides Qt widgets for browsing and managing media assets.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton,
    QGroupBox, QFileDialog, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path
from typing import Optional, List
from ..asset_tracker.asset_manager import AssetManager, AssetStatus, AssetType
from ..core.logger import get_logger
from .media_preview_widget import MediaPreviewWidget

logger = get_logger(__name__)


class AssetBrowserWidget(QWidget):
    """Widget for browsing and managing assets."""

    asset_selected = pyqtSignal(object)  # Emits Asset object

    def __init__(
        self,
        asset_manager: Optional[AssetManager] = None,
        parent: Optional[QWidget] = None
    ):
        """
        Initialize the asset browser widget.

        Args:
            asset_manager: Optional AssetManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self._asset_manager = asset_manager or AssetManager()
        self._setup_ui()
        logger.debug("AssetBrowserWidget initialized")

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - asset browser controls and list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Statistics group
        stats_group = QGroupBox("Asset Statistics")
        stats_layout = QVBoxLayout()

        self._total_label = QLabel("Total Assets: 0")
        stats_layout.addWidget(self._total_label)

        self._online_label = QLabel("Online: 0")
        self._online_label.setStyleSheet("color: green;")
        stats_layout.addWidget(self._online_label)

        self._offline_label = QLabel("Offline: 0")
        self._offline_label.setStyleSheet("color: red;")
        stats_layout.addWidget(self._offline_label)

        self._size_label = QLabel("Total Size: 0 GB")
        stats_layout.addWidget(self._size_label)

        stats_group.setLayout(stats_layout)
        left_layout.addWidget(stats_group)

        # Control buttons
        button_layout = QHBoxLayout()

        self._scan_button = QPushButton("Scan Directory")
        self._scan_button.clicked.connect(self._on_scan_clicked)
        button_layout.addWidget(self._scan_button)

        self._verify_button = QPushButton("Verify Assets")
        self._verify_button.clicked.connect(self._on_verify_clicked)
        button_layout.addWidget(self._verify_button)

        self._refresh_button = QPushButton("Refresh")
        self._refresh_button.clicked.connect(self._refresh_display)
        button_layout.addWidget(self._refresh_button)

        left_layout.addLayout(button_layout)

        # Assets list
        assets_group = QGroupBox("Assets")
        assets_layout = QVBoxLayout()

        self._assets_list = QListWidget()
        self._assets_list.itemClicked.connect(self._on_asset_selected)
        assets_layout.addWidget(self._assets_list)

        assets_group.setLayout(assets_layout)
        left_layout.addWidget(assets_group)

        # Asset details (kept smaller now that we have preview)
        details_group = QGroupBox("Quick Info")
        details_layout = QVBoxLayout()

        self._details_label = QLabel("Select an asset to view details")
        self._details_label.setWordWrap(True)
        self._details_label.setMaximumHeight(80)
        details_layout.addWidget(self._details_label)

        details_group.setLayout(details_layout)
        left_layout.addWidget(details_group)

        # Right panel - media preview
        self._preview_widget = MediaPreviewWidget()

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(self._preview_widget)

        # Set initial sizes (40% left, 60% right for preview)
        splitter.setSizes([400, 600])

        # Set minimum sizes
        left_panel.setMinimumWidth(350)
        self._preview_widget.setMinimumWidth(400)

        # Add splitter to main layout
        main_layout.addWidget(splitter)

        # Initial display
        self._refresh_display()

    def set_asset_manager(self, asset_manager: AssetManager):
        """
        Set the asset manager.

        Args:
            asset_manager: AssetManager instance
        """
        self._asset_manager = asset_manager
        self._refresh_display()
        logger.info("Asset manager updated")

    def _refresh_display(self):
        """Refresh the display with current asset information."""
        # Update statistics
        stats = self._asset_manager.get_statistics()
        self._total_label.setText(f"Total Assets: {stats['total_assets']}")
        self._online_label.setText(f"Online: {stats['by_status'].get('online', 0)}")
        self._offline_label.setText(f"Offline: {stats['by_status'].get('offline', 0)}")
        self._size_label.setText(f"Total Size: {stats['total_size_gb']} GB")

        # Update assets list
        self._assets_list.clear()
        assets = self._asset_manager.get_all_assets()

        for asset in sorted(assets, key=lambda a: a.name):
            # Create status indicator
            status_icon = "●"
            if asset.status == AssetStatus.ONLINE:
                color = "green"
            elif asset.status == AssetStatus.OFFLINE:
                color = "red"
            elif asset.status == AssetStatus.PENDING:
                color = "orange"
            else:
                color = "gray"

            item_text = f"{status_icon} {asset.name} ({asset.asset_type.value})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, asset)

            # Color code by status
            if asset.status == AssetStatus.OFFLINE:
                item.setForeground(Qt.GlobalColor.red)

            self._assets_list.addItem(item)

        logger.debug(f"Display refreshed: {len(assets)} assets")

    def _on_asset_selected(self, item: QListWidgetItem):
        """
        Handle asset selection.

        Args:
            item: Selected list item
        """
        asset = item.data(Qt.ItemDataRole.UserRole)
        if asset:
            details = self._format_asset_details(asset)
            self._details_label.setText(details)

            # Update preview widget
            self._preview_widget.set_asset(asset)

            self.asset_selected.emit(asset)
            logger.debug(f"Asset selected: {asset.name}")

    def _format_asset_details(self, asset) -> str:
        """
        Format asset details for display.

        Args:
            asset: Asset object

        Returns:
            Formatted details string
        """
        details = [
            f"<b>Name:</b> {asset.name}",
            f"<b>Type:</b> {asset.asset_type.value}",
            f"<b>Status:</b> {asset.status.value}",
            f"<b>Path:</b> {asset.path}",
        ]

        if asset.file_size:
            size_mb = asset.file_size / (1024 * 1024)
            details.append(f"<b>Size:</b> {size_mb:.2f} MB")

        if asset.resolution:
            details.append(f"<b>Resolution:</b> {asset.resolution[0]}x{asset.resolution[1]}")

        if asset.fps:
            details.append(f"<b>FPS:</b> {asset.fps}")

        if asset.color_space:
            details.append(f"<b>Color Space:</b> {asset.color_space}")

        if asset.last_modified:
            details.append(f"<b>Modified:</b> {asset.last_modified.strftime('%Y-%m-%d %H:%M:%S')}")

        return "<br>".join(details)

    def _on_scan_clicked(self):
        """Handle scan directory button click."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Scan",
            str(Path.home())
        )

        if directory:
            try:
                path = Path(directory)
                count = self._asset_manager.scan_directory(path, recursive=True)
                self._refresh_display()
                QMessageBox.information(
                    self,
                    "Scan Complete",
                    f"Registered {count} new assets from {directory}"
                )
            except Exception as e:
                logger.error(f"Scan failed: {e}")
                QMessageBox.critical(self, "Scan Error", f"Failed to scan directory: {e}")

    def _on_verify_clicked(self):
        """Handle verify assets button click."""
        try:
            results = self._asset_manager.verify_assets()
            self._refresh_display()

            message = "Asset Verification Complete:\n\n"
            for status, count in results.items():
                message += f"{status.capitalize()}: {count}\n"

            QMessageBox.information(self, "Verification Complete", message)
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            QMessageBox.critical(self, "Verification Error", f"Failed to verify assets: {e}")

    def get_asset_manager(self) -> AssetManager:
        """
        Get the asset manager.

        Returns:
            AssetManager instance
        """
        return self._asset_manager
