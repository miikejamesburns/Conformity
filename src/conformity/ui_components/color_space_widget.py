"""
Color space management widget using OCIO.

This module provides a Qt widget for visualizing and managing color spaces
in the post-production pipeline.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTreeWidget, QTreeWidgetItem, QComboBox,
    QMessageBox, QFileDialog, QTextEdit, QSplitter,
    QListWidget, QListWidgetItem, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from pathlib import Path
from typing import Optional, Dict, List
import opentimelineio as otio

from ..color_manager.color_manager import (
    ColorManager, ColorSpaceStatus, ColorSpaceAssignment,
    PipelineColorConfig
)
from ..core.logger import get_logger

logger = get_logger(__name__)


class ColorSpaceWidget(QWidget):
    """Widget for color space management and visualization."""

    color_space_changed = pyqtSignal(str, str)  # Emits (clip_name, color_space)
    timeline_analyzed = pyqtSignal(object)  # Emits analysis result

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the color space widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._color_manager = ColorManager()
        self._current_timeline: Optional[otio.schema.Timeline] = None
        self._setup_ui()
        logger.debug("ColorSpaceWidget initialized")

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # OCIO Config section
        config_group = QGroupBox("OCIO Configuration")
        config_layout = QVBoxLayout()

        # Config file selection
        file_layout = QHBoxLayout()
        self._config_label = QLabel("No config loaded")
        self._config_label.setWordWrap(True)
        file_layout.addWidget(self._config_label, 1)

        self._load_config_button = QPushButton("Load Config...")
        self._load_config_button.clicked.connect(self._on_load_config)
        file_layout.addWidget(self._load_config_button)

        self._validate_config_button = QPushButton("Validate")
        self._validate_config_button.clicked.connect(self._on_validate_config)
        self._validate_config_button.setEnabled(False)
        file_layout.addWidget(self._validate_config_button)

        config_layout.addLayout(file_layout)

        # Config info
        self._config_info_label = QLabel("Load an OCIO config to begin")
        self._config_info_label.setWordWrap(True)
        config_layout.addWidget(self._config_info_label)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Pipeline defaults section
        defaults_group = QGroupBox("Pipeline Defaults")
        defaults_layout = QVBoxLayout()

        # Working color space
        working_layout = QHBoxLayout()
        working_layout.addWidget(QLabel("Working Color Space:"))
        self._working_cs_combo = QComboBox()
        self._working_cs_combo.currentTextChanged.connect(self._on_working_cs_changed)
        working_layout.addWidget(self._working_cs_combo, 1)
        defaults_layout.addLayout(working_layout)

        # Default input
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Default Input:"))
        self._default_input_combo = QComboBox()
        input_layout.addWidget(self._default_input_combo, 1)
        defaults_layout.addLayout(input_layout)

        # Display/View
        display_layout = QHBoxLayout()
        display_layout.addWidget(QLabel("Display:"))
        self._display_combo = QComboBox()
        self._display_combo.currentTextChanged.connect(self._on_display_changed)
        display_layout.addWidget(self._display_combo, 1)

        display_layout.addWidget(QLabel("View:"))
        self._view_combo = QComboBox()
        display_layout.addWidget(self._view_combo, 1)
        defaults_layout.addLayout(display_layout)

        # Apply defaults button
        apply_layout = QHBoxLayout()
        apply_layout.addStretch()
        self._apply_defaults_button = QPushButton("Apply Defaults to Timeline")
        self._apply_defaults_button.clicked.connect(self._on_apply_defaults)
        self._apply_defaults_button.setEnabled(False)
        apply_layout.addWidget(self._apply_defaults_button)
        defaults_layout.addLayout(apply_layout)

        defaults_group.setLayout(defaults_layout)
        layout.addWidget(defaults_group)

        # Main content with tabs
        self._tab_widget = QTabWidget()

        # Color Spaces tab
        color_spaces_tab = QWidget()
        cs_layout = QVBoxLayout(color_spaces_tab)

        # Color space tree
        cs_tree_label = QLabel("<b>Available Color Spaces</b> (organized by family)")
        cs_layout.addWidget(cs_tree_label)

        self._color_space_tree = QTreeWidget()
        self._color_space_tree.setHeaderLabels(["Family / Color Space", "Description"])
        self._color_space_tree.setColumnWidth(0, 300)
        cs_layout.addWidget(self._color_space_tree)

        self._tab_widget.addTab(color_spaces_tab, "Color Spaces")

        # Timeline Analysis tab
        analysis_tab = QWidget()
        analysis_layout = QVBoxLayout(analysis_tab)

        # Analysis controls
        analysis_controls = QHBoxLayout()
        self._analyze_button = QPushButton("Analyze Timeline")
        self._analyze_button.clicked.connect(self._on_analyze_timeline)
        self._analyze_button.setEnabled(False)
        analysis_controls.addWidget(self._analyze_button)

        self._auto_assign_button = QPushButton("Auto-Assign Color Spaces")
        self._auto_assign_button.clicked.connect(self._on_auto_assign)
        self._auto_assign_button.setEnabled(False)
        analysis_controls.addWidget(self._auto_assign_button)

        analysis_controls.addStretch()

        self._export_report_button = QPushButton("Export Report...")
        self._export_report_button.clicked.connect(self._on_export_report)
        self._export_report_button.setEnabled(False)
        analysis_controls.addWidget(self._export_report_button)

        analysis_layout.addLayout(analysis_controls)

        # Analysis results
        analysis_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Clips list
        clips_group = QGroupBox("Clips")
        clips_layout = QVBoxLayout()

        self._clips_list = QListWidget()
        self._clips_list.itemClicked.connect(self._on_clip_selected)
        clips_layout.addWidget(self._clips_list)

        clips_group.setLayout(clips_layout)
        analysis_splitter.addWidget(clips_group)

        # Clip details
        details_group = QGroupBox("Color Space Details")
        details_layout = QVBoxLayout()

        self._clip_details_text = QTextEdit()
        self._clip_details_text.setReadOnly(True)
        self._clip_details_text.setFont(QFont("Monospace", 9))
        details_layout.addWidget(self._clip_details_text)

        # Override controls
        override_layout = QHBoxLayout()
        override_layout.addWidget(QLabel("Assign Color Space:"))
        self._override_cs_combo = QComboBox()
        override_layout.addWidget(self._override_cs_combo, 1)

        self._assign_button = QPushButton("Assign")
        self._assign_button.clicked.connect(self._on_assign_color_space)
        self._assign_button.setEnabled(False)
        override_layout.addWidget(self._assign_button)

        details_layout.addLayout(override_layout)

        details_group.setLayout(details_layout)
        analysis_splitter.addWidget(details_group)

        analysis_splitter.setStretchFactor(0, 1)
        analysis_splitter.setStretchFactor(1, 1)

        analysis_layout.addWidget(analysis_splitter, 1)

        self._tab_widget.addTab(analysis_tab, "Timeline Analysis")

        layout.addWidget(self._tab_widget, 1)

        # Status label
        self._status_label = QLabel("Load an OCIO config to begin")
        layout.addWidget(self._status_label)

    def _on_load_config(self):
        """Handle load config button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select OCIO Config",
            str(Path.home()),
            "OCIO Config (*.ocio *.yaml config.yaml);;All Files (*)"
        )

        if file_path:
            if self._color_manager.load_config(Path(file_path)):
                self._config_label.setText(file_path)
                self._update_config_info()
                self._populate_color_spaces()
                self._populate_displays()
                self._validate_config_button.setEnabled(True)
                self._apply_defaults_button.setEnabled(True)
                self._analyze_button.setEnabled(True)
                self._auto_assign_button.setEnabled(True)
                self._status_label.setText("OCIO config loaded successfully")
            else:
                QMessageBox.critical(self, "Error", "Failed to load OCIO config")
                self._status_label.setText("Failed to load config")

    def _update_config_info(self):
        """Update config information display."""
        config = self._color_manager.get_ocio_manager().get_config()
        if config:
            info = [
                f"<b>Description:</b> {config.getDescription() or 'None'}",
                f"<b>Color Spaces:</b> {len(self._color_manager.get_ocio_manager().get_color_spaces())}",
                f"<b>Displays:</b> {len(self._color_manager.get_ocio_manager().get_displays())}",
            ]
            self._config_info_label.setText("<br>".join(info))

    def _on_validate_config(self):
        """Handle validate config button click."""
        valid, errors = self._color_manager.validate_config()

        if valid:
            QMessageBox.information(
                self,
                "Validation Success",
                "OCIO configuration is valid!"
            )
        else:
            message = "<h3>Configuration Errors:</h3><ul>"
            for error in errors:
                message += f"<li>{error}</li>"
            message += "</ul>"

            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Validation Failed")
            msg_box.setTextFormat(Qt.TextFormat.RichText)
            msg_box.setText(message)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.exec()

    def _populate_color_spaces(self):
        """Populate color spaces tree and combos."""
        self._color_space_tree.clear()
        self._working_cs_combo.clear()
        self._default_input_combo.clear()
        self._override_cs_combo.clear()

        relationships = self._color_manager.get_color_space_relationships()

        for family, color_spaces in sorted(relationships.items()):
            # Add to tree
            family_item = QTreeWidgetItem(self._color_space_tree)
            family_item.setText(0, family)
            family_item.setFont(0, QFont("", -1, QFont.Weight.Bold))

            for cs_name in sorted(color_spaces):
                cs_item = QTreeWidgetItem(family_item)
                cs_item.setText(0, cs_name)

                # Get description
                cs_info = self._color_manager.get_ocio_manager().get_color_space_info(cs_name)
                cs_item.setText(1, cs_info.get("description", ""))

                # Add to combos
                self._working_cs_combo.addItem(cs_name)
                self._default_input_combo.addItem(cs_name)
                self._override_cs_combo.addItem(cs_name)

        self._color_space_tree.expandAll()

    def _populate_displays(self):
        """Populate display and view combos."""
        self._display_combo.clear()
        self._view_combo.clear()

        displays = self._color_manager.get_ocio_manager().get_displays()
        for display in displays:
            self._display_combo.addItem(display)

        # Set default
        config = self._color_manager.get_ocio_manager().get_config()
        if config:
            default_display = config.getDefaultDisplay()
            index = self._display_combo.findText(default_display)
            if index >= 0:
                self._display_combo.setCurrentIndex(index)

    def _on_display_changed(self, display: str):
        """Handle display combo change."""
        if not display:
            return

        self._view_combo.clear()
        views = self._color_manager.get_ocio_manager().get_views(display)
        for view in views:
            self._view_combo.addItem(view)

    def _on_working_cs_changed(self, color_space: str):
        """Handle working color space change."""
        if color_space:
            self._status_label.setText(f"Working color space: {color_space}")

    def _on_apply_defaults(self):
        """Apply pipeline defaults."""
        pipeline_config = self._color_manager.get_pipeline_config()
        pipeline_config.set_defaults(
            working=self._working_cs_combo.currentText(),
            default_input=self._default_input_combo.currentText(),
            display=self._display_combo.currentText(),
            view=self._view_combo.currentText()
        )

        # Add default rules
        pipeline_config.add_rule('.r3d', 'RedWideGamutRGB')
        pipeline_config.add_rule('.ari', 'ARRI_LogC4')
        pipeline_config.add_rule('.braw', 'BMDFilm_Gen5')
        pipeline_config.add_rule('.dng', 'CameraRec709')

        self._status_label.setText("Pipeline defaults applied")
        logger.info("Pipeline defaults configured")

    def set_timeline(self, timeline: otio.schema.Timeline):
        """
        Set the timeline to analyze.

        Args:
            timeline: OTIO timeline
        """
        self._current_timeline = timeline
        self._analyze_button.setEnabled(True)
        self._auto_assign_button.setEnabled(True)
        logger.info(f"Timeline set for color analysis: {timeline.name}")

    def _on_analyze_timeline(self):
        """Handle analyze timeline button click."""
        if not self._current_timeline:
            QMessageBox.warning(self, "Error", "No timeline loaded")
            return

        self._status_label.setText("Analyzing timeline...")

        result = self._color_manager.analyze_timeline(
            self._current_timeline,
            auto_detect=True
        )

        # Update clips list
        self._clips_list.clear()
        for assignment in result.assignments:
            item = QListWidgetItem(assignment.clip_name)
            item.setData(Qt.ItemDataRole.UserRole, assignment)

            # Color code by status
            if assignment.status == ColorSpaceStatus.VALID:
                item.setForeground(QColor("green"))
            elif assignment.status == ColorSpaceStatus.MISSING:
                item.setForeground(QColor("orange"))
            elif assignment.status == ColorSpaceStatus.INVALID:
                item.setForeground(QColor("red"))

            self._clips_list.addItem(item)

        # Show summary
        summary = (
            f"Analysis complete: {result.valid_count} valid, "
            f"{result.missing_count} missing, {result.invalid_count} invalid"
        )
        self._status_label.setText(summary)

        # Enable report export
        self._export_report_button.setEnabled(True)

        # Emit signal
        self.timeline_analyzed.emit(result)

        # Switch to analysis tab
        self._tab_widget.setCurrentIndex(1)

    def _on_clip_selected(self, item: QListWidgetItem):
        """Handle clip selection."""
        assignment = item.data(Qt.ItemDataRole.UserRole)
        if assignment:
            self._show_clip_details(assignment)
            self._assign_button.setEnabled(True)

            # Set current color space in override combo
            if assignment.input_color_space:
                index = self._override_cs_combo.findText(assignment.input_color_space)
                if index >= 0:
                    self._override_cs_combo.setCurrentIndex(index)

    def _show_clip_details(self, assignment: ColorSpaceAssignment):
        """Show detailed color space information for clip."""
        details = [
            f"<h3>Clip: {assignment.clip_name}</h3>",
            f"<b>Status:</b> {assignment.status.value.upper()}",
        ]

        if assignment.input_color_space:
            details.append(f"<b>Input Color Space:</b> {assignment.input_color_space}")
        else:
            details.append("<b>Input Color Space:</b> <span style='color:red;'>NOT ASSIGNED</span>")

        if assignment.working_color_space:
            details.append(f"<b>Working Color Space:</b> {assignment.working_color_space}")

        if assignment.output_color_space:
            details.append(f"<b>Output Color Space:</b> {assignment.output_color_space}")

        if assignment.display:
            details.append(f"<b>Display:</b> {assignment.display}")
            if assignment.view:
                details.append(f"<b>View:</b> {assignment.view}")

        if assignment.warnings:
            details.append("<br><b>Warnings:</b>")
            for warning in assignment.warnings:
                details.append(f"  <span style='color:orange;'>⚠ {warning}</span>")

        self._clip_details_text.setHtml("<br>".join(details))

    def _on_assign_color_space(self):
        """Handle assign color space button click."""
        selected = self._clips_list.currentItem()
        if not selected or not self._current_timeline:
            return

        assignment = selected.data(Qt.ItemDataRole.UserRole)
        new_cs = self._override_cs_combo.currentText()

        # Find clip in timeline
        for track in self._current_timeline.tracks:
            for item in track:
                if isinstance(item, otio.schema.Clip) and item.name == assignment.clip_name:
                    # Assign new color space
                    self._color_manager.assign_color_space_to_clip(
                        item,
                        input_color_space=new_cs,
                        working_color_space=self._working_cs_combo.currentText(),
                        display=self._display_combo.currentText(),
                        view=self._view_combo.currentText()
                    )

                    # Update UI
                    assignment.input_color_space = new_cs
                    assignment.status = ColorSpaceStatus.VALID
                    assignment.warnings = []

                    selected.setForeground(QColor("green"))
                    self._show_clip_details(assignment)

                    self._status_label.setText(
                        f"Assigned '{new_cs}' to clip '{assignment.clip_name}'"
                    )

                    # Emit signal
                    self.color_space_changed.emit(assignment.clip_name, new_cs)

                    logger.info(f"Manually assigned color space: {assignment.clip_name} -> {new_cs}")
                    return

    def _on_auto_assign(self):
        """Handle auto-assign button click."""
        if not self._current_timeline:
            QMessageBox.warning(self, "Error", "No timeline loaded")
            return

        reply = QMessageBox.question(
            self,
            "Auto-Assign Color Spaces",
            "This will automatically assign color spaces to all clips based on "
            "file extensions and pipeline defaults. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            count = self._color_manager.auto_assign_color_spaces(
                self._current_timeline,
                use_defaults=True
            )

            QMessageBox.information(
                self,
                "Auto-Assign Complete",
                f"Assigned color spaces to {count} clips"
            )

            # Re-analyze
            self._on_analyze_timeline()

    def _on_export_report(self):
        """Handle export report button click."""
        if not self._current_timeline:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Color Space Report",
            str(Path.home() / "color_space_report.txt"),
            "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            report = self._color_manager.create_color_space_report(self._current_timeline)

            # Format report as text
            lines = [
                f"Color Space Report: {report['timeline_name']}",
                "=" * 60,
                f"Total Clips: {report['total_clips']}",
                f"Valid Assignments: {report['valid_assignments']}",
                f"Missing Assignments: {report['missing_assignments']}",
                f"Invalid Assignments: {report['invalid_assignments']}",
                f"Status: {report['validation_status']}",
                "",
                "Color Spaces Used:",
            ]

            for cs, count in report['color_spaces_used'].items():
                lines.append(f"  {cs}: {count} clips")

            lines.append("")
            lines.append("Clip Details:")
            lines.append("-" * 60)

            for clip in report['clips']:
                lines.append(f"\nClip: {clip['name']}")
                lines.append(f"  Color Space: {clip['input_color_space'] or 'NOT ASSIGNED'}")
                lines.append(f"  Status: {clip['status']}")
                if clip['warnings']:
                    lines.append("  Warnings:")
                    for warning in clip['warnings']:
                        lines.append(f"    - {warning}")

            # Write to file
            with open(file_path, 'w') as f:
                f.write('\n'.join(lines))

            self._status_label.setText(f"Report exported to {file_path}")
            logger.info(f"Color space report exported to {file_path}")

    def get_color_manager(self) -> ColorManager:
        """Get the color manager instance."""
        return self._color_manager
