"""
Review panel for displaying clip metadata and technical specs.

Shows detailed information about media files during conform review.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QTextEdit, QComboBox, QPushButton, QFormLayout
)
from PyQt6.QtCore import pyqtSignal

from ..core.logger import get_logger

logger = get_logger(__name__)


class ReviewPanel(QWidget):
    """
    Review panel showing clip metadata and technical specifications.

    Features:
    - Clip metadata display
    - Color space information
    - Technical specs (resolution, frame rate, codec)
    - Status tracking
    - Review notes
    """

    # Signals
    status_changed = pyqtSignal(str)  # New status
    notes_changed = pyqtSignal(str)  # New notes

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_file: Optional[Path] = None
        self.metadata: Dict[str, Any] = {}

        self._init_ui()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout(self)

        # File info section
        file_group = QGroupBox("File Information")
        file_layout = QFormLayout(file_group)

        self.file_path_label = QLabel("No file loaded")
        self.file_path_label.setWordWrap(True)
        file_layout.addRow("File Path:", self.file_path_label)

        self.file_name_label = QLabel("-")
        file_layout.addRow("File Name:", self.file_name_label)

        self.file_size_label = QLabel("-")
        file_layout.addRow("File Size:", self.file_size_label)

        layout.addWidget(file_group)

        # Technical specs section
        tech_group = QGroupBox("Technical Specifications")
        tech_layout = QFormLayout(tech_group)

        self.resolution_label = QLabel("-")
        tech_layout.addRow("Resolution:", self.resolution_label)

        self.frame_rate_label = QLabel("-")
        tech_layout.addRow("Frame Rate:", self.frame_rate_label)

        self.duration_label = QLabel("-")
        tech_layout.addRow("Duration:", self.duration_label)

        self.codec_label = QLabel("-")
        tech_layout.addRow("Codec:", self.codec_label)

        self.pixel_format_label = QLabel("-")
        tech_layout.addRow("Pixel Format:", self.pixel_format_label)

        self.bit_depth_label = QLabel("-")
        tech_layout.addRow("Bit Depth:", self.bit_depth_label)

        layout.addWidget(tech_group)

        # Color information section
        color_group = QGroupBox("Color Information")
        color_layout = QFormLayout(color_group)

        self.color_space_label = QLabel("-")
        color_layout.addRow("Color Space:", self.color_space_label)

        self.color_primaries_label = QLabel("-")
        color_layout.addRow("Color Primaries:", self.color_primaries_label)

        self.transfer_function_label = QLabel("-")
        color_layout.addRow("Transfer Function:", self.transfer_function_label)

        self.color_range_label = QLabel("-")
        color_layout.addRow("Color Range:", self.color_range_label)

        layout.addWidget(color_group)

        # Audio information (if available)
        audio_group = QGroupBox("Audio Information")
        audio_layout = QFormLayout(audio_group)

        self.audio_codec_label = QLabel("-")
        audio_layout.addRow("Audio Codec:", self.audio_codec_label)

        self.audio_channels_label = QLabel("-")
        audio_layout.addRow("Channels:", self.audio_channels_label)

        self.audio_sample_rate_label = QLabel("-")
        audio_layout.addRow("Sample Rate:", self.audio_sample_rate_label)

        layout.addWidget(audio_group)

        # Status section
        status_group = QGroupBox("Review Status")
        status_layout = QVBoxLayout(status_group)

        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("Status:"))

        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "Not Reviewed",
            "Pending",
            "In Review",
            "Approved",
            "Needs Revision",
            "Rejected"
        ])
        self.status_combo.currentTextChanged.connect(self._on_status_changed)
        status_row.addWidget(self.status_combo)

        status_layout.addLayout(status_row)

        # Notes
        status_layout.addWidget(QLabel("Notes:"))

        self.notes_text = QTextEdit()
        self.notes_text.setMaximumHeight(100)
        self.notes_text.setPlaceholderText("Enter review notes...")
        self.notes_text.textChanged.connect(self._on_notes_changed)
        status_layout.addWidget(self.notes_text)

        layout.addWidget(status_group)

        # Action buttons
        button_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("Refresh Metadata")
        self.refresh_btn.clicked.connect(self._refresh_metadata)
        button_layout.addWidget(self.refresh_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear)
        button_layout.addWidget(self.clear_btn)

        layout.addLayout(button_layout)

        layout.addStretch()

    def load_file(self, file_path: Path, metadata: Optional[Dict[str, Any]] = None):
        """
        Load file and display metadata.

        Args:
            file_path: Path to media file
            metadata: Optional metadata dictionary (will extract if not provided)
        """
        self.current_file = file_path

        if metadata:
            self.metadata = metadata
        else:
            # Extract metadata using metadata extractor
            from ..asset_tracker.metadata_extractor import MetadataExtractor
            extractor = MetadataExtractor()
            self.metadata = extractor.extract(file_path)

        self._update_display()

        logger.info(f"Loaded file metadata: {file_path}")

    def _update_display(self):
        """Update all display fields with current metadata."""
        if not self.current_file:
            return

        # File information
        self.file_path_label.setText(str(self.current_file))
        self.file_name_label.setText(self.current_file.name)

        file_size = self.metadata.get('file_size', 0)
        if file_size:
            size_mb = file_size / (1024 ** 2)
            self.file_size_label.setText(f"{size_mb:.2f} MB")
        else:
            self.file_size_label.setText("-")

        # Technical specs
        width = self.metadata.get('width')
        height = self.metadata.get('height')
        if width and height:
            self.resolution_label.setText(f"{width} x {height}")
        else:
            self.resolution_label.setText("-")

        frame_rate = self.metadata.get('frame_rate')
        if frame_rate:
            self.frame_rate_label.setText(f"{frame_rate:.3f} fps")
        else:
            self.frame_rate_label.setText("-")

        duration = self.metadata.get('duration')
        if duration:
            self.duration_label.setText(f"{duration:.2f} seconds")
        else:
            self.duration_label.setText("-")

        codec = self.metadata.get('codec') or self.metadata.get('codec_long_name')
        self.codec_label.setText(codec or "-")

        pixel_format = self.metadata.get('pixel_format')
        self.pixel_format_label.setText(pixel_format or "-")

        bit_depth = self.metadata.get('bit_depth')
        if bit_depth:
            self.bit_depth_label.setText(f"{bit_depth} bit")
        else:
            self.bit_depth_label.setText("-")

        # Color information
        color_space = self.metadata.get('color_space')
        self.color_space_label.setText(color_space or "-")

        color_primaries = self.metadata.get('color_primaries')
        self.color_primaries_label.setText(color_primaries or "-")

        transfer_function = self.metadata.get('color_transfer')
        self.transfer_function_label.setText(transfer_function or "-")

        color_range = self.metadata.get('color_range')
        self.color_range_label.setText(color_range or "-")

        # Audio information
        audio_codec = self.metadata.get('audio_codec')
        self.audio_codec_label.setText(audio_codec or "-")

        audio_channels = self.metadata.get('audio_channels')
        if audio_channels:
            self.audio_channels_label.setText(str(audio_channels))
        else:
            self.audio_channels_label.setText("-")

        audio_sample_rate = self.metadata.get('audio_sample_rate')
        if audio_sample_rate:
            self.audio_sample_rate_label.setText(f"{audio_sample_rate} Hz")
        else:
            self.audio_sample_rate_label.setText("-")

    def _refresh_metadata(self):
        """Refresh metadata from file."""
        if self.current_file:
            self.load_file(self.current_file)

    def _on_status_changed(self, status: str):
        """Handle status change."""
        self.status_changed.emit(status)
        logger.info(f"Review status changed to: {status}")

    def _on_notes_changed(self):
        """Handle notes text change."""
        notes = self.notes_text.toPlainText()
        self.notes_changed.emit(notes)

    def get_review_data(self) -> Dict[str, Any]:
        """
        Get current review data.

        Returns:
            Dictionary with review status and notes
        """
        return {
            'file_path': str(self.current_file) if self.current_file else None,
            'status': self.status_combo.currentText(),
            'notes': self.notes_text.toPlainText(),
            'metadata': self.metadata
        }

    def set_status(self, status: str):
        """
        Set review status.

        Args:
            status: Status string
        """
        index = self.status_combo.findText(status)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)

    def set_notes(self, notes: str):
        """
        Set review notes.

        Args:
            notes: Notes text
        """
        self.notes_text.setPlainText(notes)

    def clear(self):
        """Clear all fields."""
        self.current_file = None
        self.metadata = {}

        self.file_path_label.setText("No file loaded")
        self.file_name_label.setText("-")
        self.file_size_label.setText("-")
        self.resolution_label.setText("-")
        self.frame_rate_label.setText("-")
        self.duration_label.setText("-")
        self.codec_label.setText("-")
        self.pixel_format_label.setText("-")
        self.bit_depth_label.setText("-")
        self.color_space_label.setText("-")
        self.color_primaries_label.setText("-")
        self.transfer_function_label.setText("-")
        self.color_range_label.setText("-")
        self.audio_codec_label.setText("-")
        self.audio_channels_label.setText("-")
        self.audio_sample_rate_label.setText("-")

        self.status_combo.setCurrentIndex(0)
        self.notes_text.clear()
