"""
Conform review widget with side-by-side comparison.

Provides tools for reviewing conform accuracy with source/conform comparison,
frame markers, and annotation capabilities.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSplitter, QTextEdit, QListWidget, QListWidgetItem, QGroupBox,
    QCheckBox, QSpinBox, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from .playback_widget import PlaybackWidget
from ..core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FrameMarker:
    """Frame marker with annotation."""
    frame_number: int
    timecode: str
    note: str
    marker_type: str  # issue, note, approved
    created_date: str


class ConformReviewWidget(QWidget):
    """
    Conform review widget with side-by-side comparison.

    Features:
    - Dual playback widgets for source vs conform
    - Synchronized playback
    - Frame markers for review notes
    - Difference overlay mode
    - Export marked frames
    - Review notes and status
    """

    # Signals
    review_completed = pyqtSignal(dict)  # Review results

    def __init__(self, parent=None):
        super().__init__(parent)

        self.source_file: Optional[Path] = None
        self.conform_file: Optional[Path] = None
        self.markers: List[FrameMarker] = []
        self.sync_enabled: bool = True

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("Conform Review - Side-by-Side Comparison")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(title_label)

        # Main splitter (playback vs review panel)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side - dual playback
        playback_widget = QWidget()
        playback_layout = QVBoxLayout(playback_widget)

        # Playback controls header
        controls_header = QHBoxLayout()

        controls_header.addWidget(QLabel("Playback Controls:"))

        self.sync_checkbox = QCheckBox("Synchronized Playback")
        self.sync_checkbox.setChecked(True)
        self.sync_checkbox.stateChanged.connect(self._on_sync_changed)
        controls_header.addWidget(self.sync_checkbox)

        self.difference_checkbox = QCheckBox("Difference Overlay")
        self.difference_checkbox.setToolTip("Highlight differences between source and conform")
        controls_header.addWidget(self.difference_checkbox)

        controls_header.addStretch()
        playback_layout.addLayout(controls_header)

        # Dual playback view
        playback_splitter = QSplitter(Qt.Orientation.Vertical)

        # Source playback
        source_group = QGroupBox("Source")
        source_layout = QVBoxLayout(source_group)

        self.source_player = PlaybackWidget()
        source_layout.addWidget(self.source_player)

        load_source_btn = QPushButton("Load Source Media")
        load_source_btn.clicked.connect(self._on_load_source)
        source_layout.addWidget(load_source_btn)

        playback_splitter.addWidget(source_group)

        # Conform playback
        conform_group = QGroupBox("Conform")
        conform_layout = QVBoxLayout(conform_group)

        self.conform_player = PlaybackWidget()
        conform_layout.addWidget(self.conform_player)

        load_conform_btn = QPushButton("Load Conform Media")
        load_conform_btn.clicked.connect(self._on_load_conform)
        conform_layout.addWidget(load_conform_btn)

        playback_splitter.addWidget(conform_group)

        playback_layout.addWidget(playback_splitter)
        main_splitter.addWidget(playback_widget)

        # Right side - review panel
        review_panel = self._create_review_panel()
        main_splitter.addWidget(review_panel)

        # Set initial sizes (70% playback, 30% review)
        main_splitter.setSizes([700, 300])

        layout.addWidget(main_splitter)

    def _create_review_panel(self) -> QWidget:
        """Create review panel with markers and notes."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Marker controls
        marker_group = QGroupBox("Frame Markers")
        marker_layout = QVBoxLayout(marker_group)

        # Add marker button
        add_marker_layout = QHBoxLayout()

        self.add_issue_btn = QPushButton("Add Issue")
        self.add_issue_btn.setStyleSheet("background-color: #ff6b6b;")
        self.add_issue_btn.clicked.connect(lambda: self._add_marker("issue"))
        add_marker_layout.addWidget(self.add_issue_btn)

        self.add_note_btn = QPushButton("Add Note")
        self.add_note_btn.setStyleSheet("background-color: #ffd93d;")
        self.add_note_btn.clicked.connect(lambda: self._add_marker("note"))
        add_marker_layout.addWidget(self.add_note_btn)

        self.add_approved_btn = QPushButton("Approve Frame")
        self.add_approved_btn.setStyleSheet("background-color: #6bcf7f;")
        self.add_approved_btn.clicked.connect(lambda: self._add_marker("approved"))
        add_marker_layout.addWidget(self.add_approved_btn)

        marker_layout.addLayout(add_marker_layout)

        # Marker list
        self.marker_list = QListWidget()
        self.marker_list.itemDoubleClicked.connect(self._on_marker_clicked)
        marker_layout.addWidget(self.marker_list)

        # Delete marker button
        delete_marker_btn = QPushButton("Delete Selected Marker")
        delete_marker_btn.clicked.connect(self._delete_selected_marker)
        marker_layout.addWidget(delete_marker_btn)

        layout.addWidget(marker_group)

        # Notes section
        notes_group = QGroupBox("Review Notes")
        notes_layout = QVBoxLayout(notes_group)

        self.notes_text = QTextEdit()
        self.notes_text.setPlaceholderText("Enter review notes here...")
        notes_layout.addWidget(self.notes_text)

        layout.addWidget(notes_group)

        # Export controls
        export_layout = QHBoxLayout()

        export_frames_btn = QPushButton("Export Marked Frames")
        export_frames_btn.clicked.connect(self._export_marked_frames)
        export_layout.addWidget(export_frames_btn)

        export_report_btn = QPushButton("Export Review Report")
        export_report_btn.clicked.connect(self._export_review_report)
        export_layout.addWidget(export_report_btn)

        layout.addLayout(export_layout)

        # Statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout(stats_group)

        self.stats_label = QLabel("Issues: 0 | Notes: 0 | Approved: 0")
        stats_layout.addWidget(self.stats_label)

        layout.addWidget(stats_group)

        return panel

    def _connect_signals(self):
        """Connect widget signals."""
        # Synchronize playback
        self.source_player.frame_changed.connect(self._on_source_frame_changed)
        self.conform_player.frame_changed.connect(self._on_conform_frame_changed)

    def _on_sync_changed(self, state: int):
        """Handle sync checkbox state change."""
        self.sync_enabled = state == Qt.CheckState.Checked.value

    def _on_source_frame_changed(self, frame: int):
        """
        Handle source player frame change.

        Args:
            frame: New frame number
        """
        if self.sync_enabled and self.conform_player:
            # Sync conform player to source
            if self.conform_player.get_current_frame() != frame:
                self.conform_player.seek_to_frame(frame)

    def _on_conform_frame_changed(self, frame: int):
        """
        Handle conform player frame change.

        Args:
            frame: New frame number
        """
        if self.sync_enabled and self.source_player:
            # Sync source player to conform
            if self.source_player.get_current_frame() != frame:
                self.source_player.seek_to_frame(frame)

    def _on_load_source(self):
        """Load source media file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Source Media",
            str(Path.home()),
            "Media Files (*.mp4 *.mov *.avi *.mkv *.jpg *.jpeg *.png);;All Files (*)"
        )

        if file_path:
            self.source_file = Path(file_path)
            self.source_player.load_media(self.source_file)
            logger.info(f"Loaded source: {self.source_file}")

    def _on_load_conform(self):
        """Load conform media file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Conform Media",
            str(Path.home()),
            "Media Files (*.mp4 *.mov *.avi *.mkv *.jpg *.jpeg *.png);;All Files (*)"
        )

        if file_path:
            self.conform_file = Path(file_path)
            self.conform_player.load_media(self.conform_file)
            logger.info(f"Loaded conform: {self.conform_file}")

    def _add_marker(self, marker_type: str):
        """
        Add frame marker at current position.

        Args:
            marker_type: Type of marker (issue, note, approved)
        """
        # Get current frame from source player
        frame = self.source_player.get_current_frame()
        timecode = self.source_player.get_timecode()

        # Create marker
        marker = FrameMarker(
            frame_number=frame,
            timecode=timecode,
            note="",
            marker_type=marker_type,
            created_date=datetime.now().isoformat()
        )

        self.markers.append(marker)

        # Add to list widget
        item = QListWidgetItem(f"[{marker_type.upper()}] Frame {frame} ({timecode})")

        # Color code by type
        if marker_type == "issue":
            item.setBackground(QColor("#ff6b6b"))
        elif marker_type == "note":
            item.setBackground(QColor("#ffd93d"))
        elif marker_type == "approved":
            item.setBackground(QColor("#6bcf7f"))

        self.marker_list.addItem(item)

        self._update_statistics()

        logger.info(f"Added {marker_type} marker at frame {frame}")

    def _on_marker_clicked(self, item: QListWidgetItem):
        """
        Handle marker click - jump to that frame.

        Args:
            item: Clicked list item
        """
        # Get marker index
        index = self.marker_list.row(item)

        if 0 <= index < len(self.markers):
            marker = self.markers[index]

            # Seek both players to marker frame
            self.source_player.seek_to_frame(marker.frame_number)
            if self.sync_enabled:
                self.conform_player.seek_to_frame(marker.frame_number)

            logger.info(f"Jumped to marker at frame {marker.frame_number}")

    def _delete_selected_marker(self):
        """Delete currently selected marker."""
        current_row = self.marker_list.currentRow()

        if current_row >= 0:
            # Remove from list
            del self.markers[current_row]
            self.marker_list.takeItem(current_row)

            self._update_statistics()

    def _update_statistics(self):
        """Update marker statistics display."""
        issues = sum(1 for m in self.markers if m.marker_type == "issue")
        notes = sum(1 for m in self.markers if m.marker_type == "note")
        approved = sum(1 for m in self.markers if m.marker_type == "approved")

        self.stats_label.setText(f"Issues: {issues} | Notes: {notes} | Approved: {approved}")

    def _export_marked_frames(self):
        """Export frames with markers to directory."""
        if not self.markers:
            QMessageBox.information(
                self,
                "No Markers",
                "No frames have been marked for export."
            )
            return

        # Select output directory
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            str(Path.home())
        )

        if not output_dir:
            return

        output_path = Path(output_dir)

        # Export each marked frame
        # Note: For a full implementation, we'd extract actual frame images
        # For now, create a text file listing the markers

        marker_file = output_path / "frame_markers.txt"

        with open(marker_file, 'w') as f:
            f.write("Frame Markers\n")
            f.write("=" * 50 + "\n\n")

            for marker in self.markers:
                f.write(f"Frame: {marker.frame_number}\n")
                f.write(f"Timecode: {marker.timecode}\n")
                f.write(f"Type: {marker.marker_type}\n")
                f.write(f"Note: {marker.note}\n")
                f.write(f"Date: {marker.created_date}\n")
                f.write("-" * 50 + "\n")

        QMessageBox.information(
            self,
            "Export Complete",
            f"Markers exported to:\n{marker_file}"
        )

        logger.info(f"Exported {len(self.markers)} frame markers")

    def _export_review_report(self):
        """Export comprehensive review report."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Review Report",
            str(Path.home() / "review_report.txt"),
            "Text Files (*.txt);;All Files (*)"
        )

        if not file_path:
            return

        # Generate report
        with open(file_path, 'w') as f:
            f.write("CONFORM REVIEW REPORT\n")
            f.write("=" * 70 + "\n\n")

            f.write(f"Source File: {self.source_file or 'Not loaded'}\n")
            f.write(f"Conform File: {self.conform_file or 'Not loaded'}\n")
            f.write(f"Review Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Statistics
            issues = sum(1 for m in self.markers if m.marker_type == "issue")
            notes = sum(1 for m in self.markers if m.marker_type == "note")
            approved = sum(1 for m in self.markers if m.marker_type == "approved")

            f.write("STATISTICS\n")
            f.write("-" * 70 + "\n")
            f.write(f"Total Markers: {len(self.markers)}\n")
            f.write(f"Issues: {issues}\n")
            f.write(f"Notes: {notes}\n")
            f.write(f"Approved Frames: {approved}\n\n")

            # Review notes
            f.write("REVIEW NOTES\n")
            f.write("-" * 70 + "\n")
            f.write(self.notes_text.toPlainText())
            f.write("\n\n")

            # Frame markers
            f.write("FRAME MARKERS\n")
            f.write("-" * 70 + "\n\n")

            for marker in sorted(self.markers, key=lambda m: m.frame_number):
                f.write(f"[{marker.marker_type.upper()}] Frame {marker.frame_number} ({marker.timecode})\n")
                if marker.note:
                    f.write(f"  Note: {marker.note}\n")
                f.write("\n")

        QMessageBox.information(
            self,
            "Report Exported",
            f"Review report saved to:\n{file_path}"
        )

        logger.info(f"Exported review report to {file_path}")

    def load_source_and_conform(self, source_path: Path, conform_path: Path):
        """
        Load both source and conform media.

        Args:
            source_path: Path to source media
            conform_path: Path to conform media
        """
        self.source_file = source_path
        self.conform_file = conform_path

        self.source_player.load_media(source_path)
        self.conform_player.load_media(conform_path)

        logger.info(f"Loaded source/conform pair for review")

    def get_review_results(self) -> Dict[str, Any]:
        """
        Get review results.

        Returns:
            Dictionary with review data
        """
        issues = sum(1 for m in self.markers if m.marker_type == "issue")
        notes = sum(1 for m in self.markers if m.marker_type == "note")
        approved = sum(1 for m in self.markers if m.marker_type == "approved")

        return {
            'source_file': str(self.source_file) if self.source_file else None,
            'conform_file': str(self.conform_file) if self.conform_file else None,
            'total_markers': len(self.markers),
            'issues': issues,
            'notes': notes,
            'approved': approved,
            'markers': [
                {
                    'frame': m.frame_number,
                    'timecode': m.timecode,
                    'type': m.marker_type,
                    'note': m.note,
                    'date': m.created_date
                }
                for m in self.markers
            ],
            'review_notes': self.notes_text.toPlainText()
        }

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        key = event.key()

        if key == Qt.Key.Key_I:
            # Mark issue
            self._add_marker("issue")
        elif key == Qt.Key.Key_N:
            # Mark note
            self._add_marker("note")
        elif key == Qt.Key.Key_A:
            # Approve frame
            self._add_marker("approved")
        elif key == Qt.Key.Key_D:
            # Toggle difference overlay
            self.difference_checkbox.setChecked(not self.difference_checkbox.isChecked())
        elif key == Qt.Key.Key_S:
            # Toggle sync
            self.sync_checkbox.setChecked(not self.sync_checkbox.isChecked())
        else:
            super().keyPressEvent(event)
