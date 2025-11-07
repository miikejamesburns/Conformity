# Conform Operations Guide

This guide explains how to use Conformity's automated conform functionality for timeline import, export, and conform operations.

## Overview

The conform functionality allows you to:
- Import timelines from various formats (EDL, XML, AAF, FCPXML)
- Parse and analyze timeline structure
- Validate timelines for errors
- Export to different formats
- Match clips to media files
- Perform conform operations

## UI Workflow

### Importing a Timeline

1. **Open the Conform Tab**
   - Launch Conformity
   - Click on the "Conform" tab

2. **Select Timeline File**
   - Click "Browse..."
   - Navigate to your timeline file
   - Supported formats: `.otio`, `.edl`, `.xml`, `.fcpxml`, `.aaf`, `.ale`

3. **Configure Import Options**
   - **Format**: Auto-detect or specify format explicitly
   - **Verify Media**: Check if referenced media files exist

4. **Import**
   - Click "Import" button
   - Timeline structure appears in tree view
   - Summary shown in details panel

### Viewing Timeline Structure

The tree view shows the complete timeline hierarchy:

```
Timeline
├── Video Track (V1)
│   ├── Clip: "Shot_001"
│   ├── Transition: "Dissolve"
│   └── Clip: "Shot_002"
└── Audio Track (A1)
    └── Clip: "Audio_001"
```

**Click any item** to see detailed information:
- Timeline: Overall statistics, unsupported features
- Track: Kind, duration, item count
- Clip: Media path, timecode, effects, markers, metadata
- Transition: Type, duration
- Gap: Duration

### Validating Timeline

Before export or conform, validate the timeline:

1. Click "Validate" button
2. Review validation results:
   - ✓ Valid timeline
   - Errors (negative timecodes, invalid durations)
   - Warnings (missing media, unsupported features)
   - Missing media list

### Exporting Timeline

1. **Select Export Format**
   - Choose from: OTIO, EDL, FCPXML, XML, AAF, ALE
   - Format availability depends on installed adapters

2. **Export**
   - Click "Export..." button
   - Choose destination file path
   - Timeline exported in selected format

## Programmatic API

### Basic Import/Export

```python
from pathlib import Path
from conformity.conform_engine.conform_engine import ConformEngine, TimelineFormat

# Create engine
engine = ConformEngine()

# Import timeline
timeline, info = engine.import_timeline(
    Path("project.xml"),
    verify_media=True
)

print(f"Imported: {info.num_clips} clips, {info.num_tracks} tracks")

# Export to different format
engine.export_timeline(
    timeline,
    Path("output.edl"),
    format=TimelineFormat.EDL
)
```

### Parsing Timeline Structure

```python
# Parse timeline to get information
info = engine.parse_timeline(timeline, verify_media=True)

# Access timeline information
print(f"Timeline: {info.name}")
print(f"Duration: {info.duration.to_seconds()}s")
print(f"Tracks: {info.num_tracks}")
print(f"Clips: {info.num_clips}")
print(f"Transitions: {info.num_transitions}")

# Iterate through clips
for clip_info in info.clips:
    print(f"Clip: {clip_info.name}")
    print(f"  Path: {clip_info.source_path}")
    print(f"  Duration: {clip_info.duration}")
    print(f"  Track: {clip_info.track_name}")
```

### Validating Timeline

```python
# Validate timeline
results = engine.validate_timeline(timeline, check_media=True)

if results['valid']:
    print("Timeline is valid!")
else:
    print("Timeline has errors:")
    for error in results['errors']:
        print(f"  - {error}")

# Check for missing media
if results['missing_media']:
    print("Missing media files:")
    for media in results['missing_media']:
        print(f"  Clip: {media['clip']}")
        print(f"  Path: {media['path']}")
```

### Format Detection

```python
from conformity.conform_engine.conform_engine import TimelineFormat

# Detect format from extension
fmt = TimelineFormat.from_extension('.edl')
print(f"Format: {fmt.name}, Adapter: {fmt.value}")

# Check supported formats
formats = engine.get_supported_formats()
print("Import formats:", formats['import'])
print("Export formats:", formats['export'])
```

## Advanced Operations

### Custom Import with Adapter Arguments

```python
# Import with custom adapter arguments
timeline, info = engine.import_timeline(
    Path("project.xml"),
    adapter_name="fcp_xml",
)

# Some adapters support additional arguments
adapter_args = {
    'rate': 24.0,  # Example: force frame rate
}

engine.export_timeline(
    timeline,
    Path("output.edl"),
    format=TimelineFormat.EDL,
    adapter_args=adapter_args
)
```

### Extracting Clip Metadata

```python
info = engine.parse_timeline(timeline)

for clip_info in info.clips:
    print(f"\nClip: {clip_info.name}")

    # Source information
    if clip_info.source_path:
        print(f"  Media: {clip_info.source_path}")

    # Timecode information
    if clip_info.timecode_in and clip_info.timecode_out:
        print(f"  In: {clip_info.timecode_in}")
        print(f"  Out: {clip_info.timecode_out}")

    # Effects
    if clip_info.effects:
        print(f"  Effects: {', '.join(clip_info.effects)}")

    # Markers
    if clip_info.markers:
        print(f"  Markers:")
        for marker in clip_info.markers:
            print(f"    - {marker['name']}")

    # Custom metadata
    if clip_info.metadata:
        print(f"  Metadata: {clip_info.metadata}")
```

### Conform Operations

Combine with conform_ops module for advanced operations:

```python
from conformity.conform_engine.conform_ops import ConformOperations
from conformity.conform_engine.timeline_manager import TimelineManager

# Import timeline
timeline, info = engine.import_timeline(Path("project.xml"))

# Match clips to media files
media_dir = Path("/path/to/media")
matches = ConformOperations.match_clips_by_name(
    timeline,
    media_dir,
    extensions=['.mov', '.mp4', '.mxf']
)

# Create media map for relinking
media_map = {}
for clip_name, paths in matches.items():
    if len(paths) == 1:  # Unambiguous match
        media_map[clip_name] = paths[0]

# Relink clips
relinked_count = ConformOperations.relink_clips(timeline, media_map)
print(f"Relinked {relinked_count} clips")

# Generate conform report
report = ConformOperations.create_conform_report(timeline, matches)
print(f"Match rate: {report['match_rate']:.1f}%")
print(f"Unmatched clips: {report['unmatched_clips']}")

# Save conformed timeline
engine.export_timeline(timeline, Path("conformed.otio"))
```

## Error Handling

### Import Errors

```python
from conformity.conform_engine.exceptions import (
    ImportError, AdapterNotFoundError
)

try:
    timeline, info = engine.import_timeline(Path("project.xml"))
except ImportError as e:
    print(f"Import failed: {e}")
    print(f"File: {e.file_path}")
    print(f"Reason: {e.reason}")
except AdapterNotFoundError as e:
    print(f"Adapter not available: {e.adapter_name}")
```

### Export Errors

```python
from conformity.conform_engine.exceptions import ExportError

try:
    engine.export_timeline(timeline, Path("output.edl"))
except ExportError as e:
    print(f"Export failed: {e}")
    print(f"File: {e.file_path}")
    print(f"Format: {e.format}")
    print(f"Reason: {e.reason}")
```

### Media Errors

```python
from conformity.conform_engine.exceptions import MediaNotFoundError

# Check for missing media during validation
results = engine.validate_timeline(timeline, check_media=True)

if results['missing_media']:
    for media in results['missing_media']:
        print(f"Missing: {media['clip']} -> {media['path']}")
```

## Supported Formats

### Import Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| OTIO | `.otio` | Native OpenTimelineIO format |
| EDL | `.edl` | CMX 3600 Edit Decision List |
| FCP XML | `.xml`, `.fcpxml` | Final Cut Pro XML |
| AAF | `.aaf` | Advanced Authoring Format* |
| ALE | `.ale` | Avid Log Exchange |

\* AAF support requires additional adapter installation

### Export Formats

Same as import formats. Export quality depends on format capabilities:

- **OTIO**: Preserves all data (recommended for roundtrip)
- **EDL**: Limited to cuts, no effects/markers
- **FCP XML**: Good support for clips, effects, markers
- **AAF**: Professional format, requires adapter
- **ALE**: Metadata-focused, limited timeline structure

## Best Practices

### 1. Always Validate Before Export

```python
# Validate first
results = engine.validate_timeline(timeline)

if results['valid']:
    # Safe to export
    engine.export_timeline(timeline, output_path)
else:
    # Fix errors first
    print("Timeline has errors, fix before export")
```

### 2. Use OTIO for Roundtrip

For lossless roundtrip between operations:

```python
# Export to OTIO preserves everything
engine.export_timeline(timeline, Path("backup.otio"), TimelineFormat.OTIO)

# Later, import back with full fidelity
timeline, info = engine.import_timeline(Path("backup.otio"))
```

### 3. Check Format Support

```python
# Check if AAF is available
if engine.is_adapter_available("aaf"):
    engine.export_timeline(timeline, Path("output.aaf"), TimelineFormat.AAF)
else:
    print("AAF adapter not installed")
```

### 4. Handle Unsupported Features

```python
info = engine.parse_timeline(timeline)

if info.unsupported_features:
    print("Warning: Timeline contains unsupported features:")
    for feature in info.unsupported_features:
        print(f"  - {feature}")
    print("These may be lost during export")
```

### 5. Verify Media Before Conform

```python
# Always verify media when importing for conform
timeline, info = engine.import_timeline(
    Path("project.xml"),
    verify_media=True  # Enable verification
)

# Check results
if info.missing_media:
    print(f"Warning: {len(info.missing_media)} media files not found")
```

## Integration with Other Modules

### With Color Manager

```python
from conformity.color_manager.color_pipeline import ColorPipeline

# Import timeline
timeline, info = engine.import_timeline(Path("project.xml"))

# Auto-assign color spaces
color_pipeline = ColorPipeline()
assigned = color_pipeline.auto_assign_color_spaces(timeline)
print(f"Assigned color spaces to {assigned} clips")

# Export with color metadata
engine.export_timeline(timeline, Path("output.otio"))
```

### With Asset Manager

```python
from conformity.asset_tracker.asset_manager import AssetManager

# Import timeline
timeline, info = engine.import_timeline(Path("project.xml"))

# Register media as assets
asset_mgr = AssetManager()
for clip_info in info.clips:
    if clip_info.source_path:
        asset_mgr.register_asset(
            Path(clip_info.source_path),
            metadata={'clip_name': clip_info.name}
        )

# Verify assets
status = asset_mgr.verify_assets()
print(f"Online: {status['online']}, Offline: {status['offline']}")
```

## Troubleshooting

### Timeline Won't Import

1. Check file format is supported
2. Verify file is not corrupted
3. Check adapter is available: `engine.get_supported_formats()`
4. Review error message for specific issue

### Missing Media After Import

1. Check media paths are absolute (not relative)
2. Verify media files haven't moved
3. Use conform operations to relink

### Export Fails

1. Ensure target format supports timeline features
2. Check for unsupported features: `info.unsupported_features`
3. Validate timeline before export
4. Verify adapter is available

### Validation Errors

1. Review specific error messages
2. Check for negative timecodes
3. Verify clip durations are positive
4. Fix source timeline and re-import

## Command Line Usage

(Future feature - batch processing)

```bash
# Import and validate
python -m conformity.conform_cli validate project.xml

# Convert between formats
python -m conformity.conform_cli convert project.xml output.edl

# Generate conform report
python -m conformity.conform_cli report project.xml --media-dir /path/to/media
```

## See Also

- [OTIO Data Structures](OTIO_DATA_STRUCTURES.md) - Detailed OTIO reference
- [Architecture](ARCHITECTURE.md) - System architecture
- [Quick Start](QUICKSTART.md) - Getting started guide
- API Reference: `conform_engine.py`, `conform_panel.py`
