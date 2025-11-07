"""
OpenColorIO (OCIO) integration for color management.

This module provides interfaces for working with OCIO configurations,
color spaces, and color transformations.
"""

import PyOpenColorIO as ocio
from pathlib import Path
from typing import Optional, List, Dict, Any
from ..core.logger import get_logger

logger = get_logger(__name__)


class OCIOManager:
    """Manages OCIO color management operations."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the OCIO manager.

        Args:
            config_path: Optional path to OCIO config file.
                        If not provided, will use $OCIO environment variable.
        """
        self._config: Optional[ocio.Config] = None
        self._config_path = config_path
        logger.info("OCIOManager initialized")

        if config_path or self._has_ocio_env():
            try:
                self.load_config(config_path)
            except Exception as e:
                logger.warning(f"Could not load OCIO config: {e}")

    def _has_ocio_env(self) -> bool:
        """Check if OCIO environment variable is set."""
        import os
        return 'OCIO' in os.environ

    def load_config(self, config_path: Optional[Path] = None) -> ocio.Config:
        """
        Load an OCIO configuration.

        Args:
            config_path: Path to OCIO config file. If None, uses environment variable.

        Returns:
            Loaded OCIO config

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        try:
            if config_path:
                if not config_path.exists():
                    raise FileNotFoundError(f"OCIO config not found: {config_path}")
                logger.info(f"Loading OCIO config from: {config_path}")
                self._config = ocio.Config.CreateFromFile(str(config_path))
                self._config_path = config_path
            else:
                logger.info("Loading OCIO config from environment variable")
                self._config = ocio.GetCurrentConfig()

            logger.info(f"OCIO config loaded: {self._config.getDescription()}")
            return self._config

        except Exception as e:
            logger.error(f"Failed to load OCIO config: {e}")
            raise ValueError(f"Could not load OCIO config: {e}")

    def get_config(self) -> Optional[ocio.Config]:
        """Get the current OCIO configuration."""
        return self._config

    def get_color_spaces(self) -> List[str]:
        """
        Get list of available color spaces.

        Returns:
            List of color space names
        """
        if not self._config:
            logger.warning("No OCIO config loaded")
            return []

        color_spaces = []
        for i in range(self._config.getNumColorSpaces()):
            cs = self._config.getColorSpaceNameByIndex(i)
            color_spaces.append(cs)

        logger.debug(f"Found {len(color_spaces)} color spaces")
        return color_spaces

    def get_color_space_info(self, color_space_name: str) -> Dict[str, Any]:
        """
        Get information about a specific color space.

        Args:
            color_space_name: Name of the color space

        Returns:
            Dictionary with color space information
        """
        if not self._config:
            raise ValueError("No OCIO config loaded")

        cs = self._config.getColorSpace(color_space_name)
        if not cs:
            raise ValueError(f"Color space not found: {color_space_name}")

        info = {
            "name": cs.getName(),
            "family": cs.getFamily(),
            "description": cs.getDescription(),
            "bitdepth": str(cs.getBitDepth()),
            "isdata": cs.isData(),
        }

        logger.debug(f"Color space info for '{color_space_name}': {info}")
        return info

    def get_displays(self) -> List[str]:
        """
        Get list of available displays.

        Returns:
            List of display names
        """
        if not self._config:
            logger.warning("No OCIO config loaded")
            return []

        displays = []
        for i in range(self._config.getNumDisplays()):
            display = self._config.getDisplay(i)
            displays.append(display)

        logger.debug(f"Found {len(displays)} displays")
        return displays

    def get_views(self, display: str) -> List[str]:
        """
        Get list of views for a specific display.

        Args:
            display: Display name

        Returns:
            List of view names
        """
        if not self._config:
            logger.warning("No OCIO config loaded")
            return []

        views = []
        for i in range(self._config.getNumViews(display)):
            view = self._config.getView(display, i)
            views.append(view)

        logger.debug(f"Found {len(views)} views for display '{display}'")
        return views

    def create_processor(
        self,
        src_color_space: str,
        dst_color_space: str
    ) -> Optional[ocio.Processor]:
        """
        Create a color transformation processor.

        Args:
            src_color_space: Source color space name
            dst_color_space: Destination color space name

        Returns:
            OCIO processor for the transformation
        """
        if not self._config:
            raise ValueError("No OCIO config loaded")

        try:
            logger.debug(f"Creating processor: {src_color_space} -> {dst_color_space}")

            transform = ocio.ColorSpaceTransform()
            transform.setSrc(src_color_space)
            transform.setDst(dst_color_space)

            processor = self._config.getProcessor(transform)
            logger.info(f"Processor created successfully")
            return processor

        except Exception as e:
            logger.error(f"Failed to create processor: {e}")
            raise

    def get_default_display_view(self) -> tuple[str, str]:
        """
        Get the default display and view.

        Returns:
            Tuple of (display_name, view_name)
        """
        if not self._config:
            logger.warning("No OCIO config loaded")
            return ("", "")

        default_display = self._config.getDefaultDisplay()
        default_view = self._config.getDefaultView(default_display)

        logger.debug(f"Default display/view: {default_display}/{default_view}")
        return (default_display, default_view)

    def validate_color_space(self, color_space_name: str) -> bool:
        """
        Check if a color space exists in the current config.

        Args:
            color_space_name: Name of the color space to validate

        Returns:
            True if color space exists, False otherwise
        """
        if not self._config:
            return False

        cs = self._config.getColorSpace(color_space_name)
        return cs is not None
