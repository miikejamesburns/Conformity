"""
Unit tests for ColorManager.
"""

import pytest
from pathlib import Path
import opentimelineio as otio
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from conformity.color_manager.color_manager import (
    ColorManager, PipelineColorConfig, ColorSpaceStatus,
    ColorSpaceAssignment, ColorValidationResult
)


class TestPipelineColorConfig:
    """Tests for PipelineColorConfig class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.config = PipelineColorConfig()

    def test_set_defaults(self):
        """Test setting pipeline defaults."""
        self.config.set_defaults(
            working="Linear",
            default_input="sRGB",
            default_output="Rec709"
        )

        assert self.config.working_color_space == "Linear"
        assert self.config.default_input_color_space == "sRGB"
        assert self.config.default_output_color_space == "Rec709"

    def test_add_rule(self):
        """Test adding detection rules."""
        self.config.add_rule('.r3d', 'RedWideGamutRGB')
        self.config.add_rule('.ari', 'ARRI_LogC4')

        assert self.config.get_color_space_for_extension('.r3d') == 'RedWideGamutRGB'
        assert self.config.get_color_space_for_extension('.ari') == 'ARRI_LogC4'
        assert self.config.get_color_space_for_extension('.mov') is None

    def test_case_insensitive_rules(self):
        """Test that rules are case-insensitive."""
        self.config.add_rule('.R3D', 'RedWideGamutRGB')

        assert self.config.get_color_space_for_extension('.r3d') == 'RedWideGamutRGB'
        assert self.config.get_color_space_for_extension('.R3D') == 'RedWideGamutRGB'


class TestColorManager:
    """Tests for ColorManager class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.color_mgr = ColorManager()

    def test_initialization(self):
        """Test color manager initializes correctly."""
        assert self.color_mgr is not None
        assert self.color_mgr.get_pipeline_config() is not None

    def test_detect_color_space_from_metadata(self):
        """Test color space detection from clip metadata."""
        clip = otio.schema.Clip(name="Test Clip")
        clip.metadata["color"] = {
            "input_color_space": "ACEScg"
        }

        detected = self.color_mgr.detect_color_space_from_metadata(clip)
        assert detected == "ACEScg"

    def test_detect_color_space_from_extension(self):
        """Test color space detection from file extension."""
        # Setup rules
        pipeline = self.color_mgr.get_pipeline_config()
        pipeline.add_rule('.r3d', 'RedWideGamutRGB')

        # Create clip with media reference
        media_ref = otio.schema.ExternalReference(target_url="/path/to/file.r3d")
        clip = otio.schema.Clip(name="Test", media_reference=media_ref)

        detected = self.color_mgr.detect_color_space_from_extension(clip)
        assert detected == 'RedWideGamutRGB'

    def test_assign_color_space_to_clip(self):
        """Test assigning color space to clip."""
        clip = otio.schema.Clip(name="Test Clip")

        assignment = self.color_mgr.assign_color_space_to_clip(
            clip,
            input_color_space="Linear",
            validate=False  # Skip validation since no OCIO config loaded
        )

        assert assignment.clip_name == "Test Clip"
        assert assignment.input_color_space == "Linear"
        assert clip.metadata["color"]["input_color_space"] == "Linear"

    def test_analyze_timeline_empty(self):
        """Test analyzing empty timeline."""
        timeline = otio.schema.Timeline(name="Empty")
        track = otio.schema.Track(name="V1")
        timeline.tracks.append(track)

        result = self.color_mgr.analyze_timeline(timeline)

        assert isinstance(result, ColorValidationResult)
        assert result.valid_count == 0
        assert result.missing_count == 0

    def test_analyze_timeline_with_clips(self):
        """Test analyzing timeline with clips."""
        timeline = otio.schema.Timeline(name="Test")
        track = otio.schema.Track(name="V1")

        # Clip with color space
        clip1 = otio.schema.Clip(name="Clip 1")
        clip1.metadata["color"] = {"input_color_space": "Linear"}

        # Clip without color space
        clip2 = otio.schema.Clip(name="Clip 2")

        track.append(clip1)
        track.append(clip2)
        timeline.tracks.append(track)

        result = self.color_mgr.analyze_timeline(timeline, auto_detect=False)

        assert len(result.assignments) == 2
        # One has color space, one doesn't
        assert result.missing_count >= 1

    def test_auto_assign_color_spaces(self):
        """Test auto-assigning color spaces."""
        timeline = otio.schema.Timeline(name="Test")
        track = otio.schema.Track(name="V1")

        # Setup pipeline
        pipeline = self.color_mgr.get_pipeline_config()
        pipeline.set_defaults(working="Linear", default_input="sRGB")
        pipeline.add_rule('.r3d', 'RedWideGamutRGB')

        # Add clips
        media_ref = otio.schema.ExternalReference(target_url="/path/file.r3d")
        clip1 = otio.schema.Clip(name="RED Clip", media_reference=media_ref)

        clip2 = otio.schema.Clip(name="Generic Clip")

        track.append(clip1)
        track.append(clip2)
        timeline.tracks.append(track)

        # Auto-assign
        count = self.color_mgr.auto_assign_color_spaces(timeline, use_defaults=True)

        assert count >= 1  # At least the RED clip should be assigned
        assert clip1.metadata.get("color", {}).get("input_color_space") == "RedWideGamutRGB"

    def test_create_color_space_report(self):
        """Test creating color space report."""
        timeline = otio.schema.Timeline(name="Test Timeline")
        track = otio.schema.Track(name="V1")

        clip = otio.schema.Clip(name="Test Clip")
        clip.metadata["color"] = {"input_color_space": "Linear"}

        track.append(clip)
        timeline.tracks.append(track)

        report = self.color_mgr.create_color_space_report(timeline)

        assert report["timeline_name"] == "Test Timeline"
        assert report["total_clips"] == 1
        assert "Linear" in report["color_spaces_used"]

    def test_get_assignment(self):
        """Test retrieving color space assignment."""
        clip = otio.schema.Clip(name="Test Clip")

        assignment = self.color_mgr.assign_color_space_to_clip(
            clip,
            input_color_space="ACEScg",
            validate=False
        )

        retrieved = self.color_mgr.get_assignment("Test Clip")
        assert retrieved is not None
        assert retrieved.input_color_space == "ACEScg"

    def test_clear_assignments(self):
        """Test clearing all assignments."""
        clip = otio.schema.Clip(name="Test Clip")
        self.color_mgr.assign_color_space_to_clip(clip, input_color_space="Linear", validate=False)

        self.color_mgr.clear_assignments()

        assert self.color_mgr.get_assignment("Test Clip") is None
