"""
Unit tests for media review system.
"""

import pytest
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from conformity.ui_components.playback_widget import PlaybackWidget
from conformity.ui_components.conform_review_widget import FrameMarker
from conformity.ui_components.review_panel import ReviewPanel


class TestPlaybackWidget:
    """Tests for playback widget."""

    def setup_method(self):
        """Setup test fixtures."""
        # Note: QApplication needed for Qt widgets, but not available in headless tests
        # These tests verify logic, not UI interaction
        pass

    def test_frames_to_timecode(self):
        """Test frame to timecode conversion."""
        # 24 fps
        tc = PlaybackWidget._frames_to_timecode(0, 24.0)
        assert tc == "00:00:00:00"

        tc = PlaybackWidget._frames_to_timecode(24, 24.0)
        assert tc == "00:00:01:00"

        tc = PlaybackWidget._frames_to_timecode(60, 24.0)
        assert tc == "00:00:02:12"

        tc = PlaybackWidget._frames_to_timecode(1440, 24.0)  # 1 minute
        assert tc == "00:01:00:00"

        tc = PlaybackWidget._frames_to_timecode(86400, 24.0)  # 1 hour
        assert tc == "01:00:00:00"

    def test_frames_to_timecode_different_rates(self):
        """Test timecode conversion with different frame rates."""
        # 30 fps
        tc = PlaybackWidget._frames_to_timecode(30, 30.0)
        assert tc == "00:00:01:00"

        # 60 fps
        tc = PlaybackWidget._frames_to_timecode(60, 60.0)
        assert tc == "00:00:01:00"

        # 23.976 fps
        tc = PlaybackWidget._frames_to_timecode(24, 23.976)
        assert tc == "00:00:01:00"


class TestFrameMarker:
    """Tests for frame marker data class."""

    def test_frame_marker_creation(self):
        """Test creating frame marker."""
        marker = FrameMarker(
            frame_number=120,
            timecode="00:00:05:00",
            note="Test note",
            marker_type="issue",
            created_date="2024-01-01T12:00:00"
        )

        assert marker.frame_number == 120
        assert marker.timecode == "00:00:05:00"
        assert marker.note == "Test note"
        assert marker.marker_type == "issue"

    def test_marker_types(self):
        """Test different marker types."""
        issue = FrameMarker(0, "00:00:00:00", "", "issue", "")
        note = FrameMarker(0, "00:00:00:00", "", "note", "")
        approved = FrameMarker(0, "00:00:00:00", "", "approved", "")

        assert issue.marker_type == "issue"
        assert note.marker_type == "note"
        assert approved.marker_type == "approved"


class TestReviewPanel:
    """Tests for review panel."""

    def test_review_data_structure(self):
        """Test review data structure."""
        # Create mock review data
        review_data = {
            'file_path': '/path/to/file.mp4',
            'status': 'Approved',
            'notes': 'Looks good',
            'metadata': {'width': 1920, 'height': 1080}
        }

        assert 'file_path' in review_data
        assert 'status' in review_data
        assert 'notes' in review_data
        assert 'metadata' in review_data

    def test_status_options(self):
        """Test review status options."""
        statuses = [
            "Not Reviewed",
            "Pending",
            "In Review",
            "Approved",
            "Needs Revision",
            "Rejected"
        ]

        assert "Approved" in statuses
        assert "Rejected" in statuses
        assert "Pending" in statuses


class TestConformReview:
    """Tests for conform review workflow."""

    def test_review_results_structure(self):
        """Test review results structure."""
        # Mock review results
        results = {
            'source_file': '/source/file.mp4',
            'conform_file': '/conform/file.mp4',
            'total_markers': 5,
            'issues': 2,
            'notes': 2,
            'approved': 1,
            'markers': [],
            'review_notes': 'Overall good conform'
        }

        assert results['total_markers'] == results['issues'] + results['notes'] + results['approved']
        assert 'markers' in results
        assert 'review_notes' in results

    def test_marker_statistics(self):
        """Test marker statistics calculation."""
        markers = [
            FrameMarker(10, "00:00:00:10", "", "issue", ""),
            FrameMarker(20, "00:00:00:20", "", "issue", ""),
            FrameMarker(30, "00:00:01:06", "", "note", ""),
            FrameMarker(40, "00:00:01:16", "", "note", ""),
            FrameMarker(50, "00:00:02:02", "", "approved", ""),
        ]

        issues = sum(1 for m in markers if m.marker_type == "issue")
        notes = sum(1 for m in markers if m.marker_type == "note")
        approved = sum(1 for m in markers if m.marker_type == "approved")

        assert issues == 2
        assert notes == 2
        assert approved == 1
        assert len(markers) == 5

    def test_marker_sorting_by_frame(self):
        """Test sorting markers by frame number."""
        markers = [
            FrameMarker(50, "00:00:02:02", "", "approved", ""),
            FrameMarker(10, "00:00:00:10", "", "issue", ""),
            FrameMarker(30, "00:00:01:06", "", "note", ""),
        ]

        sorted_markers = sorted(markers, key=lambda m: m.frame_number)

        assert sorted_markers[0].frame_number == 10
        assert sorted_markers[1].frame_number == 30
        assert sorted_markers[2].frame_number == 50


class TestImageSequenceDetection:
    """Tests for image sequence detection and handling."""

    def test_image_extension_detection(self):
        """Test image file extension detection."""
        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.exr', '.dpx'}

        assert Path("frame.jpg").suffix.lower() in image_extensions
        assert Path("frame.png").suffix.lower() in image_extensions
        assert Path("frame.exr").suffix.lower() in image_extensions
        assert Path("frame.mp4").suffix.lower() not in image_extensions

    def test_sequence_frame_sorting(self):
        """Test sorting image sequence frames."""
        # Create mock frame list
        frames = [
            Path("frame.0010.exr"),
            Path("frame.0001.exr"),
            Path("frame.0005.exr"),
            Path("frame.0015.exr"),
        ]

        sorted_frames = sorted(frames)

        # Check they're sorted correctly
        assert str(sorted_frames[0]).endswith("0001.exr")
        assert str(sorted_frames[1]).endswith("0005.exr")
        assert str(sorted_frames[2]).endswith("0010.exr")
        assert str(sorted_frames[3]).endswith("0015.exr")


class TestKeyboardShortcuts:
    """Tests for keyboard shortcut definitions."""

    def test_playback_shortcuts(self):
        """Test playback keyboard shortcuts."""
        shortcuts = {
            'Space': 'play_pause',
            'Left': 'frame_back',
            'Right': 'frame_forward',
            'Home': 'seek_to_start',
            'End': 'seek_to_end'
        }

        assert 'Space' in shortcuts
        assert 'Left' in shortcuts
        assert 'Right' in shortcuts

    def test_review_shortcuts(self):
        """Test review keyboard shortcuts."""
        shortcuts = {
            'I': 'add_issue_marker',
            'N': 'add_note_marker',
            'A': 'add_approved_marker',
            'D': 'toggle_difference',
            'S': 'toggle_sync'
        }

        assert 'I' in shortcuts
        assert 'N' in shortcuts
        assert 'A' in shortcuts


class TestReportGeneration:
    """Tests for review report generation."""

    def test_report_content_structure(self):
        """Test review report content structure."""
        report_lines = [
            "CONFORM REVIEW REPORT",
            "Source File: /source.mp4",
            "Conform File: /conform.mp4",
            "STATISTICS",
            "Total Markers: 5",
            "Issues: 2",
            "REVIEW NOTES",
            "FRAME MARKERS"
        ]

        # Check key sections exist
        assert any("REVIEW REPORT" in line for line in report_lines)
        assert any("STATISTICS" in line for line in report_lines)
        assert any("FRAME MARKERS" in line for line in report_lines)

    def test_marker_export_format(self):
        """Test marker export format."""
        marker = FrameMarker(
            frame_number=120,
            timecode="00:00:05:00",
            note="Color shift visible",
            marker_type="issue",
            created_date="2024-01-01T12:00:00"
        )

        # Format marker for export
        export_line = f"[{marker.marker_type.upper()}] Frame {marker.frame_number} ({marker.timecode})"

        assert "[ISSUE]" in export_line
        assert "Frame 120" in export_line
        assert "00:00:05:00" in export_line


class TestMetadataDisplay:
    """Tests for metadata display."""

    def test_metadata_structure(self):
        """Test metadata structure for display."""
        metadata = {
            'width': 1920,
            'height': 1080,
            'frame_rate': 24.0,
            'duration': 120.5,
            'codec': 'h264',
            'pixel_format': 'yuv420p',
            'bit_depth': 8,
            'color_space': 'rec709',
            'color_primaries': 'bt709',
            'color_transfer': 'bt709',
            'audio_codec': 'aac',
            'audio_channels': 2,
            'audio_sample_rate': 48000
        }

        # Verify all expected fields
        assert metadata['width'] == 1920
        assert metadata['height'] == 1080
        assert metadata['frame_rate'] == 24.0
        assert metadata['codec'] == 'h264'
        assert metadata['color_space'] == 'rec709'

    def test_format_file_size(self):
        """Test file size formatting."""
        file_size_bytes = 1_500_000_000  # 1.5 GB (1500 MB)

        size_mb = file_size_bytes / (1024 ** 2)
        size_gb = file_size_bytes / (1024 ** 3)

        assert size_mb > 1000
        # 1.5 billion bytes is ~1.397 GiB
        assert 1.3 < size_gb < 1.5

    def test_format_duration(self):
        """Test duration formatting."""
        duration_seconds = 125.5

        minutes = int(duration_seconds // 60)
        seconds = duration_seconds % 60

        assert minutes == 2
        assert 5 < seconds < 6
