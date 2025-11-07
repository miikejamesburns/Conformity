# OpenTimelineIO Data Structures in Conformity

This document explains the OTIO data structures used throughout Conformity and how they're manipulated during conform operations.

## Overview

OpenTimelineIO (OTIO) is an open-source API and interchange format for editorial timeline information. Conformity uses OTIO as the core representation for all timeline data.

## Core Data Structures

### Timeline

The top-level container for all timeline data.

```python
timeline = otio.schema.Timeline(
    name="My Project",
    global_start_time=otio.opentime.RationalTime(0, 24)
)
```

**Key Properties:**
- `name`: Timeline name
- `tracks`: Stack of tracks (video, audio, etc.)
- `global_start_time`: Starting timecode for the timeline
- `metadata`: Dictionary for custom metadata

**In Conformity:**
- Created during import from various formats (EDL, XML, AAF)
- Analyzed to extract clip information
- Validated for conform operations
- Exported to different formats

### Stack

Container for tracks, organizes them hierarchically.

```python
stack = otio.schema.Stack(
    name="Main Stack",
    children=[video_track, audio_track]
)
timeline.tracks = stack
```

**Key Properties:**
- `children`: List of tracks
- Automatically created in Timeline.tracks

### Track

Represents a single track (video or audio) in the timeline.

```python
track = otio.schema.Track(
    name="V1",
    kind=otio.schema.TrackKind.Video
)
```

**Track Kinds:**
- `Video`: Video track
- `Audio`: Audio track

**Key Properties:**
- `name`: Track name (e.g., "V1", "A1")
- `kind`: Type of track (Video/Audio)
- Children can be: Clips, Transitions, Gaps

**In Conformity:**
- Parsed to count clips and organize timeline structure
- Displayed in tree view in ConformPanel
- Used for organizing conform operations

### Clip

Represents a piece of media in the timeline.

```python
clip = otio.schema.Clip(
    name="Shot_001",
    media_reference=external_ref,
    source_range=time_range
)
```

**Key Properties:**
- `name`: Clip name
- `media_reference`: Reference to source media
- `source_range`: Time range of clip (in/out points)
- `available_range`: Full range of available media
- `effects`: List of effects applied to clip
- `markers`: List of markers on clip
- `metadata`: Custom metadata dictionary

**Source Range Example:**
```python
source_range = otio.opentime.TimeRange(
    start_time=otio.opentime.RationalTime(100, 24),  # Frame 100 at 24fps
    duration=otio.opentime.RationalTime(150, 24)     # 150 frames long
)
```

**In Conformity:**
- Primary unit of conform operations
- Matched to media files during conform
- Validated for correct timecode ranges
- Color spaces assigned via metadata
- Displayed with details in ConformPanel

### Media References

References to source media files.

#### ExternalReference

Reference to a media file on disk.

```python
media_ref = otio.schema.ExternalReference(
    target_url="/path/to/media/shot_001.mov",
    available_range=otio.opentime.TimeRange(
        start_time=otio.opentime.RationalTime(0, 24),
        duration=otio.opentime.RationalTime(1000, 24)
    )
)
```

**Key Properties:**
- `target_url`: Path to media file
- `available_range`: Available media duration

**In Conformity:**
- Used for relinking media during conform
- Verified during validation
- Updated during path remapping

#### MissingReference

Placeholder for missing media.

```python
missing_ref = otio.schema.MissingReference()
```

**In Conformity:**
- Flagged during validation
- Reported in conform reports
- Can be updated to ExternalReference when media is found

### Transition

Represents a transition between two clips (dissolve, wipe, etc.).

```python
transition = otio.schema.Transition(
    name="Dissolve",
    transition_type="SMPTE_Dissolve",
    in_offset=otio.opentime.RationalTime(12, 24),
    out_offset=otio.opentime.RationalTime(12, 24)
)
```

**Key Properties:**
- `name`: Transition name
- `transition_type`: Type of transition
- `in_offset`: Duration from end of outgoing clip
- `out_offset`: Duration from start of incoming clip

**In Conformity:**
- Counted during timeline parsing
- Preserved during export
- May trigger warnings if not supported by target format

### Gap

Represents empty space in a track.

```python
gap = otio.schema.Gap(
    source_range=otio.opentime.TimeRange(
        start_time=otio.opentime.RationalTime(0, 24),
        duration=otio.opentime.RationalTime(24, 24)  # 1 second gap
    )
)
```

**In Conformity:**
- Detected during parsing
- Preserved in timeline structure
- Not counted as clips

### Marker

Represents a marker on a clip or timeline.

```python
marker = otio.schema.Marker(
    name="VFX Shot",
    marked_range=otio.opentime.TimeRange(
        start_time=otio.opentime.RationalTime(50, 24),
        duration=otio.opentime.RationalTime(0, 24)
    ),
    color=otio.schema.MarkerColor.RED
)
```

**Key Properties:**
- `name`: Marker name
- `marked_range`: Time range for marker
- `color`: Marker color
- `metadata`: Custom metadata

**In Conformity:**
- Extracted during clip parsing
- Displayed in clip details
- Preserved during export

### Effect

Represents an effect applied to a clip.

```python
effect = otio.schema.Effect(
    name="Color Correction",
    effect_name="color_grade"
)
```

**In Conformity:**
- Listed in clip details
- May trigger unsupported feature warnings
- Metadata preserved when possible

## Time Representation

### RationalTime

Represents a point in time with frame accuracy.

```python
time = otio.opentime.RationalTime(
    value=100,  # Frame number
    rate=24     # Frame rate (fps)
)
```

**Operations:**
```python
# Convert to seconds
seconds = time.to_seconds()  # 100/24 = 4.166...

# Arithmetic
time2 = time + otio.opentime.RationalTime(50, 24)
time3 = time - otio.opentime.RationalTime(10, 24)

# Comparison
if time > time2:
    pass
```

**In Conformity:**
- Used for all time calculations
- Formatted as timecode (HH:MM:SS:FF)
- Validated for negative values

### TimeRange

Represents a time range with start time and duration.

```python
time_range = otio.opentime.TimeRange(
    start_time=otio.opentime.RationalTime(100, 24),
    duration=otio.opentime.RationalTime(150, 24)
)
```

**Properties:**
```python
start = time_range.start_time
end = time_range.end_time_exclusive()
duration = time_range.duration
```

**In Conformity:**
- Used for clip source ranges
- Validated for correct values
- Used in conform matching

## Metadata

All OTIO objects support custom metadata via a dictionary.

```python
clip.metadata = {
    "color": {
        "input_color_space": "ACEScg",
        "display": "ACES",
        "view": "sRGB"
    },
    "conform": {
        "original_path": "/original/location/shot.mov",
        "relinked": True
    }
}
```

**In Conformity:**
- Used for color space assignments
- Stores conform-related data
- Preserved during import/export when possible

## Common Operations

### Creating a Timeline from Scratch

```python
# Create timeline
timeline = otio.schema.Timeline(name="New Project")

# Create video track
video_track = otio.schema.Track(
    name="V1",
    kind=otio.schema.TrackKind.Video
)

# Create clip with media
media_ref = otio.schema.ExternalReference(
    target_url="/media/shot_001.mov"
)

clip = otio.schema.Clip(
    name="Shot 001",
    media_reference=media_ref,
    source_range=otio.opentime.TimeRange(
        start_time=otio.opentime.RationalTime(0, 24),
        duration=otio.opentime.RationalTime(100, 24)
    )
)

# Add to track and timeline
video_track.append(clip)
timeline.tracks.append(video_track)
```

### Iterating Through Clips

```python
for track in timeline.tracks:
    for item in track:
        if isinstance(item, otio.schema.Clip):
            print(f"Clip: {item.name}")
            if item.media_reference:
                if isinstance(item.media_reference, otio.schema.ExternalReference):
                    print(f"  Media: {item.media_reference.target_url}")
```

### Modifying Clip Media Reference

```python
# Relink clip to new media
new_ref = otio.schema.ExternalReference(
    target_url="/new/path/shot_001.mov"
)
clip.media_reference = new_ref
```

### Adding Metadata

```python
# Add color space metadata
if "color" not in clip.metadata:
    clip.metadata["color"] = {}

clip.metadata["color"]["input_color_space"] = "ACEScg"
```

## Conform Workflow in Conformity

### 1. Import

```
File (EDL/XML/AAF) → OTIO Adapter → Timeline Object
```

The ConformEngine uses OTIO adapters to read various formats:

```python
timeline = otio.adapters.read_from_file(
    "project.xml",
    adapter_name="fcp_xml"
)
```

### 2. Parse

```
Timeline → Extract Structure → TimelineInfo
```

ConformEngine walks the timeline hierarchy:

```python
info = conform_engine.parse_timeline(timeline)
# Returns TimelineInfo with clips, tracks, metadata
```

### 3. Validate

```
Timeline → Check Integrity → Validation Results
```

Validation checks:
- Negative timecodes
- Zero/negative durations
- Missing media references
- Unsupported features

### 4. Conform

```
Timeline + Media Mapping → Update References → Conformed Timeline
```

Operations:
- Match clips to media files
- Relink media references
- Assign color spaces
- Generate conform reports

### 5. Export

```
Timeline → OTIO Adapter → File (EDL/XML/etc.)
```

Export to various formats:

```python
conform_engine.export_timeline(
    timeline,
    Path("output.edl"),
    format=TimelineFormat.EDL
)
```

## Data Structure in ConformPanel UI

The ConformPanel displays OTIO structure as a tree:

```
Timeline: "My Project"
├── Track: "V1" (Video)
│   ├── Clip: "Shot_001"
│   ├── Transition: "Dissolve"
│   ├── Clip: "Shot_002"
│   └── Gap
└── Track: "A1" (Audio)
    ├── Clip: "Audio_001"
    └── Clip: "Audio_002"
```

Each tree item stores its OTIO object in UserRole data for detail display.

## Error Handling

### Missing Media

```python
if isinstance(clip.media_reference, otio.schema.MissingReference):
    # Handle missing media
    logger.warning(f"Missing media for clip: {clip.name}")
```

### Invalid Timecode

```python
if clip.source_range.start_time.value < 0:
    raise InvalidTimecodeError(
        str(clip.source_range.start_time),
        "Negative start time"
    )
```

### Unsupported Features

```python
if isinstance(item, UnsupportedType):
    info.unsupported_features.append(type(item).__name__)
```

## Best Practices

### 1. Always Check Types

```python
if isinstance(item, otio.schema.Clip):
    # Process clip
elif isinstance(item, otio.schema.Transition):
    # Process transition
```

### 2. Handle Missing References

```python
if clip.media_reference:
    if isinstance(clip.media_reference, otio.schema.ExternalReference):
        path = clip.media_reference.target_url
        # Verify path exists
```

### 3. Preserve Metadata

When modifying timelines, preserve existing metadata:

```python
original_metadata = clip.metadata.copy()
# Make changes
clip.metadata.update(original_metadata)
```

### 4. Use Try/Except for Adapters

```python
try:
    timeline = otio.adapters.read_from_file(path)
except otio.exceptions.OTIOError as e:
    # Handle adapter errors
    logger.error(f"Failed to read timeline: {e}")
```

## References

- [OTIO Documentation](https://opentimelineio.readthedocs.io/)
- [OTIO GitHub](https://github.com/AcademySoftwareFoundation/OpenTimelineIO)
- [OTIO Schema Reference](https://opentimelineio.readthedocs.io/en/latest/tutorials/otio-timeline-structure.html)

## See Also

- `conform_engine.py`: Implementation of conform operations
- `conform_panel.py`: UI for conform workflow
- `test_conform_engine.py`: Unit tests demonstrating OTIO usage
