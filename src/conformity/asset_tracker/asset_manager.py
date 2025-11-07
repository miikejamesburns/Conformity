"""
Asset management and tracking for media files.

This module provides functionality for tracking, organizing, and managing
media assets used in post-production workflows.
"""

from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from ..core.logger import get_logger

logger = get_logger(__name__)


class AssetStatus(Enum):
    """Status of an asset."""
    ONLINE = "online"
    OFFLINE = "offline"
    PENDING = "pending"
    ERROR = "error"


class AssetType(Enum):
    """Type of media asset."""
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    SEQUENCE = "sequence"
    OTHER = "other"


@dataclass
class Asset:
    """Represents a media asset."""

    path: Path
    name: str
    asset_type: AssetType
    status: AssetStatus = AssetStatus.PENDING
    file_size: Optional[int] = None
    duration: Optional[float] = None
    resolution: Optional[tuple[int, int]] = None
    fps: Optional[float] = None
    color_space: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: Optional[datetime] = None

    def __post_init__(self):
        """Initialize asset after creation."""
        if self.path.exists():
            self.status = AssetStatus.ONLINE
            self.file_size = self.path.stat().st_size
            self.last_modified = datetime.fromtimestamp(
                self.path.stat().st_mtime
            )
        else:
            self.status = AssetStatus.OFFLINE


class AssetManager:
    """Manages media assets and their metadata."""

    def __init__(self):
        """Initialize the asset manager."""
        self._assets: Dict[str, Asset] = {}
        logger.info("AssetManager initialized")

    def register_asset(
        self,
        path: Path,
        asset_type: Optional[AssetType] = None,
        **kwargs
    ) -> Asset:
        """
        Register a new asset.

        Args:
            path: Path to the asset file
            asset_type: Type of asset (auto-detected if not provided)
            **kwargs: Additional asset properties

        Returns:
            Created Asset object
        """
        if asset_type is None:
            asset_type = self._detect_asset_type(path)

        asset = Asset(
            path=path,
            name=path.name,
            asset_type=asset_type,
            **kwargs
        )

        self._assets[str(path)] = asset
        logger.info(f"Registered asset: {path.name} ({asset_type.value})")
        return asset

    def _detect_asset_type(self, path: Path) -> AssetType:
        """
        Auto-detect asset type from file extension.

        Args:
            path: Path to the file

        Returns:
            Detected asset type
        """
        ext = path.suffix.lower()

        video_extensions = {'.mov', '.mp4', '.mxf', '.avi', '.r3d', '.ari', '.braw'}
        audio_extensions = {'.wav', '.aif', '.aiff', '.mp3', '.aac'}
        image_extensions = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.exr', '.dpx'}

        if ext in video_extensions:
            return AssetType.VIDEO
        elif ext in audio_extensions:
            return AssetType.AUDIO
        elif ext in image_extensions:
            return AssetType.IMAGE
        else:
            return AssetType.OTHER

    def get_asset(self, path: Path) -> Optional[Asset]:
        """
        Get an asset by path.

        Args:
            path: Path to the asset

        Returns:
            Asset object or None if not found
        """
        return self._assets.get(str(path))

    def get_all_assets(self) -> List[Asset]:
        """
        Get all registered assets.

        Returns:
            List of all assets
        """
        return list(self._assets.values())

    def get_assets_by_type(self, asset_type: AssetType) -> List[Asset]:
        """
        Get all assets of a specific type.

        Args:
            asset_type: Type of assets to retrieve

        Returns:
            List of matching assets
        """
        return [
            asset for asset in self._assets.values()
            if asset.asset_type == asset_type
        ]

    def get_assets_by_status(self, status: AssetStatus) -> List[Asset]:
        """
        Get all assets with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of matching assets
        """
        return [
            asset for asset in self._assets.values()
            if asset.status == status
        ]

    def update_asset_status(self, path: Path, status: AssetStatus) -> None:
        """
        Update the status of an asset.

        Args:
            path: Path to the asset
            status: New status
        """
        asset = self.get_asset(path)
        if asset:
            asset.status = status
            logger.info(f"Updated asset status: {path.name} -> {status.value}")
        else:
            logger.warning(f"Asset not found: {path}")

    def verify_assets(self) -> Dict[str, int]:
        """
        Verify all assets and update their status.

        Returns:
            Dictionary with counts of assets by status
        """
        logger.info("Verifying all assets...")

        status_counts = {status: 0 for status in AssetStatus}

        for asset in self._assets.values():
            if asset.path.exists():
                asset.status = AssetStatus.ONLINE
                # Update file size and modification time
                asset.file_size = asset.path.stat().st_size
                asset.last_modified = datetime.fromtimestamp(
                    asset.path.stat().st_mtime
                )
            else:
                asset.status = AssetStatus.OFFLINE

            status_counts[asset.status] += 1

        logger.info(f"Verification complete: {status_counts}")
        return {status.value: count for status, count in status_counts.items()}

    def scan_directory(
        self,
        directory: Path,
        recursive: bool = True,
        extensions: Optional[Set[str]] = None
    ) -> int:
        """
        Scan a directory and register all media files.

        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories
            extensions: Set of file extensions to include (None for all)

        Returns:
            Number of assets registered
        """
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return 0

        logger.info(f"Scanning directory: {directory}")

        count = 0
        pattern = "**/*" if recursive else "*"

        for path in directory.glob(pattern):
            if path.is_file():
                if extensions is None or path.suffix.lower() in extensions:
                    if str(path) not in self._assets:
                        self.register_asset(path)
                        count += 1

        logger.info(f"Registered {count} new assets from {directory}")
        return count

    def get_statistics(self) -> Dict[str, any]:
        """
        Get statistics about registered assets.

        Returns:
            Dictionary with asset statistics
        """
        total_assets = len(self._assets)
        total_size = sum(
            asset.file_size for asset in self._assets.values()
            if asset.file_size is not None
        )

        type_counts = {}
        for asset_type in AssetType:
            type_counts[asset_type.value] = len(self.get_assets_by_type(asset_type))

        status_counts = {}
        for status in AssetStatus:
            status_counts[status.value] = len(self.get_assets_by_status(status))

        stats = {
            "total_assets": total_assets,
            "total_size_bytes": total_size,
            "total_size_gb": round(total_size / (1024**3), 2),
            "by_type": type_counts,
            "by_status": status_counts,
        }

        logger.debug(f"Asset statistics: {stats}")
        return stats

    def clear_assets(self) -> None:
        """Clear all registered assets."""
        self._assets.clear()
        logger.info("Cleared all assets")
