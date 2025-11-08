## tlRender Integration

### Overview

Conformity integrates **tlRender** for professional-grade video playback capabilities. tlRender is a high-performance playback library specifically designed for OpenTimelineIO, providing industry-standard format support and hardware acceleration.

**Key Benefits:**
- Professional format support (EXR, DPX, ProRes, RED, ARRI, etc.)
- Hardware-accelerated rendering (OpenGL, Vulkan)
- Integrated OCIO color management
- Frame-accurate playback and scrubbing
- Image sequence handling
- Timeline playback with multi-track support
- Optimized for high-resolution media (4K, 6K, 8K)

### Why tlRender?

tlRender provides capabilities essential for professional post-production workflows that basic playback systems cannot match:

| Feature | tlRender | Qt Multimedia |
|---------|----------|---------------|
| EXR/DPX Sequences | ✓ Excellent | ✗ Not supported |
| ProRes 4444 | ✓ Hardware accelerated | △ Software only |
| OCIO Integration | ✓ Real-time | ✗ Not supported |
| Timeline Playback | ✓ Full OTIO support | △ Limited |
| 4K+ Performance | ✓ Optimized | △ Variable |
| Frame Accuracy | ✓ Guaranteed | △ Limited |
| RAW Formats | ✓ R3D, BRAW, ARRIRAW | ✗ Not supported |

**When to use tlRender:**
- Working with professional formats (EXR, DPX, ProRes 4444)
- Reviewing high-resolution media (4K+)
- ACES or other OCIO-based workflows
- Frame-accurate conform verification
- Timeline playback from editorial
- VFX shot review

**When Qt Multimedia is sufficient:**
- Quick review of H.264/H.265 proxies
- Basic playback needs
- tlRender not available on system

---

## Installation

### Building tlRender from Source

tlRender is under active development and currently requires building from source:

```bash
# 1. Clone repository
git clone https://github.com/darbyjohnston/tlRender.git
cd tlRender

# 2. Install dependencies (Ubuntu/Debian)
sudo apt-get install \
    build-essential cmake git \
    libgl1-mesa-dev \
    libasound2-dev \
    libpulse-dev

# 3. Build tlRender
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
sudo make install

# 4. Set library path
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
```

### Python Bindings

Python bindings for tlRender are in development. Check the tlRender repository for the latest status:
- https://github.com/darbyjohnston/tlRender/tree/main/python

Once available:
```bash
pip install tlrender-python
```

### Verify Installation

```python
import sys

# Test tlRender import
try:
    import tlRender as tlr
    print(f"tlRender version: {tlr.__version__}")
    print("✓ tlRender available")
except ImportError as e:
    print(f"✗ tlRender not available: {e}")
```

---

## Usage

### Basic Playback

```python
from pathlib import Path
from conformity.playback.tlrender_engine import TLRenderEngine

# Create engine
engine = TLRenderEngine()

# Load media file
engine.load_media(Path("footage.mov"), frame_rate=24.0)

# Playback control
engine.play()                    # Start playback
engine.pause()                   # Pause
engine.stop()                    # Stop and return to start
engine.toggle_play_pause()       # Toggle play/pause

# Navigation
engine.seek(120)                 # Seek to frame 120
engine.step_forward()            # Next frame
engine.step_backward()           # Previous frame

# Get state
info = engine.get_playback_info()
print(f"Frame: {info.current_frame}/{info.total_frames}")
print(f"Timecode: {info.timecode}")
print(f"State: {info.state.value}")
```

### Timeline Playback

```python
import opentimelineio as otio
from conformity.playback.tlrender_engine import TLRenderEngine

# Load OTIO timeline
engine = TLRenderEngine()
engine.load_timeline(Path("editorial/sequence.otio"))

# Timeline properties detected automatically
print(f"Frame rate: {engine.frame_rate} fps")
print(f"Duration: {engine.get_duration():.2f} seconds")

# Play timeline
engine.play()

# Navigate timeline
engine.seek(240)  # Seek to frame 240
```

### Image Sequences

```python
# Load EXR sequence
engine = TLRenderEngine()
engine.load_media(Path("renders/frame.0001.exr"), frame_rate=24.0)

# tlRender automatically:
# - Detects the sequence pattern
# - Finds all frames in the directory
# - Handles missing frames gracefully

# Supported patterns:
# - frame.0001.exr, frame.0002.exr, ...
# - shot_001.1001.dpx, shot_001.1002.dpx, ...
# - render.####.tif (detected from single frame)

# Playback is optimized for sequences
engine.play()  # Smooth playback with intelligent caching
```

### OCIO Color Management

```python
from pathlib import Path
from conformity.playback.tlrender_engine import TLRenderEngine

engine = TLRenderEngine()

# Load OCIO configuration
ocio_config = Path("aces_1.2/config.ocio")
engine.set_ocio_config(ocio_config)

# Set display and view
engine.set_display("ACES", "sRGB")

# Load media - color transform applied automatically
engine.load_media(Path("footage_aces.exr"))

# Color transform runs in real-time with hardware acceleration
engine.play()

# Switch display/view during playback
engine.set_display("ACES", "Rec.709")
engine.set_display("ACES", "DCI-P3")
```

### Qt Widget Integration

```python
from PyQt6.QtWidgets import QApplication, QMainWindow
from conformity.ui_components.tlrender_widget import TLRenderWidget

app = QApplication([])

# Create main window
window = QMainWindow()

# Create tlRender widget
player = TLRenderWidget()

# Load media
player.load_media(Path("footage.mov"), frame_rate=24.0)

# Configure OCIO
player.set_ocio_config(Path("aces_1.2/config.ocio"))
player.set_display("ACES", "sRGB")

# Connect signals
player.frame_changed.connect(lambda f: print(f"Frame: {f}"))
player.timecode_changed.connect(lambda tc: print(f"TC: {tc}"))

# Show player
window.setCentralWidget(player)
window.show()

app.exec()
```

---

## API Reference

### TLRenderEngine

High-performance playback engine.

#### Methods

**`load_timeline(timeline_path: Path) -> bool`**
- Load OpenTimelineIO timeline for playback
- Automatically detects frame rate and duration
- Returns True if successful

**`load_media(media_path: Path, frame_rate: float = 24.0) -> bool`**
- Load media file or image sequence
- Auto-detects sequences from extension
- Returns True if successful

**`set_ocio_config(config_path: Path) -> bool`**
- Set OCIO configuration file
- Enables color management
- Returns True if successful

**`set_display(display: str, view: str) -> bool`**
- Set OCIO display and view
- Applied in real-time
- Returns True if successful

**`play() -> None`**
- Start playback at current speed

**`pause() -> None`**
- Pause playback

**`stop() -> None`**
- Stop and return to beginning

**`toggle_play_pause() -> None`**
- Toggle between play and pause

**`seek(frame: int) -> None`**
- Seek to specific frame number

**`seek_relative(frame_delta: int) -> None`**
- Seek relative to current position

**`step_forward() -> None`**
- Advance one frame

**`step_backward() -> None`**
- Go back one frame

**`set_speed(speed: float) -> None`**
- Set playback speed multiplier
- 1.0 = normal, 0.5 = half speed, 2.0 = double, -1.0 = reverse

**`get_current_frame() -> int`**
- Get current frame number

**`get_total_frames() -> int`**
- Get total number of frames

**`get_timecode(frame: Optional[int] = None) -> str`**
- Get timecode in HH:MM:SS:FF format

**`get_playback_info() -> PlaybackInfo`**
- Get comprehensive playback state

**`get_supported_formats() -> List[str]`**
- Get list of supported file extensions

**`cleanup() -> None`**
- Clean up resources

#### Callbacks

**`set_frame_changed_callback(callback: Callable[[int], None])`**
- Called when playback frame changes

**`set_state_changed_callback(callback: Callable[[PlaybackState], None])`**
- Called when playback state changes

### TLRenderWidget

Qt widget wrapper for tlRender playback.

#### Signals

- `frame_changed(int)` - Emitted when frame changes
- `timecode_changed(str)` - Emitted when timecode updates
- `state_changed(str)` - Emitted when playback state changes
- `playback_error(str)` - Emitted on errors

#### Methods

Inherits all methods from `TLRenderEngine` plus:

**UI-specific methods:**
- All playback controls available as buttons
- Timeline scrubber slider
- Speed selection dropdown
- OCIO display/view selection

#### Keyboard Shortcuts

- `Space` - Play/Pause
- `Left Arrow` - Step backward
- `Right Arrow` - Step forward
- `Home` - Jump to start
- `End` - Jump to end

---

## Supported Formats

### Video Codecs

- **ProRes** - All variants (Proxy, LT, 422, HQ, 4444, 4444 XQ)
- **DNxHD/DNxHR** - All resolutions and bit depths
- **H.264/H.265** - All profiles
- **Uncompressed** - v210, v216, v410
- **JPEG 2000**
- **MXF** - Various codecs

### Image Formats

- **OpenEXR (.exr)** - 16-bit half, 32-bit float, all compression types
- **DPX (.dpx)** - 10-bit, 12-bit, 16-bit
- **TIFF (.tif, .tiff)** - 8-bit, 16-bit, 32-bit
- **PNG (.png)** - 8-bit, 16-bit
- **JPEG (.jpg, .jpeg)** - Standard compression

### RAW Formats

- **RED (.r3d)** - REDCODE RAW
- **Blackmagic (.braw)** - Blackmagic RAW
- **ARRI (.ari, .arx)** - ARRIRAW

### Container Formats

- **MOV** - QuickTime
- **MP4** - MPEG-4
- **MXF** - Material Exchange Format
- **AVI** - Audio Video Interleave

### Audio Formats

- **WAV** - Uncompressed audio
- **AIFF** - Apple audio
- **MP3** - MPEG audio
- **AAC** - Advanced Audio Coding

---

## Performance Optimization

### Hardware Acceleration

tlRender automatically uses available hardware acceleration:

```python
# OpenGL acceleration (default)
engine = TLRenderEngine()

# Vulkan acceleration (if available)
# Specified during tlRender build configuration
```

### Caching Strategy

tlRender intelligently caches frames for optimal playback:

- **Forward caching** - Pre-loads upcoming frames
- **Adaptive sizing** - Adjusts cache based on available memory
- **Sequence optimization** - Efficient handling of image sequences
- **Multi-threaded** - Parallel decoding and caching

### Resolution Considerations

| Resolution | Recommended RAM | Notes |
|------------|----------------|-------|
| 1080p | 8 GB | Smooth playback |
| 2K | 16 GB | Good performance |
| 4K | 32 GB | Recommended for 4K |
| 6K/8K | 64 GB+ | Professional workflows |

### Image Sequence Performance

For best performance with image sequences:

1. **Use SSD storage** - Significantly faster than HDD
2. **Local storage** - Avoid network paths when possible
3. **Consistent numbering** - e.g., frame.0001.exr (not frame.1.exr)
4. **Appropriate compression** - Balance quality and decode speed

---

## Workflow Examples

### VFX Shot Review

```python
from conformity.playback.tlrender_engine import TLRenderEngine

# Setup for VFX review
engine = TLRenderEngine()

# Load OCIO config for ACES workflow
engine.set_ocio_config(Path("aces_1.2/config.ocio"))
engine.set_display("ACES", "sRGB")

# Load EXR sequence from VFX
engine.load_media(Path("vfx/shot_010/comp.0001.exr"), frame_rate=24.0)

# Review at native resolution with accurate color
engine.play()

# Frame-by-frame inspection
engine.pause()
engine.step_forward()  # Check each frame carefully
```

### Conform Verification

```python
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout
from conformity.ui_components.tlrender_widget import TLRenderWidget

# Create A/B comparison
class ConformReview(QWidget):
    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()

        # Source player
        self.source = TLRenderWidget()
        self.source.load_media(Path("source/master.mov"))
        layout.addWidget(self.source)

        # Conform player
        self.conform = TLRenderWidget()
        self.conform.load_media(Path("deliverables/conform.mov"))
        layout.addWidget(self.conform)

        # Sync playback
        self.source.frame_changed.connect(
            lambda f: self.conform.seek_to_frame(f)
        )

        self.setLayout(layout)

app = QApplication([])
review = ConformReview()
review.show()
app.exec()
```

### Editorial Timeline Review

```python
import opentimelineio as otio
from conformity.playback.tlrender_engine import TLRenderEngine

# Load timeline from editorial
engine = TLRenderEngine()
engine.load_timeline(Path("editorial/episode_01_v5.otio"))

# Timeline includes:
# - Multiple video/audio tracks
# - Transitions between clips
# - Source media references
# - Timing information

# Review full timeline
print(f"Duration: {engine.get_duration():.2f} seconds")
print(f"Frame rate: {engine.frame_rate} fps")

engine.play()

# Navigate to specific sections
engine.seek(1200)  # Jump to frame 1200
```

### Color Grading Review

```python
from conformity.playback.tlrender_engine import TLRenderEngine

engine = TLRenderEngine()

# Load OCIO config
engine.set_ocio_config(Path("aces_1.2/config.ocio"))

# Load graded media
engine.load_media(Path("graded/scene_01_graded.exr"))

# Compare different display transforms
displays = [
    ("ACES", "sRGB"),
    ("ACES", "Rec.709"),
    ("ACES", "DCI-P3"),
]

for display, view in displays:
    engine.set_display(display, view)
    print(f"Reviewing: {display} / {view}")
    engine.play()
    input("Press Enter for next display...")
    engine.stop()
```

---

## Troubleshooting

### tlRender Not Found

**Error:** `ImportError: No module named 'tlRender'`

**Solutions:**
1. Verify tlRender is installed: `which tlrender-play`
2. Check Python bindings: `pip list | grep tlrender`
3. Set PYTHONPATH: `export PYTHONPATH=/path/to/tlRender/python:$PYTHONPATH`
4. Build from source if not available

### Poor Playback Performance

**Symptoms:** Dropped frames, stuttering

**Solutions:**
1. Check available RAM (use `free -h`)
2. Use local SSD storage instead of network
3. Reduce playback resolution temporarily
4. Close other applications
5. Check GPU acceleration is working
6. Consider transcoding to optimized format

### OCIO Config Issues

**Error:** `Failed to load OCIO config`

**Solutions:**
1. Verify config file exists
2. Check config file format (YAML)
3. Validate with `ociocheck <config.ocio>`
4. Use absolute paths for LUT files in config

### Missing Codec Support

**Error:** `Unsupported format: <file>`

**Solutions:**
1. Check format in supported list
2. Verify tlRender build includes codec
3. Install codec libraries (ffmpeg, OpenEXR, etc.)
4. Rebuild tlRender with codec support
5. Convert to supported format

---

## Integration with Conformity Systems

### Asset Tracker Integration

```python
from conformity.asset_tracker.asset_database import AssetDatabase
from conformity.playback.tlrender_engine import TLRenderEngine

# Load asset from database
db = AssetDatabase(Path("project.db"))
asset = db.get_asset_by_id(123)

# Play asset with tlRender
engine = TLRenderEngine()
engine.load_media(Path(asset['file_path']))

# Update playback info in database
metadata = db.get_asset_metadata(asset['id'])
print(f"Resolution: {metadata['width']}x{metadata['height']}")
print(f"Frame rate: {metadata['frame_rate']} fps")
```

### Timeline Editor Integration

```python
from conformity.timeline_editor.edit_operations import RippleEdit
from conformity.playback.tlrender_engine import TLRenderEngine

# Edit timeline
edit = RippleEdit()
timeline = edit.load_timeline(Path("sequence.otio"))

# Make edits...
edit.trim_clip("clip_001", new_duration=120)

# Review edited timeline immediately
engine = TLRenderEngine()
engine.load_timeline(Path("sequence.otio"))
engine.play()
```

### Color Manager Integration

```python
from conformity.color_manager.color_manager import ColorManager
from conformity.playback.tlrender_engine import TLRenderEngine

# Get OCIO config from color manager
color_mgr = ColorManager()
ocio_config = color_mgr.get_ocio_config()

# Apply to playback
engine = TLRenderEngine()
engine.set_ocio_config(ocio_config)
engine.set_display(
    color_mgr.get_default_display(),
    color_mgr.get_default_view()
)

engine.load_media(Path("footage.exr"))
engine.play()
```

---

## Comparison with Alternatives

### tlRender vs DJV

| Feature | tlRender | DJV |
|---------|----------|-----|
| OTIO Support | Native | Plugin |
| Performance | Excellent | Excellent |
| GUI | Library + Viewer | Full application |
| Python API | In development | Limited |
| License | BSD | BSD |

### tlRender vs RV (Shotgun Review)

| Feature | tlRender | RV |
|---------|----------|-----|
| Cost | Free/Open source | Commercial |
| OTIO Support | Native | Limited |
| Performance | Excellent | Excellent |
| Customization | Full API | Limited API |
| Collaboration | DIY | Built-in |

### tlRender vs mpv

| Feature | tlRender | mpv |
|---------|----------|-----|
| Pro Formats | Excellent | Limited |
| OCIO | Native | Plugin |
| Timeline Support | Yes | No |
| Frame Accuracy | Guaranteed | Best effort |
| Python API | In development | Yes |

---

## Additional Resources

### Documentation
- **tlRender GitHub**: https://github.com/darbyjohnston/tlRender
- **OTIO Documentation**: https://opentimelineio.readthedocs.io
- **OCIO Documentation**: https://opencolorio.readthedocs.io

### Community
- **tlRender Discussions**: https://github.com/darbyjohnston/tlRender/discussions
- **ASWF Slack**: Academy Software Foundation channels
- **VFX Platform**: https://vfxplatform.com

### Related Projects
- **DJV**: https://darbyjohnston.github.io/DJV/
- **OpenTimelineIO**: https://github.com/AcademySoftwareFoundation/OpenTimelineIO
- **OpenColorIO**: https://github.com/AcademySoftwareFoundation/OpenColorIO

---

## Development Status

**Note:** tlRender is under active development. Some features may change or be enhanced in future releases.

Current Status (as of documentation):
- **Core playback**: Stable
- **OTIO support**: Stable
- **OCIO integration**: Stable
- **Python bindings**: In development
- **Qt integration**: Example implementations available

Check the tlRender repository for the latest updates and releases.
