"""
Color pipeline management for integrating OCIO with timeline operations.

This module bridges OCIO color management with OTIO timeline operations.
"""

import opentimelineio as otio
from typing import Optional, Dict, List
from .ocio_manager import OCIOManager
from ..core.logger import get_logger

logger = get_logger(__name__)


class ColorPipeline:
    """Manages color pipeline for timeline clips."""

    def __init__(self, ocio_manager: Optional[OCIOManager] = None):
        """
        Initialize the color pipeline.

        Args:
            ocio_manager: Optional OCIO manager instance
        """
        self._ocio_manager = ocio_manager or OCIOManager()
        logger.info("ColorPipeline initialized")

    def assign_color_space_to_clip(
        self,
        clip: otio.schema.Clip,
        color_space: str
    ) -> None:
        """
        Assign a color space to a clip's metadata.

        Args:
            clip: OTIO clip to assign color space to
            color_space: Name of the color space

        Raises:
            ValueError: If color space is invalid
        """
        if not self._ocio_manager.validate_color_space(color_space):
            raise ValueError(f"Invalid color space: {color_space}")

        if "color" not in clip.metadata:
            clip.metadata["color"] = {}

        clip.metadata["color"]["input_color_space"] = color_space
        logger.info(f"Assigned color space '{color_space}' to clip '{clip.name}'")

    def get_clip_color_space(self, clip: otio.schema.Clip) -> Optional[str]:
        """
        Get the color space assigned to a clip.

        Args:
            clip: OTIO clip

        Returns:
            Color space name or None if not assigned
        """
        if "color" in clip.metadata:
            return clip.metadata["color"].get("input_color_space")
        return None

    def assign_display_view_to_clip(
        self,
        clip: otio.schema.Clip,
        display: str,
        view: str
    ) -> None:
        """
        Assign a display and view to a clip's metadata.

        Args:
            clip: OTIO clip
            display: Display name
            view: View name
        """
        if "color" not in clip.metadata:
            clip.metadata["color"] = {}

        clip.metadata["color"]["display"] = display
        clip.metadata["color"]["view"] = view
        logger.info(f"Assigned display/view '{display}/{view}' to clip '{clip.name}'")

    def auto_assign_color_spaces(
        self,
        timeline: otio.schema.Timeline,
        extension_map: Optional[Dict[str, str]] = None
    ) -> int:
        """
        Automatically assign color spaces based on file extensions.

        Args:
            timeline: Timeline to process
            extension_map: Dictionary mapping file extensions to color spaces

        Returns:
            Number of clips assigned color spaces
        """
        if extension_map is None:
            # Default extension to color space mappings
            extension_map = {
                '.r3d': 'RedWideGamutRGB',
                '.ari': 'ARRI_LogC4',
                '.mxf': 'Rec709',
                '.mov': 'Rec709',
                '.mp4': 'Rec709',
            }

        assigned_count = 0

        for track in timeline.tracks:
            for item in track:
                if isinstance(item, otio.schema.Clip):
                    # Try to determine color space from media reference
                    if item.media_reference and isinstance(
                        item.media_reference, otio.schema.ExternalReference
                    ):
                        media_url = item.media_reference.target_url
                        for ext, color_space in extension_map.items():
                            if media_url.lower().endswith(ext):
                                try:
                                    self.assign_color_space_to_clip(item, color_space)
                                    assigned_count += 1
                                except ValueError:
                                    logger.warning(
                                        f"Could not assign color space '{color_space}' "
                                        f"to clip '{item.name}'"
                                    )
                                break

        logger.info(f"Auto-assigned color spaces to {assigned_count} clips")
        return assigned_count

    def create_color_report(self, timeline: otio.schema.Timeline) -> Dict[str, any]:
        """
        Create a report of color space assignments in a timeline.

        Args:
            timeline: Timeline to analyze

        Returns:
            Dictionary with color space statistics
        """
        total_clips = 0
        assigned_clips = 0
        color_space_counts = {}

        for track in timeline.tracks:
            for item in track:
                if isinstance(item, otio.schema.Clip):
                    total_clips += 1
                    color_space = self.get_clip_color_space(item)

                    if color_space:
                        assigned_clips += 1
                        color_space_counts[color_space] = (
                            color_space_counts.get(color_space, 0) + 1
                        )

        report = {
            "timeline_name": timeline.name,
            "total_clips": total_clips,
            "assigned_clips": assigned_clips,
            "unassigned_clips": total_clips - assigned_clips,
            "color_spaces": color_space_counts,
        }

        logger.info(
            f"Color report: {assigned_clips}/{total_clips} clips have color spaces assigned"
        )
        return report

    def get_ocio_manager(self) -> OCIOManager:
        """Get the OCIO manager instance."""
        return self._ocio_manager
