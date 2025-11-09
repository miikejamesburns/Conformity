"""
Holistic color management system using OpenColorIO.

This module provides comprehensive color management including validation,
tracking, and pipeline-wide color space management.
"""

import PyOpenColorIO as ocio
from pathlib import Path
from typing import Optional, List, Dict, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import opentimelineio as otio

from .ocio_manager import OCIOManager
from ..core.logger import get_logger

logger = get_logger(__name__)


class ColorSpaceStatus(Enum):
    """Status of color space assignment."""
    VALID = "valid"
    MISSING = "missing"
    INVALID = "invalid"
    AMBIGUOUS = "ambiguous"
    INCOMPATIBLE = "incompatible"


@dataclass
class ColorSpaceAssignment:
    """Represents a color space assignment for a clip."""
    clip_name: str
    input_color_space: Optional[str] = None
    working_color_space: Optional[str] = None
    output_color_space: Optional[str] = None
    display: Optional[str] = None
    view: Optional[str] = None
    status: ColorSpaceStatus = ColorSpaceStatus.MISSING
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ColorValidationResult:
    """Result of color space validation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    assignments: List[ColorSpaceAssignment] = field(default_factory=list)
    missing_count: int = 0
    invalid_count: int = 0
    valid_count: int = 0


class PipelineColorConfig:
    """Manages pipeline-wide color configuration."""

    def __init__(self):
        """Initialize pipeline color configuration."""
        self.working_color_space: Optional[str] = None
        self.default_input_color_space: Optional[str] = None
        self.default_output_color_space: Optional[str] = None
        self.default_display: Optional[str] = None
        self.default_view: Optional[str] = None
        self.color_space_rules: Dict[str, str] = {}  # Extension -> color space
        logger.debug("PipelineColorConfig initialized")

    def set_defaults(
        self,
        working: str,
        default_input: Optional[str] = None,
        default_output: Optional[str] = None,
        display: Optional[str] = None,
        view: Optional[str] = None
    ):
        """
        Set default color spaces for the pipeline.

        Args:
            working: Working color space for processing
            default_input: Default input color space
            default_output: Default output color space
            display: Default display
            view: Default view
        """
        self.working_color_space = working
        self.default_input_color_space = default_input or working
        self.default_output_color_space = default_output or working
        self.default_display = display
        self.default_view = view
        logger.info(f"Pipeline defaults set: working={working}, input={default_input}")

    def add_rule(self, extension: str, color_space: str):
        """
        Add color space detection rule.

        Args:
            extension: File extension (e.g., '.r3d')
            color_space: Color space to assign
        """
        self.color_space_rules[extension.lower()] = color_space
        logger.debug(f"Added color space rule: {extension} -> {color_space}")

    def get_color_space_for_extension(self, extension: str) -> Optional[str]:
        """Get color space for file extension."""
        return self.color_space_rules.get(extension.lower())


class ColorManager:
    """
    Holistic color management system.

    Provides validation, tracking, and utilities for managing color spaces
    throughout the post-production pipeline.
    """

    def __init__(self, ocio_manager: Optional[OCIOManager] = None):
        """
        Initialize the color manager.

        Args:
            ocio_manager: Optional OCIO manager instance
        """
        self._ocio_manager = ocio_manager or OCIOManager()
        self._pipeline_config = PipelineColorConfig()
        self._assignments: Dict[str, ColorSpaceAssignment] = {}
        logger.info("ColorManager initialized")

    def get_ocio_manager(self) -> OCIOManager:
        """Get the OCIO manager instance."""
        return self._ocio_manager

    def get_pipeline_config(self) -> PipelineColorConfig:
        """Get the pipeline configuration."""
        return self._pipeline_config

    def load_config(self, config_path: Path) -> bool:
        """
        Load OCIO configuration.

        Args:
            config_path: Path to OCIO config file

        Returns:
            True if loaded successfully
        """
        try:
            self._ocio_manager.load_config(config_path)
            logger.info(f"OCIO config loaded: {config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load OCIO config: {e}")
            return False

    def validate_config(self) -> Tuple[bool, List[str]]:
        """
        Validate the loaded OCIO configuration.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        config = self._ocio_manager.get_config()
        if not config:
            errors.append("No OCIO config loaded")
            return False, errors

        try:
            # Check for color spaces
            color_spaces = self._ocio_manager.get_color_spaces()
            if not color_spaces:
                errors.append("No color spaces defined in config")

            # Check for displays
            displays = self._ocio_manager.get_displays()
            if not displays:
                errors.append("No displays defined in config")

            # Validate default display/view
            if displays:
                default_display = config.getDefaultDisplay()
                if default_display:
                    views = self._ocio_manager.get_views(default_display)
                    if not views:
                        errors.append(f"No views for default display: {default_display}")

            logger.info(f"Config validation: {'PASSED' if not errors else 'FAILED'}")
            return len(errors) == 0, errors

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return False, errors

    def detect_color_space_from_metadata(
        self,
        clip: otio.schema.Clip
    ) -> Optional[str]:
        """
        Detect color space from clip metadata.

        Args:
            clip: OTIO clip

        Returns:
            Detected color space name or None
        """
        # Check for color metadata
        if "color" in clip.metadata:
            color_meta = clip.metadata["color"]
            if "input_color_space" in color_meta:
                return color_meta["input_color_space"]
            if "color_space" in color_meta:
                return color_meta["color_space"]

        # Check media reference metadata
        if clip.media_reference and hasattr(clip.media_reference, 'metadata'):
            meta = clip.media_reference.metadata
            if "color_space" in meta:
                return meta["color_space"]

        return None

    def detect_color_space_from_extension(
        self,
        clip: otio.schema.Clip
    ) -> Optional[str]:
        """
        Detect color space from media file extension.

        Args:
            clip: OTIO clip

        Returns:
            Detected color space name or None
        """
        if not clip.media_reference:
            return None

        if isinstance(clip.media_reference, otio.schema.ExternalReference):
            media_path = Path(clip.media_reference.target_url)
            ext = media_path.suffix.lower()
            return self._pipeline_config.get_color_space_for_extension(ext)

        return None

    def assign_color_space_to_clip(
        self,
        clip: otio.schema.Clip,
        input_color_space: Optional[str] = None,
        working_color_space: Optional[str] = None,
        output_color_space: Optional[str] = None,
        display: Optional[str] = None,
        view: Optional[str] = None,
        validate: bool = True
    ) -> ColorSpaceAssignment:
        """
        Assign color spaces to a clip.

        Args:
            clip: OTIO clip
            input_color_space: Input color space
            working_color_space: Working color space
            output_color_space: Output color space
            display: Display transform
            view: View transform
            validate: Whether to validate assignments

        Returns:
            ColorSpaceAssignment object
        """
        assignment = ColorSpaceAssignment(
            clip_name=clip.name,
            input_color_space=input_color_space,
            working_color_space=working_color_space,
            output_color_space=output_color_space,
            display=display,
            view=view
        )

        # Validate if requested
        if validate:
            assignment.status, assignment.warnings = self._validate_assignment(assignment)
        else:
            assignment.status = ColorSpaceStatus.VALID

        # Store in clip metadata
        if "color" not in clip.metadata:
            clip.metadata["color"] = {}

        if input_color_space:
            clip.metadata["color"]["input_color_space"] = input_color_space
        if working_color_space:
            clip.metadata["color"]["working_color_space"] = working_color_space
        if output_color_space:
            clip.metadata["color"]["output_color_space"] = output_color_space
        if display:
            clip.metadata["color"]["display"] = display
        if view:
            clip.metadata["color"]["view"] = view

        # Track assignment
        self._assignments[clip.name] = assignment

        logger.debug(f"Assigned color space to clip '{clip.name}': {input_color_space}")
        return assignment

    def _validate_assignment(
        self,
        assignment: ColorSpaceAssignment
    ) -> Tuple[ColorSpaceStatus, List[str]]:
        """
        Validate a color space assignment.

        Args:
            assignment: ColorSpaceAssignment to validate

        Returns:
            Tuple of (status, warnings)
        """
        warnings = []

        # Check for missing color space first (before OCIO validation)
        if not assignment.input_color_space:
            return ColorSpaceStatus.MISSING, ["No input color space assigned"]

        config = self._ocio_manager.get_config()

        if not config:
            return ColorSpaceStatus.INVALID, ["No OCIO config loaded"]

        # Check input color space
        if assignment.input_color_space:
            if not self._ocio_manager.validate_color_space(assignment.input_color_space):
                warnings.append(f"Invalid input color space: {assignment.input_color_space}")
                return ColorSpaceStatus.INVALID, warnings

        # Check working color space
        if assignment.working_color_space:
            if not self._ocio_manager.validate_color_space(assignment.working_color_space):
                warnings.append(f"Invalid working color space: {assignment.working_color_space}")
                return ColorSpaceStatus.INVALID, warnings

        # Check output color space
        if assignment.output_color_space:
            if not self._ocio_manager.validate_color_space(assignment.output_color_space):
                warnings.append(f"Invalid output color space: {assignment.output_color_space}")
                return ColorSpaceStatus.INVALID, warnings

        # Check display/view
        if assignment.display:
            displays = self._ocio_manager.get_displays()
            if assignment.display not in displays:
                warnings.append(f"Invalid display: {assignment.display}")
                return ColorSpaceStatus.INVALID, warnings

            if assignment.view:
                views = self._ocio_manager.get_views(assignment.display)
                if assignment.view not in views:
                    warnings.append(f"Invalid view '{assignment.view}' for display '{assignment.display}'")
                    return ColorSpaceStatus.INVALID, warnings

        return ColorSpaceStatus.VALID, warnings

    def analyze_timeline(
        self,
        timeline: otio.schema.Timeline,
        auto_detect: bool = True
    ) -> ColorValidationResult:
        """
        Analyze color spaces in a timeline.

        Args:
            timeline: OTIO timeline to analyze
            auto_detect: Whether to auto-detect color spaces

        Returns:
            ColorValidationResult object
        """
        result = ColorValidationResult(valid=True)

        for track in timeline.tracks:
            for item in track:
                if isinstance(item, otio.schema.Clip):
                    assignment = self._analyze_clip(item, auto_detect)
                    result.assignments.append(assignment)

                    # Update counts
                    if assignment.status == ColorSpaceStatus.VALID:
                        result.valid_count += 1
                    elif assignment.status == ColorSpaceStatus.MISSING:
                        result.missing_count += 1
                        result.warnings.append(
                            f"Clip '{item.name}': No color space assigned"
                        )
                    elif assignment.status == ColorSpaceStatus.INVALID:
                        result.invalid_count += 1
                        result.errors.append(
                            f"Clip '{item.name}': Invalid color space"
                        )
                        result.valid = False

        logger.info(
            f"Timeline analysis: {result.valid_count} valid, "
            f"{result.missing_count} missing, {result.invalid_count} invalid"
        )

        return result

    def _analyze_clip(
        self,
        clip: otio.schema.Clip,
        auto_detect: bool
    ) -> ColorSpaceAssignment:
        """Analyze a single clip for color space assignment."""
        # Check for existing assignment
        input_cs = self.detect_color_space_from_metadata(clip)

        # Try auto-detection if enabled and nothing found
        if not input_cs and auto_detect:
            input_cs = self.detect_color_space_from_extension(clip)

            # If still nothing, use pipeline default
            if not input_cs:
                input_cs = self._pipeline_config.default_input_color_space

        # Get other assignments from metadata
        working_cs = None
        output_cs = None
        display = None
        view = None

        if "color" in clip.metadata:
            color_meta = clip.metadata["color"]
            working_cs = color_meta.get("working_color_space")
            output_cs = color_meta.get("output_color_space")
            display = color_meta.get("display")
            view = color_meta.get("view")

        # Create assignment
        assignment = ColorSpaceAssignment(
            clip_name=clip.name,
            input_color_space=input_cs,
            working_color_space=working_cs,
            output_color_space=output_cs,
            display=display,
            view=view
        )

        # Validate
        assignment.status, assignment.warnings = self._validate_assignment(assignment)

        return assignment

    def auto_assign_color_spaces(
        self,
        timeline: otio.schema.Timeline,
        use_defaults: bool = True
    ) -> int:
        """
        Automatically assign color spaces to all clips in timeline.

        Args:
            timeline: Timeline to process
            use_defaults: Whether to use pipeline defaults for undetected clips

        Returns:
            Number of clips assigned
        """
        assigned_count = 0

        for track in timeline.tracks:
            for item in track:
                if isinstance(item, otio.schema.Clip):
                    # Try metadata detection
                    input_cs = self.detect_color_space_from_metadata(item)

                    # Try extension detection
                    if not input_cs:
                        input_cs = self.detect_color_space_from_extension(item)

                    # Use defaults if enabled
                    if not input_cs and use_defaults:
                        input_cs = self._pipeline_config.default_input_color_space

                    # Assign if found
                    if input_cs:
                        self.assign_color_space_to_clip(
                            item,
                            input_color_space=input_cs,
                            working_color_space=self._pipeline_config.working_color_space,
                            display=self._pipeline_config.default_display,
                            view=self._pipeline_config.default_view
                        )
                        assigned_count += 1

        logger.info(f"Auto-assigned color spaces to {assigned_count} clips")
        return assigned_count

    def get_color_space_relationships(self) -> Dict[str, List[str]]:
        """
        Get relationships between color spaces in current config.

        Returns:
            Dictionary mapping color space families to their members
        """
        relationships = {}

        config = self._ocio_manager.get_config()
        if not config:
            return relationships

        for cs_name in self._ocio_manager.get_color_spaces():
            cs = config.getColorSpace(cs_name)
            if cs:
                family = cs.getFamily() or "Other"
                if family not in relationships:
                    relationships[family] = []
                relationships[family].append(cs_name)

        return relationships

    def create_color_space_report(
        self,
        timeline: otio.schema.Timeline
    ) -> Dict[str, Any]:
        """
        Create comprehensive color space report for timeline.

        Args:
            timeline: Timeline to analyze

        Returns:
            Report dictionary
        """
        result = self.analyze_timeline(timeline, auto_detect=False)

        report = {
            "timeline_name": timeline.name,
            "total_clips": len(result.assignments),
            "valid_assignments": result.valid_count,
            "missing_assignments": result.missing_count,
            "invalid_assignments": result.invalid_count,
            "validation_status": "PASS" if result.valid else "FAIL",
            "color_spaces_used": {},
            "clips": []
        }

        # Count color space usage
        for assignment in result.assignments:
            if assignment.input_color_space:
                cs = assignment.input_color_space
                report["color_spaces_used"][cs] = report["color_spaces_used"].get(cs, 0) + 1

            # Add clip detail
            report["clips"].append({
                "name": assignment.clip_name,
                "input_color_space": assignment.input_color_space,
                "status": assignment.status.value,
                "warnings": assignment.warnings
            })

        return report

    def get_assignment(self, clip_name: str) -> Optional[ColorSpaceAssignment]:
        """Get color space assignment for a clip."""
        return self._assignments.get(clip_name)

    def clear_assignments(self):
        """Clear all tracked assignments."""
        self._assignments.clear()
        logger.debug("Cleared all color space assignments")
