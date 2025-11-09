"""
Media preview widget for displaying asset previews.

This module provides a Qt widget for previewing media assets including
images, videos, and other file types.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSizePolicy, QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QImage
from pathlib import Path
from typing import Optional
from ..core.logger import get_logger

logger = get_logger(__name__)


class MediaPreviewWidget(QWidget):
    """Widget for previewing media assets with large display area."""

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the media preview widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._current_asset = None
        self._setup_ui()
        logger.debug("MediaPreviewWidget initialized")

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Preview group
        preview_group = QGroupBox("Media Preview")
        preview_layout = QVBoxLayout()

        # Scroll area for large images
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Preview label for displaying images/thumbnails
        self._preview_label = QLabel()
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setMinimumSize(400, 300)
        self._preview_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self._preview_label.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                border: 2px solid #555555;
                border-radius: 5px;
                padding: 10px;
                color: #aaaaaa;
            }
        """)
        self._preview_label.setText("No media selected")

        scroll_area.setWidget(self._preview_label)
        preview_layout.addWidget(scroll_area)

        # Info label below preview
        self._info_label = QLabel()
        self._info_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._info_label.setWordWrap(True)
        self._info_label.setMaximumHeight(120)
        self._info_label.setStyleSheet("""
            QLabel {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 8px;
                font-size: 11px;
            }
        """)
        preview_layout.addWidget(self._info_label)

        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

    def set_asset(self, asset):
        """
        Set the asset to preview.

        Args:
            asset: Asset object to preview
        """
        self._current_asset = asset
        self._update_preview()

    def clear_preview(self):
        """Clear the preview display."""
        self._current_asset = None
        self._preview_label.clear()
        self._preview_label.setText("No media selected")
        self._info_label.clear()

    def _update_preview(self):
        """Update the preview display with current asset."""
        if not self._current_asset:
            self.clear_preview()
            return

        asset = self._current_asset
        asset_path = Path(asset.path)

        # Update info label
        self._update_info_label(asset)

        # Check if file exists
        if not asset_path.exists():
            self._preview_label.setText(
                f"⚠ Media Offline\n\n{asset.name}\n\nPath: {asset.path}"
            )
            self._preview_label.setStyleSheet("""
                QLabel {
                    background-color: #3a2020;
                    border: 2px solid #aa5555;
                    border-radius: 5px;
                    padding: 10px;
                    color: #ffaaaa;
                }
            """)
            return

        # Reset style for online media
        self._preview_label.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                border: 2px solid #555555;
                border-radius: 5px;
                padding: 10px;
                color: #aaaaaa;
            }
        """)

        # Try to load preview based on file type
        try:
            file_ext = asset_path.suffix.lower()

            # Image formats
            if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp']:
                self._load_image_preview(asset_path)

            # Video formats - show placeholder for now
            elif file_ext in ['.mp4', '.mov', '.avi', '.mkv', '.m4v', '.mxf', '.r3d', '.ari', '.braw']:
                self._show_video_placeholder(asset)

            # Sequence/DPX/EXR
            elif file_ext in ['.dpx', '.exr', '.cin']:
                self._show_sequence_placeholder(asset)

            # Unknown/unsupported
            else:
                self._show_file_info(asset)

        except Exception as e:
            logger.error(f"Failed to load preview for {asset.name}: {e}")
            self._preview_label.setText(
                f"⚠ Preview Error\n\n{asset.name}\n\n{str(e)}"
            )

    def _load_image_preview(self, image_path: Path):
        """
        Load and display an image preview.

        Args:
            image_path: Path to image file
        """
        try:
            pixmap = QPixmap(str(image_path))

            if pixmap.isNull():
                self._preview_label.setText(
                    f"⚠ Failed to load image\n\n{image_path.name}"
                )
                return

            # Scale to fit while maintaining aspect ratio
            label_size = self._preview_label.size()
            max_width = max(label_size.width() - 20, 400)
            max_height = max(label_size.height() - 20, 300)

            scaled_pixmap = pixmap.scaled(
                max_width,
                max_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            self._preview_label.setPixmap(scaled_pixmap)

            logger.debug(f"Loaded image preview: {image_path.name}")

        except Exception as e:
            logger.error(f"Error loading image {image_path}: {e}")
            self._preview_label.setText(
                f"⚠ Image Load Error\n\n{image_path.name}\n\n{str(e)}"
            )

    def _show_video_placeholder(self, asset):
        """
        Show a placeholder for video files.

        Args:
            asset: Asset object
        """
        resolution_text = ""
        if asset.resolution:
            resolution_text = f"{asset.resolution[0]}x{asset.resolution[1]}"

        fps_text = ""
        if asset.fps:
            fps_text = f"@ {asset.fps} fps"

        file_ext = Path(asset.path).suffix.upper()

        placeholder_text = f"🎬 Video File\n\n{asset.name}\n\n"
        placeholder_text += f"Format: {file_ext}\n"

        if resolution_text:
            placeholder_text += f"Resolution: {resolution_text}\n"
        if fps_text:
            placeholder_text += f"Frame Rate: {fps_text}\n"

        placeholder_text += "\n(Video playback preview coming soon)"

        self._preview_label.setText(placeholder_text)
        logger.debug(f"Showing video placeholder for: {asset.name}")

    def _show_sequence_placeholder(self, asset):
        """
        Show a placeholder for image sequences.

        Args:
            asset: Asset object
        """
        file_ext = Path(asset.path).suffix.upper()

        placeholder_text = f"🎞 Image Sequence\n\n{asset.name}\n\n"
        placeholder_text += f"Format: {file_ext}\n"

        if asset.resolution:
            placeholder_text += f"Resolution: {asset.resolution[0]}x{asset.resolution[1]}\n"

        placeholder_text += "\n(Sequence preview coming soon)"

        self._preview_label.setText(placeholder_text)
        logger.debug(f"Showing sequence placeholder for: {asset.name}")

    def _show_file_info(self, asset):
        """
        Show basic file information for unsupported preview types.

        Args:
            asset: Asset object
        """
        file_ext = Path(asset.path).suffix.upper()

        info_text = f"📄 {asset.asset_type.value.title()}\n\n{asset.name}\n\n"
        info_text += f"Format: {file_ext}\n"

        if asset.file_size:
            size_mb = asset.file_size / (1024 * 1024)
            info_text += f"Size: {size_mb:.2f} MB\n"

        info_text += "\n(No preview available for this file type)"

        self._preview_label.setText(info_text)
        logger.debug(f"Showing file info for: {asset.name}")

    def _update_info_label(self, asset):
        """
        Update the information label with asset metadata.

        Args:
            asset: Asset object
        """
        info_parts = []

        # Basic info
        info_parts.append(f"<b>Name:</b> {asset.name}")
        info_parts.append(f"<b>Type:</b> {asset.asset_type.value}")
        info_parts.append(f"<b>Status:</b> {asset.status.value}")

        # Size
        if asset.file_size:
            size_mb = asset.file_size / (1024 * 1024)
            if size_mb > 1024:
                size_gb = size_mb / 1024
                info_parts.append(f"<b>Size:</b> {size_gb:.2f} GB")
            else:
                info_parts.append(f"<b>Size:</b> {size_mb:.2f} MB")

        # Resolution
        if asset.resolution:
            info_parts.append(f"<b>Resolution:</b> {asset.resolution[0]}x{asset.resolution[1]}")

        # Frame rate
        if asset.fps:
            info_parts.append(f"<b>FPS:</b> {asset.fps}")

        # Color space
        if asset.color_space:
            info_parts.append(f"<b>Color Space:</b> {asset.color_space}")

        # Path
        info_parts.append(f"<b>Path:</b> <span style='font-size: 9px; color: #888888;'>{asset.path}</span>")

        self._info_label.setText("<br>".join(info_parts))

    def resizeEvent(self, event):
        """Handle resize events to update preview scaling."""
        super().resizeEvent(event)

        # Reload preview if we have a current asset and it's an image
        if self._current_asset and hasattr(self, '_preview_label'):
            asset_path = Path(self._current_asset.path)
            if asset_path.exists() and asset_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp']:
                # Only reload if we have a pixmap set
                if self._preview_label.pixmap() and not self._preview_label.pixmap().isNull():
                    self._load_image_preview(asset_path)
