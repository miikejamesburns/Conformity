"""
Configuration management for Conformity.

This module handles loading and managing application configuration
from YAML files and environment variables.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ConformityConfig(BaseModel):
    """Main configuration model for Conformity application."""

    # Application settings
    app_name: str = Field(default="Conformity", description="Application name")
    version: str = Field(default="0.1.0", description="Application version")
    log_level: str = Field(default="INFO", description="Logging level")

    # Project paths
    project_root: Path = Field(default_factory=Path.cwd, description="Project root directory")
    cache_dir: Optional[Path] = Field(default=None, description="Cache directory")
    temp_dir: Optional[Path] = Field(default=None, description="Temporary files directory")

    # OCIO settings
    ocio_config_path: Optional[Path] = Field(default=None, description="Path to OCIO config file")
    default_color_space: str = Field(default="linear", description="Default color space")

    # OTIO settings
    default_fps: float = Field(default=24.0, description="Default frames per second")
    default_resolution: tuple[int, int] = Field(default=(1920, 1080), description="Default resolution")

    # UI settings
    theme: str = Field(default="dark", description="UI theme (dark/light)")
    window_width: int = Field(default=1280, description="Default window width")
    window_height: int = Field(default=720, description="Default window height")

    class Config:
        arbitrary_types_allowed = True


class ConfigManager:
    """Manages application configuration loading and access."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the configuration manager.

        Args:
            config_path: Optional path to configuration file
        """
        self._config: Optional[ConformityConfig] = None
        self._config_path = config_path or self._get_default_config_path()

    def _get_default_config_path(self) -> Path:
        """Get the default configuration file path."""
        return Path(__file__).parent.parent.parent.parent / "config" / "default_config.yaml"

    def load_config(self) -> ConformityConfig:
        """
        Load configuration from file and environment variables.

        Returns:
            Loaded configuration object
        """
        config_dict = {}

        # Load from YAML file if it exists
        if self._config_path.exists():
            with open(self._config_path, 'r') as f:
                config_dict = yaml.safe_load(f) or {}

        # Override with environment variables
        config_dict = self._apply_env_overrides(config_dict)

        # Create config object
        self._config = ConformityConfig(**config_dict)
        return self._config

    def _apply_env_overrides(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides to configuration.

        Args:
            config_dict: Current configuration dictionary

        Returns:
            Updated configuration dictionary
        """
        # Check for OCIO config override
        if ocio_path := os.getenv("OCIO"):
            config_dict["ocio_config_path"] = ocio_path

        # Check for log level override
        if log_level := os.getenv("CONFORMITY_LOG_LEVEL"):
            config_dict["log_level"] = log_level

        return config_dict

    def get_config(self) -> ConformityConfig:
        """
        Get the current configuration, loading it if necessary.

        Returns:
            Current configuration object
        """
        if self._config is None:
            return self.load_config()
        return self._config

    def save_config(self, config: ConformityConfig, path: Optional[Path] = None) -> None:
        """
        Save configuration to file.

        Args:
            config: Configuration object to save
            path: Optional path to save to (defaults to current config path)
        """
        save_path = path or self._config_path
        save_path.parent.mkdir(parents=True, exist_ok=True)

        config_dict = config.model_dump(mode='json', exclude_none=True)

        with open(save_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False)


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> ConformityConfig:
    """Get the current application configuration."""
    return get_config_manager().get_config()
