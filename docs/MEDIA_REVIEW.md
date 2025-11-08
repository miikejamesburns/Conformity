# Media Review System

Comprehensive conform verification tools with frame-accurate playback and comparison.

## Overview

The media review system provides professional-grade tools for verify conform accuracy with:

- **Frame-Accurate Playback**: Standard playback controls with precise frame navigation
- **Side-by-Side Comparison**: Compare source and conform media simultaneously
- **Frame Markers**: Annotate issues, notes, and approvals at specific frames
- **Technical Metadata Display**: View detailed codec, color space, and format information
- **Keyboard Shortcuts**: Efficient workflow for rapid review
- **Export Capabilities**: Generate reports and export marked frames

## Quick Start

### Basic Playback

```python
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from conformity.ui_components.playback_widget import PlaybackWidget

app = QApplication([])

# Create playback widget
player = PlaybackWidget()

# Load media file
player.load_media(Path("media/footage.mp4"), frame_rate=24.0)

# Show player
player.show()

app.exec()
```

### Side-by-Side Conform Review

```python
from conformity.ui_components.conform_review_widget import ConformReviewWidget

app = QApplication([])

# Create review widget
review = ConformReviewWidget()

# Load source and conform for comparison
review.load_source_and_conform(
    Path("source/original.mp4"),
    Path("conform/conformed.mp4")
)

review.show()

app.exec()
```

### Metadata Review

```python
from conformity.ui_components.review_panel import ReviewPanel

app = QApplication([])

# Create review panel
panel = ReviewPanel()

# Load file with metadata
panel.load_file(Path("media/footage.mp4"))

# Set review status
panel.set_status("In Review")
panel.set_notes("Checking color accuracy")

# Get review data
review_data = panel.get_review_data()
print(f"Status: {review_data['status']}")

panel.show()

app.exec()
```

## Features

### Playback Widget

#### Standard Controls

- **Play/Pause**: Toggle playback (Space)
- **Stop**: Stop and return to beginning
- **Frame Forward**: Advance one frame (Right Arrow)
- **Frame Back**: Go back one frame (Left Arrow)
- **Scrubbing**: Click and drag timeline slider

#### Frame-Accurate Navigation

```python
# Seek to specific frame
player.seek_to_frame(120)

# Get current frame
current = player.get_current_frame()

# Get timecode
timecode = player.get_timecode()  # Returns "HH:MM:SS:FF"
```

#### Timecode Display

Supports standard timecode format (HH:MM:SS:FF) with configurable frame rates:

```python
# Load with specific frame rate
player.load_media(Path("footage.mp4"), frame_rate=23.976)
```

#### Image Sequence Support

Automatically detects and plays image sequences:

```python
# Load any frame from sequence
player.load_media(Path("sequence/frame.0001.exr"))

# Playback widget automatically:
# - Finds all frames in directory
# - Sorts them correctly
# - Plays at specified frame rate
```

Supported formats: `.jpg`, `.jpeg`, `.png`, `.tiff`, `.tif`, `.exr`, `.dpx`

### Conform Review Widget

#### Side-by-Side Comparison

```python
review = ConformReviewWidget()

# Load source and conform
review.load_source_and_conform(
    Path("source.mp4"),
    Path("conform.mp4")
)

# Enable synchronized playback (default)
# Both players stay in sync during playback and navigation
```

#### Frame Markers

Add annotated markers at specific frames:

```python
# Add markers programmatically
review._add_marker("issue")      # Red marker for issues
review._add_marker("note")       # Yellow marker for notes
review._add_marker("approved")   # Green marker for approval

# Or use keyboard shortcuts:
# I - Add issue marker
# N - Add note marker
# A - Add approved marker
```

#### Marker Navigation

```python
# Get all markers
markers = review.markers

# Jump to marker frame
review.source_player.seek_to_frame(markers[0].frame_number)

# Double-click marker in list to jump to that frame
```

#### Export Marked Frames

```python
# Export frame markers to file
review._export_marked_frames()

# Creates text file with marker details:
# - Frame number
# - Timecode
# - Marker type
# - Notes
# - Date created
```

#### Generate Review Report

```python
# Export comprehensive review report
review._export_review_report()

# Report includes:
# - Source/conform file paths
# - Marker statistics
# - All frame markers with details
# - Review notes
```

### Review Panel

#### Display Metadata

```python
panel = ReviewPanel()

# Load file and display metadata
panel.load_file(Path("media.mp4"))

# Metadata automatically displayed:
# - File information (path, name, size)
# - Technical specs (resolution, frame rate, codec)
# - Color information (color space, primaries, transfer)
# - Audio information (codec, channels, sample rate)
```

#### Review Status Tracking

```python
# Set status
panel.set_status("Approved")

# Available statuses:
# - Not Reviewed
# - Pending
# - In Review
# - Approved
# - Needs Revision
# - Rejected

# Add notes
panel.set_notes("Conform looks good, color matches source")

# Get review data
data = panel.get_review_data()
```

## Keyboard Shortcuts

### Playback Controls

| Key | Action |
|-----|--------|
| Space | Play/Pause |
| Left Arrow | Previous Frame |
| Right Arrow | Next Frame |
| Home | Jump to Start |
| End | Jump to End |

### Review Controls

| Key | Action |
|-----|--------|
| I | Add Issue Marker |
| N | Add Note Marker |
| A | Add Approved Marker |
| D | Toggle Difference Overlay |
| S | Toggle Synchronized Playback |

## Workflows

### Conform Verification Workflow

```python
from conformity.ui_components.conform_review_widget import ConformReviewWidget

# 1. Create review widget
review = ConformReviewWidget()

# 2. Load source and conform media
review.load_source_and_conform(
    Path("source/master.mp4"),
    Path("deliverables/client_conform.mp4")
)

# 3. Enable synchronized playback
review.sync_checkbox.setChecked(True)

# 4. Review timeline
# - Play through timeline
# - Use Left/Right arrows for frame-accurate inspection
# - Press I for issues, N for notes, A for approved frames

# 5. Add review notes
review.notes_text.setPlainText("""
Conform Review Notes:
- Color timing matches source
- All edits correctly placed
- Minor audio sync issue at TC 00:05:30:12
""")

# 6. Export review report
review._export_review_report()

# 7. Get results
results = review.get_review_results()
print(f"Issues found: {results['issues']}")
print(f"Total markers: {results['total_markers']}")
```

### Quality Control Review

```python
from conformity.ui_components.review_panel import ReviewPanel

# 1. Create review panel
panel = ReviewPanel()

# 2. Load media with metadata
panel.load_file(Path("deliverable.mp4"))

# 3. Check technical specs
metadata = panel.metadata

# Verify resolution
assert metadata['width'] == 1920
assert metadata['height'] == 1080

# Verify frame rate
assert metadata['frame_rate'] == 24.0

# Verify color space
assert metadata['color_space'] == 'rec709'

# 4. Set status based on checks
if all_checks_pass:
    panel.set_status("Approved")
    panel.set_notes("All technical specs verified")
else:
    panel.set_status("Needs Revision")
    panel.set_notes("Color space incorrect")

# 5. Get review data
data = panel.get_review_data()
```

### Image Sequence Review

```python
# 1. Load image sequence
player = PlaybackWidget()
player.load_media(Path("render/frame.0001.exr"), frame_rate=24.0)

# 2. Review sequence plays automatically
# - All frames loaded in order
# - Playback at specified frame rate
# - Frame-accurate navigation supported

# 3. Add markers for problem frames
# Press I at frames with issues
```

### Batch Review Workflow

```python
import opentimelineio as otio
from pathlib import Path

# Load timeline
timeline = otio.adapters.read_from_file("project.otio")

review_results = []

# Review each clip
for track in timeline.tracks:
    for clip in track:
        if isinstance(clip, otio.schema.Clip):
            # Get media reference
            media_ref = clip.media_reference

            if media_ref and isinstance(media_ref, otio.schema.ExternalReference):
                media_path = Path(media_ref.target_url)

                # Create review panel
                panel = ReviewPanel()
                panel.load_file(media_path)

                # Automated checks
                metadata = panel.metadata

                # Check for issues
                issues = []

                if metadata.get('width') != 1920:
                    issues.append("Incorrect width")

                if metadata.get('color_space') != 'rec709':
                    issues.append("Wrong color space")

                # Set status
                if issues:
                    panel.set_status("Needs Revision")
                    panel.set_notes("\n".join(issues))
                else:
                    panel.set_status("Approved")

                # Store results
                review_results.append({
                    'clip': clip.name,
                    'status': panel.get_review_data()['status'],
                    'issues': issues
                })

# Generate summary
for result in review_results:
    print(f"{result['clip']}: {result['status']}")
```

## API Reference

### PlaybackWidget

#### Constructor

```python
player = PlaybackWidget(parent=None)
```

#### Methods

**load_media**
```python
player.load_media(
    file_path: Path,
    frame_rate: float = 24.0
)
```

Load media file or image sequence.

**play_pause**
```python
player.play_pause()
```

Toggle play/pause state.

**stop**
```python
player.stop()
```

Stop playback and return to beginning.

**frame_forward**
```python
player.frame_forward()
```

Advance one frame.

**frame_back**
```python
player.frame_back()
```

Go back one frame.

**seek_to_frame**
```python
player.seek_to_frame(frame_number: int)
```

Jump to specific frame.

**get_current_frame**
```python
frame = player.get_current_frame() -> int
```

Get current frame number.

**get_timecode**
```python
timecode = player.get_timecode() -> str
```

Get current timecode (HH:MM:SS:FF).

#### Signals

**frame_changed**
```python
player.frame_changed.connect(callback)  # callback(int)
```

Emitted when current frame changes.

**timecode_changed**
```python
player.timecode_changed.connect(callback)  # callback(str)
```

Emitted when timecode changes.

### ConformReviewWidget

#### Constructor

```python
review = ConformReviewWidget(parent=None)
```

#### Methods

**load_source_and_conform**
```python
review.load_source_and_conform(
    source_path: Path,
    conform_path: Path
)
```

Load source and conform media for comparison.

**get_review_results**
```python
results = review.get_review_results() -> Dict[str, Any]
```

Get review results including markers and statistics.

#### Signals

**review_completed**
```python
review.review_completed.connect(callback)  # callback(dict)
```

Emitted when review is completed.

### ReviewPanel

#### Constructor

```python
panel = ReviewPanel(parent=None)
```

#### Methods

**load_file**
```python
panel.load_file(
    file_path: Path,
    metadata: Optional[Dict[str, Any]] = None
)
```

Load file and display metadata.

**set_status**
```python
panel.set_status(status: str)
```

Set review status.

**set_notes**
```python
panel.set_notes(notes: str)
```

Set review notes.

**get_review_data**
```python
data = panel.get_review_data() -> Dict[str, Any]
```

Get current review data.

**clear**
```python
panel.clear()
```

Clear all fields.

#### Signals

**status_changed**
```python
panel.status_changed.connect(callback)  # callback(str)
```

Emitted when status changes.

**notes_changed**
```python
panel.notes_changed.connect(callback)  # callback(str)
```

Emitted when notes change.

## Integration Examples

### Integration with Asset Tracker

```python
from conformity.asset_tracker.asset_database import AssetDatabase
from conformity.ui_components.review_panel import ReviewPanel

# Load asset from database
db = AssetDatabase(Path("project.db"))
asset = db.get_asset_by_id(123)

# Get metadata
metadata = db.get_asset_metadata(asset['id'])

# Create review panel
panel = ReviewPanel()
panel.load_file(Path(asset['file_path']), metadata)

# Update asset status based on review
review_data = panel.get_review_data()

if review_data['status'] == 'Approved':
    from conformity.asset_tracker.asset_database import AssetStatus
    db.update_asset_status(asset['id'], AssetStatus.APPROVED)
```

### Integration with Timeline Editor

```python
from conformity.timeline_editor import TimelineEditor
import opentimelineio as otio

# Load timeline
timeline = otio.adapters.read_from_file("project.otio")

# Review each clip
review = ConformReviewWidget()

for track in timeline.tracks:
    for clip in track:
        if isinstance(clip, otio.schema.Clip):
            media_ref = clip.media_reference

            if media_ref and isinstance(media_ref, otio.schema.ExternalReference):
                # Load clip for review
                review.source_player.load_media(Path(media_ref.target_url))

                # Perform review...
```

## Best Practices

### Review Workflow

1. **Load Both Source and Conform**: Always compare against original source
2. **Use Synchronized Playback**: Keep both views in sync for accurate comparison
3. **Add Markers Liberally**: Mark any questionable frames for later review
4. **Document Issues**: Add detailed notes for each marker
5. **Export Reports**: Generate reports for stakeholder review

### Frame Markers

1. **Use Color Coding**: Issue (red), Note (yellow), Approved (green)
2. **Add Context**: Include detailed notes about what's wrong or right
3. **Review Markers**: Double-click markers to review problem areas
4. **Export Early**: Save marker data frequently

### Quality Checks

1. **Technical Specs**: Verify resolution, frame rate, codec
2. **Color Space**: Confirm correct color space assignment
3. **Audio Sync**: Check audio sync at marker points
4. **Edit Accuracy**: Verify all edits match timeline
5. **Color Grading**: Compare color between source and conform

## Limitations

### Current Version (0.5.0)

- **Basic Playback**: Uses Qt Multimedia (not production-grade performance)
- **Image Sequence Playback**: Limited to simple playback (no caching)
- **Difference Overlay**: UI element present but not fully implemented
- **No LUT Support**: Cannot apply LUTs during review

### Future Enhancements

- **tlRender Integration**: High-performance playback with caching
- **Pixel Difference**: Actual pixel-by-pixel comparison
- **Waveform/Vectorscope**: Professional color analysis tools
- **LUT Application**: Apply LUTs during review
- **Multi-View**: Support for quad-split and custom layouts

## Related Documentation

- [Asset Tracking](ASSET_TRACKING.md) - Asset database integration
- [Timeline Editing](TIMELINE_EDITING.md) - Timeline operations
- [Color Workflows](COLOR_WORKFLOWS.md) - Color management
- [README](../README.md) - Main documentation
