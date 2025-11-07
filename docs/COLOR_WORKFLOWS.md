

# Color Management Workflows in Conformity

This guide explains how to use Conformity's holistic color management system powered by OpenColorIO (OCIO).

## Overview

Conformity provides comprehensive color management throughout the post-production pipeline:

- **OCIO Integration**: Industry-standard color management
- **Automatic Detection**: Smart color space assignment based on metadata and file types
- **Validation**: Pipeline-wide color space compatibility checking
- **Tracking**: Monitor color space assignments across all assets
- **Visualization**: Tree view of color space relationships

## Architecture

### Components

1. **ColorManager**: Core color management engine
   - Validates OCIO configs
   - Tracks color space assignments
   - Detects color spaces from metadata/extensions
   - Generates validation reports

2. **PipelineColorConfig**: Pipeline-wide settings
   - Working color space
   - Default input/output spaces
   - Auto-detection rules
   - Display/view transforms

3. **ColorSpaceWidget**: Interactive UI
   - Load and validate OCIO configs
   - Set pipeline defaults
   - Analyze timelines
   - Assign color spaces manually
   - Export reports

## Getting Started

### 1. Load an OCIO Configuration

**Option A: Via UI**
```
1. Open Conformity
2. Go to Color Management tab
3. Click "Load Config..."
4. Select config file (e.g., simple_config.ocio)
5. Click "Validate" to verify
```

**Option B: Via Environment Variable**
```bash
export OCIO=/path/to/config.ocio
python run.py
```

**Option C: Via Config File**
```yaml
# config/default_config.yaml
ocio_config_path: "config/ocio/simple_config.ocio"
```

### 2. Set Pipeline Defaults

Configure your pipeline's color workflow:

```
Working Color Space: Linear (or ACEScg for ACES)
Default Input: CameraRec709
Display: sRGB
View: Standard
```

Click "Apply Defaults to Timeline" to save.

### 3. Analyze a Timeline

```
1. Import or load a timeline (Conform tab or Timeline tab)
2. Go to Color Management → Timeline Analysis tab
3. Click "Analyze Timeline"
4. Review color space assignments for all clips
```

## Color Space Assignment

### Automatic Assignment

Conformity can automatically assign color spaces using:

1. **Metadata Detection**
   - Reads OTIO clip metadata
   - Checks for `color.input_color_space`
   - Uses existing assignments

2. **Extension-Based Detection**
   ```
   .r3d  → RedWideGamutRGB
   .ari  → ARRI_LogC4
   .braw → BMDFilm_Gen5
   .dng  → CameraRec709
   ```

3. **Pipeline Defaults**
   - Falls back to configured default
   - Ensures all clips have assignments

**To Auto-Assign:**
```
1. Analyze timeline
2. Click "Auto-Assign Color Spaces"
3. Confirm action
4. Review results
```

### Manual Assignment

Override color spaces for specific clips:

```
1. Analyze timeline
2. Select clip from list
3. Choose color space from dropdown
4. Click "Assign"
5. Color space saved to clip metadata
```

### Custom Rules

Add custom detection rules programmatically:

```python
from conformity.color_manager.color_manager import ColorManager

color_mgr = ColorManager()
pipeline_config = color_mgr.get_pipeline_config()

# Add custom rules
pipeline_config.add_rule('.sony', 'SonySLog3')
pipeline_config.add_rule('.canon', 'CanonCLog2')
```

## Validation Workflows

### Timeline Validation

Check entire timeline for color issues:

```python
from conformity.color_manager.color_manager import ColorManager

color_mgr = ColorManager()
color_mgr.load_config(Path("config.ocio"))

# Analyze timeline
result = color_mgr.analyze_timeline(timeline, auto_detect=True)

print(f"Valid: {result.valid_count}")
print(f"Missing: {result.missing_count}")
print(f"Invalid: {result.invalid_count}")

# Check errors
for error in result.errors:
    print(f"ERROR: {error}")

# Check warnings
for warning in result.warnings:
    print(f"WARNING: {warning}")
```

### Color Space Validation

Validate individual assignments:

```python
# Assign with validation
assignment = color_mgr.assign_color_space_to_clip(
    clip,
    input_color_space="ACEScg",
    working_color_space="Linear",
    validate=True  # Validates against loaded OCIO config
)

# Check status
if assignment.status == ColorSpaceStatus.VALID:
    print("✓ Valid assignment")
elif assignment.status == ColorSpaceStatus.INVALID:
    print("✗ Invalid assignment")
    for warning in assignment.warnings:
        print(f"  - {warning}")
```

### Config Validation

Validate OCIO configuration:

```python
valid, errors = color_mgr.validate_config()

if valid:
    print("✓ OCIO config is valid")
else:
    print("✗ Config errors:")
    for error in errors:
        print(f"  - {error}")
```

## Integration with Conform Engine

Color space tracking is integrated with timeline import/export:

### During Import

```python
from conformity.conform_engine.conform_engine import ConformEngine

engine = ConformEngine()
timeline, info = engine.import_timeline(Path("project.xml"))

# Color space info is automatically extracted
for clip_info in info.clips:
    print(f"{clip_info.name}:")
    print(f"  Color Space: {clip_info.input_color_space or 'NOT SET'}")
    if clip_info.color_space_warnings:
        for warning in clip_info.color_space_warnings:
            print(f"  WARNING: {warning}")

# Timeline-level statistics
print(f"\nTimeline Color Summary:")
print(f"  With Color Space: {info.clips_with_color_space}")
print(f"  Without: {info.clips_without_color_space}")
print(f"  Color Spaces Used: {list(info.color_spaces_used.keys())}")
```

### During Export

Color space metadata is preserved:

```python
# Color spaces are embedded in OTIO metadata
engine.export_timeline(timeline, Path("output.otio"))

# Metadata preserved:
# clip.metadata['color'] = {
#     'input_color_space': 'ACEScg',
#     'working_color_space': 'Linear',
#     'display': 'sRGB',
#     'view': 'Standard'
# }
```

## Reporting

### Generate Color Space Report

```python
report = color_mgr.create_color_space_report(timeline)

print(f"Timeline: {report['timeline_name']}")
print(f"Total Clips: {report['total_clips']}")
print(f"Valid: {report['valid_assignments']}")
print(f"Missing: {report['missing_assignments']}")
print(f"Status: {report['validation_status']}")

print("\nColor Spaces Used:")
for cs, count in report['color_spaces_used'].items():
    print(f"  {cs}: {count} clips")

print("\nClip Details:")
for clip in report['clips']:
    print(f"  {clip['name']}: {clip['input_color_space'] or 'NONE'}")
```

### Export Report

Via UI:
```
1. Analyze timeline
2. Click "Export Report..."
3. Choose filename
4. Report saved as text file
```

## Common Workflows

### Workflow 1: ACES Pipeline

```python
# Setup
color_mgr.load_config(Path("aces_config.ocio"))

pipeline = color_mgr.get_pipeline_config()
pipeline.set_defaults(
    working="ACEScg",
    default_input="ACES2065-1",
    default_output="ACEScg",
    display="ACES",
    view="sRGB"
)

# Add camera-specific rules
pipeline.add_rule('.r3d', 'Input - RED - REDWideGamutRGB')
pipeline.add_rule('.ari', 'Input - ARRI - LogC4')

# Auto-assign
count = color_mgr.auto_assign_color_spaces(timeline)
print(f"Assigned ACES color spaces to {count} clips")
```

### Workflow 2: Rec.709 Pipeline

```python
# Setup
color_mgr.load_config(Path("rec709_config.ocio"))

pipeline = color_mgr.get_pipeline_config()
pipeline.set_defaults(
    working="Linear",
    default_input="CameraRec709",
    default_output="Rec709",
    display="sRGB",
    view="Standard"
)

# Auto-assign
color_mgr.auto_assign_color_spaces(timeline)
```

### Workflow 3: Mixed Camera Pipeline

```python
# Setup with multiple camera types
pipeline = color_mgr.get_pipeline_config()
pipeline.set_defaults(
    working="Linear",
    default_input="CameraRec709"
)

# Add rules for each camera
pipeline.add_rule('.r3d', 'RedWideGamutRGB')
pipeline.add_rule('.ari', 'ARRI_LogC4')
pipeline.add_rule('.braw', 'BMDFilm_Gen5')
pipeline.add_rule('.dng', 'CameraRec709')

# Auto-assign - each camera gets correct space
color_mgr.auto_assign_color_spaces(timeline)

# Validate compatibility
result = color_mgr.analyze_timeline(timeline)
if result.invalid_count > 0:
    print("WARNING: Some color spaces are invalid!")
```

## Best Practices

### 1. Always Validate Configs

```python
valid, errors = color_mgr.validate_config()
if not valid:
    raise ValueError(f"Invalid OCIO config: {errors}")
```

### 2. Set Pipeline Defaults Early

```python
# At project start
pipeline = color_mgr.get_pipeline_config()
pipeline.set_defaults(
    working="Linear",
    default_input="CameraRec709"
)
```

### 3. Use Auto-Detection Rules

```python
# Define once, apply everywhere
pipeline.add_rule('.r3d', 'RedWideGamutRGB')
pipeline.add_rule('.ari', 'ARRI_LogC4')
```

### 4. Analyze Before Delivery

```python
# Final check
result = color_mgr.analyze_timeline(timeline)
if result.missing_count > 0:
    print(f"WARNING: {result.missing_count} clips missing color spaces!")
if result.invalid_count > 0:
    print(f"ERROR: {result.invalid_count} clips have invalid color spaces!")
```

### 5. Export Reports for Documentation

```
# Via UI
1. Analyze Timeline
2. Export Report
3. Include in delivery docs
```

## Color Space Relationships

Visualize color space families:

```python
relationships = color_mgr.get_color_space_relationships()

for family, color_spaces in relationships.items():
    print(f"{family}:")
    for cs in color_spaces:
        print(f"  - {cs}")

# Example output:
# Input/RED:
#   - RedWideGamutRGB
#   - RedLog3G10
# Input/ARRI:
#   - ARRI_LogC4
#   - ARRI_LogC3
# ACES:
#   - ACEScg
#   - ACES2065-1
```

## Troubleshooting

### Color Spaces Not Detected

**Problem:** Auto-detection not finding color spaces

**Solutions:**
1. Check metadata: `clip.metadata['color']`
2. Verify file extensions match rules
3. Set pipeline defaults
4. Manually assign if needed

### Invalid Color Space Errors

**Problem:** "Invalid color space" warnings

**Solutions:**
1. Validate OCIO config first
2. Check color space name spelling (case-sensitive)
3. Verify color space exists in loaded config
4. Use color space tree to find valid names

### Timeline Analysis Shows All Missing

**Problem:** All clips show as missing color spaces

**Solutions:**
1. Ensure OCIO config is loaded
2. Run auto-assign first
3. Check that metadata is preserved
4. Verify timeline was imported correctly

### Performance Issues

**Problem:** Slow color space operations

**Solutions:**
1. Validate config once at startup
2. Use auto-assign in batch, not per-clip
3. Cache ColorManager instance
4. Avoid repeated timeline analysis

## Advanced Features

### Custom Color Space Detection

```python
def custom_detector(clip: otio.schema.Clip) -> Optional[str]:
    """Custom color space detection logic."""
    # Check custom metadata fields
    if 'camera_model' in clip.metadata:
        model = clip.metadata['camera_model']
        if model == 'ALEXA35':
            return 'ARRI_LogC4'
        elif model == 'KOMODO':
            return 'RedWideGamutRGB'

    # Check filename patterns
    if clip.media_reference:
        path = Path(clip.media_reference.target_url)
        if '_LOG' in path.stem:
            return 'LogC'
        elif '_LIN' in path.stem:
            return 'Linear'

    return None

# Use in analysis
for clip in timeline.each_clip():
    detected_cs = custom_detector(clip)
    if detected_cs:
        color_mgr.assign_color_space_to_clip(clip, detected_cs)
```

### Batch Processing

```python
# Process multiple timelines
timelines = [
    Path("edit_v1.otio"),
    Path("edit_v2.otio"),
    Path("final.otio")
]

for timeline_path in timelines:
    timeline, info = engine.import_timeline(timeline_path)

    # Auto-assign color spaces
    count = color_mgr.auto_assign_color_spaces(timeline)

    # Validate
    result = color_mgr.analyze_timeline(timeline)

    # Report
    print(f"{timeline.name}:")
    print(f"  Assigned: {count}")
    print(f"  Valid: {result.valid_count}")
    print(f"  Issues: {result.missing_count + result.invalid_count}")

    # Re-export with color metadata
    engine.export_timeline(timeline, timeline_path)
```

## API Reference

See module documentation:
- `color_manager.py` - Core color management
- `ocio_manager.py` - OCIO operations
- `color_pipeline.py` - Timeline integration
- `color_space_widget.py` - UI components

## See Also

- [OCIO Documentation](https://opencolorio.readthedocs.io/)
- [ACES Workflows](https://acescentral.com/)
- [Conform Guide](CONFORM_GUIDE.md)
- [OTIO Data Structures](OTIO_DATA_STRUCTURES.md)
