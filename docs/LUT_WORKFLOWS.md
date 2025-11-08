# LUT Management Workflows

Comprehensive guide to LUT (Look-Up Table) management and application in Conformity.

## Overview

Conformity provides professional LUT support for color grading workflows:

- **LUT Loading**: Support for .cube and .3dl formats
- **1D and 3D LUTs**: Full support for both LUT types
- **Library Management**: Organize LUTs with categories, favorites, and tags
- **Metadata Tracking**: Track usage, notes, and descriptions
- **Timeline Integration**: Apply LUTs to clips and entire timelines
- **Trilinear Interpolation**: High-quality 3D LUT application

## Quick Start

### Loading a LUT

```python
from conformity.lut_manager import LUTLoader

loader = LUTLoader()
lut = loader.load("path/to/lut.cube")

print(f"LUT: {lut.name}")
print(f"Type: {lut.lut_type.value}")
print(f"Size: {lut.size}")
```

### Applying a LUT to RGB Values

```python
import numpy as np

# Input RGB values (0-1 range)
rgb = np.array([[0.5, 0.3, 0.8]])

# Apply LUT
result = lut.apply(rgb)

print(f"Result: {result}")
```

### Using the LUT Manager

```python
from conformity.lut_manager import LUTManager
from pathlib import Path

manager = LUTManager()

# Scan directory for LUTs
count = manager.scan_directory(
    Path("/path/to/luts"),
    category="Cinematic",
    recursive=True
)

print(f"Found {count} LUTs")

# Get statistics
stats = manager.get_statistics()
print(f"Total LUTs: {stats['total_luts']}")
print(f"Favorites: {stats['favorites']}")
```

## LUT Formats

### CUBE Format (.cube)

Adobe Cube LUT format - the most common format.

**Example**:
```
TITLE "My LUT"
DOMAIN_MIN 0.0 0.0 0.0
DOMAIN_MAX 1.0 1.0 1.0
LUT_3D_SIZE 33

# RGB data
0.000000 0.000000 0.000000
0.031250 0.000000 0.000000
...
```

### 3DL Format (.3dl)

Autodesk/Lustre 3D LUT format.

## Library Management

### Creating a Library

```python
from conformity.lut_manager import LUTLibrary, LUTMetadata

library = LUTLibrary(name="My LUT Library")

# Add LUT metadata
metadata = LUTMetadata(
    name="Vintage Film",
    file_path="/path/to/vintage.cube",
    format="cube",
    category="Film Emulation",
    description="Kodak Vision3 look",
    tags=["vintage", "film", "warm"],
    favorite=True
)

library.add_lut(metadata)
```

### Searching and Filtering

```python
# Search by name or tags
results = library.search("vintage")

# Get favorites
favorites = library.get_favorites()

# Get by category
film_luts = library.get_by_category("Film Emulation")
```

### Saving and Loading Libraries

```python
# Save library
manager.save_library(Path("my_library.json"))

# Load library
manager.load_library(Path("my_library.json"))
```

## Timeline Integration

### Apply LUT to a Clip

```python
import opentimelineio as otio
from conformity.lut_manager import LUTManager

manager = LUTManager()

# Apply LUT to clip
manager.apply_lut_to_clip(
    clip,
    "/path/to/lut.cube"
)

# Check if clip has LUT
lut_path = manager.get_clip_lut(clip)
if lut_path:
    print(f"Clip has LUT: {lut_path}")
```

### Apply LUT to Timeline

```python
# Apply to all clips in timeline
count = manager.apply_lut_to_timeline(
    timeline,
    "/path/to/lut.cube"
)

print(f"Applied LUT to {count} clips")

# Apply only to video tracks
count = manager.apply_lut_to_timeline(
    timeline,
    "/path/to/lut.cube",
    track_kind=otio.schema.TrackKind.Video
)
```

### Remove LUT from Clip

```python
manager.remove_lut_from_clip(clip)
```

## Creating LUTs

### Identity LUT

```python
# Create 3D identity LUT
identity_3d = manager.create_identity_lut(size=33, lut_type="3D")

# Create 1D identity LUT
identity_1d = manager.create_identity_lut(size=1024, lut_type="1D")

# Save it
loader.save_cube(identity_3d, Path("identity.cube"))
```

## Best Practices

### LUT Organization

1. **Use Categories**: Organize LUTs by purpose (e.g., "Color Correction", "Creative Looks", "Technical")
2. **Tag Liberally**: Use tags for quick filtering ("warm", "cool", "vintage", "modern")
3. **Mark Favorites**: Star frequently-used LUTs for quick access
4. **Add Descriptions**: Document what each LUT does and when to use it

### File Naming

- Use descriptive names: `vintage_kodak_5219.cube` not `lut1.cube`
- Include size for identity LUTs: `identity_33.cube`
- Indicate purpose: `rec709_to_aces.cube`

### Performance

- **3D LUT Size**: 33x33x33 is standard and provides good quality/performance balance
- **1D LUT Size**: 1024-4096 points for smooth gradations
- **Caching**: LUTs are cached after first load for faster application

### Integration with Color Management

LUTs work alongside the OCIO color management system:

1. **Input Color Space**: Apply first (via OCIO)
2. **LUT**: Apply creative look
3. **Output Transform**: Apply last (via OCIO)

```python
# Typical workflow
# 1. Set input color space
color_manager.assign_color_space(clip, "LogC")

# 2. Apply creative LUT
lut_manager.apply_lut_to_clip(clip, "vintage_look.cube")

# 3. Output transform handled by display
```

## API Reference

### LUTLoader

```python
class LUTLoader:
    def load(file_path: Path) -> LUTData
    def save_cube(lut_data: LUTData, file_path: Path) -> None
```

### LUTManager

```python
class LUTManager:
    def scan_directory(directory: Path, category: str, recursive: bool) -> int
    def load_lut(file_path: Path) -> LUTData
    def apply_lut_to_clip(clip: Clip, lut_file_path: Path) -> None
    def apply_lut_to_timeline(timeline: Timeline, lut_file_path: Path) -> int
    def remove_lut_from_clip(clip: Clip) -> None
    def create_identity_lut(size: int, lut_type: str) -> LUTData
    def save_library(file_path: Path) -> None
    def load_library(file_path: Path) -> None
    def get_statistics() -> Dict
```

### LUTData

```python
class LUTData:
    name: str
    format: LUTFormat
    lut_type: LUTType  # LUT_1D or LUT_3D
    size: int
    domain_min: Tuple[float, float, float]
    domain_max: Tuple[float, float, float]
    data: np.ndarray

    def apply(rgb: np.ndarray) -> np.ndarray
```

### LUTLibrary

```python
class LUTLibrary:
    name: str
    luts: Dict[str, LUTMetadata]
    categories: List[str]

    def add_lut(metadata: LUTMetadata) -> None
    def remove_lut(file_path: str) -> None
    def get_favorites() -> List[LUTMetadata]
    def get_by_category(category: str) -> List[LUTMetadata]
    def search(query: str) -> List[LUTMetadata]
```

## Examples

### Batch Apply LUT to Multiple Timelines

```python
from pathlib import Path

timelines_dir = Path("/path/to/timelines")
lut_path = Path("/path/to/creative_look.cube")

for timeline_file in timelines_dir.glob("*.otio"):
    timeline = otio.adapters.read_from_file(str(timeline_file))

    count = manager.apply_lut_to_timeline(timeline, lut_path)

    # Save modified timeline
    otio.adapters.write_to_file(timeline, str(timeline_file))

    print(f"Applied LUT to {count} clips in {timeline_file.name}")
```

### Create LUT Collection

```python
lut_dirs = [
    ("/path/to/creative", "Creative"),
    ("/path/to/technical", "Technical"),
    ("/path/to/film-em", "Film Emulation")
]

for directory, category in lut_dirs:
    count = manager.scan_directory(
        Path(directory),
        category=category,
        recursive=True
    )
    print(f"Added {count} LUTs from {category}")

manager.save_library(Path("my_collection.json"))
```

### LUT Preview

```python
# Load LUT
lut = manager.load_lut("/path/to/lut.cube")

# Create color ramp for preview
import numpy as np
ramp = np.linspace(0, 1, 256)
colors = np.column_stack([ramp, ramp, ramp])

# Apply LUT to ramp
result = lut.apply(colors)

# Visualize with matplotlib
import matplotlib.pyplot as plt
plt.plot(ramp, result[:, 0], 'r-', label='Red')
plt.plot(ramp, result[:, 1], 'g-', label='Green')
plt.plot(ramp, result[:, 2], 'b-', label='Blue')
plt.legend()
plt.show()
```

## Troubleshooting

**Issue: "Unsupported LUT format"**
- Only .cube and .3dl formats are currently supported
- Verify file extension
- Check file is valid CUBE or 3DL format

**Issue: "LUT data size mismatch"**
- CUBE file may be corrupted
- Verify LUT_3D_SIZE matches actual data points
- For 3D LUT, data points = size³

**Issue: "LUT application produces unexpected colors"**
- Verify input color space matches LUT's expected input
- Check domain_min/domain_max match your color range
- Ensure RGB values are in 0-1 range

**Issue: "Performance is slow"**
- 3D LUTs larger than 65³ can be slow
- Use 33³ for realtime performance
- LUTs are cached after first load

## Related Documentation

- [Color Workflows](COLOR_WORKFLOWS.md) - OCIO color management
- [Conform Workflows](CONFORM_WORKFLOWS.md) - Timeline operations
- [README](../README.md) - Main documentation
