"""
LUT loader for parsing and loading various LUT formats.

Supports:
- .cube files (Adobe Cube LUT format)
- .3dl files (Autodesk/Lustre 3D LUT)
- 1D and 3D LUTs
"""

import re
import numpy as np
from pathlib import Path
from typing import Optional, Union, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..core.logger import get_logger

logger = get_logger(__name__)


class LUTFormat(Enum):
    """Supported LUT formats."""
    CUBE = "cube"
    LUT_3DL = "3dl"
    UNKNOWN = "unknown"

    @classmethod
    def from_extension(cls, ext: str) -> 'LUTFormat':
        """Get format from file extension."""
        ext_map = {
            '.cube': cls.CUBE,
            '.3dl': cls.LUT_3DL,
        }
        return ext_map.get(ext.lower(), cls.UNKNOWN)


class LUTType(Enum):
    """LUT dimensionality."""
    LUT_1D = "1D"
    LUT_3D = "3D"


@dataclass
class LUTData:
    """
    Container for LUT data.

    Attributes:
        name: LUT name
        format: LUT file format
        lut_type: 1D or 3D LUT
        size: LUT size (samples per dimension)
        domain_min: Input domain minimum (RGB)
        domain_max: Input domain maximum (RGB)
        data: LUT data array
        title: Optional title from LUT file
        comments: Comments from LUT file
        metadata: Additional metadata
    """
    name: str
    format: LUTFormat
    lut_type: LUTType
    size: int
    domain_min: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    domain_max: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    data: Optional[np.ndarray] = None
    title: Optional[str] = None
    comments: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def apply(self, rgb: np.ndarray) -> np.ndarray:
        """
        Apply LUT to RGB values.

        Args:
            rgb: Input RGB array (shape: [..., 3])

        Returns:
            Transformed RGB array
        """
        if self.data is None:
            raise ValueError("LUT data not loaded")

        # Ensure input is numpy array
        rgb = np.asarray(rgb, dtype=np.float32)
        original_shape = rgb.shape

        # Reshape to [..., 3]
        rgb_flat = rgb.reshape(-1, 3)

        # Normalize to domain
        rgb_normalized = (rgb_flat - np.array(self.domain_min)) / \
                        (np.array(self.domain_max) - np.array(self.domain_min))

        # Clamp to [0, 1]
        rgb_normalized = np.clip(rgb_normalized, 0.0, 1.0)

        if self.lut_type == LUTType.LUT_1D:
            result = self._apply_1d(rgb_normalized)
        else:  # 3D LUT
            result = self._apply_3d(rgb_normalized)

        # Reshape back to original
        return result.reshape(original_shape)

    def _apply_1d(self, rgb: np.ndarray) -> np.ndarray:
        """Apply 1D LUT (per-channel interpolation)."""
        result = np.zeros_like(rgb)

        for channel in range(3):
            # Scale to LUT indices
            indices = rgb[:, channel] * (self.size - 1)

            # Linear interpolation
            idx_low = np.floor(indices).astype(int)
            idx_high = np.ceil(indices).astype(int)

            # Clamp indices
            idx_low = np.clip(idx_low, 0, self.size - 1)
            idx_high = np.clip(idx_high, 0, self.size - 1)

            # Interpolation weight
            weight = indices - idx_low

            # Interpolate
            result[:, channel] = (
                self.data[idx_low, channel] * (1 - weight) +
                self.data[idx_high, channel] * weight
            )

        return result

    def _apply_3d(self, rgb: np.ndarray) -> np.ndarray:
        """Apply 3D LUT (trilinear interpolation)."""
        # Scale to LUT indices
        indices = rgb * (self.size - 1)

        # Get surrounding cube indices
        idx_low = np.floor(indices).astype(int)
        idx_high = np.ceil(indices).astype(int)

        # Clamp indices
        idx_low = np.clip(idx_low, 0, self.size - 1)
        idx_high = np.clip(idx_high, 0, self.size - 1)

        # Interpolation weights
        weights = indices - idx_low

        # Extract weights for each dimension
        wr, wg, wb = weights[:, 0], weights[:, 1], weights[:, 2]

        # Get 8 corner values of the cube
        c000 = self.data[idx_low[:, 0], idx_low[:, 1], idx_low[:, 2]]
        c001 = self.data[idx_low[:, 0], idx_low[:, 1], idx_high[:, 2]]
        c010 = self.data[idx_low[:, 0], idx_high[:, 1], idx_low[:, 2]]
        c011 = self.data[idx_low[:, 0], idx_high[:, 1], idx_high[:, 2]]
        c100 = self.data[idx_high[:, 0], idx_low[:, 1], idx_low[:, 2]]
        c101 = self.data[idx_high[:, 0], idx_low[:, 1], idx_high[:, 2]]
        c110 = self.data[idx_high[:, 0], idx_high[:, 1], idx_low[:, 2]]
        c111 = self.data[idx_high[:, 0], idx_high[:, 1], idx_high[:, 2]]

        # Trilinear interpolation
        # Interpolate along R
        c00 = c000 * (1 - wr[:, np.newaxis]) + c100 * wr[:, np.newaxis]
        c01 = c001 * (1 - wr[:, np.newaxis]) + c101 * wr[:, np.newaxis]
        c10 = c010 * (1 - wr[:, np.newaxis]) + c110 * wr[:, np.newaxis]
        c11 = c011 * (1 - wr[:, np.newaxis]) + c111 * wr[:, np.newaxis]

        # Interpolate along G
        c0 = c00 * (1 - wg[:, np.newaxis]) + c10 * wg[:, np.newaxis]
        c1 = c01 * (1 - wg[:, np.newaxis]) + c11 * wg[:, np.newaxis]

        # Interpolate along B
        result = c0 * (1 - wb[:, np.newaxis]) + c1 * wb[:, np.newaxis]

        return result


class CubeLUTParser:
    """Parser for Adobe .cube LUT format."""

    TITLE_PATTERN = re.compile(r'^TITLE\s+"(.+)"', re.IGNORECASE)
    SIZE_PATTERN = re.compile(r'^LUT_(?:1D|3D)_SIZE\s+(\d+)', re.IGNORECASE)
    DOMAIN_MIN_PATTERN = re.compile(r'^DOMAIN_MIN\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', re.IGNORECASE)
    DOMAIN_MAX_PATTERN = re.compile(r'^DOMAIN_MAX\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', re.IGNORECASE)
    LUT_1D_PATTERN = re.compile(r'^LUT_1D_SIZE\s+(\d+)', re.IGNORECASE)
    LUT_3D_PATTERN = re.compile(r'^LUT_3D_SIZE\s+(\d+)', re.IGNORECASE)

    def __init__(self):
        """Initialize the CUBE parser."""
        self.logger = get_logger(__name__)

    def parse(self, file_path: Path) -> LUTData:
        """
        Parse a .cube LUT file.

        Args:
            file_path: Path to .cube file

        Returns:
            LUTData object

        Raises:
            ValueError: If file format is invalid
        """
        if not file_path.exists():
            raise ValueError(f"LUT file not found: {file_path}")

        self.logger.info(f"Parsing CUBE LUT: {file_path}")

        lut_data = LUTData(
            name=file_path.stem,
            format=LUTFormat.CUBE,
            lut_type=LUTType.LUT_3D,  # Default, will be updated
            size=33  # Default size
        )

        data_lines = []

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # Skip comments
                if line.startswith('#'):
                    lut_data.comments.append(line[1:].strip())
                    continue

                # Parse TITLE
                match = self.TITLE_PATTERN.match(line)
                if match:
                    lut_data.title = match.group(1)
                    self.logger.debug(f"Found title: {lut_data.title}")
                    continue

                # Parse LUT_1D_SIZE
                match = self.LUT_1D_PATTERN.match(line)
                if match:
                    lut_data.size = int(match.group(1))
                    lut_data.lut_type = LUTType.LUT_1D
                    self.logger.debug(f"1D LUT size: {lut_data.size}")
                    continue

                # Parse LUT_3D_SIZE
                match = self.LUT_3D_PATTERN.match(line)
                if match:
                    lut_data.size = int(match.group(1))
                    lut_data.lut_type = LUTType.LUT_3D
                    self.logger.debug(f"3D LUT size: {lut_data.size}")
                    continue

                # Parse DOMAIN_MIN
                match = self.DOMAIN_MIN_PATTERN.match(line)
                if match:
                    lut_data.domain_min = (
                        float(match.group(1)),
                        float(match.group(2)),
                        float(match.group(3))
                    )
                    self.logger.debug(f"Domain min: {lut_data.domain_min}")
                    continue

                # Parse DOMAIN_MAX
                match = self.DOMAIN_MAX_PATTERN.match(line)
                if match:
                    lut_data.domain_max = (
                        float(match.group(1)),
                        float(match.group(2)),
                        float(match.group(3))
                    )
                    self.logger.debug(f"Domain max: {lut_data.domain_max}")
                    continue

                # Parse data lines (R G B values)
                try:
                    values = line.split()
                    if len(values) == 3:
                        r, g, b = map(float, values)
                        data_lines.append([r, g, b])
                except ValueError:
                    # Not a data line, skip
                    pass

        # Convert data to numpy array
        if not data_lines:
            raise ValueError("No LUT data found in file")

        data_array = np.array(data_lines, dtype=np.float32)

        # Reshape based on LUT type
        if lut_data.lut_type == LUTType.LUT_1D:
            # 1D LUT: shape (size, 3)
            expected_size = lut_data.size
            if len(data_array) != expected_size:
                raise ValueError(
                    f"1D LUT data size mismatch: expected {expected_size}, got {len(data_array)}"
                )
            lut_data.data = data_array

        else:  # 3D LUT
            # 3D LUT: shape (size, size, size, 3)
            expected_size = lut_data.size ** 3
            if len(data_array) != expected_size:
                raise ValueError(
                    f"3D LUT data size mismatch: expected {expected_size}, got {len(data_array)}"
                )
            lut_data.data = data_array.reshape(
                lut_data.size, lut_data.size, lut_data.size, 3
            )

        self.logger.info(
            f"Successfully parsed {lut_data.lut_type.value} LUT with size {lut_data.size}"
        )

        return lut_data


class LUT3DLParser:
    """Parser for Autodesk .3dl LUT format."""

    def __init__(self):
        """Initialize the 3DL parser."""
        self.logger = get_logger(__name__)

    def parse(self, file_path: Path) -> LUTData:
        """
        Parse a .3dl LUT file.

        Args:
            file_path: Path to .3dl file

        Returns:
            LUTData object

        Raises:
            ValueError: If file format is invalid
        """
        if not file_path.exists():
            raise ValueError(f"LUT file not found: {file_path}")

        self.logger.info(f"Parsing 3DL LUT: {file_path}")

        lut_data = LUTData(
            name=file_path.stem,
            format=LUTFormat.LUT_3DL,
            lut_type=LUTType.LUT_3D,
            size=33  # Default, may be detected
        )

        data_lines = []

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Parse data lines (R G B values, typically 0-1023 or 0-4095)
                try:
                    values = line.split()
                    if len(values) == 3:
                        r, g, b = map(int, values)
                        # Normalize from integer range to 0-1
                        # Assume 10-bit (0-1023) or 12-bit (0-4095)
                        max_val = max(r, g, b, 1023)
                        if max_val > 1023:
                            scale = 4095.0
                        else:
                            scale = 1023.0

                        data_lines.append([r / scale, g / scale, b / scale])
                except ValueError:
                    pass

        if not data_lines:
            raise ValueError("No LUT data found in file")

        # Detect size (common sizes: 17, 33, 65)
        total_points = len(data_lines)
        size = round(total_points ** (1/3))

        if size ** 3 != total_points:
            raise ValueError(
                f"3DL LUT data size is not a perfect cube: {total_points} points"
            )

        lut_data.size = size
        lut_data.data = np.array(data_lines, dtype=np.float32).reshape(
            size, size, size, 3
        )

        self.logger.info(f"Successfully parsed 3D LUT with size {size}")

        return lut_data


class LUTLoader:
    """Main LUT loader supporting multiple formats."""

    def __init__(self):
        """Initialize the LUT loader."""
        self.cube_parser = CubeLUTParser()
        self.lut_3dl_parser = LUT3DLParser()
        self.logger = get_logger(__name__)

    def load(self, file_path: Union[str, Path]) -> LUTData:
        """
        Load a LUT file.

        Args:
            file_path: Path to LUT file

        Returns:
            LUTData object

        Raises:
            ValueError: If format is unsupported or file is invalid
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise ValueError(f"LUT file not found: {file_path}")

        format = LUTFormat.from_extension(file_path.suffix)

        if format == LUTFormat.CUBE:
            return self.cube_parser.parse(file_path)
        elif format == LUTFormat.LUT_3DL:
            return self.lut_3dl_parser.parse(file_path)
        else:
            raise ValueError(f"Unsupported LUT format: {file_path.suffix}")

    def save_cube(self, lut_data: LUTData, file_path: Union[str, Path]) -> None:
        """
        Save LUT as .cube format.

        Args:
            lut_data: LUT data to save
            file_path: Destination file path
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            # Write header
            if lut_data.title:
                f.write(f'TITLE "{lut_data.title}"\n')
            else:
                f.write(f'TITLE "{lut_data.name}"\n')

            # Write domain
            f.write(f"DOMAIN_MIN {lut_data.domain_min[0]} {lut_data.domain_min[1]} {lut_data.domain_min[2]}\n")
            f.write(f"DOMAIN_MAX {lut_data.domain_max[0]} {lut_data.domain_max[1]} {lut_data.domain_max[2]}\n")

            # Write size
            if lut_data.lut_type == LUTType.LUT_1D:
                f.write(f"LUT_1D_SIZE {lut_data.size}\n")
            else:
                f.write(f"LUT_3D_SIZE {lut_data.size}\n")

            f.write("\n")

            # Write comments
            for comment in lut_data.comments:
                f.write(f"# {comment}\n")

            if lut_data.comments:
                f.write("\n")

            # Write data
            if lut_data.lut_type == LUTType.LUT_1D:
                for i in range(lut_data.size):
                    r, g, b = lut_data.data[i]
                    f.write(f"{r:.6f} {g:.6f} {b:.6f}\n")
            else:  # 3D LUT
                for b in range(lut_data.size):
                    for g in range(lut_data.size):
                        for r in range(lut_data.size):
                            rgb = lut_data.data[r, g, b]
                            f.write(f"{rgb[0]:.6f} {rgb[1]:.6f} {rgb[2]:.6f}\n")

        self.logger.info(f"Saved LUT to {file_path}")
