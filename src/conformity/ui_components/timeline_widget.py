"""
Timeline display widget for visualizing OTIO timelines.

This module provides Qt widgets for displaying and interacting with timelines.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Optional
import opentimelineio as otio
from ..core.logger import get_logger

logger = get_logger(__name__)


class TimelineWidget(QWidget):
    """Widget for displaying timeline information."""

    timeline_selected = pyqtSignal(object)  # Emits timeline object

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the timeline widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._timeline: Optional[otio.schema.Timeline] = None
        self._setup_ui()
        logger.debug("TimelineWidget initialized")

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Timeline info group
        info_group = QGroupBox("Timeline Information")
        info_layout = QVBoxLayout()

        self._name_label = QLabel("No timeline loaded")
        self._name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        info_layout.addWidget(self._name_label)

        self._duration_label = QLabel("Duration: --")
        info_layout.addWidget(self._duration_label)

        self._tracks_label = QLabel("Tracks: 0")
        info_layout.addWidget(self._tracks_label)

        self._clips_label = QLabel("Clips: 0")
        info_layout.addWidget(self._clips_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Tracks list group
        tracks_group = QGroupBox("Tracks")
        tracks_layout = QVBoxLayout()

        self._tracks_list = QListWidget()
        self._tracks_list.itemClicked.connect(self._on_track_selected)
        tracks_layout.addWidget(self._tracks_list)

        tracks_group.setLayout(tracks_layout)
        layout.addWidget(tracks_group)

        # Clips list group
        clips_group = QGroupBox("Clips")
        clips_layout = QVBoxLayout()

        self._clips_list = QListWidget()
        clips_layout.addWidget(self._clips_list)

        clips_group.setLayout(clips_layout)
        layout.addWidget(clips_group)

    def set_timeline(self, timeline: otio.schema.Timeline):
        """
        Set the timeline to display.

        Args:
            timeline: OTIO timeline object
        """
        self._timeline = timeline
        self._update_display()
        logger.info(f"Timeline set: {timeline.name}")

    def _update_display(self):
        """Update the display with current timeline information."""
        if not self._timeline:
            self._name_label.setText("No timeline loaded")
            self._duration_label.setText("Duration: --")
            self._tracks_label.setText("Tracks: 0")
            self._clips_label.setText("Clips: 0")
            self._tracks_list.clear()
            self._clips_list.clear()
            return

        # Update info labels
        self._name_label.setText(f"Timeline: {self._timeline.name}")

        duration = self._timeline.duration()
        self._duration_label.setText(f"Duration: {duration.value}/{duration.rate} ({duration.to_seconds():.2f}s)")

        num_tracks = len(self._timeline.tracks)
        self._tracks_label.setText(f"Tracks: {num_tracks}")

        # Count clips
        num_clips = 0
        for track in self._timeline.tracks:
            for item in track:
                if isinstance(item, otio.schema.Clip):
                    num_clips += 1

        self._clips_label.setText(f"Clips: {num_clips}")

        # Update tracks list
        self._tracks_list.clear()
        for i, track in enumerate(self._timeline.tracks):
            track_name = track.name or f"Track {i+1}"
            track_kind = track.kind.name if track.kind else "Unknown"
            item = QListWidgetItem(f"{track_name} ({track_kind})")
            item.setData(Qt.ItemDataRole.UserRole, i)
            self._tracks_list.addItem(item)

    def _on_track_selected(self, item: QListWidgetItem):
        """
        Handle track selection.

        Args:
            item: Selected list item
        """
        if not self._timeline:
            return

        track_index = item.data(Qt.ItemDataRole.UserRole)
        track = self._timeline.tracks[track_index]

        # Update clips list for selected track
        self._clips_list.clear()
        for i, item in enumerate(track):
            if isinstance(item, otio.schema.Clip):
                clip_info = f"{item.name}"
                if item.source_range:
                    duration = item.source_range.duration
                    clip_info += f" ({duration.to_seconds():.2f}s)"
                list_item = QListWidgetItem(clip_info)
                self._clips_list.addItem(list_item)

        logger.debug(f"Track selected: {track.name}")

    def get_timeline(self) -> Optional[otio.schema.Timeline]:
        """
        Get the current timeline.

        Returns:
            Current timeline or None
        """
        return self._timeline

    def clear(self):
        """Clear the timeline display."""
        self._timeline = None
        self._update_display()
        logger.debug("Timeline widget cleared")
