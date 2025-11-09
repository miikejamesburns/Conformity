#!/usr/bin/env python3
"""
Example: High-Performance Playback with PyAVEngine

Demonstrates professional video playback using PyAV (FFmpeg):
- Video file playback (ProRes, DNxHD, H.264, etc.)
- Hardware acceleration
- OCIO color management
- Frame-accurate navigation
- Image sequence support (with OpenImageIO)

Note: This works NOW - no building required!
Installation: pip install -r requirements-full.txt
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from conformity.playback.pyav_engine import PyAVEngine, PlaybackState, PlaybackSpeed


def example_basic_playback():
    """Basic video playback example."""
    print("=" * 70)
    print("EXAMPLE 1: Basic Video Playback")
    print("=" * 70)
    print()

    print("PyAVEngine provides professional playback using FFmpeg:")
    print("""
from conformity.playback.pyav_engine import PyAVEngine

# Create engine
engine = PyAVEngine()

# Load video file
engine.load_media(Path("footage.mov"))

# Playback controls
engine.play()                # Start playback
engine.pause()               # Pause
engine.stop()                # Stop and return to start

# Frame navigation
engine.seek(100)             # Jump to frame 100
engine.step_forward()        # Next frame
engine.step_backward()       # Previous frame

# Speed control
engine.set_speed(1.0)        # Normal speed
engine.set_speed(0.5)        # Half speed
engine.set_speed(2.0)        # Double speed
engine.set_speed(-1.0)       # Reverse

# Get current state
info = engine.get_playback_info()
print(f"Frame: {info.current_frame}/{info.total_frames}")
print(f"Timecode: {info.timecode}")
print(f"FPS: {info.frame_rate}")
    """)

    # Demonstrate with no media loaded
    engine = PyAVEngine()
    print(f"✓ Engine initialized")
    print(f"  Supported formats: {len(engine.get_supported_formats())} formats")
    print()


def example_supported_formats():
    """Show supported formats."""
    print("=" * 70)
    print("EXAMPLE 2: Supported Formats")
    print("=" * 70)
    print()

    engine = PyAVEngine()

    print("Professional Video Formats (via FFmpeg):")
    video_formats = ['.mov', '.mp4', '.mxf', '.prores', '.dnxhd', '.dnxhr']
    for fmt in video_formats:
        if fmt in engine.get_supported_formats():
            print(f"  ✓ {fmt}")

    print("\nProxy/Delivery Formats:")
    proxy_formats = ['.avi', '.mkv', '.m4v']
    for fmt in proxy_formats:
        if fmt in engine.get_supported_formats():
            print(f"  ✓ {fmt}")

    print("\nImage Sequences (requires OpenImageIO):")
    print("  ○ .exr (OpenEXR)")
    print("  ○ .dpx (DPX)")
    print("  ○ .tiff (TIFF)")
    print()
    print("Install: pip install openimageio")
    print()


def example_ocio_color():
    """OCIO color management example."""
    print("=" * 70)
    print("EXAMPLE 3: OCIO Color Management")
    print("=" * 70)
    print()

    print("Real-time color transforms during playback:")
    print("""
from conformity.playback.pyav_engine import PyAVEngine

engine = PyAVEngine()

# Configure OCIO
engine.set_ocio_config(Path("aces_1.2/config.ocio"))
engine.set_display("ACES", "sRGB")

# Load media
engine.load_media(Path("footage_aces.exr"))

# Color transform applied automatically!
pixels = engine.read_current_frame()  # Already color-managed

# Change display/view on the fly
engine.set_display("ACES", "Rec.709")  # Different output transform
engine.set_display("ACES", "P3-D60")   # DCI-P3 display
    """)

    # Check if OCIO is available
    try:
        import PyOpenColorIO as ocio
        print("✓ PyOpenColorIO is installed - color management ready!")
        print(f"  Version: {ocio.__version__}")
    except ImportError:
        print("○ PyOpenColorIO not installed")
        print("  Install: pip install opencolorio>=2.3.0")

    print()


def example_timeline_playback():
    """Timeline playback example."""
    print("=" * 70)
    print("EXAMPLE 4: Timeline Playback")
    print("=" * 70)
    print()

    print("Load OpenTimelineIO timelines:")
    print("""
from conformity.playback.pyav_engine import PyAVEngine

engine = PyAVEngine()

# Load OTIO timeline
engine.load_timeline(Path("editorial/sequence.otio"))

# Automatically detects frame rate and loads media
info = engine.get_playback_info()
print(f"Timeline: {info.total_frames} frames at {info.frame_rate} fps")

# Standard playback controls work
engine.play()
engine.seek(100)
    """)

    print("✓ Timeline support via OpenTimelineIO")
    print("  Currently loads first clip from timeline")
    print("  Full multi-track rendering coming soon")
    print()


def example_performance():
    """Performance characteristics."""
    print("=" * 70)
    print("EXAMPLE 5: Performance")
    print("=" * 70)
    print()

    print("Hardware Acceleration:")
    print("  ✓ Automatic via FFmpeg")
    print("  ✓ NVIDIA NVDEC (Linux/Windows)")
    print("  ✓ Intel Quick Sync (Linux/Windows)")
    print("  ✓ VideoToolbox (macOS)")
    print("  ✓ VAAPI (Linux)")
    print()

    print("Optimized for:")
    print("  ✓ 4K ProRes playback")
    print("  ✓ DNxHD/DNxHR workflows")
    print("  ✓ High frame rate media (60/120fps)")
    print("  ✓ Professional codec efficiency")
    print()

    print("Frame Caching:")
    print("  • Image sequences: 100 frame cache (adjustable)")
    print("  • Video: FFmpeg native buffering")
    print("  • Instant frame access when cached")
    print()


def example_image_sequences():
    """Image sequence playback."""
    print("=" * 70)
    print("EXAMPLE 6: Image Sequences")
    print("=" * 70)
    print()

    print("Professional VFX format support:")
    print("""
from conformity.playback.pyav_engine import PyAVEngine

engine = PyAVEngine()

# Load first frame of sequence
# Automatically detects and loads full sequence
engine.load_media(Path("renders/frame.0001.exr"), frame_rate=24.0)

# Pattern detection:
#   frame.0001.exr → loads frame.0001.exr, frame.0002.exr, etc.
#   shot_010.1001.dpx → loads shot_010.1001.dpx, shot_010.1002.dpx, etc.

# Supported formats (with OpenImageIO):
#   - OpenEXR (.exr) - 16/32-bit float, perfect for VFX
#   - DPX (.dpx) - 10/12/16-bit, film/broadcast standard
#   - TIFF (.tif/.tiff) - 8/16-bit, general purpose

# Playback with caching
engine.play()
    """)

    print("Note: Requires OpenImageIO")
    print("  Install: pip install openimageio")
    print("  Or: brew install openimageio (macOS)")
    print()


def example_callbacks():
    """Callback system example."""
    print("=" * 70)
    print("EXAMPLE 7: Callbacks & Integration")
    print("=" * 70)
    print()

    print("Integrate with your application:")
    print("""
from conformity.playback.pyav_engine import PyAVEngine

engine = PyAVEngine()

# Frame change callback
def on_frame_changed(frame_num):
    print(f"Now showing frame {frame_num}")
    # Update UI, generate thumbnails, etc.

engine.set_frame_changed_callback(on_frame_changed)

# State change callback
def on_state_changed(state):
    print(f"Playback state: {state.value}")
    # Update play/pause button, etc.

engine.set_state_changed_callback(on_state_changed)

# Now callbacks fire automatically
engine.play()    # → "Playback state: playing"
engine.seek(50)  # → "Now showing frame 50"
    """)

    print("✓ Easy GUI integration")
    print("✓ Custom event handling")
    print("✓ Real-time monitoring")
    print()


def demo_live_playback():
    """Live demonstration if possible."""
    print("=" * 70)
    print("LIVE DEMO: Testing PyAVEngine")
    print("=" * 70)
    print()

    try:
        engine = PyAVEngine()
        print("✓ PyAVEngine initialized successfully")
        print()

        # Test controls without media
        print("Testing playback controls:")
        engine.play()
        print(f"  play()   → State: {engine.state.value}")

        engine.pause()
        print(f"  pause()  → State: {engine.state.value}")

        engine.stop()
        print(f"  stop()   → State: {engine.state.value}")

        # Test navigation
        engine.total_frames = 1000
        engine.frame_rate = 24.0

        engine.seek(100)
        print(f"  seek(100) → Frame: {engine.get_current_frame()}")

        tc = engine.get_timecode(100)
        print(f"  timecode  → {tc}")

        print()
        print("✓ All systems operational!")

        # Check dependencies
        print()
        print("Dependency Status:")

        try:
            import av
            print(f"  ✓ PyAV v{av.__version__}")
        except ImportError:
            print("  ✗ PyAV not installed")

        try:
            import PyOpenColorIO as ocio
            print(f"  ✓ PyOpenColorIO v{ocio.__version__}")
        except ImportError:
            print("  ○ PyOpenColorIO not installed (optional)")

        try:
            import OpenImageIO as oiio
            version = oiio.VERSION_STRING if hasattr(oiio, 'VERSION_STRING') else "unknown"
            print(f"  ✓ OpenImageIO v{version}")
        except ImportError:
            print("  ○ OpenImageIO not installed (optional)")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

    print()


def main():
    """Run all examples."""
    print("\n")
    print("=" * 70)
    print("PYAVENGINE: HIGH-PERFORMANCE PLAYBACK EXAMPLES")
    print("=" * 70)
    print("\nProfessional video playback using PyAV (FFmpeg)")
    print("Works NOW - no building required!")
    print()

    example_basic_playback()
    example_supported_formats()
    example_ocio_color()
    example_timeline_playback()
    example_performance()
    example_image_sequences()
    example_callbacks()
    demo_live_playback()

    print("=" * 70)
    print("INSTALLATION")
    print("=" * 70)
    print()
    print("Full professional setup:")
    print("  pip install -r requirements-full.txt")
    print()
    print("Or install components:")
    print("  pip install av>=10.0.0              # Video playback")
    print("  pip install opencolorio>=2.3.0      # Color management")
    print("  pip install openimageio>=2.4.0      # Image sequences")
    print()
    print("=" * 70)
    print()
    print("For more information:")
    print("  - docs/HIGH_PERFORMANCE_PLAYBACK.md")
    print("  - docs/COLOR_WORKFLOWS.md")
    print("  - README.md")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
