"""
Asset tracker UI widget.

Provides search, filtering, and batch operations for asset management.
"""

from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QComboBox, QLabel, QProgressBar, QMessageBox,
    QFileDialog, QGroupBox, QCheckBox, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from ..asset_tracker.asset_database import AssetDatabase, AssetType, AssetStatus
from ..asset_tracker.asset_scanner import AssetScanner
from ..core.logger import get_logger

logger = get_logger(__name__)


class ScanThread(QThread):
    """Background thread for scanning directories."""

    progress = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal(dict)  # results

    def __init__(self, scanner: AssetScanner, directory: Path, recursive: bool):
        super().__init__()
        self.scanner = scanner
        self.directory = directory
        self.recursive = recursive

    def run(self):
        """Run scan in background."""
        try:
            results = self.scanner.scan_directory(
                self.directory,
                recursive=self.recursive,
                progress_callback=self.progress.emit
            )
            self.finished.emit(results)
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            self.finished.emit({'error': str(e)})


class VerifyThread(QThread):
    """Background thread for verifying assets."""

    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(dict)

    def __init__(self, scanner: AssetScanner):
        super().__init__()
        self.scanner = scanner

    def run(self):
        """Run verification in background."""
        try:
            results = self.scanner.verify_assets(
                progress_callback=self.progress.emit
            )
            self.finished.emit(results)
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            self.finished.emit({'error': str(e)})


class AssetTrackerWidget(QWidget):
    """
    Asset tracking UI with search, filtering, and batch operations.

    Features:
    - Text search across metadata
    - Filter by type, status, color space
    - Sortable table view
    - Batch status updates
    - Directory scanning
    - Asset verification
    """

    def __init__(self, database: AssetDatabase, parent=None):
        super().__init__(parent)

        self.database = database
        self.scanner = AssetScanner(database)
        self.current_results = []

        self._init_ui()
        self._refresh_assets()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout(self)

        # Search and filter section
        search_group = QGroupBox("Search and Filter")
        search_layout = QVBoxLayout()

        # Search row
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Search:"))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search file paths and notes...")
        self.search_input.textChanged.connect(self._on_search)
        search_row.addWidget(self.search_input)

        search_layout.addLayout(search_row)

        # Filter row
        filter_row = QHBoxLayout()

        filter_row.addWidget(QLabel("Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(['All', 'video', 'image', 'audio', 'other'])
        self.type_filter.currentTextChanged.connect(self._on_search)
        filter_row.addWidget(self.type_filter)

        filter_row.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems([
            'All', 'pending', 'in_progress', 'approved', 'needs_review', 'archived'
        ])
        self.status_filter.currentTextChanged.connect(self._on_search)
        filter_row.addWidget(self.status_filter)

        filter_row.addWidget(QLabel("Color Space:"))
        self.colorspace_filter = QLineEdit()
        self.colorspace_filter.setPlaceholderText("Filter by color space...")
        self.colorspace_filter.textChanged.connect(self._on_search)
        filter_row.addWidget(self.colorspace_filter)

        self.online_only_cb = QCheckBox("Online Only")
        self.online_only_cb.setChecked(True)
        self.online_only_cb.stateChanged.connect(self._on_search)
        filter_row.addWidget(self.online_only_cb)

        search_layout.addLayout(filter_row)
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)

        # Results table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            'ID', 'File Name', 'Type', 'Status', 'Size (MB)',
            'Color Space', 'Resolution', 'Online'
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)

        layout.addWidget(self.table)

        # Statistics row
        stats_layout = QHBoxLayout()

        self.stats_label = QLabel()
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()

        layout.addLayout(stats_layout)

        # Actions section
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()

        # Scan row
        scan_row = QHBoxLayout()

        scan_btn = QPushButton("Scan Directory")
        scan_btn.clicked.connect(self._on_scan_directory)
        scan_row.addWidget(scan_btn)

        verify_btn = QPushButton("Verify Assets")
        verify_btn.clicked.connect(self._on_verify_assets)
        scan_row.addWidget(verify_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_assets)
        scan_row.addWidget(refresh_btn)

        scan_row.addStretch()
        actions_layout.addLayout(scan_row)

        # Batch operations row
        batch_row = QHBoxLayout()
        batch_row.addWidget(QLabel("Batch Operations:"))

        self.batch_status_combo = QComboBox()
        self.batch_status_combo.addItems([
            'pending', 'in_progress', 'approved', 'needs_review', 'archived'
        ])
        batch_row.addWidget(self.batch_status_combo)

        update_status_btn = QPushButton("Update Status")
        update_status_btn.clicked.connect(self._on_batch_update_status)
        batch_row.addWidget(update_status_btn)

        batch_row.addStretch()
        actions_layout.addLayout(batch_row)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def _refresh_assets(self):
        """Refresh asset list from database."""
        self._on_search()

    def _on_search(self):
        """Handle search/filter changes."""
        # Get filter values
        query = self.search_input.text().strip() or None

        asset_type = None
        if self.type_filter.currentText() != 'All':
            asset_type = AssetType(self.type_filter.currentText())

        status = None
        if self.status_filter.currentText() != 'All':
            status = AssetStatus(self.status_filter.currentText())

        color_space = self.colorspace_filter.text().strip() or None
        online_only = self.online_only_cb.isChecked()

        # Search database
        self.current_results = self.database.search_assets(
            query=query,
            asset_type=asset_type,
            status=status,
            color_space=color_space,
            online_only=online_only
        )

        # Update table
        self._update_table()

        # Update statistics
        self._update_statistics()

    def _update_table(self):
        """Update table with current results."""
        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)

        for asset in self.current_results:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(asset['id'])))

            # File name
            self.table.setItem(row, 1, QTableWidgetItem(asset['file_name']))

            # Type
            self.table.setItem(row, 2, QTableWidgetItem(asset['asset_type']))

            # Status
            self.table.setItem(row, 3, QTableWidgetItem(asset['status']))

            # Size
            size_mb = asset['file_size'] / (1024**2) if asset['file_size'] else 0
            self.table.setItem(row, 4, QTableWidgetItem(f"{size_mb:.2f}"))

            # Get metadata
            metadata = self.database.get_asset_metadata(asset['id'])

            # Color space
            color_space = metadata.get('color_space', '') if metadata else ''
            self.table.setItem(row, 5, QTableWidgetItem(color_space))

            # Resolution
            resolution = ''
            if metadata and metadata.get('width') and metadata.get('height'):
                resolution = f"{metadata['width']}x{metadata['height']}"
            self.table.setItem(row, 6, QTableWidgetItem(resolution))

            # Online status
            online = "Yes" if asset['is_online'] else "No"
            self.table.setItem(row, 7, QTableWidgetItem(online))

        self.table.setSortingEnabled(True)

    def _update_statistics(self):
        """Update statistics label."""
        total = len(self.current_results)
        stats = self.database.get_statistics()

        self.stats_label.setText(
            f"Showing {total} assets | "
            f"Total: {stats.get('total_assets', 0)} | "
            f"Online: {stats.get('online', 0)} | "
            f"Offline: {stats.get('offline', 0)} | "
            f"Size: {stats.get('total_size_gb', 0):.2f} GB"
        )

    def _on_scan_directory(self):
        """Handle scan directory button click."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Scan",
            str(Path.home())
        )

        if not directory:
            return

        # Ask about recursive scanning
        reply = QMessageBox.question(
            self,
            "Recursive Scan",
            "Scan subdirectories recursively?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        recursive = reply == QMessageBox.StandardButton.Yes

        # Start scan in background
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.scan_thread = ScanThread(
            self.scanner,
            Path(directory),
            recursive
        )
        self.scan_thread.progress.connect(self._on_scan_progress)
        self.scan_thread.finished.connect(self._on_scan_finished)
        self.scan_thread.start()

    def _on_scan_progress(self, current: int, total: int, message: str):
        """Handle scan progress update."""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)

    def _on_scan_finished(self, results: dict):
        """Handle scan completion."""
        self.progress_bar.setVisible(False)

        if 'error' in results:
            QMessageBox.critical(
                self,
                "Scan Error",
                f"Scan failed: {results['error']}"
            )
        else:
            QMessageBox.information(
                self,
                "Scan Complete",
                f"Scan completed successfully:\n"
                f"Added: {results.get('added', 0)}\n"
                f"Updated: {results.get('updated', 0)}\n"
                f"Skipped: {results.get('skipped', 0)}\n"
                f"Errors: {results.get('errors', 0)}\n"
                f"Time: {results.get('scan_time_seconds', 0):.1f}s"
            )

        # Refresh display
        self._refresh_assets()

    def _on_verify_assets(self):
        """Handle verify assets button click."""
        reply = QMessageBox.question(
            self,
            "Verify Assets",
            "Verify all assets in database?\nThis may take some time.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Start verification in background
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.verify_thread = VerifyThread(self.scanner)
        self.verify_thread.progress.connect(self._on_scan_progress)
        self.verify_thread.finished.connect(self._on_verify_finished)
        self.verify_thread.start()

    def _on_verify_finished(self, results: dict):
        """Handle verification completion."""
        self.progress_bar.setVisible(False)

        if 'error' in results:
            QMessageBox.critical(
                self,
                "Verification Error",
                f"Verification failed: {results['error']}"
            )
        else:
            changed = len(results.get('changed', []))
            QMessageBox.information(
                self,
                "Verification Complete",
                f"Verification completed:\n"
                f"Online: {results.get('online', 0)}\n"
                f"Offline: {results.get('offline', 0)}\n"
                f"Changed: {changed}"
            )

        # Refresh display
        self._refresh_assets()

    def _on_batch_update_status(self):
        """Handle batch status update."""
        selected_rows = self.table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select assets to update."
            )
            return

        # Get selected asset IDs
        asset_ids = []
        for row in selected_rows:
            asset_id = int(self.table.item(row.row(), 0).text())
            asset_ids.append(asset_id)

        new_status = AssetStatus(self.batch_status_combo.currentText())

        # Confirm
        reply = QMessageBox.question(
            self,
            "Update Status",
            f"Update status for {len(asset_ids)} assets to '{new_status.value}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Update status
        count = self.scanner.batch_update_status(asset_ids, new_status)

        QMessageBox.information(
            self,
            "Status Updated",
            f"Updated status for {count} assets."
        )

        # Refresh display
        self._refresh_assets()

    def _on_item_double_clicked(self, item):
        """Handle table item double-click."""
        row = item.row()
        asset_id = int(self.table.item(row, 0).text())

        # Get full asset info
        asset = self.database.get_asset_by_id(asset_id)
        metadata = self.database.get_asset_metadata(asset_id)

        if not asset:
            return

        # Show detailed info dialog
        info = f"Asset Details\n\n"
        info += f"ID: {asset['id']}\n"
        info += f"File: {asset['file_path']}\n"
        info += f"Type: {asset['asset_type']}\n"
        info += f"Status: {asset['status']}\n"
        info += f"Size: {asset['file_size'] / (1024**2):.2f} MB\n"
        info += f"Online: {'Yes' if asset['is_online'] else 'No'}\n"
        info += f"Checksum: {asset['checksum'] or 'N/A'}\n"

        if metadata:
            info += f"\nTechnical Metadata:\n"
            if metadata.get('width') and metadata.get('height'):
                info += f"Resolution: {metadata['width']}x{metadata['height']}\n"
            if metadata.get('frame_rate'):
                info += f"Frame Rate: {metadata['frame_rate']} fps\n"
            if metadata.get('duration'):
                info += f"Duration: {metadata['duration']:.2f} seconds\n"
            if metadata.get('codec'):
                info += f"Codec: {metadata['codec']}\n"
            if metadata.get('color_space'):
                info += f"Color Space: {metadata['color_space']}\n"

        QMessageBox.information(self, "Asset Details", info)

    def get_selected_assets(self) -> List[int]:
        """
        Get list of selected asset IDs.

        Returns:
            List of asset IDs
        """
        selected_rows = self.table.selectionModel().selectedRows()
        asset_ids = []

        for row in selected_rows:
            asset_id = int(self.table.item(row.row(), 0).text())
            asset_ids.append(asset_id)

        return asset_ids
