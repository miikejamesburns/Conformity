"""
Unit tests for timeline editor.
"""

import pytest
import sys
from pathlib import Path
import opentimelineio as otio

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from conformity.timeline_editor import (
    TimelineEditor,
    split_clip,
    trim_clip,
    copy_clip,
    paste_clip,
    duplicate_clip,
    delete_clip,
    add_track,
    remove_track,
    reorder_tracks,
    find_gaps,
    remove_gaps,
    insert_gap,
)


class TestClipOperations:
    """Tests for clip manipulation operations."""

    def setup_method(self):
        """Setup test fixtures."""
        self.timeline = otio.schema.Timeline(name="Test Timeline")
        self.track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)
        self.timeline.tracks.append(self.track)

        # Create test clip
        self.clip = otio.schema.Clip(
            name="Test Clip",
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(120, 24)  # 5 seconds
            )
        )
        self.track.append(self.clip)

    def test_split_clip(self):
        """Test splitting a clip."""
        split_time = otio.opentime.RationalTime(60, 24)  # 2.5 seconds

        result = split_clip(self.track, self.clip, split_time)

        assert result is not None
        first_clip, second_clip = result

        # Check split was successful
        assert first_clip.name == "Test Clip_A"
        assert second_clip.name == "Test Clip_B"

        # Check durations
        assert first_clip.duration() == split_time
        assert second_clip.duration() == otio.opentime.RationalTime(60, 24)

        # Check track has both clips
        assert len(self.track) == 2

    def test_trim_clip(self):
        """Test trimming a clip."""
        new_in = otio.opentime.RationalTime(10, 24)
        new_out = otio.opentime.RationalTime(100, 24)

        success = trim_clip(self.clip, new_in, new_out)

        assert success
        assert self.clip.source_range.start_time == new_in
        assert self.clip.source_range.duration == (new_out - new_in)

    def test_copy_clip(self):
        """Test copying a clip."""
        clip_copy = copy_clip(self.clip)

        assert clip_copy is not None
        assert clip_copy.name == self.clip.name
        assert clip_copy != self.clip  # Different objects
        assert clip_copy.source_range.duration == self.clip.source_range.duration

    def test_paste_clip(self):
        """Test pasting a clip."""
        clip_copy = copy_clip(self.clip)

        success = paste_clip(self.track, clip_copy, index=1)

        assert success
        assert len(self.track) == 2

    def test_duplicate_clip(self):
        """Test duplicating a clip."""
        duplicates = duplicate_clip(self.track, self.clip, count=2)

        assert len(duplicates) == 2
        assert len(self.track) == 3  # Original + 2 duplicates

        # Check names
        assert duplicates[0].name == "Test Clip_copy1"
        assert duplicates[1].name == "Test Clip_copy2"

    def test_delete_clip(self):
        """Test deleting a clip."""
        success = delete_clip(self.track, self.clip, close_gap=True)

        assert success
        assert len(self.track) == 0

    def test_delete_clip_with_gap(self):
        """Test deleting a clip and leaving gap."""
        success = delete_clip(self.track, self.clip, close_gap=False)

        assert success
        assert len(self.track) == 1
        assert isinstance(self.track[0], otio.schema.Gap)


class TestTrackOperations:
    """Tests for track management operations."""

    def setup_method(self):
        """Setup test fixtures."""
        self.timeline = otio.schema.Timeline(name="Test Timeline")

    def test_add_track(self):
        """Test adding a track."""
        track = add_track(self.timeline, name="V1", kind=otio.schema.TrackKind.Video)

        assert track is not None
        assert track.name == "V1"
        assert track.kind == otio.schema.TrackKind.Video
        assert len(self.timeline.tracks) == 1

    def test_add_track_auto_name(self):
        """Test adding track with auto-generated name."""
        track1 = add_track(self.timeline, kind=otio.schema.TrackKind.Video)
        track2 = add_track(self.timeline, kind=otio.schema.TrackKind.Video)

        assert track1.name == "V1"
        assert track2.name == "V2"

    def test_remove_track(self):
        """Test removing a track."""
        track = add_track(self.timeline, name="V1")

        success = remove_track(self.timeline, track)

        assert success
        assert len(self.timeline.tracks) == 0

    def test_reorder_tracks(self):
        """Test reordering tracks."""
        track1 = add_track(self.timeline, name="V1")
        track2 = add_track(self.timeline, name="V2")
        track3 = add_track(self.timeline, name="V3")

        # Move track3 to index 0
        success = reorder_tracks(self.timeline, track3, 0)

        assert success
        assert self.timeline.tracks[0] == track3
        assert self.timeline.tracks[1] == track1
        assert self.timeline.tracks[2] == track2


class TestGapOperations:
    """Tests for gap management operations."""

    def setup_method(self):
        """Setup test fixtures."""
        self.timeline = otio.schema.Timeline(name="Test Timeline")
        self.track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)
        self.timeline.tracks.append(self.track)

    def test_find_gaps(self):
        """Test finding gaps in track."""
        # Add clip
        clip = otio.schema.Clip(
            name="Clip 1",
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(48, 24)
            )
        )
        self.track.append(clip)

        # Add gap
        gap = otio.schema.Gap(
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(24, 24)
            )
        )
        self.track.append(gap)

        # Find gaps
        gaps = find_gaps(self.track)

        assert len(gaps) == 1
        assert gaps[0][1] == gap

    def test_remove_gaps(self):
        """Test removing gaps from track."""
        # Add clips and gaps
        clip1 = otio.schema.Clip(
            name="Clip 1",
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(24, 24)
            )
        )
        self.track.append(clip1)

        gap = otio.schema.Gap(
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(12, 24)
            )
        )
        self.track.append(gap)

        clip2 = otio.schema.Clip(
            name="Clip 2",
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(24, 24)
            )
        )
        self.track.append(clip2)

        # Remove gaps
        count = remove_gaps(self.track)

        assert count == 1
        assert len(self.track) == 2

    def test_insert_gap(self):
        """Test inserting a gap."""
        # Add clip
        clip = otio.schema.Clip(
            name="Clip",
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(24, 24)
            )
        )
        self.track.append(clip)

        # Insert gap at start
        gap_duration = otio.opentime.RationalTime(12, 24)
        success = insert_gap(self.track, 0, gap_duration)

        assert success
        assert len(self.track) == 2
        assert isinstance(self.track[0], otio.schema.Gap)


class TestTimelineEditor:
    """Tests for Timeline Editor with undo/redo."""

    def setup_method(self):
        """Setup test fixtures."""
        self.timeline = otio.schema.Timeline(name="Test Timeline")
        self.track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)
        self.timeline.tracks.append(self.track)

        self.clip = otio.schema.Clip(
            name="Test Clip",
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(120, 24)
            )
        )
        self.track.append(self.clip)

        self.editor = TimelineEditor(self.timeline)

    def test_ripple_edit(self):
        """Test ripple edit operation."""
        new_duration = otio.opentime.RationalTime(96, 24)  # 4 seconds

        success = self.editor.ripple_edit(
            self.track,
            self.clip,
            new_duration,
            ripple_following=True
        )

        assert success
        assert self.clip.duration() == new_duration

    def test_undo_redo(self):
        """Test undo/redo functionality."""
        original_duration = self.clip.duration()
        new_duration = otio.opentime.RationalTime(96, 24)

        # Perform edit
        self.editor.ripple_edit(self.track, self.clip, new_duration)
        assert self.clip.duration() == new_duration

        # Undo
        self.editor.undo()
        assert self.clip.duration() == original_duration

        # Redo
        self.editor.redo()
        assert self.clip.duration() == new_duration

    def test_can_undo_redo(self):
        """Test undo/redo availability checks."""
        assert not self.editor.can_undo()
        assert not self.editor.can_redo()

        # Perform edit
        self.editor.ripple_edit(
            self.track,
            self.clip,
            otio.opentime.RationalTime(96, 24)
        )

        assert self.editor.can_undo()
        assert not self.editor.can_redo()

        # Undo
        self.editor.undo()

        assert not self.editor.can_undo()
        assert self.editor.can_redo()

    def test_slip_edit(self):
        """Test slip edit operation."""
        offset = otio.opentime.RationalTime(12, 24)

        success = self.editor.slip_edit(self.track, self.clip, offset)

        assert success
        # Duration should remain the same
        assert self.clip.duration() == otio.opentime.RationalTime(120, 24)
        # Source start should be offset
        assert self.clip.source_range.start_time == offset


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def setup_method(self):
        """Setup test fixtures."""
        self.timeline = otio.schema.Timeline(name="Test Timeline")
        self.track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)
        self.timeline.tracks.append(self.track)

    def test_split_invalid_time(self):
        """Test splitting with invalid time."""
        clip = otio.schema.Clip(
            name="Clip",
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(24, 24)
            )
        )
        self.track.append(clip)

        # Try to split outside clip range
        result = split_clip(
            self.track,
            clip,
            otio.opentime.RationalTime(100, 24)
        )

        assert result is None

    def test_trim_invalid_range(self):
        """Test trimming with invalid range."""
        clip = otio.schema.Clip(
            name="Clip",
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(24, 24)
            )
        )

        # Try to trim with in > out
        success = trim_clip(
            clip,
            new_in=otio.opentime.RationalTime(20, 24),
            new_out=otio.opentime.RationalTime(10, 24)
        )

        assert not success

    def test_remove_nonexistent_track(self):
        """Test removing non-existent track."""
        fake_track = otio.schema.Track(name="Fake", kind=otio.schema.TrackKind.Video)

        success = remove_track(self.timeline, fake_track)

        assert not success
