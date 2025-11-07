"""
Unit tests for AssetManager.
"""

import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from conformity.asset_tracker.asset_manager import (
    AssetManager, AssetType, AssetStatus
)


class TestAssetManager:
    """Tests for AssetManager class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.manager = AssetManager()

    def test_asset_type_detection(self):
        """Test automatic asset type detection."""
        test_cases = [
            (Path("test.mov"), AssetType.VIDEO),
            (Path("test.mp4"), AssetType.VIDEO),
            (Path("test.wav"), AssetType.AUDIO),
            (Path("test.jpg"), AssetType.IMAGE),
            (Path("test.unknown"), AssetType.OTHER),
        ]

        for path, expected_type in test_cases:
            detected = self.manager._detect_asset_type(path)
            assert detected == expected_type

    def test_get_statistics(self):
        """Test getting asset statistics."""
        stats = self.manager.get_statistics()

        assert "total_assets" in stats
        assert "by_type" in stats
        assert "by_status" in stats
        assert stats["total_assets"] == 0

    def test_get_assets_by_type(self):
        """Test filtering assets by type."""
        assets = self.manager.get_assets_by_type(AssetType.VIDEO)
        assert isinstance(assets, list)
        assert len(assets) == 0

    def test_clear_assets(self):
        """Test clearing all assets."""
        self.manager.clear_assets()
        stats = self.manager.get_statistics()
        assert stats["total_assets"] == 0
