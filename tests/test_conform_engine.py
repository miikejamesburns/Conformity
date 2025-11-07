"""
Unit tests for ConformEngine.
"""

import pytest
from pathlib import Path
import opentimelineio as otio
import sys
import tempfile

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from conformity.conform_engine.conform_engine import (
    ConformEngine, TimelineFormat, ClipInfo, TimelineInfo
)
from conformity.conform_engine.exceptions import (
    ConformError, ImportError, ExportError, AdapterNotFoundError
)


class TestConformEngine:
    """Tests for ConformEngine class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.engine = ConformEngine()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Cleanup test fixtures."""
        # Clean up temp files
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_engine_initialization(self):
        """Test engine initializes correctly."""
        assert self.engine is not None
        assert isinstance(self.engine._supported_adapters, list)

    def test_adapter_detection(self):
        """Test adapter detection."""
        # OTIO JSON adapter should always be available
        assert self.engine.is_adapter_available("otio_json")

    def test_create_simple_timeline(self):
        """Test creating a simple timeline for testing."""
        timeline = otio.schema.Timeline(name="Test Timeline")
        track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)

        # Create a clip
        clip = otio.schema.Clip(
            name="Test Clip",
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(100, 24)
            )
        )

        track.append(clip)
        timeline.tracks.append(track)

        assert timeline is not None
        assert len(timeline.tracks) == 1
        assert len(timeline.tracks[0]) == 1

    def test_parse_timeline(self):
        """Test parsing timeline structure."""
        # Create a test timeline
        timeline = otio.schema.Timeline(name="Test Timeline")
        track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)

        clip1 = otio.schema.Clip(
            name="Clip 1",
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(100, 24)
            )
        )
        clip2 = otio.schema.Clip(
            name="Clip 2",
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(50, 24)
            )
        )

        track.append(clip1)
        track.append(clip2)
        timeline.tracks.append(track)

        # Parse the timeline
        info = self.engine.parse_timeline(timeline)

        assert isinstance(info, TimelineInfo)
        assert info.name == "Test Timeline"
        assert info.num_tracks == 1
        assert info.num_clips == 2
        assert len(info.clips) == 2

    def test_parse_clip_with_media_reference(self):
        """Test parsing clip with external media reference."""
        timeline = otio.schema.Timeline(name="Test")
        track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)

        media_ref = otio.schema.ExternalReference(
            target_url="/path/to/media.mov"
        )

        clip = otio.schema.Clip(
            name="Media Clip",
            media_reference=media_ref,
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(100, 24)
            )
        )

        track.append(clip)
        timeline.tracks.append(track)

        info = self.engine.parse_timeline(timeline)

        assert len(info.clips) == 1
        assert info.clips[0].source_path == "/path/to/media.mov"
        assert info.clips[0].name == "Media Clip"

    def test_import_export_otio(self):
        """Test import and export of OTIO format."""
        # Create a test timeline
        timeline = otio.schema.Timeline(name="Export Test")
        track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)

        clip = otio.schema.Clip(
            name="Test Clip",
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(100, 24)
            )
        )

        track.append(clip)
        timeline.tracks.append(track)

        # Export the timeline
        export_path = self.temp_dir / "test_timeline.otio"
        self.engine.export_timeline(
            timeline,
            export_path,
            format=TimelineFormat.OTIO
        )

        assert export_path.exists()

        # Import it back
        imported_timeline, imported_info = self.engine.import_timeline(export_path)

        assert imported_timeline.name == "Export Test"
        assert imported_info.num_clips == 1
        assert imported_info.num_tracks == 1

    def test_export_nonexistent_adapter(self):
        """Test export with non-existent adapter raises error."""
        timeline = otio.schema.Timeline(name="Test")

        # Try to export with invalid adapter (if AAF is not available)
        if not self.engine.is_adapter_available("aaf"):
            export_path = self.temp_dir / "test.aaf"

            with pytest.raises((ExportError, AdapterNotFoundError)):
                self.engine.export_timeline(
                    timeline,
                    export_path,
                    format=TimelineFormat.AAF
                )

    def test_import_nonexistent_file(self):
        """Test import of non-existent file raises error."""
        nonexistent_path = self.temp_dir / "nonexistent.otio"

        with pytest.raises(ImportError):
            self.engine.import_timeline(nonexistent_path)

    def test_validate_timeline_basic(self):
        """Test timeline validation."""
        # Create a valid timeline
        timeline = otio.schema.Timeline(name="Valid Timeline")
        track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)

        clip = otio.schema.Clip(
            name="Valid Clip",
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(100, 24)
            )
        )

        track.append(clip)
        timeline.tracks.append(track)

        # Validate
        results = self.engine.validate_timeline(timeline, check_media=False)

        assert 'valid' in results
        assert 'errors' in results
        assert 'warnings' in results
        # Should be valid since we're not checking media
        assert results['valid'] == True

    def test_validate_timeline_negative_timecode(self):
        """Test validation catches negative timecode."""
        timeline = otio.schema.Timeline(name="Invalid Timeline")
        track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)

        # Create clip with negative start time
        clip = otio.schema.Clip(
            name="Invalid Clip",
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(-10, 24),
                duration=otio.opentime.RationalTime(100, 24)
            )
        )

        track.append(clip)
        timeline.tracks.append(track)

        # Validate
        results = self.engine.validate_timeline(timeline, check_media=False)

        assert results['valid'] == False
        assert len(results['errors']) > 0
        assert len(results['invalid_timecodes']) > 0

    def test_validate_timeline_zero_duration(self):
        """Test validation catches zero/negative duration."""
        timeline = otio.schema.Timeline(name="Invalid Timeline")
        track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)

        # Create clip with zero duration
        clip = otio.schema.Clip(
            name="Zero Duration Clip",
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(0, 24)
            )
        )

        track.append(clip)
        timeline.tracks.append(track)

        # Validate
        results = self.engine.validate_timeline(timeline, check_media=False)

        assert results['valid'] == False
        assert len(results['errors']) > 0

    def test_get_supported_formats(self):
        """Test getting supported formats."""
        formats = self.engine.get_supported_formats()

        assert 'import' in formats
        assert 'export' in formats
        assert isinstance(formats['import'], list)
        assert isinstance(formats['export'], list)
        # OTIO should always be supported
        assert 'OTIO' in formats['import']
        assert 'OTIO' in formats['export']

    def test_timeline_format_from_extension(self):
        """Test format detection from file extension."""
        assert TimelineFormat.from_extension('.otio') == TimelineFormat.OTIO
        assert TimelineFormat.from_extension('.edl') == TimelineFormat.EDL
        assert TimelineFormat.from_extension('.xml') == TimelineFormat.XML
        assert TimelineFormat.from_extension('.fcpxml') == TimelineFormat.FCPXML
        assert TimelineFormat.from_extension('.unknown') is None

    def test_parse_timeline_with_transitions(self):
        """Test parsing timeline with transitions."""
        timeline = otio.schema.Timeline(name="Transition Test")
        track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)

        clip1 = otio.schema.Clip(
            name="Clip 1",
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(100, 24)
            )
        )

        transition = otio.schema.Transition(
            name="Dissolve",
            transition_type="SMPTE_Dissolve",
            in_offset=otio.opentime.RationalTime(12, 24),
            out_offset=otio.opentime.RationalTime(12, 24)
        )

        clip2 = otio.schema.Clip(
            name="Clip 2",
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(100, 24)
            )
        )

        track.append(clip1)
        track.append(transition)
        track.append(clip2)
        timeline.tracks.append(track)

        info = self.engine.parse_timeline(timeline)

        assert info.num_clips == 2
        assert info.num_transitions == 1

    def test_parse_timeline_with_gap(self):
        """Test parsing timeline with gaps."""
        timeline = otio.schema.Timeline(name="Gap Test")
        track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)

        clip1 = otio.schema.Clip(
            name="Clip 1",
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(100, 24)
            )
        )

        gap = otio.schema.Gap(
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(24, 24)
            )
        )

        clip2 = otio.schema.Clip(
            name="Clip 2",
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(100, 24)
            )
        )

        track.append(clip1)
        track.append(gap)
        track.append(clip2)
        timeline.tracks.append(track)

        info = self.engine.parse_timeline(timeline)

        # Gaps shouldn't be counted as clips
        assert info.num_clips == 2

    def test_timecode_formatting(self):
        """Test timecode formatting."""
        time_24fps = otio.opentime.RationalTime(100, 24)
        timecode = self.engine._format_timecode(time_24fps)

        # Should be formatted as HH:MM:SS:FF
        assert isinstance(timecode, str)
        assert ':' in timecode
