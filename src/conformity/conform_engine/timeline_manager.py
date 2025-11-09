"""
Timeline management using OpenTimelineIO.

This module provides high-level interfaces for working with OTIO timelines,
including loading, saving, and manipulating timeline data.
"""

import opentimelineio as otio
from pathlib import Path
from typing import Optional, List, Dict, Any
from ..core.logger import get_logger

logger = get_logger(__name__)


class TimelineManager:
    """Manages OTIO timeline operations."""

    def __init__(self):
        """Initialize the timeline manager."""
        self._current_timeline: Optional[otio.schema.Timeline] = None
        logger.info("TimelineManager initialized")

    def load_timeline(self, file_path: Path) -> otio.schema.Timeline:
        """
        Load a timeline from a file.

        Args:
            file_path: Path to the timeline file

        Returns:
            Loaded timeline object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Timeline file not found: {file_path}")

        try:
            logger.info(f"Loading timeline from: {file_path}")
            self._current_timeline = otio.adapters.read_from_file(str(file_path))
            logger.info(f"Successfully loaded timeline: {self._current_timeline.name}")
            return self._current_timeline
        except Exception as e:
            logger.error(f"Failed to load timeline: {e}")
            raise ValueError(f"Could not load timeline: {e}")

    def save_timeline(
        self,
        timeline: Optional[otio.schema.Timeline] = None,
        file_path: Optional[Path] = None,
        adapter: str = "otio_json"
    ) -> None:
        """
        Save a timeline to a file.

        Args:
            timeline: Timeline to save (defaults to current timeline)
            file_path: Path to save the timeline
            adapter: OTIO adapter to use for saving

        Raises:
            ValueError: If no timeline is available or path is not provided
        """
        timeline = timeline or self._current_timeline
        if timeline is None:
            raise ValueError("No timeline to save")
        if file_path is None:
            raise ValueError("File path must be provided")

        try:
            logger.info(f"Saving timeline to: {file_path}")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            otio.adapters.write_to_file(timeline, str(file_path), adapter)
            logger.info("Timeline saved successfully")
        except Exception as e:
            logger.error(f"Failed to save timeline: {e}")
            raise

    def create_timeline(
        self,
        name: str = "New Timeline",
        fps: float = 24.0
    ) -> otio.schema.Timeline:
        """
        Create a new empty timeline.

        Args:
            name: Name of the timeline
            fps: Frames per second

        Returns:
            New timeline object
        """
        logger.info(f"Creating new timeline: {name} @ {fps} fps")

        # Create a timeline with a single video track
        track = otio.schema.Track(
            name="V1",
            kind=otio.schema.TrackKind.Video
        )

        # Create empty stack first, then append track to avoid parent issues
        stack = otio.schema.Stack()
        stack.append(track)

        timeline = otio.schema.Timeline(
            name=name,
            tracks=stack
        )

        # Set the global start time
        timeline.global_start_time = otio.opentime.RationalTime(0, fps)

        self._current_timeline = timeline
        logger.info("Timeline created successfully")
        return timeline

    def get_timeline_info(
        self,
        timeline: Optional[otio.schema.Timeline] = None
    ) -> Dict[str, Any]:
        """
        Get information about a timeline.

        Args:
            timeline: Timeline to analyze (defaults to current timeline)

        Returns:
            Dictionary containing timeline information
        """
        timeline = timeline or self._current_timeline
        if timeline is None:
            return {}

        info = {
            "name": timeline.name,
            "duration": timeline.duration(),
            "tracks": len(timeline.tracks),
            "clips": self._count_clips(timeline),
        }

        logger.debug(f"Timeline info: {info}")
        return info

    def _count_clips(self, timeline: otio.schema.Timeline) -> int:
        """Count total number of clips in timeline."""
        count = 0
        for track in timeline.tracks:
            for item in track:
                if isinstance(item, otio.schema.Clip):
                    count += 1
        return count

    def add_clip(
        self,
        media_path: Path,
        track_index: int = 0,
        name: Optional[str] = None,
        timeline: Optional[otio.schema.Timeline] = None
    ) -> otio.schema.Clip:
        """
        Add a clip to the timeline.

        Args:
            media_path: Path to the media file
            track_index: Index of track to add clip to
            name: Optional name for the clip
            timeline: Timeline to add to (defaults to current timeline)

        Returns:
            Created clip object

        Raises:
            ValueError: If timeline or track doesn't exist
        """
        timeline = timeline or self._current_timeline
        if timeline is None:
            raise ValueError("No timeline available")

        if track_index >= len(timeline.tracks):
            raise ValueError(f"Track index {track_index} out of range")

        # Create media reference
        media_ref = otio.schema.ExternalReference(
            target_url=str(media_path)
        )

        # Create clip
        clip = otio.schema.Clip(
            name=name or media_path.stem,
            media_reference=media_ref
        )

        # Add to track
        track = timeline.tracks[track_index]
        track.append(clip)

        logger.info(f"Added clip '{clip.name}' to track {track_index}")
        return clip

    def get_current_timeline(self) -> Optional[otio.schema.Timeline]:
        """Get the current timeline."""
        return self._current_timeline

    def set_current_timeline(self, timeline: otio.schema.Timeline) -> None:
        """Set the current timeline."""
        self._current_timeline = timeline
        logger.info(f"Current timeline set to: {timeline.name}")
