# Conformity

A Python-based post-production pipeline management system for professional video workflows.

## Overview

Conformity is a modular application designed to streamline post-production workflows by integrating industry-standard tools for timeline management, color pipeline management, and asset tracking.

### Key Features

- **Automated Conform**: Import/export timelines from multiple formats (EDL, XML, AAF, FCPXML)
  - Parse timeline structure with clips, tracks, transitions, and markers
  - Validate timelines for errors and missing media
  - Match clips to media files automatically
  - Export to different formats with full metadata preservation
- **Timeline Management**: Built on OpenTimelineIO (OTIO) for robust timeline operations
- **Color Management**: Integrated OpenColorIO (OCIO) for professional color pipeline management
- **Professional Playback**: tlRender integration for high-performance video playback
  - Hardware-accelerated rendering
  - Professional format support (EXR, DPX, ProRes, RED, ARRI)
  - Frame-accurate scrubbing
  - Image sequence handling
- **Natural Language Commands**: Query interface for intuitive project navigation
  - Pattern-based query parsing ("find clips with shot_010")
  - Command history and saved queries
  - Autocomplete suggestions
  - LLM-ready architecture for future AI integration
- **Production Tracker**: Comprehensive post-production workflow management
  - Shot tracking through multiple departments (Editorial, VFX, Color, Sound, Finishing, Delivery)
  - Task assignment and priority management
  - Review and approval workflows
  - Deliverables checklist and tracking
  - Team and vendor directory
  - Progress reporting and statistics
  - Qt dashboard with visual progress indicators
- **Asset Tracking**: Comprehensive media asset management and organization
- **Modern UI**: Clean, intuitive interface built with PyQt6

## 📚 Documentation

Complete documentation is available in the `/docs` directory:

- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Complete installation, quick start, API reference, and roadmap
- **[Architecture](docs/ARCHITECTURE.md)** - Technical architecture with diagrams and design patterns
- **[Testing Guide](docs/TESTING.md)** - Comprehensive testing documentation
- **[Production Tracker](docs/PRODUCTION_TRACKER.md)** - Production workflow management guide
- **[Command Interface](docs/COMMAND_INTERFACE.md)** - Natural language query system
- **[tlRender Integration](docs/TLRENDER.md)** - Professional playback system

### Quick Links

- **Installation**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#installation)
- **Quick Start**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#quick-start)
- **API Reference**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#api-reference)
- **Examples**: See [examples/README.md](examples/README.md)
- **Testing**: See [docs/TESTING.md](docs/TESTING.md)

## Architecture

Conformity follows a modular architecture with clear separation of concerns:

```
conformity/
├── src/conformity/
│   ├── core/                 # Core utilities
│   │   ├── config.py        # Configuration management
│   │   └── logger.py        # Logging system
│   ├── conform_engine/      # OTIO timeline operations
│   │   ├── conform_engine.py    # Automated import/export
│   │   ├── timeline_manager.py
│   │   ├── conform_ops.py
│   │   ├── edl_utils.py     # EDL/CMX 3600 support
│   │   └── exceptions.py
│   ├── timeline_editor/     # Advanced editing tools
│   │   ├── edit_operations.py   # Ripple/Roll/Slip/Slide
│   │   ├── clip_operations.py   # Split/Trim/Copy/Paste
│   │   ├── track_operations.py  # Track management
│   │   └── gap_utils.py         # Gap management
│   ├── lut_manager/         # LUT management
│   │   ├── lut_loader.py    # CUBE/3DL parsing
│   │   └── lut_manager.py   # Library management
│   ├── color_manager/       # OCIO color management
│   │   ├── color_manager.py     # Holistic color engine
│   │   ├── ocio_manager.py
│   │   └── color_pipeline.py
│   ├── asset_tracker/       # Asset management
│   │   └── asset_manager.py
│   ├── production_tracker/  # Production workflow tracking
│   │   ├── production_database.py  # SQLite database
│   │   └── shot_tracker.py         # Workflow manager
│   ├── commands/            # Natural language commands
│   │   ├── command_parser.py      # Query parser
│   │   ├── command_executor.py    # Command execution
│   │   └── command_history.py     # History/saved queries
│   └── ui_components/       # Qt UI widgets
│       ├── conform_panel.py      # Conform operations UI
│       ├── color_space_widget.py # Color management UI
│       ├── timeline_widget.py
│       ├── command_interface.py  # Command query UI
│       ├── production_tracker_widget.py  # Production dashboard
│       └── asset_browser.py
├── tests/                   # Unit tests
├── config/                  # Configuration files
├── docs/                    # Documentation
└── requirements.txt         # Dependencies
```

### Module Overview

#### Core (`src/conformity/core/`)

Provides foundational services used across the application:

- **config.py**: Configuration management using Pydantic models and YAML
  - Load/save configuration
  - Environment variable overrides
  - Type-safe configuration access

- **logger.py**: Centralized logging system
  - File and console output
  - Configurable log levels
  - Timestamped log files

#### Conform Engine (`src/conformity/conform_engine/`)

Handles all timeline and conform operations using OpenTimelineIO:

- **conform_engine.py**: Automated timeline import/export
  - Import from EDL, XML, AAF, FCPXML formats
  - Parse timeline structure (clips, tracks, transitions, markers)
  - Validate timelines for errors and missing media
  - Export to multiple formats with metadata preservation
  - Error handling with custom exceptions

- **edl_utils.py**: Comprehensive EDL/CMX 3600 support
  - EDLParser: Parse CMX 3600 EDL files
  - EDLWriter: Write EDL files with custom options
  - EDLConverter: Bidirectional OTIO↔EDL conversion
  - Reel name management and comment preservation
  - Timecode validation and formatting
  - Support for cuts, dissolves, wipes, and keys
  - Multi-track video and audio handling
  - EDL validation utilities

- **timeline_manager.py**: High-level timeline operations
  - Load/save timelines from various formats
  - Create new timelines
  - Add clips and manage tracks
  - Extract timeline metadata

- **conform_ops.py**: Advanced conform operations
  - Match clips by name
  - Relink media references
  - Generate conform reports
  - Extract clip metadata

- **exceptions.py**: Custom exception classes
  - ImportError, ExportError, MediaNotFoundError
  - InvalidTimecodeError, UnsupportedFeatureError
  - Detailed error reporting

#### Timeline Editor (`src/conformity/timeline_editor/`)

Advanced timeline editing operations with professional NLE functionality:

- **edit_operations.py**: Professional editing modes with undo/redo
  - TimelineEditor: Central editing controller with history management
  - Ripple Edit: Change clip duration and shift following clips
  - Roll Edit: Adjust edit points between clips
  - Slip Edit: Change source content without moving timeline position
  - Slide Edit: Move clip position while maintaining duration
  - Full undo/redo support with operation history

- **clip_operations.py**: Clip-level editing tools
  - Split: Cut clip at specified time
  - Trim: Adjust in/out points
  - Copy/Paste: Clipboard operations
  - Duplicate: Create multiple copies
  - Delete: Remove with optional gap closing
  - Replace: Swap clips with duration matching
  - Move: Transfer clips between tracks
  - Speed Control: Adjust playback speed (slow/fast motion)
  - Reverse: Flip playback direction

- **track_operations.py**: Track management operations
  - Add/Remove: Manage tracks with auto-naming
  - Reorder: Change track stacking order
  - Duplicate: Copy entire tracks with contents
  - Merge: Combine multiple tracks
  - Lock/Unlock: Prevent accidental edits
  - Mute/Solo: Audio/video track control
  - Rename: Update track names
  - Filter: Get video or audio tracks

- **gap_utils.py**: Gap management utilities
  - Find: Locate all gaps in tracks
  - Remove: Delete gaps with optional duration filter
  - Insert: Add gaps at specific positions
  - Close: Remove specific gaps with ripple option
  - Consolidate: Merge adjacent gaps
  - Fill: Replace gaps with black/silence clips
  - Split: Divide gaps into multiple sections
  - Query: Check gap existence and total duration

#### LUT Manager (`src/conformity/lut_manager/`)

Comprehensive LUT (Look-Up Table) management system:

- **lut_loader.py**: LUT loading and application
  - Parse CUBE and 3DL format LUTs
  - 1D LUT support with linear interpolation
  - 3D LUT support with trilinear interpolation
  - Apply LUTs to RGB arrays
  - Identity LUT creation
  - Format validation and error handling

- **lut_manager.py**: LUT library management
  - Library organization with categories
  - Metadata tracking (usage count, tags, descriptions)
  - Search and filtering by name, category, tags
  - Favorite LUT management
  - Apply LUTs to clips and timelines
  - Batch LUT operations
  - Export usage reports

#### Color Manager (`src/conformity/color_manager/`)

Holistic color management system using OpenColorIO:

- **color_manager.py**: Comprehensive color management engine
  - Validate OCIO configurations
  - Track color space assignments across pipeline
  - Auto-detect color spaces from metadata and extensions
  - Generate validation reports with status tracking
  - Pipeline-wide color configuration management

- **ocio_manager.py**: OCIO configuration and operations
  - Load and validate OCIO configs
  - Query color spaces, displays, and views
  - Create color transformation processors
  - Validate color space compatibility

- **color_pipeline.py**: Integration with timelines
  - Assign color spaces to clips with validation
  - Auto-assign based on file types and metadata
  - Generate comprehensive color reports
  - Manage display/view assignments
  - Track color space usage statistics

#### Asset Tracker (`src/conformity/asset_tracker/`)

Comprehensive asset tracking system with SQLite backend:

- **asset_database.py**: SQLite database manager
  - Asset metadata storage (paths, types, technical specs)
  - Timeline associations (clip-to-file relationships)
  - Version history and dependencies
  - Color space information tracking
  - Status workflow management (pending, approved, needs_review)
  - Tag-based organization
  - Search and filtering with indices

- **metadata_extractor.py**: Technical metadata extraction
  - Extract from video files using ffprobe
  - Image metadata with PIL
  - Audio file metadata
  - Automatic codec, resolution, frame rate detection
  - Color space information extraction
  - File checksum calculation (MD5/SHA256)

- **asset_scanner.py**: Directory scanning and verification
  - Recursive media file discovery
  - Automatic metadata extraction and storage
  - Asset verification (online/offline status)
  - Batch operations (status update, tag addition)
  - Progress callback support for UI integration
  - Asset relocation tracking

- **timeline_analyzer.py**: Timeline-to-asset relationship tracking
  - Analyze OTIO timelines for media references
  - Create clip-to-asset associations
  - Find missing media
  - Automatic media relinking
  - Usage reports (most used, unused assets)
  - Timeline asset queries

- **asset_manager.py**: Legacy asset management
  - Basic asset registration
  - Directory scanning
  - Status tracking

#### UI Components (`src/conformity/ui_components/`)

Qt-based user interface widgets:

- **conform_panel.py**: Automated conform operations UI
  - Import timelines from multiple formats
  - Display timeline structure in tree view
  - Show detailed clip information
  - Validate timelines for errors
  - Export to different formats
  - Interactive conform workflow

- **color_space_widget.py**: Color management UI
  - Load and validate OCIO configurations
  - Set pipeline-wide color defaults
  - Visualize color space families and relationships
  - Analyze timelines for color space assignments
  - Manually assign/override color spaces
  - Auto-assign based on rules and metadata
  - Export color space reports

- **timeline_widget.py**: Timeline visualization
  - Display timeline information
  - Browse tracks and clips
  - Show duration and metadata

- **asset_tracker_widget.py**: Advanced asset tracking UI
  - Text search across file paths and metadata
  - Filter by type, status, color space
  - Sortable table with multi-select
  - Batch status updates
  - Directory scanning with progress bar
  - Asset verification (online/offline check)
  - Double-click for detailed asset information
  - Real-time statistics display

- **playback_widget.py**: Media playback for conform review
  - Frame-accurate video playback with Qt Multimedia
  - Standard controls (play, pause, stop, scrub)
  - Frame-by-frame navigation (forward/back)
  - Timecode display (HH:MM:SS:FF)
  - Image sequence support (auto-detection and playback)
  - Keyboard shortcuts for efficient navigation
  - Progress tracking and duration display

- **conform_review_widget.py**: Side-by-side conform verification
  - Dual playback widgets for source vs conform
  - Synchronized playback option
  - Frame markers (issue, note, approved)
  - Marker navigation (double-click to jump)
  - Difference overlay mode
  - Export marked frames to file
  - Generate comprehensive review reports
  - Review statistics (issues, notes, approved frames)

- **review_panel.py**: Clip metadata and review panel
  - Display file information (path, name, size)
  - Technical specifications (resolution, frame rate, codec)
  - Color information (color space, primaries, transfer)
  - Audio information (codec, channels, sample rate)
  - Review status tracking (pending, approved, rejected)
  - Review notes text field
  - Status and notes signals

- **asset_browser.py**: Legacy asset management UI
  - Browse registered assets
  - Scan directories
  - Verify asset status
  - View asset details and statistics

## Installation

### 🐧 Ubuntu/Debian Users

**We have a dedicated Ubuntu installation guide with automated scripts!**

👉 **[Ubuntu Installation Guide](docs/UBUNTU_INSTALLATION.md)**

```bash
# Quick automated install for OpenColorIO
cd /path/to/Conformity
./scripts/install_opencolorio_ubuntu.sh

# Optional: Install OpenImageIO for image sequences (EXR, DPX)
source venv/bin/activate  # If using venv
./scripts/install_openimageio_ubuntu.sh
```

**Getting `GLIBCXX_3.4.32 not found` errors?**
If you're using miniconda/anaconda Python 3.13, build OTIO from source:
```bash
source venv/bin/activate
./scripts/install_opentimelineio_ubuntu.sh
```

See [Quick Fix Guide](docs/QUICK_FIX_UBUNTU.md) for more solutions.

This handles all dependencies and builds OpenColorIO automatically. For other platforms, continue below.

---

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install from source

1. Clone the repository:
```bash
git clone https://github.com/yourusername/conformity.git
cd conformity
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

**Core only** (timeline operations):
```bash
pip install -r requirements.txt
```

**Full install** (includes optional color management):
```bash
pip install -r requirements-full.txt
```

4. Install in development mode (optional):
```bash
pip install -e .
```

### Optional Dependencies

Conformity includes optional professional features:

#### Check What's Installed
```bash
python3 -m conformity.core.dependencies
```

#### PyOpenColorIO (Color Management) ✨ Pre-built wheels available!
Enables professional color workflows, LUTs, and ACES pipelines.

**Easy install via PyPI:**
```bash
pip install opencolorio>=2.3.0
```
*Note: Package name is `opencolorio`, but imports as `PyOpenColorIO`*

Or use the full requirements file:
```bash
pip install -r requirements-full.txt
```

**Alternative methods**: [docs/BUILDING_OPTIONAL_DEPS.md](docs/BUILDING_OPTIONAL_DEPS.md#pyopencolorio)

#### tlRender (Professional Playback)
Enables hardware-accelerated playback, professional formats (EXR, DPX, ProRes, RED, ARRI), and image sequences.

**Build from source**: See [docs/BUILDING_OPTIONAL_DEPS.md](docs/BUILDING_OPTIONAL_DEPS.md#tlrender)

> **Note:** Conformity works without these dependencies - they only enable advanced features. The application detects and uses them automatically if installed.

## Running the Application

### Quick Start

Run the application directly:
```bash
python run.py
```

Or if installed:
```bash
conformity
```

### Configuration

The application uses a YAML configuration file located at `config/default_config.yaml`. You can customize:

- Application settings (name, version, log level)
- Project paths (cache, temp directories)
- OCIO settings (config path, default color space)
- OTIO settings (default FPS, resolution)
- UI settings (theme, window size)

### Environment Variables

You can override configuration using environment variables:

- `OCIO`: Path to OCIO configuration file
- `CONFORMITY_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

Example:
```bash
export OCIO=/path/to/config.ocio
export CONFORMITY_LOG_LEVEL=DEBUG
python run.py
```

## Usage Examples

### Automated Conform Operations

```python
from pathlib import Path
from conformity.conform_engine.conform_engine import ConformEngine, TimelineFormat

# Create conform engine
engine = ConformEngine()

# Import timeline from XML
timeline, info = engine.import_timeline(
    Path("project.xml"),
    verify_media=True
)

print(f"Imported: {info.num_clips} clips, {info.num_tracks} tracks")

# Validate timeline
results = engine.validate_timeline(timeline, check_media=True)
if results['valid']:
    print("Timeline is valid!")
else:
    print(f"Errors: {len(results['errors'])}")

# Export to EDL
engine.export_timeline(
    timeline,
    Path("output.edl"),
    format=TimelineFormat.EDL
)
```

### Working with Timelines

```python
from conformity.conform_engine.timeline_manager import TimelineManager

# Create a timeline manager
manager = TimelineManager()

# Create a new timeline
timeline = manager.create_timeline(name="My Project", fps=24.0)

# Load an existing timeline
timeline = manager.load_timeline(Path("timeline.otio"))

# Get timeline information
info = manager.get_timeline_info(timeline)
print(f"Timeline: {info['name']}, Clips: {info['clips']}")

# Save timeline
manager.save_timeline(timeline, Path("output.otio"))
```

### Working with EDL Files

```python
from pathlib import Path
from conformity.conform_engine.edl_utils import EDLParser, EDLWriter, EDLConverter

# Parse an EDL file
parser = EDLParser()
edl_info = parser.parse_file(Path("timeline.edl"))

print(f"Title: {edl_info.title}")
print(f"Events: {len(edl_info.events)}")

for event in edl_info.events:
    print(f"Event {event.event_number}: {event.clip_name or event.reel_name}")
    print(f"  Track: {event.track_type.value}, Edit: {event.edit_type.value}")
    print(f"  Source TC: {event.source_in} - {event.source_out}")

# Convert EDL to OTIO timeline
converter = EDLConverter()
timeline = converter.edl_to_timeline(edl_info, fps=24.0)

# Modify timeline...

# Convert back to EDL and save
output_edl = converter.timeline_to_edl(timeline, title="Modified Timeline")
writer = EDLWriter()
writer.write_file(output_edl, Path("output.edl"))
```

### Holistic Color Management

```python
from pathlib import Path
from conformity.color_manager.color_manager import ColorManager

# Create color manager
color_mgr = ColorManager()

# Load and validate OCIO config
color_mgr.load_config(Path("config/ocio/simple_config.ocio"))
valid, errors = color_mgr.validate_config()
print(f"Config valid: {valid}")

# Set pipeline defaults
pipeline = color_mgr.get_pipeline_config()
pipeline.set_defaults(
    working="Linear",
    default_input="CameraRec709",
    display="sRGB",
    view="Standard"
)

# Add auto-detection rules
pipeline.add_rule('.r3d', 'RedWideGamutRGB')
pipeline.add_rule('.ari', 'ARRI_LogC4')
pipeline.add_rule('.braw', 'BMDFilm_Gen5')

# Auto-assign color spaces to timeline
count = color_mgr.auto_assign_color_spaces(timeline, use_defaults=True)
print(f"Assigned color spaces to {count} clips")

# Analyze timeline
result = color_mgr.analyze_timeline(timeline, auto_detect=True)
print(f"Valid: {result.valid_count}, Missing: {result.missing_count}")

# Generate report
report = color_mgr.create_color_space_report(timeline)
print(f"Color spaces used: {list(report['color_spaces_used'].keys())}")
```

### Tracking Assets

```python
from conformity.asset_tracker.asset_manager import AssetManager

# Create asset manager
asset_mgr = AssetManager()

# Scan a directory
count = asset_mgr.scan_directory(
    Path("/path/to/media"),
    recursive=True
)
print(f"Found {count} assets")

# Get statistics
stats = asset_mgr.get_statistics()
print(f"Total assets: {stats['total_assets']}")
print(f"Total size: {stats['total_size_gb']} GB")

# Verify assets
status = asset_mgr.verify_assets()
print(f"Online: {status['online']}, Offline: {status['offline']}")
```

### Advanced Timeline Editing

```python
from conformity.timeline_editor import TimelineEditor
import opentimelineio as otio

# Load timeline
timeline = otio.adapters.read_from_file("timeline.otio")

# Create editor with undo/redo support
editor = TimelineEditor(timeline)

track = timeline.tracks[0]
clip = track[0]

# Ripple edit - change duration and shift following clips
new_duration = otio.opentime.RationalTime(96, 24)  # 4 seconds at 24fps
editor.ripple_edit(track, clip, new_duration, ripple_following=True)

# Undo if needed
if editor.can_undo():
    editor.undo()

# Roll edit - adjust edit point between two clips
delta = otio.opentime.RationalTime(12, 24)  # Shift 12 frames
editor.roll_edit(track, clip, track[1], delta)

# Slip edit - change source content without moving timeline position
offset = otio.opentime.RationalTime(24, 24)
editor.slip_edit(track, clip, offset)

# Slide edit - move clip along timeline
editor.slide_edit(track, clip, offset)
```

### Clip Operations

```python
from conformity.timeline_editor import (
    split_clip, trim_clip, copy_clip, paste_clip,
    duplicate_clip, delete_clip
)

# Split clip at 2 seconds
split_time = otio.opentime.RationalTime(48, 24)
result = split_clip(track, clip, split_time)
if result:
    first_clip, second_clip = result
    print(f"Split into '{first_clip.name}' and '{second_clip.name}'")

# Trim clip in/out points
new_in = otio.opentime.RationalTime(10, 24)
new_out = otio.opentime.RationalTime(110, 24)
trim_clip(clip, new_in=new_in, new_out=new_out)

# Copy and paste
clip_copy = copy_clip(clip)
paste_clip(destination_track, clip_copy, index=5)

# Duplicate clip 3 times
duplicates = duplicate_clip(track, clip, count=3)

# Delete with gap closing (ripple delete)
delete_clip(track, clip, close_gap=True)

# Speed control
from conformity.timeline_editor.clip_operations import set_clip_speed, reverse_clip

set_clip_speed(clip, speed=2.0)  # Double speed
reverse_clip(clip)  # Reverse playback
```

### Track Management

```python
from conformity.timeline_editor import (
    add_track, remove_track, reorder_tracks
)
from conformity.timeline_editor.track_operations import (
    merge_tracks, lock_track, solo_track
)

# Add video track
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

# Reorder tracks
reorder_tracks(timeline, video_track, new_index=0)

# Merge multiple tracks
merged = merge_tracks(
    timeline,
    tracks=[track1, track2, track3],
    name="Merged Track",
    remove_source=True
)

# Lock track to prevent editing
lock_track(track, locked=True)

# Solo track (mutes all others of same kind)
solo_track(timeline, track, solo=True)
```

### Gap Management

```python
from conformity.timeline_editor import find_gaps, remove_gaps, insert_gap
from conformity.timeline_editor.gap_utils import (
    consolidate_gaps, fill_gaps_with_black
)

# Find all gaps in track
gaps = find_gaps(track)
for index, gap in gaps:
    print(f"Gap at index {index}: duration {gap.duration()}")

# Remove all gaps
count = remove_gaps(track)

# Remove only long gaps (> 1 second)
min_duration = otio.opentime.RationalTime(24, 24)
count = remove_gaps(track, min_duration=min_duration)

# Insert 1-second gap at position 5
gap_duration = otio.opentime.RationalTime(24, 24)
insert_gap(track, index=5, duration=gap_duration)

# Consolidate adjacent gaps
count = consolidate_gaps(track)

# Fill gaps with black/silence clips
count = fill_gaps_with_black(track)
```

### Asset Tracking

```python
from pathlib import Path
from conformity.asset_tracker.asset_database import AssetDatabase, AssetType, AssetStatus
from conformity.asset_tracker.asset_scanner import AssetScanner
from conformity.asset_tracker.timeline_analyzer import TimelineAnalyzer
import opentimelineio as otio

# Create database
db_path = Path("project.db")
db = AssetDatabase(db_path)

# Create scanner
scanner = AssetScanner(db)

# Scan directory for media files
results = scanner.scan_directory(
    Path("/media/footage"),
    recursive=True
)

print(f"Added {results['added']} assets")

# Search for assets
assets = db.search_assets(
    asset_type=AssetType.VIDEO,
    status=AssetStatus.APPROVED
)

for asset in assets:
    print(f"{asset['file_name']}: {asset['status']}")

# Analyze timeline
timeline = otio.adapters.read_from_file("timeline.otio")
analyzer = TimelineAnalyzer(db)

results = analyzer.analyze_timeline(timeline)
print(f"Linked clips: {results['linked_clips']}")
print(f"Missing clips: {results['missing_clips']}")

# Verify assets are online
verify_results = scanner.verify_assets()
print(f"Online: {verify_results['online']}, Offline: {verify_results['offline']}")

# Batch update status
selected_ids = [1, 2, 3]
count = scanner.batch_update_status(selected_ids, AssetStatus.APPROVED)
print(f"Updated {count} assets")

# Generate usage report
report = analyzer.generate_usage_report()
print(f"Total associations: {report['total_associations']}")
print(f"Unused assets: {report['unused_assets']}")
```

### Media Review and Conform Verification

```python
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from conformity.ui_components.playback_widget import PlaybackWidget
from conformity.ui_components.conform_review_widget import ConformReviewWidget
from conformity.ui_components.review_panel import ReviewPanel

# Basic playback
app = QApplication([])
player = PlaybackWidget()
player.load_media(Path("media/footage.mp4"), frame_rate=24.0)
player.show()

# Side-by-side conform review
review = ConformReviewWidget()
review.load_source_and_conform(
    Path("source/original.mp4"),
    Path("conform/conformed.mp4")
)

# Enable synchronized playback
review.sync_checkbox.setChecked(True)

# Add markers during review (or use keyboard: I=issue, N=note, A=approved)
review._add_marker("issue")  # Red marker
review._add_marker("note")   # Yellow marker
review._add_marker("approved")  # Green marker

# Export review report
review._export_review_report()

# Get review results
results = review.get_review_results()
print(f"Issues: {results['issues']}")
print(f"Approved frames: {results['approved']}")

review.show()

# Metadata review panel
panel = ReviewPanel()
panel.load_file(Path("media/deliverable.mp4"))

# Set review status
panel.set_status("In Review")
panel.set_notes("Checking color accuracy against source")

# Get review data
data = panel.get_review_data()
print(f"Status: {data['status']}")
print(f"Resolution: {data['metadata']['width']}x{data['metadata']['height']}")

panel.show()

app.exec()
```

## Examples

The `examples/` directory contains comprehensive, runnable examples demonstrating all systems:

```bash
# Asset tracking system examples
python examples/asset_tracking_example.py

# Media review system examples
python examples/media_review_example.py

# Integrated workflow examples
python examples/integrated_workflow_example.py

# tlRender professional playback examples
python examples/tlrender_example.py

# Natural language command interface examples
python examples/command_interface_example.py
```

Each example includes:
- Complete working code
- Clear documentation
- Real-world scenarios
- Integration patterns

See [examples/README.md](examples/README.md) for detailed information about each example.

## Development

### Running Tests

Run the test suite with pytest:
```bash
pytest tests/
```

With coverage:
```bash
pytest --cov=src/conformity tests/
```

### Code Style

Format code with black:
```bash
black src/ tests/
```

Lint with flake8:
```bash
flake8 src/ tests/
```

Type checking with mypy:
```bash
mypy src/
```

## Project Structure

```
Conformity/
├── src/
│   └── conformity/
│       ├── __init__.py
│       ├── main.py              # Application entry point
│       ├── main_window.py       # Main Qt window
│       ├── core/                # Core utilities
│       ├── conform_engine/      # Timeline operations
│       ├── color_manager/       # Color management
│       ├── asset_tracker/       # Asset management
│       └── ui_components/       # UI widgets
├── tests/                       # Unit tests
│   ├── __init__.py
│   ├── test_timeline_manager.py
│   └── test_asset_manager.py
├── config/                      # Configuration files
│   └── default_config.yaml
├── docs/                        # Documentation
├── logs/                        # Log files (generated)
├── requirements.txt             # Python dependencies
├── setup.py                     # Package setup
├── run.py                       # Convenience run script
├── .gitignore
└── README.md
```

## Dependencies

### Core Libraries

- **OpenTimelineIO**: Timeline interchange format and operations
- **PyOpenColorIO**: Color management and transformations
- **PyQt6**: GUI framework

### Supporting Libraries

- **PyYAML**: Configuration file parsing
- **Pydantic**: Data validation and settings management
- **python-dotenv**: Environment variable management

### Development Dependencies

- **pytest**: Testing framework
- **pytest-qt**: Qt testing support
- **pytest-cov**: Coverage reporting
- **black**: Code formatting
- **flake8**: Code linting
- **mypy**: Static type checking

## Roadmap

Future enhancements planned:

- [x] **EDL import/export support** - Complete CMX 3600 support with parsing, writing, validation
- [x] **Advanced timeline editing tools** - Professional editing operations with undo/redo support
- [x] **LUT application and management** - Full LUT loading, library management, and timeline integration
- [ ] Render queue management
- [ ] Multi-project workspace
- [ ] Plugin architecture
- [ ] REST API for pipeline integration
- [ ] Database backend for asset metadata

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Ensure code passes linting and tests
6. Submit a pull request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Acknowledgments

- Built with [OpenTimelineIO](https://github.com/AcademySoftwareFoundation/OpenTimelineIO)
- Color management by [OpenColorIO](https://github.com/AcademySoftwareFoundation/OpenColorIO)
- UI powered by [Qt for Python](https://www.qt.io/qt-for-python)

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/yourusername/conformity/issues
- Documentation: https://github.com/yourusername/conformity/docs

## Version History

### 0.9.0 (Current)
- **Production Tracker**
  - Comprehensive production workflow tracking system
  - SQLite database with 9 interconnected tables
  - Project hierarchy: Projects → Sequences → Shots
  - Multi-department tracking (Editorial, VFX, Color, Sound, Finishing, Delivery)
  - Shot-level status tracking per department
  - VFX complexity categorization (simple/medium/complex)
  - Task management with assignment, priority, and time tracking
  - Review and approval workflow with multi-stage feedback
  - Deliverables checklist with category organization
  - Team and vendor directory management
  - Progress statistics and reporting
  - Shots needing attention alerts (review/revision/blocked)
  - Qt dashboard widget with visual progress bars
  - Tabbed interface: Dashboard, Shots, Tasks, Deliverables, Team
  - Department status color coding in shot table
  - High-level ShotTracker workflow manager
  - Direct ProductionDatabase access for advanced use
  - Comprehensive documentation in docs/PRODUCTION_TRACKER.md
  - Complete example workflows in examples/production_tracker_example.py
  - Professional post-production management inspired by industry needs

### 0.8.0
- **Natural Language Command Interface**
  - Pattern-based natural language query parser
  - Command types: find, show, list, count, filter
  - Multiple filter types: keyword, color space, status, type, codec, resolution, frame rate, tags
  - Autocomplete suggestions with live preview
  - Command history with search and statistics
  - Saved queries with categories and import/export
  - Qt GUI widget with table and text result views
  - Built-in help system with examples
  - LLM-ready architecture with clear separation of concerns
  - Structured command representation (ParsedCommand)
  - Stateless executor for any command source
  - Command registry for documentation and LLM context
  - Keyboard shortcuts for history navigation
  - Confidence scoring for parse quality
  - Extensible design for adding commands and filters
  - Comprehensive documentation in docs/COMMAND_INTERFACE.md
  - Example queries: "find clips with shot_010", "show assets in rec709", "list missing media"

### 0.7.0
- **Professional Playback with tlRender**
  - High-performance playback engine using tlRender
  - Professional format support (EXR, DPX, ProRes, RED, ARRI, Blackmagic RAW)
  - Hardware-accelerated rendering (OpenGL/Vulkan)
  - OCIO color management integration
  - Frame-accurate navigation and scrubbing
  - Image sequence playback with intelligent caching
  - Timeline playback with multi-track support
  - Qt widget wrapper for GUI integration
  - Speed control (normal, half, double, reverse playback)
  - Keyboard shortcuts for efficient operation
  - Optimized for high-resolution media (4K, 6K, 8K)
  - Professional playback controls and monitoring
  - Comprehensive documentation in docs/TLRENDER.md
  - Example workflows and integration patterns

### 0.6.0
- **Media Review and Conform Verification**
  - Frame-accurate video playback with Qt Multimedia
  - Standard playback controls (play, pause, stop, scrub)
  - Frame-by-frame navigation (forward/back with arrow keys)
  - Timecode display (HH:MM:SS:FF) with configurable frame rates
  - Image sequence support (auto-detection and playback)
  - Side-by-side conform verification widget
  - Synchronized playback for source vs conform comparison
  - Frame marker system (issue, note, approved)
  - Marker navigation and management
  - Export marked frames and comprehensive review reports
  - Review panel with technical metadata display
  - Color space information display
  - Review status tracking (pending, approved, rejected)
  - Keyboard shortcuts for efficient workflow
  - Comprehensive test suite (15+ tests passing)
  - Full documentation in docs/MEDIA_REVIEW.md

### 0.5.0
- **Asset Tracking System**
  - SQLite database backend for persistent storage
  - Asset metadata storage (paths, types, technical specs)
  - Timeline associations (clip-to-file relationships)
  - Metadata extraction from video/image/audio files using ffprobe/PIL
  - Automatic codec, resolution, frame rate detection
  - Color space information extraction
  - File checksum calculation (MD5/SHA256)
  - Recursive directory scanning with progress tracking
  - Asset verification (online/offline status)
  - Batch operations (status update, tag addition, relocation)
  - Timeline analyzer for media references
  - Automatic media relinking
  - Usage reports (most used, unused assets)
  - Qt search/filter UI with sortable table
  - Text search across metadata
  - Filter by type, status, color space
  - Comprehensive test suite (20+ tests passing)
  - Full documentation in docs/ASSET_TRACKING.md with schema and examples

### 0.4.0
- **Advanced Timeline Editing Tools**
  - Professional editing modes: Ripple, Roll, Slip, Slide
  - Full undo/redo support with operation history
  - Clip operations: split, trim, copy, paste, duplicate, delete
  - Replace clips with duration matching
  - Move clips between tracks
  - Speed control (slow/fast motion) and reverse playback
  - Track management: add, remove, reorder, duplicate, merge
  - Lock/unlock and mute/solo track controls
  - Gap management: find, remove, insert, consolidate, fill
  - Comprehensive test suite (21/21 tests passing)
  - Full documentation in docs/TIMELINE_EDITING.md
  - API reference with examples and workflow patterns

### 0.3.0
- **LUT Management System**
  - LUT loading and parsing (.cube, .3dl formats)
  - 1D and 3D LUT support with trilinear interpolation
  - LUT library management with categories and favorites
  - Metadata tracking (usage, tags, descriptions)
  - Search and filtering capabilities
  - Apply LUTs to clips and timelines
  - Identity LUT creation
  - Sample LUT files for testing
  - Comprehensive test suite (14/16 tests passing)
  - Full documentation in docs/LUT_WORKFLOWS.md

### 0.2.0
- **EDL Import/Export Support**
  - Complete CMX 3600 format parser and writer
  - EDL↔OTIO bidirectional conversion
  - Reel name management and comment preservation
  - Support for cuts, dissolves, wipes, and keys
  - Multi-track video and audio handling
  - Timecode validation and formatting
  - Sample EDL files and comprehensive tests
  - Full documentation in docs/EDL_WORKFLOWS.md
- UI enhancements for EDL metadata display
- Updated conform panel to show reel names and CMX data

### 0.1.0
- Initial prototype release
- Basic timeline management with OTIO
- OCIO integration for color management
- Asset tracking and management
- Qt-based user interface
- Configuration and logging systems
