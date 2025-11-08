# Timeline Editing Workflows

Comprehensive guide to advanced timeline editing in Conformity.

## Overview

Conformity provides professional timeline editing tools with industry-standard operations:

- **Ripple, Roll, Slip, Slide** - Professional editing modes
- **Clip Operations** - Split, trim, copy, paste, duplicate, delete
- **Track Management** - Add, remove, reorder, merge tracks
- **Gap Management** - Find, remove, insert, close gaps
- **Undo/Redo** - Full edit history support

## Quick Start

### Basic Timeline Editing

```python
from conformity.timeline_editor import TimelineEditor
import opentimelineio as otio

# Load timeline
timeline = otio.adapters.read_from_file("timeline.otio")

# Create editor
editor = TimelineEditor(timeline)

# Perform edit
track = timeline.tracks[0]
clip = track[0]

# Ripple edit - change duration and shift following clips
new_duration = otio.opentime.RationalTime(96, 24)  # 4 seconds at 24fps
editor.ripple_edit(track, clip, new_duration)

# Undo if needed
if editor.can_undo():
    editor.undo()

# Save timeline
otio.adapters.write_to_file(timeline, "edited_timeline.otio")
```

## Professional Editing Modes

### Ripple Edit

**Ripple editing** changes a clip's duration and shifts all following clips.

```python
from conformity.timeline_editor import TimelineEditor

editor = TimelineEditor(timeline)

# Shorten clip and ripple following clips
new_duration = otio.opentime.RationalTime(72, 24)  # 3 seconds

editor.ripple_edit(
    track=timeline.tracks[0],
    clip=clip,
    new_duration=new_duration,
    ripple_following=True  # Shift clips after this one
)
```

**Use Cases:**
- Trimming clips without leaving gaps
- Tightening edit pace
- Removing unwanted frames

### Roll Edit

**Roll editing** adjusts the edit point between two clips without affecting total timeline duration.

```python
# Shift edit point 12 frames to the right
delta = otio.opentime.RationalTime(12, 24)

editor.roll_edit(
    track=timeline.tracks[0],
    clip_a=clip1,  # Will be extended
    clip_b=clip2,  # Will be shortened
    delta=delta
)
```

**Use Cases:**
- Fine-tuning edit points
- Finding better cut points
- Adjusting performance timing

### Slip Edit

**Slip editing** changes the source content without moving the clip's timeline position.

```python
# Slip clip content 24 frames forward
offset = otio.opentime.RationalTime(24, 24)

editor.slip_edit(
    track=timeline.tracks[0],
    clip=clip,
    offset=offset
)
```

**Use Cases:**
- Finding better action within clip
- Adjusting sync without moving clip
- Selecting different performance take

### Slide Edit

**Slide editing** moves a clip along the timeline while maintaining its duration.

```python
# Slide clip 12 frames later
offset = otio.opentime.RationalTime(12, 24)

editor.slide_edit(
    track=timeline.tracks[0],
    clip=clip,
    offset=offset
)
```

**Use Cases:**
- Repositioning clips
- Adjusting timing relationships
- Finding better edit rhythm

## Clip Operations

### Split Clip

Split a clip at a specific point:

```python
from conformity.timeline_editor import split_clip

# Split at 2 seconds (48 frames at 24fps)
split_time = otio.opentime.RationalTime(48, 24)

result = split_clip(track, clip, split_time)

if result:
    first_clip, second_clip = result
    print(f"Split into '{first_clip.name}' and '{second_clip.name}'")
```

### Trim Clip

Adjust clip in/out points:

```python
from conformity.timeline_editor import trim_clip

# New in point (start 10 frames in)
new_in = otio.opentime.RationalTime(10, 24)

# New out point (end 10 frames early)
new_out = otio.opentime.RationalTime(110, 24)

trim_clip(clip, new_in=new_in, new_out=new_out)
```

### Copy and Paste

```python
from conformity.timeline_editor import copy_clip, paste_clip

# Copy clip
clip_copy = copy_clip(clip)

# Paste to another track
paste_clip(destination_track, clip_copy, index=5)
```

### Duplicate Clip

```python
from conformity.timeline_editor import duplicate_clip

# Create 3 duplicates
duplicates = duplicate_clip(track, clip, count=3)

# Duplicates are inserted immediately after original
for dup in duplicates:
    print(f"Created: {dup.name}")
```

### Delete Clip

```python
from conformity.timeline_editor import delete_clip

# Delete and close gap (ripple delete)
delete_clip(track, clip, close_gap=True)

# Delete and leave gap (lift)
delete_clip(track, clip, close_gap=False)
```

### Replace Clip

```python
from conformity.timeline_editor.clip_operations import replace_clip

# Replace one clip with another
replace_clip(
    track,
    old_clip=old_clip,
    new_clip=new_clip,
    match_duration=True  # Adjust new clip to match old duration
)
```

### Move Clip Between Tracks

```python
from conformity.timeline_editor.clip_operations import move_clip

# Move clip from one track to another
move_clip(
    source_track=timeline.tracks[0],
    dest_track=timeline.tracks[1],
    clip=clip,
    dest_index=3  # Position in destination track
)
```

### Clip Speed

```python
from conformity.timeline_editor.clip_operations import set_clip_speed

# Double speed (fast motion)
set_clip_speed(clip, speed=2.0)

# Half speed (slow motion)
set_clip_speed(clip, speed=0.5)

# Reverse clip
from conformity.timeline_editor.clip_operations import reverse_clip
reverse_clip(clip)
```

## Track Management

### Add Track

```python
from conformity.timeline_editor import add_track

# Add video track with specific name
video_track = add_track(
    timeline,
    name="V2",
    kind=otio.schema.TrackKind.Video
)

# Add audio track (auto-named)
audio_track = add_track(
    timeline,
    kind=otio.schema.TrackKind.Audio
)
```

### Remove Track

```python
from conformity.timeline_editor import remove_track

remove_track(timeline, track)
```

### Reorder Tracks

```python
from conformity.timeline_editor import reorder_tracks

# Move track to new position
reorder_tracks(timeline, track, new_index=0)
```

### Merge Tracks

```python
from conformity.timeline_editor.track_operations import merge_tracks

# Merge multiple tracks into one
merged = merge_tracks(
    timeline,
    tracks=[track1, track2, track3],
    name="Merged Track",
    remove_source=True  # Remove original tracks
)
```

### Lock/Unlock Track

```python
from conformity.timeline_editor.track_operations import lock_track, is_track_locked

# Lock track to prevent editing
lock_track(track, locked=True)

# Check if locked
if is_track_locked(track):
    print("Track is locked")

# Unlock
lock_track(track, locked=False)
```

### Mute/Solo Track

```python
from conformity.timeline_editor.track_operations import mute_track, solo_track

# Mute track
mute_track(track, muted=True)

# Solo track (mutes all others of same kind)
solo_track(timeline, track, solo=True)
```

## Gap Management

### Find Gaps

```python
from conformity.timeline_editor import find_gaps

# Find all gaps in track
gaps = find_gaps(track)

for index, gap in gaps:
    print(f"Gap at index {index}: duration {gap.duration()}")
```

### Remove Gaps

```python
from conformity.timeline_editor import remove_gaps

# Remove all gaps
count = remove_gaps(track)

# Remove only long gaps (> 1 second)
min_duration = otio.opentime.RationalTime(24, 24)
count = remove_gaps(track, min_duration=min_duration)
```

### Insert Gap

```python
from conformity.timeline_editor import insert_gap

# Insert 1-second gap at position 5
gap_duration = otio.opentime.RationalTime(24, 24)
insert_gap(track, index=5, duration=gap_duration)
```

### Close Gap

```python
from conformity.timeline_editor.gap_utils import close_gap

# Close specific gap
close_gap(track, gap, ripple=True)
```

### Fill Gaps with Black

```python
from conformity.timeline_editor.gap_utils import fill_gaps_with_black

# Fill gaps with black/silence clips
count = fill_gaps_with_black(track)
```

### Consolidate Gaps

```python
from conformity.timeline_editor.gap_utils import consolidate_gaps

# Merge adjacent gaps into single gaps
count = consolidate_gaps(track)
```

## Undo/Redo System

### Using Undo/Redo

```python
editor = TimelineEditor(timeline)

# Perform edits
editor.ripple_edit(track, clip, new_duration)
editor.slip_edit(track, clip2, offset)

# Undo last edit
if editor.can_undo():
    editor.undo()

# Redo
if editor.can_redo():
    editor.redo()

# Clear history
editor.clear_history()
```

### History Management

```python
# Check undo/redo availability
print(f"Can undo: {editor.can_undo()}")
print(f"Can redo: {editor.can_redo()}")

# Set history limit
editor.max_history = 50  # Keep last 50 operations
```

## Best Practices

### Organizing Edits

1. **Use Undo/Redo**: Experiment freely knowing you can undo
2. **Lock Tracks**: Lock finished tracks to prevent accidental changes
3. **Clear Gaps**: Remove unnecessary gaps for cleaner timelines
4. **Consolidate**: Merge adjacent gaps before removing them

### Performance Tips

- **Batch Operations**: Group related edits together
- **Clear History**: Clear undo history after major milestones
- **Track Count**: Keep track count reasonable (< 20 for complex timelines)
- **Gap Management**: Remove gaps periodically to keep timeline clean

### Workflow Patterns

**Rough Cut to Fine Cut:**
```python
# 1. Assembly (rough cut)
# - Add all clips in rough order
# - Don't worry about timing

# 2. Remove unwanted sections
for clip in unwanted_clips:
    delete_clip(track, clip, close_gap=True)

# 3. Fine tune edit points
for i in range(len(track) - 1):
    if isinstance(track[i], otio.schema.Clip):
        # Use roll edit to adjust cut points
        editor.roll_edit(track, track[i], track[i+1], delta)

# 4. Polish
consolidate_gaps(track)
remove_gaps(track)
```

**Multi-Camera Edit:**
```python
# Create track per camera
cam1_track = add_track(timeline, name="Camera 1", kind=otio.schema.TrackKind.Video)
cam2_track = add_track(timeline, name="Camera 2", kind=otio.schema.TrackKind.Video)

# Cut between cameras by moving clips to different tracks
move_clip(cam1_track, cam2_track, clip, dest_index=5)
```

## API Reference

### TimelineEditor

```python
class TimelineEditor:
    def __init__(timeline: Timeline)
    def ripple_edit(track, clip, new_duration, ripple_following=True) -> bool
    def roll_edit(track, clip_a, clip_b, delta) -> bool
    def slip_edit(track, clip, offset) -> bool
    def slide_edit(track, clip, offset) -> bool
    def undo() -> bool
    def redo() -> bool
    def can_undo() -> bool
    def can_redo() -> bool
    def clear_history()
```

### Clip Operations

```python
def split_clip(track, clip, split_time) -> Optional[Tuple[Clip, Clip]]
def trim_clip(clip, new_in=None, new_out=None) -> bool
def copy_clip(clip) -> Clip
def paste_clip(track, clip, index=None) -> bool
def duplicate_clip(track, clip, count=1) -> List[Clip]
def delete_clip(track, clip, close_gap=False) -> bool
def replace_clip(track, old_clip, new_clip, match_duration=True) -> bool
def move_clip(source_track, dest_track, clip, dest_index=None) -> bool
def set_clip_speed(clip, speed) -> bool
def reverse_clip(clip) -> bool
```

### Track Operations

```python
def add_track(timeline, name=None, kind=TrackKind.Video, index=None) -> Track
def remove_track(timeline, track) -> bool
def reorder_tracks(timeline, track, new_index) -> bool
def duplicate_track(timeline, track, new_name=None) -> Track
def merge_tracks(timeline, tracks, name=None, remove_source=False) -> Track
def lock_track(track, locked=True) -> bool
def mute_track(track, muted=True) -> bool
def solo_track(timeline, track, solo=True) -> bool
```

### Gap Operations

```python
def find_gaps(track) -> List[Tuple[int, Gap]]
def remove_gaps(track, min_duration=None) -> int
def insert_gap(track, index, duration) -> bool
def close_gap(track, gap, ripple=True) -> bool
def consolidate_gaps(track) -> int
def fill_gaps_with_black(track, min_duration=None) -> int
```

## Examples

### Three-Point Edit

```python
# Insert clip at specific point with specific in/out
def three_point_edit(track, clip, insert_point, clip_in, clip_out):
    # Trim clip to desired range
    trim_clip(clip, new_in=clip_in, new_out=clip_out)

    # Find insertion index
    insert_index = 0
    for i, item in enumerate(track):
        if item.range_in_parent().start_time >= insert_point:
            insert_index = i
            break

    # Insert clip
    paste_clip(track, clip, index=insert_index)
```

### Batch Trim

```python
# Trim all clips in track by same amount
def batch_trim(track, head_frames, tail_frames, fps=24):
    for item in track:
        if isinstance(item, otio.schema.Clip) and item.source_range:
            new_in = item.source_range.start_time + otio.opentime.RationalTime(head_frames, fps)
            new_out = item.source_range.end_time_exclusive() - otio.opentime.RationalTime(tail_frames, fps)

            if new_in < new_out:
                trim_clip(item, new_in=new_in, new_out=new_out)
```

### Match Cut

```python
# Create match cut between two clips
def match_cut(track, clip1, clip2, match_point):
    # Split first clip at match point
    result = split_clip(track, clip1, match_point)

    if result:
        # Trim second clip to start at match point
        trim_clip(clip2, new_in=match_point)
```

## Related Documentation

- [EDL Workflows](EDL_WORKFLOWS.md) - EDL import/export
- [LUT Workflows](LUT_WORKFLOWS.md) - LUT management
- [Color Workflows](COLOR_WORKFLOWS.md) - Color management
- [README](../README.md) - Main documentation
