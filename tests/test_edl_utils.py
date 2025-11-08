"""
Unit tests for EDL utilities.
"""

import pytest
from pathlib import Path
import sys
import tempfile
import opentimelineio as otio

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from conformity.conform_engine.edl_utils import (
    EDLParser, EDLWriter, EDLConverter, EDLInfo, EDLEvent,
    EditType, TrackType, validate_edl_file
)


class TestEDLParser:
    """Tests for EDL parsing."""

    def setup_method(self):
        """Setup test fixtures."""
        self.test_data_dir = Path(__file__).parent / "test_data" / "edl"
        self.parser = EDLParser()

    def test_parse_simple_cuts(self):
        """Test parsing simple EDL with cuts."""
        edl_path = self.test_data_dir / "simple_cuts.edl"

        if not edl_path.exists():
            pytest.skip(f"Test data file not found: {edl_path}")

        edl_info = self.parser.parse_file(edl_path)

        assert edl_info is not None
        assert edl_info.title == "Simple Cuts Timeline"
        assert edl_info.fcm == "NON-DROP FRAME"
        assert len(edl_info.events) == 3

        # Check first event
        event1 = edl_info.events[0]
        assert event1.event_number == 1
        assert event1.reel_name == "CLIP001"
        assert event1.track_type == TrackType.VIDEO
        assert event1.edit_type == EditType.CUT
        assert event1.source_in == "01:00:00:00"
        assert event1.source_out == "01:00:05:00"
        assert event1.record_in == "00:00:00:00"
        assert event1.record_out == "00:00:05:00"
        assert event1.clip_name == "Opening Shot.mov"

    def test_parse_with_dissolves(self):
        """Test parsing EDL with dissolves."""
        edl_path = self.test_data_dir / "with_dissolves.edl"

        if not edl_path.exists():
            pytest.skip(f"Test data file not found: {edl_path}")

        edl_info = self.parser.parse_file(edl_path)

        assert edl_info is not None
        assert len(edl_info.events) == 4

        # Check dissolve event
        event2 = edl_info.events[1]
        assert event2.edit_type == EditType.DISSOLVE
        assert "DISSOLVE" in [c.upper() for c in event2.comments]

    def test_parse_multi_track(self):
        """Test parsing multi-track EDL."""
        edl_path = self.test_data_dir / "multi_track.edl"

        if not edl_path.exists():
            pytest.skip(f"Test data file not found: {edl_path}")

        edl_info = self.parser.parse_file(edl_path)

        assert edl_info is not None
        assert edl_info.fcm == "DROP FRAME"
        assert len(edl_info.events) == 4

        # Check we have both video and audio
        track_types = [e.track_type for e in edl_info.events]
        assert TrackType.VIDEO in track_types
        assert TrackType.AUDIO in track_types

    def test_parse_complex_project(self):
        """Test parsing complex EDL."""
        edl_path = self.test_data_dir / "complex_project.edl"

        if not edl_path.exists():
            pytest.skip(f"Test data file not found: {edl_path}")

        edl_info = self.parser.parse_file(edl_path)

        assert edl_info is not None
        assert edl_info.title == "Complex Project Timeline"
        assert len(edl_info.events) == 9

        # Check multiple reel names
        reel_names = set(e.reel_name for e in edl_info.events)
        assert "RED001" in reel_names
        assert "ARRI001" in reel_names
        assert "BMDFILM1" in reel_names

        # Check source files are extracted
        event1 = edl_info.events[0]
        assert 'source_file' in event1.metadata
        assert event1.metadata['source_file'] == "/media/red/A001_C001.R3D"

        # Check audio tracks
        audio_events = [e for e in edl_info.events if e.track_type in [TrackType.AUDIO_1, TrackType.AUDIO_2]]
        assert len(audio_events) == 2

    def test_parse_string(self):
        """Test parsing EDL from string."""
        edl_content = """TITLE: Test EDL
FCM: NON-DROP FRAME

001  AX       V     C        01:00:00:00 01:00:05:00 00:00:00:00 00:00:05:00
* FROM CLIP NAME: Test.mov
"""

        edl_info = self.parser.parse_string(edl_content)

        assert edl_info is not None
        assert edl_info.title == "Test EDL"
        assert len(edl_info.events) == 1
        assert edl_info.events[0].clip_name == "Test.mov"

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file raises error."""
        with pytest.raises(ValueError):
            self.parser.parse_file(Path("/nonexistent/file.edl"))


class TestEDLWriter:
    """Tests for EDL writing."""

    def setup_method(self):
        """Setup test fixtures."""
        self.writer = EDLWriter()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Cleanup test fixtures."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_write_simple_edl(self):
        """Test writing simple EDL."""
        edl_info = EDLInfo(
            title="Test Timeline",
            fcm="NON-DROP FRAME"
        )

        event = EDLEvent(
            event_number=1,
            reel_name="AX",
            track_type=TrackType.VIDEO,
            edit_type=EditType.CUT,
            source_in="01:00:00:00",
            source_out="01:00:05:00",
            record_in="00:00:00:00",
            record_out="00:00:05:00",
            clip_name="Test Clip.mov"
        )
        edl_info.events.append(event)

        output_path = self.temp_dir / "test_output.edl"
        self.writer.write_file(edl_info, output_path)

        assert output_path.exists()

        # Verify content
        content = output_path.read_text()
        assert "TITLE: Test Timeline" in content
        assert "FCM: NON-DROP FRAME" in content
        assert "001  AX" in content
        assert "FROM CLIP NAME: Test Clip.mov" in content

    def test_write_without_comments(self):
        """Test writing EDL without comments."""
        edl_info = EDLInfo(title="No Comments")

        event = EDLEvent(
            event_number=1,
            reel_name="AX",
            track_type=TrackType.VIDEO,
            edit_type=EditType.CUT,
            source_in="01:00:00:00",
            source_out="01:00:05:00",
            record_in="00:00:00:00",
            record_out="00:00:05:00",
            clip_name="Test.mov"
        )
        event.comments.append("Some comment")
        edl_info.events.append(event)

        output_path = self.temp_dir / "no_comments.edl"
        self.writer.write_file(edl_info, output_path, include_comments=False)

        content = output_path.read_text()
        assert "FROM CLIP NAME" not in content
        assert "Some comment" not in content

    def test_to_string(self):
        """Test converting EDL to string."""
        edl_info = EDLInfo(title="String Test")

        event = EDLEvent(
            event_number=1,
            reel_name="AX",
            track_type=TrackType.VIDEO,
            edit_type=EditType.CUT,
            source_in="01:00:00:00",
            source_out="01:00:05:00",
            record_in="00:00:00:00",
            record_out="00:00:05:00"
        )
        edl_info.events.append(event)

        edl_string = self.writer.to_string(edl_info)

        assert isinstance(edl_string, str)
        assert "TITLE: String Test" in edl_string
        assert "001  AX" in edl_string


class TestEDLConverter:
    """Tests for EDL/Timeline conversion."""

    def setup_method(self):
        """Setup test fixtures."""
        self.converter = EDLConverter()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Cleanup test fixtures."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_timeline_to_edl_simple(self):
        """Test converting simple timeline to EDL."""
        # Create a test timeline
        timeline = otio.schema.Timeline(name="Test Timeline")
        track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)

        clip = otio.schema.Clip(
            name="Test Clip",
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(120, 24)  # 5 seconds
            )
        )

        # Add CMX metadata
        clip.metadata["cmx_3600"] = {"reel": "CLIP001"}

        track.append(clip)
        timeline.tracks.append(track)

        # Convert to EDL
        edl_info = self.converter.timeline_to_edl(timeline)

        assert edl_info is not None
        assert edl_info.title == "Test Timeline"
        assert len(edl_info.events) == 1

        event = edl_info.events[0]
        assert event.reel_name == "CLIP001"
        assert event.track_type == TrackType.VIDEO
        assert event.edit_type == EditType.CUT
        assert event.clip_name == "Test Clip"

    def test_timeline_to_edl_with_media_reference(self):
        """Test converting timeline with media references to EDL."""
        timeline = otio.schema.Timeline(name="Media Test")
        track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)

        media_ref = otio.schema.ExternalReference(
            target_url="/path/to/media.mov"
        )

        clip = otio.schema.Clip(
            name="Media Clip",
            media_reference=media_ref,
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(120, 24)
            )
        )

        track.append(clip)
        timeline.tracks.append(track)

        edl_info = self.converter.timeline_to_edl(timeline, use_clip_names=True)

        assert len(edl_info.events) == 1
        event = edl_info.events[0]
        assert 'source_file' in event.metadata
        assert event.metadata['source_file'] == "/path/to/media.mov"

    def test_edl_to_timeline_simple(self):
        """Test converting simple EDL to timeline."""
        edl_info = EDLInfo(title="Test Timeline")

        event = EDLEvent(
            event_number=1,
            reel_name="CLIP001",
            track_type=TrackType.VIDEO,
            edit_type=EditType.CUT,
            source_in="01:00:00:00",
            source_out="01:00:05:00",
            record_in="00:00:00:00",
            record_out="00:00:05:00",
            clip_name="Test Clip.mov"
        )
        edl_info.events.append(event)

        timeline = self.converter.edl_to_timeline(edl_info, fps=24.0)

        assert timeline is not None
        assert timeline.name == "Test Timeline"
        assert len(timeline.tracks) == 1

        track = timeline.tracks[0]
        assert track.kind == otio.schema.TrackKind.Video
        assert len(track) == 1

        clip = track[0]
        assert isinstance(clip, otio.schema.Clip)
        assert clip.name == "Test Clip.mov"
        assert "cmx_3600" in clip.metadata

    def test_edl_to_timeline_with_audio(self):
        """Test converting EDL with audio to timeline."""
        edl_info = EDLInfo(title="Multi Track")

        # Video event
        video_event = EDLEvent(
            event_number=1,
            reel_name="VID001",
            track_type=TrackType.VIDEO,
            edit_type=EditType.CUT,
            source_in="01:00:00:00",
            source_out="01:00:05:00",
            record_in="00:00:00:00",
            record_out="00:00:05:00"
        )
        edl_info.events.append(video_event)

        # Audio event (should be skipped for now)
        audio_event = EDLEvent(
            event_number=2,
            reel_name="AUD001",
            track_type=TrackType.AUDIO,
            edit_type=EditType.CUT,
            source_in="01:00:00:00",
            source_out="01:00:05:00",
            record_in="00:00:00:00",
            record_out="00:00:05:00"
        )
        edl_info.events.append(audio_event)

        timeline = self.converter.edl_to_timeline(edl_info, fps=24.0)

        assert timeline is not None
        # Currently only video track is created
        assert len(timeline.tracks) == 1
        assert timeline.tracks[0].kind == otio.schema.TrackKind.Video

    def test_roundtrip_conversion(self):
        """Test EDL -> Timeline -> EDL roundtrip."""
        # Create original EDL
        original_edl = EDLInfo(title="Roundtrip Test", fcm="NON-DROP FRAME")

        event = EDLEvent(
            event_number=1,
            reel_name="TEST001",
            track_type=TrackType.VIDEO,
            edit_type=EditType.CUT,
            source_in="01:00:00:00",
            source_out="01:00:05:00",
            record_in="00:00:00:00",
            record_out="00:00:05:00",
            clip_name="Original Clip.mov"
        )
        original_edl.events.append(event)

        # Convert to timeline
        timeline = self.converter.edl_to_timeline(original_edl, fps=24.0)

        # Convert back to EDL
        result_edl = self.converter.timeline_to_edl(timeline, title=original_edl.title)

        assert result_edl.title == original_edl.title
        assert len(result_edl.events) == len(original_edl.events)

    def test_timecode_formatting(self):
        """Test timecode formatting."""
        time = otio.opentime.RationalTime(120, 24)  # 5 seconds at 24fps
        tc = self.converter._format_timecode(time)

        assert tc == "00:00:05:00"

    def test_timecode_parsing(self):
        """Test timecode parsing."""
        tc_str = "00:00:05:00"
        time = self.converter._parse_timecode(tc_str, 24.0)

        assert time.value == 120
        assert time.rate == 24.0


class TestEDLValidation:
    """Tests for EDL validation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.test_data_dir = Path(__file__).parent / "test_data" / "edl"

    def test_validate_valid_edl(self):
        """Test validation of valid EDL."""
        edl_path = self.test_data_dir / "simple_cuts.edl"

        if not edl_path.exists():
            pytest.skip(f"Test data file not found: {edl_path}")

        valid, errors = validate_edl_file(edl_path)

        assert valid is True
        assert len(errors) == 0

    def test_validate_complex_edl(self):
        """Test validation of complex EDL."""
        edl_path = self.test_data_dir / "complex_project.edl"

        if not edl_path.exists():
            pytest.skip(f"Test data file not found: {edl_path}")

        valid, errors = validate_edl_file(edl_path)

        assert valid is True
        assert len(errors) == 0

    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file."""
        valid, errors = validate_edl_file(Path("/nonexistent/file.edl"))

        assert valid is False
        assert len(errors) > 0


class TestEditType:
    """Tests for EditType enum."""

    def test_from_string(self):
        """Test creating EditType from string."""
        assert EditType.from_string("C") == EditType.CUT
        assert EditType.from_string("D") == EditType.DISSOLVE
        assert EditType.from_string("W") == EditType.WIPE
        assert EditType.from_string("K") == EditType.KEY
        assert EditType.from_string("c") == EditType.CUT  # Case insensitive


class TestTrackType:
    """Tests for TrackType enum."""

    def test_from_string(self):
        """Test creating TrackType from string."""
        assert TrackType.from_string("V") == TrackType.VIDEO
        assert TrackType.from_string("A") == TrackType.AUDIO
        assert TrackType.from_string("A1") == TrackType.AUDIO_1
        assert TrackType.from_string("A2") == TrackType.AUDIO_2
        assert TrackType.from_string("B") == TrackType.VIDEO_AUDIO
        assert TrackType.from_string("v") == TrackType.VIDEO  # Case insensitive
        assert TrackType.from_string("INVALID") == TrackType.NONE
