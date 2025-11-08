"""
Unit tests for asset scanner and timeline analyzer.
"""

import pytest
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from conformity.asset_tracker.asset_database import AssetDatabase, AssetType, AssetStatus
from conformity.asset_tracker.asset_scanner import AssetScanner
from conformity.asset_tracker.metadata_extractor import MetadataExtractor
from conformity.asset_tracker.timeline_analyzer import TimelineAnalyzer

import opentimelineio as otio


class TestMetadataExtractor:
    """Tests for metadata extractor."""

    def setup_method(self):
        """Setup test fixtures."""
        self.extractor = MetadataExtractor()

    def test_is_media_file(self):
        """Test media file detection."""
        assert self.extractor.is_media_file(Path("video.mp4"))
        assert self.extractor.is_media_file(Path("image.jpg"))
        assert self.extractor.is_media_file(Path("audio.wav"))
        assert not self.extractor.is_media_file(Path("document.txt"))

    def test_get_asset_type(self):
        """Test asset type detection."""
        assert self.extractor.get_asset_type(Path("video.mp4")) == 'video'
        assert self.extractor.get_asset_type(Path("image.jpg")) == 'image'
        assert self.extractor.get_asset_type(Path("audio.wav")) == 'audio'
        assert self.extractor.get_asset_type(Path("other.txt")) == 'other'

    def test_extract_nonexistent_file(self):
        """Test extracting from nonexistent file."""
        metadata = self.extractor.extract(Path("/nonexistent/file.mp4"))
        assert metadata == {}


class TestAssetScanner:
    """Tests for asset scanner."""

    def setup_method(self):
        """Setup test fixtures."""
        self.db = AssetDatabase()
        self.scanner = AssetScanner(self.db)

    def teardown_method(self):
        """Cleanup after tests."""
        self.db.close()

    def test_scan_empty_directory(self):
        """Test scanning empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results = self.scanner.scan_directory(
                Path(tmpdir),
                recursive=False
            )

            assert results['total_found'] == 0
            assert results['added'] == 0

    def test_scan_nonexistent_directory(self):
        """Test scanning nonexistent directory."""
        results = self.scanner.scan_directory(
            Path("/nonexistent"),
            recursive=False
        )

        assert 'error' in results

    def test_verify_assets(self):
        """Test asset verification."""
        # Add an asset with nonexistent path
        asset_id = self.db.add_asset(
            Path("/nonexistent/file.mp4"),
            AssetType.VIDEO
        )

        # Verify assets
        results = self.scanner.verify_assets()

        assert results['total'] == 1
        assert results['offline'] == 1
        assert len(results['changed']) == 1

    def test_batch_update_status(self):
        """Test batch status update."""
        # Add some assets
        id1 = self.db.add_asset(Path("/video1.mp4"), AssetType.VIDEO)
        id2 = self.db.add_asset(Path("/video2.mp4"), AssetType.VIDEO)

        # Batch update
        count = self.scanner.batch_update_status(
            [id1, id2],
            AssetStatus.APPROVED
        )

        assert count == 2

        # Verify updates
        asset1 = self.db.get_asset_by_id(id1)
        asset2 = self.db.get_asset_by_id(id2)
        assert asset1['status'] == 'approved'
        assert asset2['status'] == 'approved'

    def test_batch_add_tags(self):
        """Test batch tag addition."""
        # Add assets
        id1 = self.db.add_asset(Path("/video1.mp4"), AssetType.VIDEO)
        id2 = self.db.add_asset(Path("/video2.mp4"), AssetType.VIDEO)

        # Add tags
        count = self.scanner.batch_add_tags(
            [id1, id2],
            ["important", "vfx"]
        )

        assert count == 4  # 2 assets * 2 tags

    def test_relocate_asset(self):
        """Test asset relocation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a real file
            test_file = Path(tmpdir) / "test.mp4"
            test_file.write_text("test")

            # Add asset with different path
            asset_id = self.db.add_asset(
                Path("/old/path.mp4"),
                AssetType.VIDEO
            )

            # Relocate
            success = self.scanner.relocate_asset(asset_id, test_file)
            assert success

            # Verify
            asset = self.db.get_asset_by_id(asset_id)
            assert asset['file_path'] == str(test_file)

    def test_relocate_to_nonexistent_path(self):
        """Test relocating to nonexistent path fails."""
        asset_id = self.db.add_asset(
            Path("/old/path.mp4"),
            AssetType.VIDEO
        )

        success = self.scanner.relocate_asset(
            asset_id,
            Path("/nonexistent/file.mp4")
        )

        assert not success


class TestTimelineAnalyzer:
    """Tests for timeline analyzer."""

    def setup_method(self):
        """Setup test fixtures."""
        self.db = AssetDatabase()
        self.analyzer = TimelineAnalyzer(self.db)

    def teardown_method(self):
        """Cleanup after tests."""
        self.db.close()

    def test_analyze_empty_timeline(self):
        """Test analyzing empty timeline."""
        timeline = otio.schema.Timeline(name="Empty Timeline")

        results = self.analyzer.analyze_timeline(timeline)

        assert results['total_clips'] == 0
        assert results['linked_clips'] == 0

    def test_analyze_timeline_with_clips(self):
        """Test analyzing timeline with clips."""
        # Create timeline
        timeline = otio.schema.Timeline(name="Test Timeline")
        track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)
        timeline.tracks.append(track)

        # Add asset to database
        asset_id = self.db.add_asset(
            Path("/media/video.mp4"),
            AssetType.VIDEO
        )

        # Create clip with media reference
        clip = otio.schema.Clip(
            name="Test Clip",
            media_reference=otio.schema.ExternalReference(
                target_url="/media/video.mp4"
            ),
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 24),
                duration=otio.opentime.RationalTime(240, 24)
            )
        )
        track.append(clip)

        # Analyze timeline
        results = self.analyzer.analyze_timeline(timeline)

        assert results['total_clips'] == 1
        assert results['linked_clips'] == 1
        assert results['missing_clips'] == 0

    def test_analyze_timeline_missing_media(self):
        """Test analyzing timeline with missing media."""
        timeline = otio.schema.Timeline(name="Test Timeline")
        track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)
        timeline.tracks.append(track)

        # Create clip with media not in database
        clip = otio.schema.Clip(
            name="Missing Clip",
            media_reference=otio.schema.ExternalReference(
                target_url="/missing/video.mp4"
            )
        )
        track.append(clip)

        # Analyze timeline
        results = self.analyzer.analyze_timeline(timeline)

        assert results['total_clips'] == 1
        assert results['linked_clips'] == 0
        assert results['missing_clips'] == 1
        assert len(results['missing_media']) == 1

    def test_get_timeline_assets(self):
        """Test getting assets for a timeline."""
        timeline_path = Path("/timelines/test.otio")

        # Add asset and association
        asset_id = self.db.add_asset(
            Path("/media/video.mp4"),
            AssetType.VIDEO
        )

        self.db.add_timeline_association(
            asset_id=asset_id,
            timeline_path=str(timeline_path),
            clip_name="Clip 1",
            track_name="V1"
        )

        # Get assets for timeline
        assets = self.analyzer.get_timeline_assets(timeline_path)

        assert len(assets) == 1
        assert assets[0]['id'] == asset_id
        assert assets[0]['clip_name'] == "Clip 1"

    def test_get_asset_timelines(self):
        """Test getting timelines that use an asset."""
        asset_id = self.db.add_asset(
            Path("/media/video.mp4"),
            AssetType.VIDEO
        )

        # Add multiple timeline associations
        self.db.add_timeline_association(
            asset_id=asset_id,
            timeline_path="timeline1.otio",
            clip_name="Clip 1"
        )

        self.db.add_timeline_association(
            asset_id=asset_id,
            timeline_path="timeline2.otio",
            clip_name="Clip 2"
        )

        # Get timelines
        timelines = self.analyzer.get_asset_timelines(asset_id)

        assert len(timelines) == 2

    def test_generate_usage_report(self):
        """Test usage report generation."""
        # Add assets
        id1 = self.db.add_asset(Path("/video1.mp4"), AssetType.VIDEO)
        id2 = self.db.add_asset(Path("/video2.mp4"), AssetType.VIDEO)
        id3 = self.db.add_asset(Path("/video3.mp4"), AssetType.VIDEO)

        # Add associations (video1 used twice, video2 once, video3 not used)
        self.db.add_timeline_association(id1, "timeline.otio", "Clip 1")
        self.db.add_timeline_association(id1, "timeline.otio", "Clip 2")
        self.db.add_timeline_association(id2, "timeline.otio", "Clip 3")

        # Generate report
        report = self.analyzer.generate_usage_report()

        assert report['total_associations'] == 3
        assert len(report['most_used']) > 0
        assert report['unused_assets'] == 1  # video3 not used
