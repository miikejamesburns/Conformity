"""
Automated conform engine for timeline import/export using OpenTimelineIO.

This module provides comprehensive functionality for importing timelines from
various formats (XML, AAF, EDL, etc.), parsing their structure, and exporting
to different formats.
"""

import opentimelineio as otio
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .exceptions import (
    ConformError, MediaNotFoundError, UnsupportedFeatureError,
    InvalidTimecodeError, ImportError, ExportError, AdapterNotFoundError
)
from ..core.logger import get_logger

logger = get_logger(__name__)


class TimelineFormat(Enum):
    """Supported timeline formats."""
    OTIO = "otio_json"
    EDL = "cmx_3600"
    FCPXML = "fcp_xml"
    AAF = "aaf"
    XML = "fcp_xml"  # Final Cut Pro XML
    ALE = "ale"

    @classmethod
    def from_extension(cls, ext: str) -> Optional['TimelineFormat']:
        """Get format from file extension."""
        ext_map = {
            '.otio': cls.OTIO,
            '.edl': cls.EDL,
            '.fcpxml': cls.FCPXML,
            '.xml': cls.XML,
            '.aaf': cls.AAF,
            '.ale': cls.ALE,
        }
        return ext_map.get(ext.lower())


@dataclass
class ClipInfo:
    """Information extracted from a clip."""
    name: str
    source_path: Optional[str] = None
    source_range: Optional[otio.opentime.TimeRange] = None
    available_range: Optional[otio.opentime.TimeRange] = None
    duration: Optional[otio.opentime.RationalTime] = None
    track_name: Optional[str] = None
    track_kind: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    effects: List[str] = field(default_factory=list)
    markers: List[Dict[str, Any]] = field(default_factory=list)
    timecode_in: Optional[str] = None
    timecode_out: Optional[str] = None
    # Color space information
    input_color_space: Optional[str] = None
    working_color_space: Optional[str] = None
    color_space_warnings: List[str] = field(default_factory=list)


@dataclass
class TimelineInfo:
    """Information extracted from a timeline."""
    name: str
    duration: Optional[otio.opentime.RationalTime] = None
    global_start_time: Optional[otio.opentime.RationalTime] = None
    num_tracks: int = 0
    num_clips: int = 0
    num_transitions: int = 0
    num_markers: int = 0
    clips: List[ClipInfo] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    unsupported_features: List[str] = field(default_factory=list)
    missing_media: List[str] = field(default_factory=list)
    # Color space tracking
    clips_with_color_space: int = 0
    clips_without_color_space: int = 0
    color_spaces_used: Dict[str, int] = field(default_factory=dict)


class ConformEngine:
    """Engine for automated timeline conform operations."""

    def __init__(self):
        """Initialize the conform engine."""
        self._supported_adapters = self._detect_available_adapters()
        logger.info(f"ConformEngine initialized with adapters: {self._supported_adapters}")

    def _detect_available_adapters(self) -> List[str]:
        """Detect available OTIO adapters."""
        try:
            manifest = otio.plugins.ActiveManifest()
            adapters = []
            for adapter in manifest.adapters:
                # Adapter object has a .name attribute
                adapters.append(adapter.name)
            logger.debug(f"Detected {len(adapters)} OTIO adapters")
            return adapters
        except Exception as e:
            logger.error(f"Failed to detect OTIO adapters: {e}")
            logger.error("This usually means OpenTimelineIO is not installed or not working properly")
            logger.error("Install it with: pip install opentimelineio==0.16.0")
            return []

    def is_adapter_available(self, adapter_name: str) -> bool:
        """
        Check if an adapter is available.

        Args:
            adapter_name: Name of the adapter

        Returns:
            True if adapter is available
        """
        return adapter_name in self._supported_adapters

    def import_timeline(
        self,
        file_path: Path,
        adapter_name: Optional[str] = None,
        verify_media: bool = False
    ) -> Tuple[otio.schema.Timeline, TimelineInfo]:
        """
        Import a timeline from file.

        Args:
            file_path: Path to the timeline file
            adapter_name: Optional adapter name (auto-detected if not provided)
            verify_media: Whether to verify media files exist

        Returns:
            Tuple of (timeline, timeline_info)

        Raises:
            ImportError: If import fails
            AdapterNotFoundError: If adapter is not available
        """
        if not file_path.exists():
            raise ImportError(str(file_path), "File not found")

        # Determine adapter
        if adapter_name is None:
            fmt = TimelineFormat.from_extension(file_path.suffix)
            if fmt:
                adapter_name = fmt.value
            else:
                # Try to auto-detect
                adapter_name = "otio_json"

        # Check adapter availability
        if not self.is_adapter_available(adapter_name):
            # Provide helpful context about available adapters
            if not self._supported_adapters:
                logger.error("No OTIO adapters detected. OpenTimelineIO may not be installed.")
                raise AdapterNotFoundError(
                    adapter_name +
                    " (No adapters available - is OpenTimelineIO installed?)"
                )
            else:
                logger.error(
                    f"Adapter '{adapter_name}' not available. "
                    f"Available adapters: {', '.join(self._supported_adapters)}"
                )
                raise AdapterNotFoundError(adapter_name)

        try:
            logger.info(f"Importing timeline from {file_path} using adapter '{adapter_name}'")

            # Read the timeline
            timeline = otio.adapters.read_from_file(
                str(file_path),
                adapter_name=adapter_name
            )

            if not isinstance(timeline, otio.schema.Timeline):
                raise ImportError(
                    str(file_path),
                    f"Expected Timeline object, got {type(timeline)}"
                )

            # Parse timeline info
            timeline_info = self.parse_timeline(timeline, verify_media=verify_media)

            logger.info(
                f"Successfully imported timeline: {timeline.name} "
                f"({timeline_info.num_clips} clips, {timeline_info.num_tracks} tracks)"
            )

            return timeline, timeline_info

        except otio.exceptions.OTIOError as e:
            logger.error(f"OTIO error during import: {e}")
            raise ImportError(str(file_path), str(e))
        except Exception as e:
            logger.error(f"Unexpected error during import: {e}")
            raise ImportError(str(file_path), str(e))

    def parse_timeline(
        self,
        timeline: otio.schema.Timeline,
        verify_media: bool = False
    ) -> TimelineInfo:
        """
        Parse timeline structure and extract information.

        Args:
            timeline: OTIO timeline object
            verify_media: Whether to verify media files exist

        Returns:
            TimelineInfo object with extracted data
        """
        logger.debug(f"Parsing timeline: {timeline.name}")

        info = TimelineInfo(
            name=timeline.name,
            duration=timeline.duration(),
            global_start_time=timeline.global_start_time,
            metadata=dict(timeline.metadata)
        )

        # Count tracks
        info.num_tracks = len(timeline.tracks)

        # Parse each track
        for track in timeline.tracks:
            self._parse_track(track, info, verify_media)

        # Count markers
        # In OTIO 0.16+, markers is a property not a method
        if hasattr(timeline, 'markers') and timeline.markers:
            info.num_markers = len(timeline.markers)

        logger.debug(
            f"Parsed timeline: {info.num_clips} clips, "
            f"{info.num_transitions} transitions, {info.num_markers} markers"
        )

        return info

    def _parse_track(
        self,
        track: otio.schema.Track,
        info: TimelineInfo,
        verify_media: bool
    ) -> None:
        """Parse a track and add its contents to timeline info."""
        track_name = track.name or f"Track_{info.num_tracks}"
        # In OTIO 0.16+, track.kind is already a string, not an enum
        track_kind = str(track.kind) if track.kind else "Unknown"

        for item in track:
            if isinstance(item, otio.schema.Clip):
                clip_info = self._parse_clip(item, track_name, track_kind, verify_media)
                info.clips.append(clip_info)
                info.num_clips += 1

                # Track color space statistics
                if clip_info.input_color_space:
                    info.clips_with_color_space += 1
                    cs = clip_info.input_color_space
                    info.color_spaces_used[cs] = info.color_spaces_used.get(cs, 0) + 1
                else:
                    info.clips_without_color_space += 1

            elif isinstance(item, otio.schema.Transition):
                info.num_transitions += 1

            elif isinstance(item, otio.schema.Gap):
                # Gaps are normal, just log them
                logger.debug(f"Gap found in track {track_name}")

            else:
                # Unknown item type
                feature = f"Unknown item type: {type(item).__name__}"
                if feature not in info.unsupported_features:
                    info.unsupported_features.append(feature)
                    logger.warning(f"Unsupported feature: {feature}")

    def _parse_clip(
        self,
        clip: otio.schema.Clip,
        track_name: str,
        track_kind: str,
        verify_media: bool
    ) -> ClipInfo:
        """
        Parse a clip and extract its information.

        Args:
            clip: OTIO clip object
            track_name: Name of the track containing the clip
            track_kind: Kind of track (Video/Audio)
            verify_media: Whether to verify media exists

        Returns:
            ClipInfo object
        """
        # Try to get available_range, but handle cases where it can't be computed
        available_range = None
        try:
            available_range = clip.available_range()
        except Exception:
            # MissingReference or other cases where available_range can't be computed
            # Use source_range as fallback if available
            if clip.source_range:
                available_range = clip.source_range

        clip_info = ClipInfo(
            name=clip.name,
            source_range=clip.source_range,
            available_range=available_range,
            duration=clip.duration(),
            track_name=track_name,
            track_kind=track_kind,
            metadata=dict(clip.metadata)
        )

        # Extract source path
        if clip.media_reference:
            if isinstance(clip.media_reference, otio.schema.ExternalReference):
                clip_info.source_path = clip.media_reference.target_url

                # Verify media if requested
                if verify_media and clip_info.source_path:
                    media_path = Path(clip_info.source_path)
                    if not media_path.exists():
                        logger.warning(f"Media not found for clip '{clip.name}': {clip_info.source_path}")
                        # Note: we don't raise here, just log it

            elif isinstance(clip.media_reference, otio.schema.MissingReference):
                logger.warning(f"Missing reference for clip: {clip.name}")

        # Extract effects
        # In OTIO 0.16+, effects is a property not a method
        if hasattr(clip, 'effects') and clip.effects:
            for effect in clip.effects:
                clip_info.effects.append(effect.name or type(effect).__name__)

        # Extract markers
        # In OTIO 0.16+, markers is a property not a method
        if hasattr(clip, 'markers') and clip.markers:
            for marker in clip.markers:
                marker_data = {
                    'name': marker.name,
                    'marked_range': str(marker.marked_range) if marker.marked_range else None,
                    'color': marker.color.name if marker.color else None,
                    'metadata': dict(marker.metadata)
                }
                clip_info.markers.append(marker_data)

        # Extract color space information
        if "color" in clip.metadata:
            color_meta = clip.metadata["color"]
            clip_info.input_color_space = color_meta.get("input_color_space")
            clip_info.working_color_space = color_meta.get("working_color_space")

            # Log if found
            if clip_info.input_color_space:
                logger.debug(f"Clip '{clip.name}' has color space: {clip_info.input_color_space}")
            else:
                clip_info.color_space_warnings.append("No input color space defined")

        # Calculate timecodes if possible
        if clip_info.source_range:
            try:
                start_time = clip_info.source_range.start_time
                end_time = clip_info.source_range.end_time_exclusive()
                clip_info.timecode_in = self._format_timecode(start_time)
                clip_info.timecode_out = self._format_timecode(end_time)
            except Exception as e:
                logger.debug(f"Could not calculate timecodes for clip {clip.name}: {e}")

        return clip_info

    def _format_timecode(self, rational_time: otio.opentime.RationalTime) -> str:
        """
        Format a RationalTime as timecode string.

        Args:
            rational_time: Time to format

        Returns:
            Timecode string in HH:MM:SS:FF format
        """
        try:
            # Convert to timecode
            total_frames = int(rational_time.value)
            rate = rational_time.rate

            frames = total_frames % int(rate)
            total_seconds = total_frames // int(rate)
            seconds = total_seconds % 60
            total_minutes = total_seconds // 60
            minutes = total_minutes % 60
            hours = total_minutes // 60

            return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"
        except Exception as e:
            logger.debug(f"Error formatting timecode: {e}")
            return str(rational_time)

    def export_timeline(
        self,
        timeline: otio.schema.Timeline,
        file_path: Path,
        format: Optional[TimelineFormat] = None,
        adapter_args: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Export timeline to file.

        Args:
            timeline: Timeline to export
            file_path: Destination file path
            format: Export format (auto-detected if not provided)
            adapter_args: Optional arguments for the adapter

        Raises:
            ExportError: If export fails
            AdapterNotFoundError: If adapter is not available
        """
        # Determine format
        if format is None:
            format = TimelineFormat.from_extension(file_path.suffix)
            if format is None:
                raise ExportError(
                    str(file_path),
                    reason="Could not determine format from extension"
                )

        adapter_name = format.value

        # Check adapter availability
        if not self.is_adapter_available(adapter_name):
            # Provide helpful context about available adapters
            if not self._supported_adapters:
                logger.error("No OTIO adapters detected. OpenTimelineIO may not be installed.")
                raise AdapterNotFoundError(
                    adapter_name +
                    " (No adapters available - is OpenTimelineIO installed?)"
                )
            else:
                logger.error(
                    f"Adapter '{adapter_name}' not available. "
                    f"Available adapters: {', '.join(self._supported_adapters)}"
                )
                raise AdapterNotFoundError(adapter_name)

        try:
            logger.info(f"Exporting timeline to {file_path} using adapter '{adapter_name}'")

            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the timeline
            # Note: OTIO 0.16+ doesn't support adapter_args in write_to_file
            # Use write_to_string with adapter then write manually if needed
            if adapter_args:
                # If adapter_args provided, use write_to_string and write manually
                content = otio.adapters.write_to_string(
                    timeline,
                    adapter_name=adapter_name
                )
                file_path.write_text(content)
            else:
                # Standard write path
                otio.adapters.write_to_file(
                    timeline,
                    str(file_path),
                    adapter_name=adapter_name
                )

            logger.info(f"Successfully exported timeline to {file_path}")

        except otio.exceptions.OTIOError as e:
            logger.error(f"OTIO error during export: {e}")
            raise ExportError(str(file_path), format.name, str(e))
        except Exception as e:
            logger.error(f"Unexpected error during export: {e}")
            raise ExportError(str(file_path), format.name, str(e))

    def validate_timeline(
        self,
        timeline: otio.schema.Timeline,
        check_media: bool = True
    ) -> Dict[str, Any]:
        """
        Validate timeline and check for issues.

        Args:
            timeline: Timeline to validate
            check_media: Whether to check for missing media

        Returns:
            Dictionary with validation results
        """
        logger.info(f"Validating timeline: {timeline.name}")

        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'missing_media': [],
            'invalid_timecodes': [],
            'unsupported_features': []
        }

        # Parse timeline
        info = self.parse_timeline(timeline, verify_media=check_media)

        # Check for missing media
        if check_media:
            for clip_info in info.clips:
                if clip_info.source_path:
                    media_path = Path(clip_info.source_path)
                    if not media_path.exists():
                        results['missing_media'].append({
                            'clip': clip_info.name,
                            'path': clip_info.source_path
                        })
                        results['warnings'].append(
                            f"Missing media for clip '{clip_info.name}': {clip_info.source_path}"
                        )

        # Check for unsupported features
        if info.unsupported_features:
            results['unsupported_features'] = info.unsupported_features
            results['warnings'].extend(
                [f"Unsupported feature: {f}" for f in info.unsupported_features]
            )

        # Validate timecodes
        for clip_info in info.clips:
            if clip_info.source_range:
                try:
                    start = clip_info.source_range.start_time
                    duration = clip_info.source_range.duration

                    # Check for negative values
                    if start.value < 0:
                        results['invalid_timecodes'].append({
                            'clip': clip_info.name,
                            'issue': 'Negative start time',
                            'value': str(start)
                        })
                        results['errors'].append(
                            f"Invalid timecode for clip '{clip_info.name}': negative start time"
                        )
                        results['valid'] = False

                    if duration.value <= 0:
                        results['invalid_timecodes'].append({
                            'clip': clip_info.name,
                            'issue': 'Invalid duration',
                            'value': str(duration)
                        })
                        results['errors'].append(
                            f"Invalid duration for clip '{clip_info.name}': {duration}"
                        )
                        results['valid'] = False

                except Exception as e:
                    results['errors'].append(
                        f"Error validating timecode for clip '{clip_info.name}': {e}"
                    )
                    results['valid'] = False

        logger.info(
            f"Validation complete: valid={results['valid']}, "
            f"errors={len(results['errors'])}, warnings={len(results['warnings'])}"
        )

        return results

    def get_supported_formats(self) -> Dict[str, List[str]]:
        """
        Get supported import and export formats.

        Returns:
            Dictionary with 'import' and 'export' format lists
        """
        formats = {
            'import': [],
            'export': []
        }

        # Check each known format
        for fmt in TimelineFormat:
            if self.is_adapter_available(fmt.value):
                formats['import'].append(fmt.name)
                formats['export'].append(fmt.name)

        return formats
