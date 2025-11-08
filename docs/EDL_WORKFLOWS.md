# EDL Workflows

Comprehensive guide to EDL (Edit Decision List) import/export in Conformity.

## Overview

Conformity provides full support for CMX 3600 EDL format, the industry-standard format for exchanging edit decisions between different post-production systems. EDL support includes:

- **Complete parsing** of CMX 3600 format
- **Reel name management** for source media tracking
- **Comment preservation** for metadata retention
- **Timecode validation** for accuracy
- **Multi-track support** for video and audio
- **Transition handling** for dissolves, wipes, and keys
- **Bidirectional conversion** between OTIO and EDL formats

## Table of Contents

- [Quick Start](#quick-start)
- [Importing EDL Files](#importing-edl-files)
- [Exporting to EDL](#exporting-to-edl)
- [Working with EDL Data](#working-with-edl-data)
- [Advanced Features](#advanced-features)
- [EDL Format Reference](#edl-format-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

## Quick Start

### Basic EDL Import

```python
from pathlib import Path
from conformity.conform_engine.edl_utils import EDLParser

# Parse an EDL file
parser = EDLParser()
edl_info = parser.parse_file(Path("timeline.edl"))

print(f"Title: {edl_info.title}")
print(f"Events: {len(edl_info.events)}")

for event in edl_info.events:
    print(f"  {event.event_number}: {event.clip_name or event.reel_name}")
```

### Basic EDL Export

```python
from conformity.conform_engine.edl_utils import EDLWriter, EDLInfo, EDLEvent
from conformity.conform_engine.edl_utils import TrackType, EditType

# Create EDL data
edl_info = EDLInfo(title="My Timeline", fcm="NON-DROP FRAME")

event = EDLEvent(
    event_number=1,
    reel_name="CLIP001",
    track_type=TrackType.VIDEO,
    edit_type=EditType.CUT,
    source_in="01:00:00:00",
    source_out="01:00:05:00",
    record_in="00:00:00:00",
    record_out="00:00:05:00",
    clip_name="Opening Shot.mov"
)
edl_info.events.append(event)

# Write to file
writer = EDLWriter()
writer.write_file(edl_info, Path("output.edl"))
```

### Converting Between OTIO and EDL

```python
from conformity.conform_engine.edl_utils import EDLConverter
from conformity.conform_engine.conform_engine import ConformEngine

# Import EDL as OTIO timeline
converter = EDLConverter()
edl_info = converter.parser.parse_file(Path("source.edl"))
timeline = converter.edl_to_timeline(edl_info, fps=24.0)

# Export OTIO timeline as EDL
edl_info = converter.timeline_to_edl(timeline, title="Exported Timeline")
converter.writer.write_file(edl_info, Path("output.edl"))
```

## Importing EDL Files

### Using ConformEngine

The easiest way to import EDL files is through the ConformEngine:

```python
from pathlib import Path
from conformity.conform_engine.conform_engine import ConformEngine, TimelineFormat

engine = ConformEngine()

# Import EDL (automatically detected from .edl extension)
timeline, info = engine.import_timeline(
    Path("project.edl"),
    verify_media=True
)

print(f"Imported: {info.name}")
print(f"Clips: {info.num_clips}")
print(f"Tracks: {info.num_tracks}")

# Access clip information
for clip_info in info.clips:
    print(f"  {clip_info.name}")
    print(f"    Source: {clip_info.source_path}")
    print(f"    In: {clip_info.timecode_in}")
    print(f"    Out: {clip_info.timecode_out}")
```

### Using EDLParser Directly

For more control and access to EDL-specific features:

```python
from conformity.conform_engine.edl_utils import EDLParser

parser = EDLParser()
edl_info = parser.parse_file(Path("timeline.edl"))

# Access EDL metadata
print(f"Title: {edl_info.title}")
print(f"Frame Code Mode: {edl_info.fcm}")

# Access events
for event in edl_info.events:
    print(f"Event {event.event_number}:")
    print(f"  Reel: {event.reel_name}")
    print(f"  Track: {event.track_type.value}")
    print(f"  Edit: {event.edit_type.value}")
    print(f"  Source TC: {event.source_in} - {event.source_out}")
    print(f"  Record TC: {event.record_in} - {event.record_out}")

    if event.clip_name:
        print(f"  Clip Name: {event.clip_name}")

    if 'source_file' in event.metadata:
        print(f"  Source File: {event.metadata['source_file']}")

    for comment in event.comments:
        print(f"  Comment: {comment}")
```

### Parsing from String

You can also parse EDL content directly from a string:

```python
edl_content = """
TITLE: Quick Test
FCM: NON-DROP FRAME

001  AX       V     C        01:00:00:00 01:00:05:00 00:00:00:00 00:00:05:00
* FROM CLIP NAME: Test Clip.mov
"""

edl_info = parser.parse_string(edl_content)
```

## Exporting to EDL

### Using ConformEngine

Export any OTIO timeline to EDL format:

```python
from conformity.conform_engine.conform_engine import ConformEngine, TimelineFormat

engine = ConformEngine()

# Export timeline to EDL
engine.export_timeline(
    timeline,
    Path("output.edl"),
    format=TimelineFormat.EDL
)
```

### Using EDLConverter

For more control over the conversion:

```python
from conformity.conform_engine.edl_utils import EDLConverter

converter = EDLConverter()

# Convert timeline to EDL
edl_info = converter.timeline_to_edl(
    timeline,
    title="My Project",
    fcm="NON-DROP FRAME",
    use_clip_names=True  # Include clip names as comments
)

# Write to file
converter.writer.write_file(edl_info, Path("output.edl"))
```

### Customizing EDL Output

Control what gets included in the EDL:

```python
# Exclude comments
writer.write_file(
    edl_info,
    Path("no_comments.edl"),
    include_comments=False
)

# Get EDL as string instead of file
edl_string = writer.to_string(edl_info, include_comments=True)
print(edl_string)
```

## Working with EDL Data

### Creating EDL Events Manually

```python
from conformity.conform_engine.edl_utils import EDLInfo, EDLEvent, TrackType, EditType

# Create EDL structure
edl = EDLInfo(title="Manual EDL", fcm="DROP FRAME")

# Add video cut
video_event = EDLEvent(
    event_number=1,
    reel_name="CLIP001",
    track_type=TrackType.VIDEO,
    edit_type=EditType.CUT,
    source_in="01:00:00:00",
    source_out="01:00:10:00",
    record_in="00:00:00:00",
    record_out="00:00:10:00",
    clip_name="First Shot.mov"
)
video_event.comments.append("Wide establishing shot")
video_event.metadata['source_file'] = "/media/footage/shot001.mov"
edl.events.append(video_event)

# Add dissolve
dissolve_event = EDLEvent(
    event_number=2,
    reel_name="CLIP002",
    track_type=TrackType.VIDEO,
    edit_type=EditType.DISSOLVE,
    source_in="01:00:00:00",
    source_out="01:00:08:00",
    record_in="00:00:09:12",  # Overlaps with previous
    record_out="00:00:18:00",
    clip_name="Second Shot.mov"
)
dissolve_event.comments.append("DISSOLVE")
dissolve_event.comments.append("24 frame dissolve")
edl.events.append(dissolve_event)

# Add audio
audio_event = EDLEvent(
    event_number=3,
    reel_name="AUDIO001",
    track_type=TrackType.AUDIO_1,
    edit_type=EditType.CUT,
    source_in="01:00:00:00",
    source_out="01:00:18:00",
    record_in="00:00:00:00",
    record_out="00:00:18:00",
    clip_name="Dialog.wav"
)
edl.events.append(audio_event)
```

### Modifying Existing EDL

```python
# Parse existing EDL
parser = EDLParser()
edl_info = parser.parse_file(Path("original.edl"))

# Modify events
for event in edl_info.events:
    # Change reel names
    if event.reel_name == "AX":
        event.reel_name = "NEWREEL"

    # Add comments
    if not event.clip_name:
        event.clip_name = f"Clip_{event.event_number:03d}"

    # Add metadata
    event.metadata['conform_date'] = "2025-11-08"

# Update title
edl_info.title = "Modified Timeline"

# Save modified EDL
writer = EDLWriter()
writer.write_file(edl_info, Path("modified.edl"))
```

## Advanced Features

### Reel Name Management

EDL reel names identify source media. Conformity provides tools for managing them:

```python
# When converting from OTIO, reel names come from metadata
clip.metadata["cmx_3600"] = {"reel": "RED001"}

# When parsing EDL, reel names are preserved
for event in edl_info.events:
    print(f"{event.clip_name}: Reel {event.reel_name}")

# Group events by reel
from collections import defaultdict
events_by_reel = defaultdict(list)
for event in edl_info.events:
    events_by_reel[event.reel_name].append(event)

for reel, events in events_by_reel.items():
    print(f"Reel {reel}: {len(events)} events")
```

### Timecode Handling

Work with timecodes in various formats:

```python
from conformity.conform_engine.edl_utils import EDLConverter

converter = EDLConverter()

# Parse timecode string to OTIO RationalTime
time = converter._parse_timecode("01:00:05:12", fps=24.0)
print(f"Frames: {time.value}, Rate: {time.rate}")

# Format RationalTime to timecode string
import opentimelineio as otio
time = otio.opentime.RationalTime(150, 24.0)
tc = converter._format_timecode(time)
print(f"Timecode: {tc}")  # Output: 00:00:06:06
```

### Multi-Track Workflows

Handle complex multi-track EDLs:

```python
# Parse multi-track EDL
edl_info = parser.parse_file(Path("multi_track.edl"))

# Separate by track type
video_events = [e for e in edl_info.events if e.track_type == TrackType.VIDEO]
audio_events = [e for e in edl_info.events if e.track_type in [
    TrackType.AUDIO, TrackType.AUDIO_1, TrackType.AUDIO_2
]]

print(f"Video events: {len(video_events)}")
print(f"Audio events: {len(audio_events)}")

# Create separate EDLs
video_edl = EDLInfo(title=f"{edl_info.title} - Video Only")
video_edl.events = video_events

audio_edl = EDLInfo(title=f"{edl_info.title} - Audio Only")
audio_edl.events = audio_events
```

### Validation

Validate EDL files before processing:

```python
from conformity.conform_engine.edl_utils import validate_edl_file

valid, errors = validate_edl_file(Path("timeline.edl"))

if valid:
    print("EDL is valid!")
else:
    print("EDL has errors:")
    for error in errors:
        print(f"  - {error}")
```

Validation checks:
- File exists and is readable
- Events are present
- No duplicate event numbers
- Timecode format is correct
- Source in/out timecodes are valid
- Record in/out timecodes are valid

### Comment Preservation

EDL comments contain valuable metadata:

```python
# Read EDL with comments
edl_info = parser.parse_file(Path("with_comments.edl"))

for event in edl_info.events:
    print(f"Event {event.event_number}:")

    # Standard comments
    if event.clip_name:
        print(f"  Clip: {event.clip_name}")

    if 'source_file' in event.metadata:
        print(f"  Source: {event.metadata['source_file']}")

    # Custom comments
    for comment in event.comments:
        if not comment.upper().startswith('FROM CLIP NAME:') and \
           not comment.upper().startswith('SOURCE FILE:'):
            print(f"  Note: {comment}")

# Add comments when creating EDL
event.comments.append("VFX shot - greenscreen")
event.comments.append("Color grade: teal & orange")
```

## EDL Format Reference

### CMX 3600 Format Structure

```
TITLE: <Timeline Name>
FCM: <DROP FRAME | NON-DROP FRAME>

<event#> <reel> <track> <edit> <source_in> <source_out> <record_in> <record_out>
* <comment line>
* FROM CLIP NAME: <clip_name>
* SOURCE FILE: <file_path>

<next event...>
```

### Track Types

- `V` - Video
- `A` - Audio (general)
- `A1` - Audio channel 1
- `A2` - Audio channel 2
- `A3` - Audio channel 3
- `A4` - Audio channel 4
- `B` - Both video and audio
- `NONE` - No track

### Edit Types

- `C` - Cut (straight edit)
- `D` - Dissolve (cross-fade)
- `W` - Wipe
- `K` - Key (compositing)

### Timecode Format

- Format: `HH:MM:SS:FF`
- HH: Hours (00-23)
- MM: Minutes (00-59)
- SS: Seconds (00-59)
- FF: Frames (00-FPS-1)

Example: `01:30:45:12` = 1 hour, 30 minutes, 45 seconds, 12 frames

### Frame Code Modes

- `DROP FRAME` - NTSC drop-frame timecode (29.97 fps)
- `NON-DROP FRAME` - Non-drop timecode (24, 25, 30 fps, etc.)

## Best Practices

### Reel Naming

- Keep reel names to 8 characters or less (CMX limitation)
- Use consistent naming convention (e.g., `RED001`, `ARRI001`)
- Include camera type or source information
- Use alphanumeric characters only

### Clip Names

- Always include `FROM CLIP NAME:` comments for clarity
- Use descriptive names that match source files
- Include file extensions for clarity
- Keep names under 80 characters

### Source File Paths

- Include `SOURCE FILE:` comments with full paths
- Use absolute paths when possible
- Use forward slashes even on Windows (more portable)
- Verify paths exist before exporting

### Timecodes

- Ensure source and record timecodes are sequential
- Validate no overlaps (except for transitions)
- Use consistent frame rate throughout
- Choose correct FCM for your frame rate

### Comments

- Add meaningful comments for complex edits
- Include VFX, color, or audio notes
- Document any special requirements
- Keep comments concise and clear

## Troubleshooting

### Common Issues

**Issue: "Failed to parse EDL"**
- Check file encoding (should be UTF-8 or ASCII)
- Verify EDL has proper header (TITLE and FCM lines)
- Ensure timecodes are formatted correctly
- Check for invalid characters

**Issue: "Invalid timecode format"**
- Verify timecode is HH:MM:SS:FF format
- Check that frame values don't exceed frame rate
- Ensure all fields are two digits (use leading zeros)

**Issue: "Duplicate event numbers"**
- EDL event numbers must be unique
- Renumber events sequentially
- Check for merge errors if combining EDLs

**Issue: "Missing media references"**
- EDL only stores paths, not actual media
- Verify `SOURCE FILE:` comments are present
- Check that paths are correct for your system
- Use relative paths or update paths after import

**Issue: "Transitions not preserved"**
- Dissolves require overlapping timecodes
- Ensure dissolve duration is specified
- Check that both clips in transition exist
- Verify transition type is supported (C, D, W, K)

### Debugging

Enable detailed logging:

```python
import logging
from conformity.core.logger import get_logger

logger = get_logger("conformity.conform_engine.edl_utils")
logger.setLevel(logging.DEBUG)

# Now parse with detailed output
edl_info = parser.parse_file(Path("debug.edl"))
```

## API Reference

### EDLParser

```python
class EDLParser:
    def parse_file(self, file_path: Path) -> EDLInfo
    def parse_string(self, edl_content: str) -> EDLInfo
```

### EDLWriter

```python
class EDLWriter:
    def write_file(
        self,
        edl_info: EDLInfo,
        file_path: Path,
        include_comments: bool = True
    ) -> None

    def to_string(
        self,
        edl_info: EDLInfo,
        include_comments: bool = True
    ) -> str
```

### EDLConverter

```python
class EDLConverter:
    def timeline_to_edl(
        self,
        timeline: otio.schema.Timeline,
        title: Optional[str] = None,
        fcm: str = "NON-DROP FRAME",
        use_clip_names: bool = True
    ) -> EDLInfo

    def edl_to_timeline(
        self,
        edl_info: EDLInfo,
        fps: float = 24.0
    ) -> otio.schema.Timeline
```

### Validation

```python
def validate_edl_file(file_path: Path) -> Tuple[bool, List[str]]
```

### Data Classes

```python
@dataclass
class EDLEvent:
    event_number: int
    reel_name: str
    track_type: TrackType
    edit_type: EditType
    source_in: str
    source_out: str
    record_in: str
    record_out: str
    clip_name: Optional[str] = None
    comments: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EDLInfo:
    title: str = "UNTITLED"
    fcm: str = "NON-DROP FRAME"
    events: List[EDLEvent] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Enums

```python
class EditType(Enum):
    CUT = "C"
    DISSOLVE = "D"
    WIPE = "W"
    KEY = "K"

class TrackType(Enum):
    VIDEO = "V"
    AUDIO = "A"
    AUDIO_1 = "A1"
    AUDIO_2 = "A2"
    AUDIO_3 = "A3"
    AUDIO_4 = "A4"
    VIDEO_AUDIO = "B"
    NONE = "NONE"
```

## Examples

See the `tests/test_data/edl/` directory for example EDL files:

- `simple_cuts.edl` - Basic cuts-only timeline
- `with_dissolves.edl` - Timeline with transitions
- `multi_track.edl` - Video and audio tracks
- `complex_project.edl` - Full-featured professional project

## Related Documentation

- [Conform Workflows](CONFORM_WORKFLOWS.md) - General conform operations
- [Color Workflows](COLOR_WORKFLOWS.md) - Color space management
- [README](../README.md) - Main documentation

## Support

For issues or questions about EDL support:
- Check the troubleshooting section above
- Review example EDL files in `tests/test_data/edl/`
- Consult the API reference
- Enable debug logging for detailed output
