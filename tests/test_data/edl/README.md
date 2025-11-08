# Test EDL Files

This directory contains sample EDL files for testing the Conformity EDL import/export functionality.

## Files

### simple_cuts.edl
A basic EDL with simple cut edits. Good for testing basic import/export functionality.
- 3 events
- Video track only
- All cuts (no dissolves)
- Includes clip names and source file paths

### with_dissolves.edl
An EDL demonstrating dissolve transitions between clips.
- 4 events
- Includes both cuts and dissolves
- Tests transition handling

### multi_track.edl
An EDL with both video and audio tracks.
- 4 events (2 video, 2 audio)
- Tests multi-track handling
- Uses DROP FRAME timecode mode

### complex_project.edl
A comprehensive EDL representing a real-world professional project.
- 9 events
- Multiple source reels (RED, ARRI, Blackmagic)
- Video and audio tracks
- Dissolves and cuts
- Comments and metadata
- Tests full feature set

## Usage

These EDL files are used by the test suite in `tests/test_edl_utils.py` to verify:
- EDL parsing accuracy
- Timecode handling
- Metadata preservation
- Comment extraction
- Reel name management
- Multi-track support
- Transition handling

## CMX 3600 Format

All EDL files follow the CMX 3600 standard format:
- TITLE: header line
- FCM: frame code mode (DROP FRAME or NON-DROP FRAME)
- Event lines: event# reel track edit source_in source_out record_in record_out
- Comments: lines starting with *

## Testing

To test with these files:

```python
from conformity.conform_engine.edl_utils import EDLParser

parser = EDLParser()
edl_info = parser.parse_file(Path("tests/test_data/edl/simple_cuts.edl"))
print(f"Parsed {len(edl_info.events)} events")
```
