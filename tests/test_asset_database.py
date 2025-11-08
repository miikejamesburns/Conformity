"""
Unit tests for asset database.
"""

import pytest
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from conformity.asset_tracker.asset_database import (
    AssetDatabase, AssetType, AssetStatus
)


class TestAssetDatabase:
    """Tests for asset database operations."""

    def setup_method(self):
        """Setup test fixtures."""
        # Use in-memory database for testing
        self.db = AssetDatabase()

    def teardown_method(self):
        """Cleanup after tests."""
        self.db.close()

    def test_add_asset(self):
        """Test adding an asset."""
        asset_id = self.db.add_asset(
            file_path=Path("/path/to/video.mp4"),
            asset_type=AssetType.VIDEO,
            status=AssetStatus.PENDING,
            file_size=1024000,
            checksum="abc123"
        )

        assert asset_id > 0

        # Verify asset was added
        asset = self.db.get_asset_by_id(asset_id)
        assert asset is not None
        assert asset['file_name'] == "video.mp4"
        assert asset['asset_type'] == 'video'
        assert asset['status'] == 'pending'

    def test_add_duplicate_asset(self):
        """Test adding duplicate asset returns existing ID."""
        path = Path("/path/to/video.mp4")

        asset_id1 = self.db.add_asset(
            file_path=path,
            asset_type=AssetType.VIDEO
        )

        asset_id2 = self.db.add_asset(
            file_path=path,
            asset_type=AssetType.VIDEO
        )

        # Should return same ID
        assert asset_id1 == asset_id2

    def test_add_metadata(self):
        """Test adding asset metadata."""
        asset_id = self.db.add_asset(
            file_path=Path("/path/to/video.mp4"),
            asset_type=AssetType.VIDEO
        )

        metadata = {
            'width': 1920,
            'height': 1080,
            'frame_rate': 24.0,
            'duration': 120.5,
            'codec': 'h264',
            'color_space': 'rec709'
        }

        metadata_id = self.db.add_metadata(asset_id, metadata)
        assert metadata_id > 0

        # Verify metadata was added
        stored_metadata = self.db.get_asset_metadata(asset_id)
        assert stored_metadata is not None
        assert stored_metadata['width'] == 1920
        assert stored_metadata['height'] == 1080
        assert stored_metadata['color_space'] == 'rec709'

    def test_get_asset_by_path(self):
        """Test getting asset by file path."""
        path = Path("/path/to/video.mp4")

        asset_id = self.db.add_asset(
            file_path=path,
            asset_type=AssetType.VIDEO
        )

        asset = self.db.get_asset_by_path(path)
        assert asset is not None
        assert asset['id'] == asset_id

    def test_search_assets_by_type(self):
        """Test searching assets by type."""
        # Add different types
        self.db.add_asset(Path("/video1.mp4"), AssetType.VIDEO)
        self.db.add_asset(Path("/video2.mp4"), AssetType.VIDEO)
        self.db.add_asset(Path("/image1.jpg"), AssetType.IMAGE)

        # Search for videos
        results = self.db.search_assets(asset_type=AssetType.VIDEO)
        assert len(results) == 2

        # Search for images
        results = self.db.search_assets(asset_type=AssetType.IMAGE)
        assert len(results) == 1

    def test_search_assets_by_status(self):
        """Test searching assets by status."""
        self.db.add_asset(
            Path("/pending.mp4"),
            AssetType.VIDEO,
            status=AssetStatus.PENDING
        )
        self.db.add_asset(
            Path("/approved.mp4"),
            AssetType.VIDEO,
            status=AssetStatus.APPROVED
        )

        # Search by status
        results = self.db.search_assets(status=AssetStatus.APPROVED)
        assert len(results) == 1
        assert results[0]['status'] == 'approved'

    def test_search_assets_text_query(self):
        """Test text search."""
        self.db.add_asset(Path("/path/footage.mp4"), AssetType.VIDEO)
        self.db.add_asset(Path("/other/file.mp4"), AssetType.VIDEO)

        results = self.db.search_assets(query="footage")
        assert len(results) == 1
        assert "footage" in results[0]['file_path']

    def test_update_asset_status(self):
        """Test updating asset status."""
        asset_id = self.db.add_asset(
            Path("/video.mp4"),
            AssetType.VIDEO,
            status=AssetStatus.PENDING
        )

        # Update status
        success = self.db.update_asset_status(
            asset_id,
            AssetStatus.APPROVED
        )

        assert success

        # Verify update
        asset = self.db.get_asset_by_id(asset_id)
        assert asset['status'] == 'approved'

    def test_update_online_status(self):
        """Test updating online status."""
        asset_id = self.db.add_asset(
            Path("/video.mp4"),
            AssetType.VIDEO
        )

        # Mark offline
        success = self.db.update_asset_online_status(asset_id, False)
        assert success

        # Verify
        asset = self.db.get_asset_by_id(asset_id)
        assert asset['is_online'] == 0

    def test_add_timeline_association(self):
        """Test adding timeline association."""
        asset_id = self.db.add_asset(
            Path("/video.mp4"),
            AssetType.VIDEO
        )

        assoc_id = self.db.add_timeline_association(
            asset_id=asset_id,
            timeline_path="timeline.otio",
            clip_name="Clip 1",
            track_name="V1",
            source_in=0.0,
            source_out=10.0,
            record_in=5.0,
            record_out=15.0
        )

        assert assoc_id > 0

    def test_add_tag(self):
        """Test adding tags to asset."""
        asset_id = self.db.add_asset(
            Path("/video.mp4"),
            AssetType.VIDEO
        )

        success = self.db.add_tag(asset_id, "important")
        assert success

        success = self.db.add_tag(asset_id, "vfx")
        assert success

    def test_get_statistics(self):
        """Test database statistics."""
        # Add some assets
        self.db.add_asset(Path("/video1.mp4"), AssetType.VIDEO, file_size=1000000)
        self.db.add_asset(Path("/video2.mp4"), AssetType.VIDEO, file_size=2000000)
        self.db.add_asset(Path("/image1.jpg"), AssetType.IMAGE, file_size=500000)

        stats = self.db.get_statistics()

        assert stats['total_assets'] == 3
        assert stats['by_type']['video'] == 2
        assert stats['by_type']['image'] == 1
        assert stats['online'] == 3
        assert stats['total_size_bytes'] == 3500000


class TestAssetDatabasePersistence:
    """Tests for database persistence."""

    def test_database_persistence(self):
        """Test that database persists to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create database and add asset
            db1 = AssetDatabase(db_path)
            asset_id = db1.add_asset(
                Path("/test.mp4"),
                AssetType.VIDEO
            )
            db1.close()

            # Reopen database and verify asset exists
            db2 = AssetDatabase(db_path)
            asset = db2.get_asset_by_id(asset_id)
            assert asset is not None
            assert asset['file_name'] == "test.mp4"
            db2.close()
