"""
Unit tests for TimelineManager.
"""

import pytest
from pathlib import Path
import opentimelineio as otio
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from conformity.conform_engine.timeline_manager import TimelineManager


class TestTimelineManager:
    """Tests for TimelineManager class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.manager = TimelineManager()

    def test_create_timeline(self):
        """Test creating a new timeline."""
        timeline = self.manager.create_timeline(name="Test Timeline", fps=24.0)

        assert timeline is not None
        assert timeline.name == "Test Timeline"
        assert len(timeline.tracks) == 1

    def test_get_timeline_info(self):
        """Test getting timeline information."""
        timeline = self.manager.create_timeline(name="Test Timeline")
        info = self.manager.get_timeline_info(timeline)

        assert info["name"] == "Test Timeline"
        assert info["tracks"] == 1
        assert info["clips"] == 0

    def test_set_current_timeline(self):
        """Test setting current timeline."""
        timeline = self.manager.create_timeline(name="Test Timeline")
        self.manager.set_current_timeline(timeline)

        current = self.manager.get_current_timeline()
        assert current == timeline
        assert current.name == "Test Timeline"
