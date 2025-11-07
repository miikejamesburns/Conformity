"""
Conform panel UI for automated timeline import/export.

This module provides a Qt widget for importing timelines, viewing their structure,
and exporting to different formats.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTreeWidget, QTreeWidgetItem, QFileDialog,
    QMessageBox, QComboBox, QTextEdit, QSplitter, QProgressDialog,
    QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from pathlib import Path
from typing import Optional
import opentimelineio as otio

from ..conform_engine.conform_engine import ConformEngine, TimelineFormat, TimelineInfo, ClipInfo
from ..conform_engine.exceptions import ConformError
from ..core.logger import get_logger

logger = get_logger(__name__)


class ConformPanel(QWidget):
    """Panel for timeline conform operations."""

    timeline_imported = pyqtSignal(object, object)  # Emits (timeline, timeline_info)

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the conform panel.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._conform_engine = ConformEngine()
        self._current_timeline: Optional[otio.schema.Timeline] = None
        self._current_info: Optional[TimelineInfo] = None
        self._setup_ui()
        logger.debug("ConformPanel initialized")

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Import section
        import_group = QGroupBox("Import Timeline")
        import_layout = QVBoxLayout()

        # File selection
        file_layout = QHBoxLayout()
        self._file_label = QLabel("No file selected")
        self._file_label.setWordWrap(True)
        file_layout.addWidget(self._file_label, 1)

        self._browse_button = QPushButton("Browse...")
        self._browse_button.clicked.connect(self._on_browse_clicked)
        file_layout.addWidget(self._browse_button)

        import_layout.addLayout(file_layout)

        # Import options
        options_layout = QHBoxLayout()

        options_layout.addWidget(QLabel("Format:"))
        self._format_combo = QComboBox()
        self._format_combo.addItem("Auto-detect", None)
        for fmt in TimelineFormat:
            self._format_combo.addItem(fmt.name, fmt.value)
        options_layout.addWidget(self._format_combo)

        self._verify_media_check = QCheckBox("Verify Media")
        self._verify_media_check.setChecked(True)
        options_layout.addWidget(self._verify_media_check)

        options_layout.addStretch()

        self._import_button = QPushButton("Import")
        self._import_button.clicked.connect(self._on_import_clicked)
        self._import_button.setEnabled(False)
        options_layout.addWidget(self._import_button)

        import_layout.addLayout(options_layout)
        import_group.setLayout(import_layout)
        layout.addWidget(import_group)

        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Timeline structure tree
        tree_group = QGroupBox("Timeline Structure")
        tree_layout = QVBoxLayout()

        self._timeline_tree = QTreeWidget()
        self._timeline_tree.setHeaderLabels(["Name", "Type", "Duration", "Info"])
        self._timeline_tree.setColumnWidth(0, 200)
        self._timeline_tree.setColumnWidth(1, 100)
        self._timeline_tree.setColumnWidth(2, 100)
        self._timeline_tree.itemClicked.connect(self._on_tree_item_clicked)
        tree_layout.addWidget(self._timeline_tree)

        tree_group.setLayout(tree_layout)
        splitter.addWidget(tree_group)

        # Details panel
        details_group = QGroupBox("Details")
        details_layout = QVBoxLayout()

        self._details_text = QTextEdit()
        self._details_text.setReadOnly(True)
        self._details_text.setFont(QFont("Monospace", 9))
        details_layout.addWidget(self._details_text)

        details_group.setLayout(details_layout)
        splitter.addWidget(details_group)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

        # Export section
        export_group = QGroupBox("Export Timeline")
        export_layout = QHBoxLayout()

        export_layout.addWidget(QLabel("Export as:"))
        self._export_format_combo = QComboBox()
        for fmt in TimelineFormat:
            self._export_format_combo.addItem(fmt.name, fmt.value)
        export_layout.addWidget(self._export_format_combo)

        export_layout.addStretch()

        self._validate_button = QPushButton("Validate")
        self._validate_button.clicked.connect(self._on_validate_clicked)
        self._validate_button.setEnabled(False)
        export_layout.addWidget(self._validate_button)

        self._export_button = QPushButton("Export...")
        self._export_button.clicked.connect(self._on_export_clicked)
        self._export_button.setEnabled(False)
        export_layout.addWidget(self._export_button)

        export_group.setLayout(export_layout)
        layout.addWidget(export_group)

        # Status label
        self._status_label = QLabel("Ready")
        layout.addWidget(self._status_label)

    def _on_browse_clicked(self):
        """Handle browse button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Timeline File",
            str(Path.home()),
            "All Supported Files (*.otio *.edl *.xml *.fcpxml *.aaf *.ale);;"
            "OTIO Files (*.otio);;"
            "EDL Files (*.edl);;"
            "FCP XML Files (*.xml *.fcpxml);;"
            "AAF Files (*.aaf);;"
            "ALE Files (*.ale);;"
            "All Files (*)"
        )

        if file_path:
            self._file_label.setText(file_path)
            self._import_button.setEnabled(True)
            logger.info(f"File selected: {file_path}")

    def _on_import_clicked(self):
        """Handle import button click."""
        file_path = Path(self._file_label.text())

        if not file_path.exists():
            QMessageBox.warning(self, "Error", "Selected file does not exist")
            return

        # Get import options
        adapter_data = self._format_combo.currentData()
        adapter_name = adapter_data if adapter_data else None
        verify_media = self._verify_media_check.isChecked()

        try:
            self._status_label.setText("Importing timeline...")
            logger.info(f"Importing timeline from {file_path}")

            # Import timeline
            timeline, timeline_info = self._conform_engine.import_timeline(
                file_path,
                adapter_name=adapter_name,
                verify_media=verify_media
            )

            self._current_timeline = timeline
            self._current_info = timeline_info

            # Update UI
            self._populate_timeline_tree(timeline, timeline_info)
            self._show_timeline_summary(timeline_info)

            # Enable export buttons
            self._validate_button.setEnabled(True)
            self._export_button.setEnabled(True)

            self._status_label.setText(
                f"Imported: {timeline_info.num_clips} clips, "
                f"{timeline_info.num_tracks} tracks"
            )

            # Emit signal
            self.timeline_imported.emit(timeline, timeline_info)

            logger.info("Timeline imported successfully")

        except ConformError as e:
            logger.error(f"Conform error: {e}")
            QMessageBox.critical(self, "Import Error", str(e))
            self._status_label.setText(f"Import failed: {e}")

        except Exception as e:
            logger.error(f"Unexpected error during import: {e}")
            QMessageBox.critical(self, "Error", f"Unexpected error: {e}")
            self._status_label.setText(f"Import failed: {e}")

    def _populate_timeline_tree(
        self,
        timeline: otio.schema.Timeline,
        timeline_info: TimelineInfo
    ):
        """
        Populate the tree widget with timeline structure.

        Args:
            timeline: OTIO timeline
            timeline_info: Parsed timeline information
        """
        self._timeline_tree.clear()

        # Root item (timeline)
        root = QTreeWidgetItem(self._timeline_tree)
        root.setText(0, timeline.name or "Timeline")
        root.setText(1, "Timeline")
        root.setText(2, self._format_duration(timeline_info.duration))
        root.setText(3, f"{timeline_info.num_clips} clips")
        root.setData(0, Qt.ItemDataRole.UserRole, {'type': 'timeline', 'data': timeline})

        # Add tracks
        for i, track in enumerate(timeline.tracks):
            track_item = QTreeWidgetItem(root)
            track_name = track.name or f"Track {i+1}"
            track_kind = track.kind.name if track.kind else "Unknown"

            track_item.setText(0, track_name)
            track_item.setText(1, track_kind)
            track_item.setText(2, self._format_duration(track.duration()))

            # Count clips in track
            clip_count = sum(1 for item in track if isinstance(item, otio.schema.Clip))
            track_item.setText(3, f"{clip_count} clips")
            track_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'track', 'data': track})

            # Add clips
            for item in track:
                if isinstance(item, otio.schema.Clip):
                    clip_item = QTreeWidgetItem(track_item)
                    clip_item.setText(0, item.name)
                    clip_item.setText(1, "Clip")
                    clip_item.setText(2, self._format_duration(item.duration()))

                    # Add source info
                    if item.media_reference and isinstance(
                        item.media_reference, otio.schema.ExternalReference
                    ):
                        source_path = Path(item.media_reference.target_url)
                        clip_item.setText(3, source_path.name)

                    clip_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'clip', 'data': item})

                elif isinstance(item, otio.schema.Transition):
                    trans_item = QTreeWidgetItem(track_item)
                    trans_item.setText(0, item.name or "Transition")
                    trans_item.setText(1, "Transition")
                    trans_item.setText(2, self._format_duration(item.duration()))
                    trans_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'transition', 'data': item})

                elif isinstance(item, otio.schema.Gap):
                    gap_item = QTreeWidgetItem(track_item)
                    gap_item.setText(0, "Gap")
                    gap_item.setText(1, "Gap")
                    gap_item.setText(2, self._format_duration(item.duration()))
                    gap_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'gap', 'data': item})

        # Expand the root
        self._timeline_tree.expandItem(root)

    def _format_duration(self, duration: Optional[otio.opentime.RationalTime]) -> str:
        """Format duration for display."""
        if not duration:
            return "--"
        try:
            seconds = duration.to_seconds()
            return f"{seconds:.2f}s"
        except:
            return str(duration)

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        """
        Handle tree item click.

        Args:
            item: Clicked tree item
            column: Column index
        """
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            return

        item_type = item_data.get('type')
        data = item_data.get('data')

        if item_type == 'timeline':
            self._show_timeline_details(data)
        elif item_type == 'track':
            self._show_track_details(data)
        elif item_type == 'clip':
            self._show_clip_details(data)
        elif item_type == 'transition':
            self._show_transition_details(data)
        elif item_type == 'gap':
            self._show_gap_details(data)

    def _show_timeline_summary(self, timeline_info: TimelineInfo):
        """Show timeline summary in details panel."""
        details = [
            f"<h3>Timeline: {timeline_info.name}</h3>",
            f"<b>Duration:</b> {self._format_duration(timeline_info.duration)}",
            f"<b>Tracks:</b> {timeline_info.num_tracks}",
            f"<b>Clips:</b> {timeline_info.num_clips}",
            f"<b>Transitions:</b> {timeline_info.num_transitions}",
            f"<b>Markers:</b> {timeline_info.num_markers}",
        ]

        if timeline_info.global_start_time:
            details.append(f"<b>Global Start Time:</b> {timeline_info.global_start_time}")

        if timeline_info.unsupported_features:
            details.append("<br><b>Unsupported Features:</b>")
            for feature in timeline_info.unsupported_features:
                details.append(f"  • {feature}")

        if timeline_info.missing_media:
            details.append("<br><b>Missing Media:</b>")
            for media in timeline_info.missing_media:
                details.append(f"  • {media}")

        self._details_text.setHtml("<br>".join(details))

    def _show_timeline_details(self, timeline: otio.schema.Timeline):
        """Show detailed timeline information."""
        if self._current_info:
            self._show_timeline_summary(self._current_info)

    def _show_track_details(self, track: otio.schema.Track):
        """Show detailed track information."""
        details = [
            f"<h3>Track: {track.name or 'Unnamed'}</h3>",
            f"<b>Kind:</b> {track.kind.name if track.kind else 'Unknown'}",
            f"<b>Duration:</b> {self._format_duration(track.duration())}",
        ]

        # Count items
        clips = sum(1 for item in track if isinstance(item, otio.schema.Clip))
        transitions = sum(1 for item in track if isinstance(item, otio.schema.Transition))
        gaps = sum(1 for item in track if isinstance(item, otio.schema.Gap))

        details.append(f"<b>Items:</b> {clips} clips, {transitions} transitions, {gaps} gaps")

        if track.metadata:
            details.append("<br><b>Metadata:</b>")
            for key, value in track.metadata.items():
                details.append(f"  • {key}: {value}")

        self._details_text.setHtml("<br>".join(details))

    def _show_clip_details(self, clip: otio.schema.Clip):
        """Show detailed clip information."""
        details = [
            f"<h3>Clip: {clip.name}</h3>",
            f"<b>Duration:</b> {self._format_duration(clip.duration())}",
        ]

        # Source range
        if clip.source_range:
            sr = clip.source_range
            details.append(
                f"<b>Source Range:</b> {sr.start_time.value}/{sr.start_time.rate} "
                f"for {sr.duration.value} frames"
            )

        # Media reference
        if clip.media_reference:
            if isinstance(clip.media_reference, otio.schema.ExternalReference):
                details.append(f"<b>Media Path:</b> {clip.media_reference.target_url}")
                # Check if file exists
                media_path = Path(clip.media_reference.target_url)
                status = "✓ Online" if media_path.exists() else "✗ Offline"
                details.append(f"<b>Status:</b> {status}")
            elif isinstance(clip.media_reference, otio.schema.MissingReference):
                details.append("<b>Media:</b> Missing Reference")

        # Effects
        if hasattr(clip, 'effects'):
            effects = list(clip.effects())
            if effects:
                details.append(f"<br><b>Effects ({len(effects)}):</b>")
                for effect in effects:
                    effect_name = effect.name or type(effect).__name__
                    details.append(f"  • {effect_name}")

        # Markers
        if hasattr(clip, 'markers'):
            markers = list(clip.markers())
            if markers:
                details.append(f"<br><b>Markers ({len(markers)}):</b>")
                for marker in markers:
                    marker_name = marker.name or "Unnamed"
                    details.append(f"  • {marker_name}")

        # Metadata
        if clip.metadata:
            details.append("<br><b>Metadata:</b>")
            for key, value in clip.metadata.items():
                details.append(f"  • {key}: {value}")

        self._details_text.setHtml("<br>".join(details))

    def _show_transition_details(self, transition: otio.schema.Transition):
        """Show detailed transition information."""
        details = [
            f"<h3>Transition: {transition.name or 'Unnamed'}</h3>",
            f"<b>Duration:</b> {self._format_duration(transition.duration())}",
            f"<b>Transition Type:</b> {transition.transition_type or 'Unknown'}",
        ]

        if transition.metadata:
            details.append("<br><b>Metadata:</b>")
            for key, value in transition.metadata.items():
                details.append(f"  • {key}: {value}")

        self._details_text.setHtml("<br>".join(details))

    def _show_gap_details(self, gap: otio.schema.Gap):
        """Show detailed gap information."""
        details = [
            "<h3>Gap</h3>",
            f"<b>Duration:</b> {self._format_duration(gap.duration())}",
        ]

        self._details_text.setHtml("<br>".join(details))

    def _on_validate_clicked(self):
        """Handle validate button click."""
        if not self._current_timeline:
            QMessageBox.warning(self, "Error", "No timeline loaded")
            return

        try:
            self._status_label.setText("Validating timeline...")

            results = self._conform_engine.validate_timeline(
                self._current_timeline,
                check_media=True
            )

            # Show results
            message = f"<h3>Validation Results</h3>"
            message += f"<b>Status:</b> {'✓ Valid' if results['valid'] else '✗ Invalid'}<br><br>"

            if results['errors']:
                message += f"<b>Errors ({len(results['errors'])}):</b><br>"
                for error in results['errors']:
                    message += f"  • {error}<br>"
                message += "<br>"

            if results['warnings']:
                message += f"<b>Warnings ({len(results['warnings'])}):</b><br>"
                for warning in results['warnings']:
                    message += f"  • {warning}<br>"
                message += "<br>"

            if results['missing_media']:
                message += f"<b>Missing Media ({len(results['missing_media'])}):</b><br>"
                for media in results['missing_media']:
                    message += f"  • {media['clip']}: {media['path']}<br>"

            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Validation Results")
            msg_box.setTextFormat(Qt.TextFormat.RichText)
            msg_box.setText(message)
            msg_box.setIcon(
                QMessageBox.Icon.Information if results['valid']
                else QMessageBox.Icon.Warning
            )
            msg_box.exec()

            self._status_label.setText(
                "Validation complete: " + ("Valid" if results['valid'] else "Invalid")
            )

        except Exception as e:
            logger.error(f"Validation error: {e}")
            QMessageBox.critical(self, "Error", f"Validation failed: {e}")
            self._status_label.setText("Validation failed")

    def _on_export_clicked(self):
        """Handle export button click."""
        if not self._current_timeline:
            QMessageBox.warning(self, "Error", "No timeline loaded")
            return

        # Get export format
        format_name = self._export_format_combo.currentText()
        format_value = self._export_format_combo.currentData()
        format_enum = TimelineFormat(format_value)

        # Determine file extension
        ext_map = {
            TimelineFormat.OTIO: ".otio",
            TimelineFormat.EDL: ".edl",
            TimelineFormat.FCPXML: ".fcpxml",
            TimelineFormat.XML: ".xml",
            TimelineFormat.AAF: ".aaf",
            TimelineFormat.ALE: ".ale",
        }
        extension = ext_map.get(format_enum, ".otio")

        # Get file path
        default_name = f"{self._current_timeline.name}{extension}"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Timeline",
            str(Path.home() / default_name),
            f"{format_name} Files (*{extension});;All Files (*)"
        )

        if not file_path:
            return

        try:
            self._status_label.setText(f"Exporting to {format_name}...")

            self._conform_engine.export_timeline(
                self._current_timeline,
                Path(file_path),
                format=format_enum
            )

            QMessageBox.information(
                self,
                "Export Complete",
                f"Timeline exported successfully to:\n{file_path}"
            )

            self._status_label.setText(f"Exported to {format_name}")
            logger.info(f"Timeline exported to {file_path}")

        except ConformError as e:
            logger.error(f"Export error: {e}")
            QMessageBox.critical(self, "Export Error", str(e))
            self._status_label.setText("Export failed")

        except Exception as e:
            logger.error(f"Unexpected error during export: {e}")
            QMessageBox.critical(self, "Error", f"Export failed: {e}")
            self._status_label.setText("Export failed")

    def get_current_timeline(self) -> Optional[otio.schema.Timeline]:
        """Get the currently loaded timeline."""
        return self._current_timeline

    def get_timeline_info(self) -> Optional[TimelineInfo]:
        """Get information about the current timeline."""
        return self._current_info

    def clear(self):
        """Clear the panel."""
        self._current_timeline = None
        self._current_info = None
        self._timeline_tree.clear()
        self._details_text.clear()
        self._file_label.setText("No file selected")
        self._import_button.setEnabled(False)
        self._validate_button.setEnabled(False)
        self._export_button.setEnabled(False)
        self._status_label.setText("Ready")
