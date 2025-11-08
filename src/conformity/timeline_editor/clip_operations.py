"""
Clip manipulation operations.

Provides clip-level editing tools:
- Split: Cut clip at a point
- Trim: Adjust in/out points
- Copy/Paste: Clipboard operations
- Duplicate: Create copy of clip
- Delete: Remove clip from track
"""

import copy
from typing import Optional, List
import opentimelineio as otio

from ..core.logger import get_logger

logger = get_logger(__name__)


def split_clip(
    track: otio.schema.Track,
    clip: otio.schema.Clip,
    split_time: otio.opentime.RationalTime
) -> Optional[tuple[otio.schema.Clip, otio.schema.Clip]]:
    """
    Split a clip at the specified time.

    Args:
        track: Track containing the clip
        clip: Clip to split
        split_time: Time (in clip's source) to split at

    Returns:
        Tuple of (first_clip, second_clip) if successful, None otherwise
    """
    try:
        if not clip.source_range:
            logger.error("Cannot split clip without source range")
            return None

        # Validate split time is within clip
        if split_time < clip.source_range.start_time or \
           split_time >= clip.source_range.end_time_exclusive():
            logger.error("Split time is outside clip range")
            return None

        # Find clip index in track
        clip_index = None
        for i, item in enumerate(track):
            if item == clip:
                clip_index = i
                break

        if clip_index is None:
            logger.error("Clip not found in track")
            return None

        # Create first half
        first_duration = split_time - clip.source_range.start_time
        first_clip = copy.deepcopy(clip)
        first_clip.name = f"{clip.name}_A"
        first_clip.source_range = otio.opentime.TimeRange(
            start_time=clip.source_range.start_time,
            duration=first_duration
        )

        # Create second half
        second_start = split_time
        second_duration = clip.source_range.end_time_exclusive() - split_time
        second_clip = copy.deepcopy(clip)
        second_clip.name = f"{clip.name}_B"
        second_clip.source_range = otio.opentime.TimeRange(
            start_time=second_start,
            duration=second_duration
        )

        # Replace original clip with split clips
        track[clip_index] = first_clip
        track.insert(clip_index + 1, second_clip)

        logger.info(f"Split clip '{clip.name}' at {split_time}")
        return (first_clip, second_clip)

    except Exception as e:
        logger.error(f"Split clip failed: {e}")
        return None


def trim_clip(
    clip: otio.schema.Clip,
    new_in: Optional[otio.opentime.RationalTime] = None,
    new_out: Optional[otio.opentime.RationalTime] = None
) -> bool:
    """
    Trim clip by adjusting in/out points.

    Args:
        clip: Clip to trim
        new_in: New in point (None to keep current)
        new_out: New out point (None to keep current)

    Returns:
        True if successful
    """
    try:
        if not clip.source_range:
            logger.error("Cannot trim clip without source range")
            return False

        # Use current values if not specified
        start_time = new_in if new_in is not None else clip.source_range.start_time
        end_time = new_out if new_out is not None else clip.source_range.end_time_exclusive()

        # Validate
        if start_time >= end_time:
            logger.error("Invalid trim: in point must be before out point")
            return False

        # Apply trim
        clip.source_range = otio.opentime.TimeRange(
            start_time=start_time,
            duration=end_time - start_time
        )

        logger.info(f"Trimmed clip '{clip.name}'")
        return True

    except Exception as e:
        logger.error(f"Trim clip failed: {e}")
        return False


def copy_clip(clip: otio.schema.Clip) -> otio.schema.Clip:
    """
    Create a deep copy of a clip.

    Args:
        clip: Clip to copy

    Returns:
        Copy of the clip
    """
    try:
        clip_copy = copy.deepcopy(clip)
        logger.info(f"Copied clip '{clip.name}'")
        return clip_copy

    except Exception as e:
        logger.error(f"Copy clip failed: {e}")
        return None


def paste_clip(
    track: otio.schema.Track,
    clip: otio.schema.Clip,
    index: Optional[int] = None
) -> bool:
    """
    Paste a clip into a track.

    Args:
        track: Target track
        clip: Clip to paste
        index: Position to insert (None = append to end)

    Returns:
        True if successful
    """
    try:
        clip_copy = copy.deepcopy(clip)

        if index is None:
            track.append(clip_copy)
        else:
            track.insert(index, clip_copy)

        logger.info(f"Pasted clip '{clip.name}' to track '{track.name}'")
        return True

    except Exception as e:
        logger.error(f"Paste clip failed: {e}")
        return False


def duplicate_clip(
    track: otio.schema.Track,
    clip: otio.schema.Clip,
    count: int = 1
) -> List[otio.schema.Clip]:
    """
    Duplicate a clip multiple times.

    Args:
        track: Track containing the clip
        clip: Clip to duplicate
        count: Number of duplicates to create

    Returns:
        List of duplicated clips
    """
    try:
        # Find clip index
        clip_index = None
        for i, item in enumerate(track):
            if item == clip:
                clip_index = i
                break

        if clip_index is None:
            logger.error("Clip not found in track")
            return []

        duplicates = []

        for i in range(count):
            dup = copy.deepcopy(clip)
            dup.name = f"{clip.name}_copy{i+1}"
            track.insert(clip_index + i + 1, dup)
            duplicates.append(dup)

        logger.info(f"Duplicated clip '{clip.name}' {count} time(s)")
        return duplicates

    except Exception as e:
        logger.error(f"Duplicate clip failed: {e}")
        return []


def delete_clip(
    track: otio.schema.Track,
    clip: otio.schema.Clip,
    close_gap: bool = False
) -> bool:
    """
    Delete a clip from a track.

    Args:
        track: Track containing the clip
        clip: Clip to delete
        close_gap: If True, remove resulting gap; if False, leave gap

    Returns:
        True if successful
    """
    try:
        # Find and remove clip
        for i, item in enumerate(track):
            if item == clip:
                if close_gap:
                    # Remove clip and shift following clips
                    del track[i]
                else:
                    # Replace with gap
                    gap = otio.schema.Gap(
                        source_range=clip.source_range
                    )
                    track[i] = gap

                logger.info(f"Deleted clip '{clip.name}'")
                return True

        logger.error("Clip not found in track")
        return False

    except Exception as e:
        logger.error(f"Delete clip failed: {e}")
        return False


def extract_clip(
    track: otio.schema.Track,
    clip: otio.schema.Clip
) -> Optional[otio.schema.Clip]:
    """
    Extract (remove and return) a clip from track.

    Args:
        track: Track containing the clip
        clip: Clip to extract

    Returns:
        Extracted clip if successful, None otherwise
    """
    try:
        for i, item in enumerate(track):
            if item == clip:
                extracted = track.pop(i)
                logger.info(f"Extracted clip '{clip.name}'")
                return extracted

        logger.error("Clip not found in track")
        return None

    except Exception as e:
        logger.error(f"Extract clip failed: {e}")
        return None


def replace_clip(
    track: otio.schema.Track,
    old_clip: otio.schema.Clip,
    new_clip: otio.schema.Clip,
    match_duration: bool = True
) -> bool:
    """
    Replace one clip with another.

    Args:
        track: Track containing the clip
        old_clip: Clip to replace
        new_clip: Replacement clip
        match_duration: If True, adjust new clip duration to match old clip

    Returns:
        True if successful
    """
    try:
        # Find clip index
        for i, item in enumerate(track):
            if item == old_clip:
                replacement = copy.deepcopy(new_clip)

                if match_duration and old_clip.source_range and replacement.source_range:
                    # Adjust duration to match
                    replacement.source_range = otio.opentime.TimeRange(
                        start_time=replacement.source_range.start_time,
                        duration=old_clip.source_range.duration
                    )

                track[i] = replacement
                logger.info(f"Replaced clip '{old_clip.name}' with '{new_clip.name}'")
                return True

        logger.error("Clip not found in track")
        return False

    except Exception as e:
        logger.error(f"Replace clip failed: {e}")
        return False


def move_clip(
    source_track: otio.schema.Track,
    dest_track: otio.schema.Track,
    clip: otio.schema.Clip,
    dest_index: Optional[int] = None
) -> bool:
    """
    Move a clip from one track to another.

    Args:
        source_track: Track containing the clip
        dest_track: Destination track
        clip: Clip to move
        dest_index: Position in destination track (None = append)

    Returns:
        True if successful
    """
    try:
        # Extract from source
        extracted = extract_clip(source_track, clip)
        if not extracted:
            return False

        # Insert in destination
        if dest_index is None:
            dest_track.append(extracted)
        else:
            dest_track.insert(dest_index, extracted)

        logger.info(f"Moved clip '{clip.name}' from '{source_track.name}' to '{dest_track.name}'")
        return True

    except Exception as e:
        logger.error(f"Move clip failed: {e}")
        return False


def reverse_clip(clip: otio.schema.Clip) -> bool:
    """
    Reverse clip playback direction.

    Note: This sets metadata to indicate reversal; actual reversal
    would be handled by playback engine.

    Args:
        clip: Clip to reverse

    Returns:
        True if successful
    """
    try:
        if 'reverse' not in clip.metadata:
            clip.metadata['reverse'] = {}

        # Toggle reverse flag
        current = clip.metadata['reverse'].get('enabled', False)
        clip.metadata['reverse']['enabled'] = not current

        logger.info(f"Reversed clip '{clip.name}': {not current}")
        return True

    except Exception as e:
        logger.error(f"Reverse clip failed: {e}")
        return False


def set_clip_speed(
    clip: otio.schema.Clip,
    speed: float
) -> bool:
    """
    Set clip playback speed.

    Args:
        clip: Clip to modify
        speed: Speed multiplier (1.0 = normal, 2.0 = double speed, 0.5 = half speed)

    Returns:
        True if successful
    """
    try:
        if speed <= 0:
            logger.error("Speed must be positive")
            return False

        if not clip.source_range:
            logger.error("Clip has no source range")
            return False

        # Store original duration if not already stored
        if 'speed' not in clip.metadata:
            clip.metadata['speed'] = {
                'original_duration': float(clip.source_range.duration.value),
                'original_rate': float(clip.source_range.duration.rate)
            }

        # Calculate new duration
        original_duration = clip.metadata['speed']['original_duration']
        new_duration_value = original_duration / speed

        clip.source_range = otio.opentime.TimeRange(
            start_time=clip.source_range.start_time,
            duration=otio.opentime.RationalTime(
                new_duration_value,
                clip.source_range.duration.rate
            )
        )

        clip.metadata['speed']['current'] = speed

        logger.info(f"Set clip '{clip.name}' speed to {speed}x")
        return True

    except Exception as e:
        logger.error(f"Set clip speed failed: {e}")
        return False
