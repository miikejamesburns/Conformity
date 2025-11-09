"""
EDL (Edit Decision List) utilities for enhanced CMX 3600 support.

This module provides comprehensive EDL import/export functionality with
support for:
- CMX 3600 format compliance
- Reel name management
- Comment preservation
- Custom metadata handling
- Edit decision tracking
- Timecode utilities
- Source/record timecode validation
"""

import re
import opentimelineio as otio
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..core.logger import get_logger

logger = get_logger(__name__)


class EditType(Enum):
    """EDL edit types."""
    CUT = "C"
    DISSOLVE = "D"
    WIPE = "W"
    KEY = "K"

    @classmethod
    def from_string(cls, value: str) -> Optional['EditType']:
        """Get edit type from string."""
        mapping = {
            'C': cls.CUT,
            'D': cls.DISSOLVE,
            'W': cls.WIPE,
            'K': cls.KEY,
        }
        return mapping.get(value.upper())


class TrackType(Enum):
    """EDL track types."""
    VIDEO = "V"
    AUDIO = "A"
    AUDIO_1 = "A1"
    AUDIO_2 = "A2"
    AUDIO_3 = "A3"
    AUDIO_4 = "A4"
    VIDEO_AUDIO = "B"  # Both
    NONE = "NONE"

    @classmethod
    def from_string(cls, value: str) -> 'TrackType':
        """Get track type from string."""
        mapping = {
            'V': cls.VIDEO,
            'A': cls.AUDIO,
            'A1': cls.AUDIO_1,
            'A2': cls.AUDIO_2,
            'A3': cls.AUDIO_3,
            'A4': cls.AUDIO_4,
            'B': cls.VIDEO_AUDIO,
            'NONE': cls.NONE,
        }
        return mapping.get(value.upper(), cls.NONE)


@dataclass
class EDLEvent:
    """
    Represents a single EDL event (edit decision).

    Attributes:
        event_number: Event number in the EDL
        reel_name: Source reel/tape name
        track_type: Track type (V, A, A1, etc.)
        edit_type: Type of edit (C, D, W, K)
        source_in: Source in timecode
        source_out: Source out timecode
        record_in: Record in timecode
        record_out: Record out timecode
        clip_name: Optional clip name from comment
        comments: List of comment lines
        metadata: Additional metadata
    """
    event_number: int
    reel_name: str
    track_type: TrackType
    edit_type: EditType
    source_in: str
    source_out: str
    record_in: str
    record_out: str
    clip_name: Optional[str] = None
    comments: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EDLInfo:
    """
    Information about an EDL file.

    Attributes:
        title: EDL title
        fcm: Frame code mode (DROP FRAME or NON-DROP FRAME)
        events: List of EDL events
        metadata: Additional metadata
    """
    title: str = "UNTITLED"
    fcm: str = "NON-DROP FRAME"
    events: List[EDLEvent] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class EDLParser:
    """Parser for CMX 3600 EDL files."""

    # Regex patterns for EDL parsing
    TITLE_PATTERN = re.compile(r'^TITLE:\s*(.+)$')
    FCM_PATTERN = re.compile(r'^FCM:\s*(.+)$')
    EVENT_PATTERN = re.compile(
        r'^(\d+)\s+(\S+)\s+(\S+)\s+(\S+)(?:\s+\d+)?\s+'
        r'(\d{2}:\d{2}:\d{2}:\d{2})\s+'
        r'(\d{2}:\d{2}:\d{2}:\d{2})\s+'
        r'(\d{2}:\d{2}:\d{2}:\d{2})\s+'
        r'(\d{2}:\d{2}:\d{2}:\d{2})'
    )
    COMMENT_PATTERN = re.compile(r'^\*\s*(.+)$')
    CLIP_NAME_PATTERN = re.compile(r'^\*\s*FROM CLIP NAME:\s*(.+)$', re.IGNORECASE)
    SOURCE_FILE_PATTERN = re.compile(r'^\*\s*SOURCE FILE:\s*(.+)$', re.IGNORECASE)

    def __init__(self):
        """Initialize the EDL parser."""
        self.logger = get_logger(__name__)

    def parse_file(self, file_path: Path) -> EDLInfo:
        """
        Parse an EDL file.

        Args:
            file_path: Path to EDL file

        Returns:
            EDLInfo object with parsed data

        Raises:
            ValueError: If EDL format is invalid
        """
        if not file_path.exists():
            raise ValueError(f"EDL file not found: {file_path}")

        self.logger.info(f"Parsing EDL file: {file_path}")

        edl_info = EDLInfo()
        current_event = None

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.rstrip()

                # Skip empty lines
                if not line:
                    continue

                # Parse title
                match = self.TITLE_PATTERN.match(line)
                if match:
                    edl_info.title = match.group(1).strip()
                    self.logger.debug(f"Found title: {edl_info.title}")
                    continue

                # Parse FCM
                match = self.FCM_PATTERN.match(line)
                if match:
                    edl_info.fcm = match.group(1).strip()
                    self.logger.debug(f"Found FCM: {edl_info.fcm}")
                    continue

                # Parse event
                match = self.EVENT_PATTERN.match(line)
                if match:
                    # Save previous event if exists
                    if current_event:
                        edl_info.events.append(current_event)

                    # Create new event
                    event_num = int(match.group(1))
                    reel = match.group(2)
                    track = TrackType.from_string(match.group(3))
                    edit = EditType.from_string(match.group(4))

                    current_event = EDLEvent(
                        event_number=event_num,
                        reel_name=reel,
                        track_type=track,
                        edit_type=edit if edit else EditType.CUT,
                        source_in=match.group(5),
                        source_out=match.group(6),
                        record_in=match.group(7),
                        record_out=match.group(8)
                    )

                    self.logger.debug(f"Found event {event_num}: {reel}")
                    continue

                # Parse comments
                match = self.COMMENT_PATTERN.match(line)
                if match and current_event:
                    comment = match.group(1)
                    current_event.comments.append(comment)

                    # Check for clip name
                    clip_match = self.CLIP_NAME_PATTERN.match(line)
                    if clip_match:
                        current_event.clip_name = clip_match.group(1).strip()
                        self.logger.debug(f"Found clip name: {current_event.clip_name}")

                    # Check for source file
                    source_match = self.SOURCE_FILE_PATTERN.match(line)
                    if source_match:
                        current_event.metadata['source_file'] = source_match.group(1).strip()

        # Add final event
        if current_event:
            edl_info.events.append(current_event)

        self.logger.info(f"Parsed {len(edl_info.events)} events from EDL")

        return edl_info

    def parse_string(self, edl_content: str) -> EDLInfo:
        """
        Parse EDL content from a string.

        Args:
            edl_content: EDL content as string

        Returns:
            EDLInfo object with parsed data
        """
        # Create temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.edl', delete=False) as f:
            f.write(edl_content)
            temp_path = Path(f.name)

        try:
            return self.parse_file(temp_path)
        finally:
            temp_path.unlink()


class EDLWriter:
    """Writer for CMX 3600 EDL files."""

    def __init__(self):
        """Initialize the EDL writer."""
        self.logger = get_logger(__name__)

    def write_file(
        self,
        edl_info: EDLInfo,
        file_path: Path,
        include_comments: bool = True
    ) -> None:
        """
        Write EDL to file.

        Args:
            edl_info: EDL information to write
            file_path: Destination file path
            include_comments: Whether to include comments
        """
        self.logger.info(f"Writing EDL to: {file_path}")

        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"TITLE: {edl_info.title}\n")
            f.write(f"FCM: {edl_info.fcm}\n")
            f.write("\n")

            # Write events
            for event in edl_info.events:
                # Write event line
                f.write(
                    f"{event.event_number:03d}  {event.reel_name:<8s} "
                    f"{event.track_type.value:<4s} {event.edit_type.value:<4s} "
                    f"{event.source_in} {event.source_out} "
                    f"{event.record_in} {event.record_out}\n"
                )

                # Write comments if enabled
                if include_comments:
                    # Write clip name if available
                    if event.clip_name:
                        f.write(f"* FROM CLIP NAME: {event.clip_name}\n")

                    # Write source file if available
                    if 'source_file' in event.metadata:
                        f.write(f"* SOURCE FILE: {event.metadata['source_file']}\n")

                    # Write other comments
                    for comment in event.comments:
                        if not comment.upper().startswith('FROM CLIP NAME:') and \
                           not comment.upper().startswith('SOURCE FILE:'):
                            f.write(f"* {comment}\n")

                f.write("\n")

        self.logger.info(f"Successfully wrote {len(edl_info.events)} events to EDL")

    def to_string(self, edl_info: EDLInfo, include_comments: bool = True) -> str:
        """
        Convert EDL to string.

        Args:
            edl_info: EDL information to write
            include_comments: Whether to include comments

        Returns:
            EDL content as string
        """
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.edl', delete=False) as f:
            temp_path = Path(f.name)

        try:
            self.write_file(edl_info, temp_path, include_comments)
            return temp_path.read_text(encoding='utf-8')
        finally:
            temp_path.unlink()


class EDLConverter:
    """Convert between OTIO Timeline and EDL format."""

    def __init__(self):
        """Initialize the EDL converter."""
        self.logger = get_logger(__name__)
        self.parser = EDLParser()
        self.writer = EDLWriter()

    def timeline_to_edl(
        self,
        timeline: otio.schema.Timeline,
        title: Optional[str] = None,
        fcm: str = "NON-DROP FRAME",
        use_clip_names: bool = True
    ) -> EDLInfo:
        """
        Convert OTIO Timeline to EDL format.

        Args:
            timeline: OTIO timeline
            title: EDL title (uses timeline name if not provided)
            fcm: Frame code mode
            use_clip_names: Whether to include clip names in comments

        Returns:
            EDLInfo object
        """
        self.logger.info(f"Converting timeline to EDL: {timeline.name}")

        edl_info = EDLInfo(
            title=title or timeline.name or "UNTITLED",
            fcm=fcm
        )

        event_num = 1

        # Process video tracks
        for track in timeline.tracks:
            if track.kind != otio.schema.TrackKind.Video:
                continue

            for item in track:
                if isinstance(item, otio.schema.Clip):
                    event = self._clip_to_event(
                        item,
                        event_num,
                        TrackType.VIDEO,
                        use_clip_names
                    )
                    if event:
                        edl_info.events.append(event)
                        event_num += 1

                elif isinstance(item, otio.schema.Transition):
                    event = self._transition_to_event(
                        item,
                        event_num,
                        TrackType.VIDEO
                    )
                    if event:
                        edl_info.events.append(event)
                        event_num += 1

        self.logger.info(f"Converted {len(edl_info.events)} events to EDL")

        return edl_info

    def _clip_to_event(
        self,
        clip: otio.schema.Clip,
        event_num: int,
        track_type: TrackType,
        use_clip_names: bool
    ) -> Optional[EDLEvent]:
        """Convert a clip to an EDL event."""
        if not clip.source_range:
            self.logger.warning(f"Clip '{clip.name}' has no source range, skipping")
            return None

        # Get reel name from metadata or use clip name
        reel_name = "AX"  # Default
        if "cmx_3600" in clip.metadata:
            reel_name = clip.metadata["cmx_3600"].get("reel", "AX")

        # Format timecodes
        source_in = self._format_timecode(clip.source_range.start_time)
        source_out = self._format_timecode(clip.source_range.end_time_exclusive())

        # Get record timecodes from range in parent
        record_in = self._format_timecode(clip.range_in_parent().start_time)
        record_out = self._format_timecode(clip.range_in_parent().end_time_exclusive())

        event = EDLEvent(
            event_number=event_num,
            reel_name=reel_name[:8],  # Max 8 characters
            track_type=track_type,
            edit_type=EditType.CUT,
            source_in=source_in,
            source_out=source_out,
            record_in=record_in,
            record_out=record_out
        )

        # Add clip name as comment
        if use_clip_names and clip.name:
            event.clip_name = clip.name

        # Add source file from media reference
        if clip.media_reference and isinstance(
            clip.media_reference, otio.schema.ExternalReference
        ):
            if clip.media_reference.target_url:
                event.metadata['source_file'] = clip.media_reference.target_url

        return event

    def _transition_to_event(
        self,
        transition: otio.schema.Transition,
        event_num: int,
        track_type: TrackType
    ) -> Optional[EDLEvent]:
        """Convert a transition to an EDL event."""
        # For now, we'll skip transitions as they require special handling
        # In a full implementation, you'd create dissolve events
        self.logger.debug(f"Transition '{transition.name}' - special handling needed")
        return None

    def _format_timecode(self, rational_time: otio.opentime.RationalTime) -> str:
        """
        Format RationalTime as EDL timecode (HH:MM:SS:FF).

        Args:
            rational_time: Time to format

        Returns:
            Timecode string
        """
        total_frames = int(rational_time.value)
        rate = int(rational_time.rate)

        frames = total_frames % rate
        total_seconds = total_frames // rate
        seconds = total_seconds % 60
        total_minutes = total_seconds // 60
        minutes = total_minutes % 60
        hours = total_minutes // 60

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"

    def edl_to_timeline(
        self,
        edl_info: EDLInfo,
        fps: float = 24.0
    ) -> otio.schema.Timeline:
        """
        Convert EDL to OTIO Timeline.

        Args:
            edl_info: EDL information
            fps: Frame rate for timeline

        Returns:
            OTIO Timeline object
        """
        self.logger.info(f"Converting EDL to timeline: {edl_info.title}")

        timeline = otio.schema.Timeline(name=edl_info.title)
        video_track = otio.schema.Track(
            name="V1",
            kind=otio.schema.TrackKind.Video
        )

        for event in edl_info.events:
            if event.track_type == TrackType.VIDEO or \
               event.track_type == TrackType.VIDEO_AUDIO:
                clip = self._event_to_clip(event, fps)
                if clip:
                    video_track.append(clip)

        timeline.tracks.append(video_track)

        self.logger.info(f"Converted EDL to timeline with {len(video_track)} clips")

        return timeline

    def _event_to_clip(
        self,
        event: EDLEvent,
        fps: float
    ) -> Optional[otio.schema.Clip]:
        """Convert an EDL event to a clip."""
        try:
            # Parse timecodes
            source_in = self._parse_timecode(event.source_in, fps)
            source_out = self._parse_timecode(event.source_out, fps)

            # Create clip
            clip = otio.schema.Clip(
                name=event.clip_name or f"Event_{event.event_number:03d}",
                source_range=otio.opentime.TimeRange(
                    start_time=source_in,
                    duration=source_out - source_in
                )
            )

            # Add metadata
            clip.metadata["cmx_3600"] = {
                "reel": event.reel_name,
                "event_number": event.event_number,
                "comments": event.comments
            }

            # Add media reference if source file is available
            if 'source_file' in event.metadata:
                clip.media_reference = otio.schema.ExternalReference(
                    target_url=event.metadata['source_file']
                )

            return clip

        except Exception as e:
            self.logger.error(f"Error converting event {event.event_number}: {e}")
            return None

    def _parse_timecode(self, tc_str: str, fps: float) -> otio.opentime.RationalTime:
        """
        Parse EDL timecode string to RationalTime.

        Args:
            tc_str: Timecode string (HH:MM:SS:FF)
            fps: Frame rate

        Returns:
            RationalTime object
        """
        parts = tc_str.split(':')
        if len(parts) != 4:
            raise ValueError(f"Invalid timecode format: {tc_str}")

        hours, minutes, seconds, frames = map(int, parts)

        total_frames = (
            (hours * 3600 + minutes * 60 + seconds) * int(fps) + frames
        )

        return otio.opentime.RationalTime(total_frames, fps)


def validate_edl_file(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate an EDL file.

    Args:
        file_path: Path to EDL file

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    try:
        parser = EDLParser()
        edl_info = parser.parse_file(file_path)

        # Check for events
        if not edl_info.events:
            errors.append("No events found in EDL")

        # Check for duplicate event numbers
        event_nums = [e.event_number for e in edl_info.events]
        if len(event_nums) != len(set(event_nums)):
            errors.append("Duplicate event numbers found")

        # Validate timecodes and check durations
        for event in edl_info.events:
            try:
                # Check format
                if not re.match(r'\d{2}:\d{2}:\d{2}:\d{2}', event.source_in):
                    errors.append(
                        f"Event {event.event_number}: Invalid source in timecode"
                    )
                if not re.match(r'\d{2}:\d{2}:\d{2}:\d{2}', event.source_out):
                    errors.append(
                        f"Event {event.event_number}: Invalid source out timecode"
                    )

                # Check for duration mismatches
                src_frames = _tc_to_frames(event.source_out) - _tc_to_frames(event.source_in)
                rec_frames = _tc_to_frames(event.record_out) - _tc_to_frames(event.record_in)

                if src_frames != rec_frames:
                    errors.append(
                        f"Event {event.event_number} ({event.clip_name or event.reel_name}): "
                        f"Duration mismatch - Source: {src_frames}f, Record: {rec_frames}f "
                        f"(difference: {abs(src_frames - rec_frames)}f)"
                    )

            except Exception as e:
                errors.append(
                    f"Event {event.event_number}: Timecode validation error: {e}"
                )

    except Exception as e:
        errors.append(f"Failed to parse EDL: {e}")

    return (len(errors) == 0, errors)


def _tc_to_frames(tc_str: str, fps: int = 24) -> int:
    """
    Convert timecode string to frame count.

    Args:
        tc_str: Timecode string (HH:MM:SS:FF)
        fps: Frames per second (default: 24)

    Returns:
        Total frame count
    """
    try:
        parts = tc_str.split(':')
        if len(parts) != 4:
            return 0
        hours, minutes, seconds, frames = map(int, parts)
        return (hours * 3600 + minutes * 60 + seconds) * fps + frames
    except:
        return 0


def analyze_edl_duration_issues(file_path: Path) -> Dict[str, Any]:
    """
    Analyze an EDL file for duration mismatch issues.

    This is helpful for diagnosing OTIO import failures caused by
    source/record duration mismatches.

    Args:
        file_path: Path to EDL file

    Returns:
        Dictionary containing:
            - total_events: Total number of events
            - issues: List of events with duration mismatches
            - suggestions: List of recommendations
    """
    logger.info(f"Analyzing EDL for duration issues: {file_path}")

    result = {
        "file": str(file_path),
        "total_events": 0,
        "issues": [],
        "suggestions": []
    }

    try:
        parser = EDLParser()
        edl_info = parser.parse_file(file_path)
        result["total_events"] = len(edl_info.events)

        # Check each event for duration mismatches
        for event in edl_info.events:
            src_frames = _tc_to_frames(event.source_out) - _tc_to_frames(event.source_in)
            rec_frames = _tc_to_frames(event.record_out) - _tc_to_frames(event.record_in)

            if src_frames != rec_frames:
                result["issues"].append({
                    "event_number": event.event_number,
                    "clip_name": event.clip_name or event.reel_name,
                    "source_duration": src_frames,
                    "record_duration": rec_frames,
                    "difference": abs(src_frames - rec_frames),
                    "source_in": event.source_in,
                    "source_out": event.source_out,
                    "record_in": event.record_in,
                    "record_out": event.record_out
                })

        # Generate suggestions
        if result["issues"]:
            result["suggestions"] = [
                "Re-export the EDL from your NLE without handles or additional frames",
                "Check if any clips have speed changes or freeze frames applied",
                "Try exporting as AAF or FCP XML instead (more robust formats)",
                "Manually edit the EDL to match source and record durations",
                "Check your NLE's EDL export settings for compatibility mode"
            ]

    except Exception as e:
        logger.error(f"Error analyzing EDL: {e}")
        result["error"] = str(e)

    return result


def print_edl_analysis(analysis: Dict[str, Any]) -> None:
    """
    Print a formatted EDL analysis report.

    Args:
        analysis: Analysis results from analyze_edl_duration_issues()
    """
    print("=" * 70)
    print("EDL DURATION ANALYSIS REPORT")
    print("=" * 70)

    if "error" in analysis:
        print(f"\nERROR: {analysis['error']}")
        return

    print(f"\nFile: {analysis['file']}")
    print(f"Total Events: {analysis['total_events']}")
    print(f"Issues Found: {len(analysis['issues'])}")

    if analysis['issues']:
        print("\nDURATION MISMATCHES:")
        print("-" * 70)
        for issue in analysis['issues']:
            print(f"\nEvent {issue['event_number']}: {issue['clip_name']}")
            print(f"  Source Duration:  {issue['source_duration']} frames")
            print(f"  Record Duration:  {issue['record_duration']} frames")
            print(f"  Difference:       {issue['difference']} frames")
            print(f"  Source: {issue['source_in']} -> {issue['source_out']}")
            print(f"  Record: {issue['record_in']} -> {issue['record_out']}")

        print("\nRECOMMENDATIONS:")
        print("-" * 70)
        for i, suggestion in enumerate(analysis['suggestions'], 1):
            print(f"  {i}. {suggestion}")

    else:
        print("\n✓ No duration mismatch issues found!")

    print("=" * 70)
