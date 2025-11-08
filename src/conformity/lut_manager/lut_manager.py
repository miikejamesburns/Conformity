"""
LUT manager for organizing and managing LUT libraries.

Provides functionality for:
- LUT library organization
- Metadata management
- Favorites and categories
- Search and filtering
- Integration with color management
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
import opentimelineio as otio

from .lut_loader import LUTLoader, LUTData, LUTFormat
from ..core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LUTMetadata:
    """
    Metadata for a LUT.

    Attributes:
        name: LUT name
        file_path: Path to LUT file
        format: LUT format
        category: Category/folder
        description: User description
        tags: List of tags
        favorite: Whether LUT is favorited
        created_date: Creation date
        modified_date: Last modified date
        use_count: Number of times used
        notes: User notes
    """
    name: str
    file_path: str
    format: str
    category: str = "Uncategorized"
    description: str = ""
    tags: List[str] = field(default_factory=list)
    favorite: bool = False
    created_date: Optional[str] = None
    modified_date: Optional[str] = None
    use_count: int = 0
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LUTMetadata':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class LUTLibrary:
    """
    Collection of LUTs with metadata.

    Attributes:
        name: Library name
        description: Library description
        luts: Dictionary of LUT metadata (path -> metadata)
        categories: List of category names
    """
    name: str
    description: str = ""
    luts: Dict[str, LUTMetadata] = field(default_factory=dict)
    categories: List[str] = field(default_factory=list)

    def add_lut(self, metadata: LUTMetadata) -> None:
        """Add a LUT to the library."""
        self.luts[metadata.file_path] = metadata

        # Add category if new
        if metadata.category and metadata.category not in self.categories:
            self.categories.append(metadata.category)

    def remove_lut(self, file_path: str) -> None:
        """Remove a LUT from the library."""
        if file_path in self.luts:
            del self.luts[file_path]

    def get_lut(self, file_path: str) -> Optional[LUTMetadata]:
        """Get LUT metadata by file path."""
        return self.luts.get(file_path)

    def get_favorites(self) -> List[LUTMetadata]:
        """Get all favorite LUTs."""
        return [lut for lut in self.luts.values() if lut.favorite]

    def get_by_category(self, category: str) -> List[LUTMetadata]:
        """Get LUTs in a specific category."""
        return [lut for lut in self.luts.values() if lut.category == category]

    def search(self, query: str) -> List[LUTMetadata]:
        """Search LUTs by name, description, or tags."""
        query_lower = query.lower()
        results = []

        for lut in self.luts.values():
            if (query_lower in lut.name.lower() or
                query_lower in lut.description.lower() or
                any(query_lower in tag.lower() for tag in lut.tags)):
                results.append(lut)

        return results

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'description': self.description,
            'luts': {path: meta.to_dict() for path, meta in self.luts.items()},
            'categories': self.categories
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LUTLibrary':
        """Create from dictionary."""
        library = cls(
            name=data['name'],
            description=data.get('description', ''),
            categories=data.get('categories', [])
        )

        for path, meta_dict in data.get('luts', {}).items():
            library.luts[path] = LUTMetadata.from_dict(meta_dict)

        return library


class LUTManager:
    """Manager for LUT libraries and operations."""

    def __init__(self, library_path: Optional[Path] = None):
        """
        Initialize LUT manager.

        Args:
            library_path: Path to library JSON file
        """
        self.loader = LUTLoader()
        self.library_path = library_path
        self.library: Optional[LUTLibrary] = None
        self.loaded_luts: Dict[str, LUTData] = {}  # Cache of loaded LUTs
        self.logger = get_logger(__name__)

        if library_path and library_path.exists():
            self.load_library(library_path)
        else:
            self.library = LUTLibrary(name="Default Library")

    def scan_directory(
        self,
        directory: Path,
        category: str = "Uncategorized",
        recursive: bool = True
    ) -> int:
        """
        Scan directory for LUT files and add to library.

        Args:
            directory: Directory to scan
            category: Category for discovered LUTs
            recursive: Whether to scan recursively

        Returns:
            Number of LUTs added
        """
        if not directory.exists():
            raise ValueError(f"Directory not found: {directory}")

        self.logger.info(f"Scanning directory for LUTs: {directory}")

        count = 0
        pattern = '**/*' if recursive else '*'

        for file_path in directory.glob(pattern):
            if not file_path.is_file():
                continue

            format = LUTFormat.from_extension(file_path.suffix)
            if format == LUTFormat.UNKNOWN:
                continue

            # Check if already in library
            file_path_str = str(file_path.absolute())
            if file_path_str in self.library.luts:
                continue

            # Create metadata
            metadata = LUTMetadata(
                name=file_path.stem,
                file_path=file_path_str,
                format=format.value,
                category=category,
                created_date=datetime.now().isoformat()
            )

            self.library.add_lut(metadata)
            count += 1
            self.logger.debug(f"Added LUT: {file_path.name}")

        self.logger.info(f"Added {count} LUTs from {directory}")
        return count

    def load_lut(self, file_path: Union[str, Path]) -> LUTData:
        """
        Load a LUT file.

        Args:
            file_path: Path to LUT file

        Returns:
            Loaded LUT data
        """
        file_path_str = str(Path(file_path).absolute())

        # Check cache
        if file_path_str in self.loaded_luts:
            return self.loaded_luts[file_path_str]

        # Load LUT
        lut_data = self.loader.load(file_path)

        # Cache it
        self.loaded_luts[file_path_str] = lut_data

        # Update metadata if in library
        if file_path_str in self.library.luts:
            metadata = self.library.luts[file_path_str]
            metadata.use_count += 1
            metadata.modified_date = datetime.now().isoformat()

        return lut_data

    def apply_lut_to_clip(
        self,
        clip: otio.schema.Clip,
        lut_file_path: Union[str, Path]
    ) -> None:
        """
        Apply LUT to a clip by storing reference in metadata.

        Args:
            clip: OTIO clip
            lut_file_path: Path to LUT file
        """
        file_path_str = str(Path(lut_file_path).absolute())

        # Ensure LUT is loaded and valid
        lut_data = self.load_lut(file_path_str)

        # Store LUT reference in clip metadata
        if 'lut' not in clip.metadata:
            clip.metadata['lut'] = {}

        clip.metadata['lut'] = {
            'file_path': file_path_str,
            'name': lut_data.name,
            'format': lut_data.format.value,
            'applied_date': datetime.now().isoformat()
        }

        self.logger.info(f"Applied LUT '{lut_data.name}' to clip '{clip.name}'")

    def remove_lut_from_clip(self, clip: otio.schema.Clip) -> None:
        """
        Remove LUT from clip.

        Args:
            clip: OTIO clip
        """
        if 'lut' in clip.metadata:
            del clip.metadata['lut']
            self.logger.info(f"Removed LUT from clip '{clip.name}'")

    def get_clip_lut(self, clip: otio.schema.Clip) -> Optional[str]:
        """
        Get LUT file path applied to clip.

        Args:
            clip: OTIO clip

        Returns:
            LUT file path if applied, None otherwise
        """
        if 'lut' in clip.metadata:
            return clip.metadata['lut'].get('file_path')
        return None

    def apply_lut_to_timeline(
        self,
        timeline: otio.schema.Timeline,
        lut_file_path: Union[str, Path],
        track_kind: Optional[otio.schema.TrackKind] = None
    ) -> int:
        """
        Apply LUT to all clips in timeline.

        Args:
            timeline: OTIO timeline
            lut_file_path: Path to LUT file
            track_kind: Optional track kind filter (Video/Audio)

        Returns:
            Number of clips modified
        """
        count = 0

        for track in timeline.tracks:
            # Filter by track kind if specified
            if track_kind and track.kind != track_kind:
                continue

            for item in track:
                if isinstance(item, otio.schema.Clip):
                    self.apply_lut_to_clip(item, lut_file_path)
                    count += 1

        self.logger.info(f"Applied LUT to {count} clips in timeline '{timeline.name}'")
        return count

    def create_identity_lut(
        self,
        size: int = 33,
        lut_type: str = "3D"
    ) -> LUTData:
        """
        Create an identity (pass-through) LUT.

        Args:
            size: LUT size
            lut_type: "1D" or "3D"

        Returns:
            Identity LUT data
        """
        from .lut_loader import LUTType
        import numpy as np

        if lut_type == "1D":
            # 1D identity: straight diagonal
            data = np.linspace(0, 1, size)
            data = np.column_stack([data, data, data]).astype(np.float32)

            lut_data = LUTData(
                name="Identity_1D",
                format=LUTFormat.CUBE,
                lut_type=LUTType.LUT_1D,
                size=size,
                data=data,
                title="Identity 1D LUT"
            )

        else:  # 3D
            # 3D identity: R,G,B = normalized position
            data = np.zeros((size, size, size, 3), dtype=np.float32)

            for r in range(size):
                for g in range(size):
                    for b in range(size):
                        data[r, g, b] = [
                            r / (size - 1),
                            g / (size - 1),
                            b / (size - 1)
                        ]

            lut_data = LUTData(
                name="Identity_3D",
                format=LUTFormat.CUBE,
                lut_type=LUTType.LUT_3D,
                size=size,
                data=data,
                title="Identity 3D LUT"
            )

        return lut_data

    def save_library(self, file_path: Optional[Path] = None) -> None:
        """
        Save library to JSON file.

        Args:
            file_path: Optional file path (uses self.library_path if not provided)
        """
        if file_path is None:
            file_path = self.library_path

        if file_path is None:
            raise ValueError("No library path specified")

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.library.to_dict(), f, indent=2)

        self.library_path = file_path
        self.logger.info(f"Saved library to {file_path}")

    def load_library(self, file_path: Path) -> None:
        """
        Load library from JSON file.

        Args:
            file_path: Path to library file
        """
        if not file_path.exists():
            raise ValueError(f"Library file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.library = LUTLibrary.from_dict(data)
        self.library_path = file_path
        self.logger.info(f"Loaded library from {file_path} ({len(self.library.luts)} LUTs)")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get library statistics.

        Returns:
            Dictionary with statistics
        """
        total_luts = len(self.library.luts)
        favorites = len(self.library.get_favorites())
        categories = len(self.library.categories)

        # Count by format
        format_counts = {}
        for lut in self.library.luts.values():
            format_counts[lut.format] = format_counts.get(lut.format, 0) + 1

        # Most used
        most_used = sorted(
            self.library.luts.values(),
            key=lambda x: x.use_count,
            reverse=True
        )[:5]

        return {
            'total_luts': total_luts,
            'favorites': favorites,
            'categories': categories,
            'formats': format_counts,
            'most_used': [{'name': lut.name, 'count': lut.use_count} for lut in most_used]
        }
