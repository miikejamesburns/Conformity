"""
Track management operations.

Provides track-level editing tools:
- Add/Remove tracks
- Reorder tracks
- Merge tracks
- Lock/Unlock tracks
- Mute/Solo tracks
"""

import copy
from typing import Optional, List
import opentimelineio as otio

from ..core.logger import get_logger

logger = get_logger(__name__)


def add_track(
    timeline: otio.schema.Timeline,
    name: Optional[str] = None,
    kind: otio.schema.TrackKind = otio.schema.TrackKind.Video,
    index: Optional[int] = None
) -> otio.schema.Track:
    """
    Add a new track to timeline.

    Args:
        timeline: Timeline to modify
        name: Track name (auto-generated if None)
        kind: Track kind (Video/Audio)
        index: Position to insert (None = append)

    Returns:
        The created track
    """
    try:
        # Auto-generate name if not provided
        if name is None:
            kind_prefix = "V" if kind == otio.schema.TrackKind.Video else "A"
            existing_count = sum(1 for t in timeline.tracks if t.kind == kind)
            name = f"{kind_prefix}{existing_count + 1}"

        # Create track
        track = otio.schema.Track(name=name, kind=kind)

        # Add to timeline
        if index is None:
            timeline.tracks.append(track)
        else:
            timeline.tracks.insert(index, track)

        logger.info(f"Added track '{name}' at index {index if index is not None else len(timeline.tracks)-1}")
        return track

    except Exception as e:
        logger.error(f"Add track failed: {e}")
        return None


def remove_track(
    timeline: otio.schema.Timeline,
    track: otio.schema.Track
) -> bool:
    """
    Remove a track from timeline.

    Args:
        timeline: Timeline to modify
        track: Track to remove

    Returns:
        True if successful
    """
    try:
        if track in timeline.tracks:
            timeline.tracks.remove(track)
            logger.info(f"Removed track '{track.name}'")
            return True
        else:
            logger.error("Track not found in timeline")
            return False

    except Exception as e:
        logger.error(f"Remove track failed: {e}")
        return False


def reorder_tracks(
    timeline: otio.schema.Timeline,
    track: otio.schema.Track,
    new_index: int
) -> bool:
    """
    Reorder tracks in timeline.

    Args:
        timeline: Timeline to modify
        track: Track to move
        new_index: New position

    Returns:
        True if successful
    """
    try:
        # Find current index
        try:
            current_index = timeline.tracks.index(track)
        except ValueError:
            logger.error("Track not found in timeline")
            return False

        # Validate new index
        if new_index < 0 or new_index >= len(timeline.tracks):
            logger.error(f"Invalid index: {new_index}")
            return False

        # Remove and reinsert
        timeline.tracks.pop(current_index)
        timeline.tracks.insert(new_index, track)

        logger.info(f"Moved track '{track.name}' from index {current_index} to {new_index}")
        return True

    except Exception as e:
        logger.error(f"Reorder tracks failed: {e}")
        return False


def duplicate_track(
    timeline: otio.schema.Timeline,
    track: otio.schema.Track,
    new_name: Optional[str] = None
) -> Optional[otio.schema.Track]:
    """
    Duplicate a track with all its contents.

    Args:
        timeline: Timeline to modify
        track: Track to duplicate
        new_name: Name for new track (auto-generated if None)

    Returns:
        The duplicated track if successful, None otherwise
    """
    try:
        # Create deep copy
        new_track = copy.deepcopy(track)

        # Set name
        if new_name:
            new_track.name = new_name
        else:
            new_track.name = f"{track.name}_copy"

        # Add to timeline
        track_index = timeline.tracks.index(track)
        timeline.tracks.insert(track_index + 1, new_track)

        logger.info(f"Duplicated track '{track.name}' as '{new_track.name}'")
        return new_track

    except Exception as e:
        logger.error(f"Duplicate track failed: {e}")
        return None


def merge_tracks(
    timeline: otio.schema.Timeline,
    tracks: List[otio.schema.Track],
    name: Optional[str] = None,
    remove_source: bool = False
) -> Optional[otio.schema.Track]:
    """
    Merge multiple tracks into one.

    Args:
        timeline: Timeline to modify
        tracks: Tracks to merge
        name: Name for merged track (auto-generated if None)
        remove_source: If True, remove source tracks after merge

    Returns:
        The merged track if successful, None otherwise
    """
    try:
        if not tracks:
            logger.error("No tracks to merge")
            return None

        # Use first track's kind
        kind = tracks[0].kind

        # Create new track
        if name is None:
            name = f"Merged_{tracks[0].name}"

        merged_track = otio.schema.Track(name=name, kind=kind)

        # Collect all clips from all tracks, sorted by timeline position
        all_items = []

        for track in tracks:
            # Verify all tracks are same kind
            if track.kind != kind:
                logger.warning(f"Track '{track.name}' has different kind, skipping")
                continue

            for item in track:
                all_items.append((item, track))

        # Add items to merged track
        # Note: This is a simplified merge that just concatenates
        # A more sophisticated implementation would handle overlaps
        for item, source_track in all_items:
            merged_track.append(copy.deepcopy(item))

        # Add merged track to timeline
        timeline.tracks.append(merged_track)

        # Remove source tracks if requested
        if remove_source:
            for track in tracks:
                if track in timeline.tracks:
                    timeline.tracks.remove(track)

        logger.info(f"Merged {len(tracks)} tracks into '{name}'")
        return merged_track

    except Exception as e:
        logger.error(f"Merge tracks failed: {e}")
        return None


def lock_track(track: otio.schema.Track, locked: bool = True) -> bool:
    """
    Lock or unlock a track.

    Args:
        track: Track to modify
        locked: True to lock, False to unlock

    Returns:
        True if successful
    """
    try:
        if 'locked' not in track.metadata:
            track.metadata['locked'] = {}

        track.metadata['locked']['enabled'] = locked

        logger.info(f"Track '{track.name}' {'locked' if locked else 'unlocked'}")
        return True

    except Exception as e:
        logger.error(f"Lock track failed: {e}")
        return False


def is_track_locked(track: otio.schema.Track) -> bool:
    """
    Check if track is locked.

    Args:
        track: Track to check

    Returns:
        True if locked
    """
    return track.metadata.get('locked', {}).get('enabled', False)


def mute_track(track: otio.schema.Track, muted: bool = True) -> bool:
    """
    Mute or unmute a track.

    Args:
        track: Track to modify
        muted: True to mute, False to unmute

    Returns:
        True if successful
    """
    try:
        if 'muted' not in track.metadata:
            track.metadata['muted'] = {}

        track.metadata['muted']['enabled'] = muted

        logger.info(f"Track '{track.name}' {'muted' if muted else 'unmuted'}")
        return True

    except Exception as e:
        logger.error(f"Mute track failed: {e}")
        return False


def solo_track(
    timeline: otio.schema.Timeline,
    track: otio.schema.Track,
    solo: bool = True
) -> bool:
    """
    Solo a track (mute all others of same kind).

    Args:
        timeline: Timeline containing the track
        track: Track to solo
        solo: True to solo, False to unsolo

    Returns:
        True if successful
    """
    try:
        if solo:
            # Mute all tracks of same kind except this one
            for t in timeline.tracks:
                if t.kind == track.kind:
                    if t == track:
                        mute_track(t, False)
                    else:
                        mute_track(t, True)
        else:
            # Unmute all tracks
            for t in timeline.tracks:
                if t.kind == track.kind:
                    mute_track(t, False)

        logger.info(f"Track '{track.name}' {'soloed' if solo else 'unsoloed'}")
        return True

    except Exception as e:
        logger.error(f"Solo track failed: {e}")
        return False


def rename_track(track: otio.schema.Track, new_name: str) -> bool:
    """
    Rename a track.

    Args:
        track: Track to rename
        new_name: New name

    Returns:
        True if successful
    """
    try:
        old_name = track.name
        track.name = new_name
        logger.info(f"Renamed track '{old_name}' to '{new_name}'")
        return True

    except Exception as e:
        logger.error(f"Rename track failed: {e}")
        return False


def get_video_tracks(timeline: otio.schema.Timeline) -> List[otio.schema.Track]:
    """
    Get all video tracks from timeline.

    Args:
        timeline: Timeline to query

    Returns:
        List of video tracks
    """
    return [t for t in timeline.tracks if t.kind == otio.schema.TrackKind.Video]


def get_audio_tracks(timeline: otio.schema.Timeline) -> List[otio.schema.Track]:
    """
    Get all audio tracks from timeline.

    Args:
        timeline: Timeline to query

    Returns:
        List of audio tracks
    """
    return [t for t in timeline.tracks if t.kind == otio.schema.TrackKind.Audio]


def clear_track(track: otio.schema.Track) -> bool:
    """
    Remove all items from a track.

    Args:
        track: Track to clear

    Returns:
        True if successful
    """
    try:
        count = len(track)
        track.clear()
        logger.info(f"Cleared {count} items from track '{track.name}'")
        return True

    except Exception as e:
        logger.error(f"Clear track failed: {e}")
        return False
