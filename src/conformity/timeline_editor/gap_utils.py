"""
Gap management utilities.

Provides tools for managing gaps (empty spaces) in timelines:
- Find gaps in tracks
- Remove gaps
- Insert gaps
- Close gaps
"""

from typing import List, Optional, Tuple
import opentimelineio as otio

from ..core.logger import get_logger

logger = get_logger(__name__)


def find_gaps(track: otio.schema.Track) -> List[Tuple[int, otio.schema.Gap]]:
    """
    Find all gaps in a track.

    Args:
        track: Track to search

    Returns:
        List of (index, gap) tuples
    """
    gaps = []

    for i, item in enumerate(track):
        if isinstance(item, otio.schema.Gap):
            gaps.append((i, item))

    logger.debug(f"Found {len(gaps)} gaps in track '{track.name}'")
    return gaps


def remove_gaps(
    track: otio.schema.Track,
    min_duration: Optional[otio.opentime.RationalTime] = None
) -> int:
    """
    Remove all gaps from a track.

    Args:
        track: Track to modify
        min_duration: Only remove gaps longer than this (None = remove all)

    Returns:
        Number of gaps removed
    """
    try:
        count = 0
        indices_to_remove = []

        for i, item in enumerate(track):
            if isinstance(item, otio.schema.Gap):
                # Check minimum duration if specified
                if min_duration is None or item.duration() >= min_duration:
                    indices_to_remove.append(i)
                    count += 1

        # Remove in reverse order to preserve indices
        for i in reversed(indices_to_remove):
            del track[i]

        logger.info(f"Removed {count} gaps from track '{track.name}'")
        return count

    except Exception as e:
        logger.error(f"Remove gaps failed: {e}")
        return 0


def insert_gap(
    track: otio.schema.Track,
    index: int,
    duration: otio.opentime.RationalTime
) -> bool:
    """
    Insert a gap at specified position.

    Args:
        track: Track to modify
        index: Position to insert gap
        duration: Duration of gap

    Returns:
        True if successful
    """
    try:
        if index < 0 or index > len(track):
            logger.error(f"Invalid index: {index}")
            return False

        # Get rate from track or use default
        if len(track) > 0:
            rate = track[0].duration().rate if hasattr(track[0], 'duration') else 24.0
        else:
            rate = 24.0

        gap = otio.schema.Gap(
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, rate),
                duration=duration
            )
        )

        track.insert(index, gap)
        logger.info(f"Inserted gap of {duration} at index {index} in track '{track.name}'")
        return True

    except Exception as e:
        logger.error(f"Insert gap failed: {e}")
        return False


def close_gap(
    track: otio.schema.Track,
    gap: otio.schema.Gap,
    ripple: bool = True
) -> bool:
    """
    Close a specific gap.

    Args:
        track: Track containing the gap
        gap: Gap to close
        ripple: If True, move following clips; if False, just remove gap

    Returns:
        True if successful
    """
    try:
        # Find gap index
        gap_index = None
        for i, item in enumerate(track):
            if item == gap:
                gap_index = i
                break

        if gap_index is None:
            logger.error("Gap not found in track")
            return False

        # Remove gap
        del track[gap_index]

        # If not rippling, insert empty gap
        if not ripple:
            insert_gap(track, gap_index, gap.duration())

        logger.info(f"Closed gap at index {gap_index} in track '{track.name}'")
        return True

    except Exception as e:
        logger.error(f"Close gap failed: {e}")
        return False


def consolidate_gaps(track: otio.schema.Track) -> int:
    """
    Merge adjacent gaps into single gaps.

    Args:
        track: Track to modify

    Returns:
        Number of gaps consolidated
    """
    try:
        count = 0
        i = 0

        while i < len(track) - 1:
            current = track[i]
            next_item = track[i + 1]

            # Check if both are gaps
            if isinstance(current, otio.schema.Gap) and isinstance(next_item, otio.schema.Gap):
                # Merge next gap into current
                new_duration = current.duration() + next_item.duration()

                current.source_range = otio.opentime.TimeRange(
                    start_time=current.source_range.start_time,
                    duration=new_duration
                )

                # Remove next gap
                del track[i + 1]
                count += 1

                # Don't increment i, check again from same position
            else:
                i += 1

        logger.info(f"Consolidated {count} adjacent gaps in track '{track.name}'")
        return count

    except Exception as e:
        logger.error(f"Consolidate gaps failed: {e}")
        return 0


def fill_gaps_with_black(
    track: otio.schema.Track,
    min_duration: Optional[otio.opentime.RationalTime] = None
) -> int:
    """
    Fill gaps with black/silence clips.

    Args:
        track: Track to modify
        min_duration: Only fill gaps longer than this (None = fill all)

    Returns:
        Number of gaps filled
    """
    try:
        count = 0
        indices_to_fill = []

        for i, item in enumerate(track):
            if isinstance(item, otio.schema.Gap):
                # Check minimum duration if specified
                if min_duration is None or item.duration() >= min_duration:
                    indices_to_fill.append((i, item))

        # Fill gaps (in reverse to preserve indices)
        for i, gap in reversed(indices_to_fill):
            # Create black/silence clip
            filler_name = "Black" if track.kind == otio.schema.TrackKind.Video else "Silence"

            filler = otio.schema.Clip(
                name=filler_name,
                source_range=gap.source_range
            )

            # Replace gap with filler
            track[i] = filler
            count += 1

        logger.info(f"Filled {count} gaps in track '{track.name}'")
        return count

    except Exception as e:
        logger.error(f"Fill gaps failed: {e}")
        return 0


def get_gap_duration(track: otio.schema.Track) -> otio.opentime.RationalTime:
    """
    Get total duration of all gaps in track.

    Args:
        track: Track to analyze

    Returns:
        Total gap duration
    """
    try:
        if not track:
            return otio.opentime.RationalTime(0, 24)

        total = otio.opentime.RationalTime(0, track[0].duration().rate if track else 24)

        for item in track:
            if isinstance(item, otio.schema.Gap):
                total += item.duration()

        return total

    except Exception as e:
        logger.error(f"Get gap duration failed: {e}")
        return otio.opentime.RationalTime(0, 24)


def has_gaps(track: otio.schema.Track) -> bool:
    """
    Check if track has any gaps.

    Args:
        track: Track to check

    Returns:
        True if track contains gaps
    """
    return any(isinstance(item, otio.schema.Gap) for item in track)


def split_gap(
    track: otio.schema.Track,
    gap: otio.schema.Gap,
    split_time: otio.opentime.RationalTime
) -> Optional[Tuple[otio.schema.Gap, otio.schema.Gap]]:
    """
    Split a gap into two gaps.

    Args:
        track: Track containing the gap
        gap: Gap to split
        split_time: Time (relative to gap start) to split at

    Returns:
        Tuple of (first_gap, second_gap) if successful, None otherwise
    """
    try:
        if not gap.source_range:
            logger.error("Gap has no source range")
            return None

        # Validate split time
        if split_time <= otio.opentime.RationalTime(0, gap.source_range.duration.rate) or \
           split_time >= gap.source_range.duration:
            logger.error("Invalid split time")
            return None

        # Find gap index
        gap_index = None
        for i, item in enumerate(track):
            if item == gap:
                gap_index = i
                break

        if gap_index is None:
            logger.error("Gap not found in track")
            return None

        # Create two gaps
        first_gap = otio.schema.Gap(
            source_range=otio.opentime.TimeRange(
                start_time=gap.source_range.start_time,
                duration=split_time
            )
        )

        second_gap = otio.schema.Gap(
            source_range=otio.opentime.TimeRange(
                start_time=gap.source_range.start_time + split_time,
                duration=gap.source_range.duration - split_time
            )
        )

        # Replace original gap with split gaps
        track[gap_index] = first_gap
        track.insert(gap_index + 1, second_gap)

        logger.info(f"Split gap at {split_time}")
        return (first_gap, second_gap)

    except Exception as e:
        logger.error(f"Split gap failed: {e}")
        return None
