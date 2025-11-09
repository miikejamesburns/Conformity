# High-Performance Playback Guide

Conformity provides professional-grade video playback through multiple engines, each optimized for different use cases.

## 📊 Playback Engine Comparison

| Feature | PyAVEngine | OpenImageIO | tlRender (Future) |
|---------|-----------|-------------|-------------------|
| **Status** | ✅ Available NOW | ✅ Available | ⏳ Waiting for Python bindings |
| **Video Files** | ✅ Excellent | ❌ No | ✅ Excellent |
| **Image Sequences** | ⚠️ Via OIIO | ✅ Native | ✅ Native |
| **Professional Codecs** | ✅ ProRes, DNxHD | ❌ No | ✅ All |
| **Hardware Accel** | ✅ FFmpeg | ❌ CPU only | ✅ OpenGL/Vulkan |
| **OCIO Integration** | ✅ Yes | ✅ Yes | ✅ Native |
| **Timeline Playback** | ✅ Yes | ⚠️ Clips only | ✅ Full |
| **Installation** | `pip install` | Build from source | Build from source |

### **Recommended Setup (NOW):**
```bash
pip install -r requirements-full.txt  # Includes PyAV + OCIO
```

---

## 🚀 Quick Start: PyAVEngine

### Installation

```bash
# Full professional setup
pip install -r requirements-full.txt

# Or install components individually
pip install av>=10.0.0           # PyAV for video
pip install numpy>=1.24.0        # Frame processing
pip install opencolorio>=2.3.0   # Color management
```

### Basic Usage

```python
from pathlib import Path
from conformity.playback.pyav_engine import PyAVEngine

# Create engine
engine = PyAVEngine()

# Load media
engine.load_media(Path("footage.mov"))

# Playback controls
engine.play()
engine.pause()
engine.seek(100)          # Seek to frame 100
engine.step_forward()     # Next frame
engine.step_backward()    # Previous frame

# Get current state
info = engine.get_playback_info()
print(f"Frame: {info.current_frame}/{info.total_frames}")
print(f"Timecode: {info.timecode}")
print(f"FPS: {info.frame_rate}")
```

### OCIO Color Management

```python
# Configure color pipeline
engine.set_ocio_config(Path("aces_1.2/config.ocio"))
engine.set_display("ACES", "sRGB")

# Color transform applied automatically during playback
pixels = engine.read_current_frame()  # Returns color-managed pixels
```

### Timeline Playback

```python
# Load OTIO timeline
engine.load_timeline(Path("editorial/sequence.otio"))

# Automatically loads first clip with timeline frame rate
# Full multi-track timeline support coming soon
```

---

## 🎬 Supported Formats

### Video (via PyAV/FFmpeg)

**Professional Codecs:**
- ProRes 422/4444/XQ
- DNxHD/DNxHR
- XDCAM HD
- MPEG IMX

**Delivery Codecs:**
- H.264/AVC
- H.265/HEVC
- VP9

**Containers:**
- MOV, MP4, MXF
- AVI, MKV

### Image Sequences (via OpenImageIO - optional)

**VFX Formats:**
- OpenEXR (.exr) - 16/32-bit float
- DPX (.dpx) - 10/12/16-bit
- TIFF (.tif/.tiff) - 8/16-bit

**Proxy Formats:**
- PNG (.png)
- JPEG (.jpg)

**Installation:**
```bash
# macOS
brew install openimageio
pip install openimageio

# Linux
sudo apt-get install libopenimageio-dev python3-openimageio

# Or build from source - see docs/BUILDING_OPTIONAL_DEPS.md
```

---

## ⚙️ Advanced Features

### Hardware Acceleration

PyAVEngine automatically uses FFmpeg's hardware acceleration:

```python
engine = PyAVEngine()
engine.load_media(Path("4k_prores.mov"))

# Hardware decoding enabled automatically
# Check logs for: "Hardware acceleration: Enabled"
```

**Supported Hardware:**
- NVIDIA NVDEC (Linux/Windows)
- Intel Quick Sync (Linux/Windows)
- VideoToolbox (macOS)
- VAAPI (Linux)

### Frame Caching

```python
from conformity.playback.pyav_engine import ImageSequenceReader

# Load image sequence with caching
reader = ImageSequenceReader(
    Path("renders/frame.0001.exr"),
    frame_rate=24.0
)

# Automatically caches 100 most recent frames
reader.cache_size = 200  # Adjust cache size

pixels = reader.read_frame(100)  # Cached for instant access
```

### Callbacks

```python
def on_frame_changed(frame_num):
    print(f"Now showing frame {frame_num}")

def on_state_changed(state):
    print(f"Playback state: {state.value}")

engine.set_frame_changed_callback(on_frame_changed)
engine.set_state_changed_callback(on_state_changed)

engine.play()  # Triggers: "Playback state: playing"
engine.seek(50)  # Triggers: "Now showing frame 50"
```

### Speed Control

```python
from conformity.playback.pyav_engine import PlaybackSpeed

# Normal playback
engine.set_speed(PlaybackSpeed.NORMAL.value)  # 1.0x

# Slow motion
engine.set_speed(PlaybackSpeed.HALF_SPEED.value)  # 0.5x

# Fast forward
engine.set_speed(PlaybackSpeed.DOUBLE_SPEED.value)  # 2.0x

# Reverse
engine.set_speed(PlaybackSpeed.REVERSE.value)  # -1.0x

# Custom speed
engine.set_speed(0.25)  # Quarter speed
```

---

## 🔧 Performance Optimization

### For 4K+ Video

```python
# Use hardware acceleration (automatic)
engine = PyAVEngine()
engine.load_media(Path("4k_prores.mov"))

# For best performance:
# - Use ProRes or DNxHD (optimized codecs)
# - Enable hardware decoding (automatic via FFmpeg)
# - Use SSD storage for media files
```

### For Image Sequences

```python
# Increase cache size for smoother playback
reader = ImageSequenceReader(first_frame, frame_rate=24.0)
reader.cache_size = 500  # Cache 500 frames (~20 seconds at 24fps)

# Pre-load frames
for i in range(100):
    reader.read_frame(i)  # Populate cache
```

### Memory Management

```python
# Clean up when done
engine.cleanup()  # Closes files, clears caches

# For long-running applications
import gc
engine.cleanup()
gc.collect()  # Force garbage collection
```

---

## 🎨 Color Management Workflows

### ACES Workflow

```python
# Load ACES config
engine.set_ocio_config(Path("OpenColorIO-Configs/aces_1.2/config.ocio"))

# sRGB display
engine.set_display("ACES", "sRGB")

# Rec.709 display
engine.set_display("ACES", "Rec.709")

# DCI-P3 display
engine.set_display("ACES", "P3-D60")

# Load ACES footage
engine.load_media(Path("footage_acescg.exr"))
# Color transform applied automatically
```

### Log Footage

```python
# Configure for Log C
engine.set_ocio_config(Path("vendor_luts/arri_alexa.ocio"))
engine.set_display("Log C", "Rec.709")

engine.load_media(Path("alexa_logc.mov"))
```

### Custom LUTs

```python
# Load config with custom LUTs
engine.set_ocio_config(Path("project/color_config.ocio"))

# Apply show LUT
engine.set_display("Rec.709", "Show LUT")
```

---

## 📝 Complete Example

```python
#!/usr/bin/env python3
"""
Complete high-performance playback example.
"""

from pathlib import Path
from conformity.playback.pyav_engine import PyAVEngine, PlaybackState

def main():
    # Initialize engine
    engine = PyAVEngine()
    print(f"Supported formats: {engine.get_supported_formats()}")

    # Configure color management
    ocio_config = Path("aces_1.2/config.ocio")
    if ocio_config.exists():
        engine.set_ocio_config(ocio_config)
        engine.set_display("ACES", "sRGB")
        print("✓ OCIO color management enabled")

    # Load media
    media_file = Path("footage.mov")
    if media_file.exists():
        engine.load_media(media_file)
        print(f"✓ Loaded: {media_file.name}")

        # Get media info
        info = engine.get_playback_info()
        print(f"  Duration: {info.duration:.2f}s")
        print(f"  Frames: {info.total_frames}")
        print(f"  Frame rate: {info.frame_rate} fps")

        # Set up callbacks
        def on_frame(frame):
            if frame % 24 == 0:  # Every second at 24fps
                tc = engine.get_timecode(frame)
                print(f"  Frame {frame} - TC: {tc}")

        engine.set_frame_changed_callback(on_frame)

        # Playback demonstration
        print("\nPlayback demonstration:")

        # Play first 5 seconds
        engine.play()
        for i in range(120):  # 5 seconds at 24fps
            engine.seek(i)

        # Pause and examine a frame
        engine.pause()
        print(f"\n✓ Paused at frame {engine.get_current_frame()}")

        # Read current frame pixels
        pixels = engine.read_current_frame()
        if pixels is not None:
            print(f"  Frame shape: {pixels.shape}")
            print(f"  Frame dtype: {pixels.dtype}")

        # Clean up
        engine.cleanup()
        print("\n✓ Playback complete")

    else:
        print(f"Media file not found: {media_file}")
        print("\nTo test with your own media:")
        print("  engine.load_media(Path('/path/to/your/video.mov'))")

if __name__ == "__main__":
    main()
```

---

## 🔮 Future: tlRender Integration

When tlRender Python bindings become available, switching is seamless:

```python
# Current (PyAVEngine)
from conformity.playback.pyav_engine import PyAVEngine
engine = PyAVEngine()

# Future (tlRender) - Same API!
from conformity.playback.tlrender_engine import TLRenderEngine
engine = TLRenderEngine()

# All the same methods work
engine.load_media(Path("footage.mov"))
engine.play()
```

**Monitor tlRender development:**
- https://github.com/darbyjohnston/tlRender
- Check "Issues" for Python binding updates
- Or contribute pybind11 bindings yourself!

---

## 🐛 Troubleshooting

### PyAV Installation Issues

**Problem:** `ERROR: Could not find a version that satisfies the requirement av`

**Solution:**
```bash
# Make sure you have FFmpeg libraries
# macOS:
brew install ffmpeg

# Linux:
sudo apt-get install libavformat-dev libavcodec-dev libavutil-dev

# Then install PyAV
pip install av
```

### Hardware Acceleration Not Working

**Check:**
```python
import av
print(av.library_versions)  # Should show FFmpeg 4.0+

# In engine logs, look for:
# "Hardware acceleration: Enabled"
```

**Linux:**
```bash
# Install VAAPI drivers
sudo apt-get install vainfo libva-dev
```

**macOS:**
VideoToolbox should work automatically with FFmpeg 4.0+

### Image Sequence Performance

**Problem:** Slow playback of EXR sequences

**Solutions:**
1. Increase cache size:
   ```python
   reader.cache_size = 1000  # More frames cached
   ```

2. Pre-load frames:
   ```python
   for i in range(start, end):
       reader.read_frame(i)  # Load into cache
   ```

3. Use proxy format (DPX or TIFF instead of EXR)

4. Check storage speed (SSD recommended for 4K+)

### OCIO Transform Errors

**Problem:** `Failed to apply OCIO transform`

**Check:**
1. Config file exists and is valid
2. Display/view names are correct
3. Source color space matches media

```python
# List available displays
config = ocio.Config.CreateFromFile("config.ocio")
for i in range(config.getNumDisplays()):
    display = config.getDisplay(i)
    print(f"Display: {display}")
    for j in range(config.getNumViews(display)):
        view = config.getView(display, j)
        print(f"  View: {view}")
```

---

## 📚 Additional Resources

- **PyAV Documentation:** https://pyav.org/
- **OpenImageIO:** https://openimageio.readthedocs.io/
- **OpenColorIO:** https://opencolorio.readthedocs.io/
- **FFmpeg Codecs:** https://ffmpeg.org/general.html#Supported-File-Formats
- **tlRender:** https://github.com/darbyjohnston/tlRender

---

## ✅ Current Status Summary

**What Works NOW:**
- ✅ Professional video playback (ProRes, DNxHD, H.264/5)
- ✅ Hardware-accelerated decoding
- ✅ OCIO color management
- ✅ Frame-accurate seeking
- ✅ Timeline playback (OTIO)
- ✅ Image sequences (with OpenImageIO)
- ✅ Timecode generation
- ✅ Playback speed control

**Coming Soon:**
- ⏳ tlRender Python bindings (ultimate performance)
- 🔄 Multi-track timeline rendering
- 🔄 Transition/effect processing
- 🔄 Audio synchronization

**Ready for:**
- ✅ Editorial review
- ✅ Conform verification
- ✅ VFX shot review
- ✅ Color grading prep
- ✅ Client review sessions

---

**You have high-performance playback NOW.** Install with:

```bash
pip install -r requirements-full.txt
```

Then start playing professional media immediately!
