#!/usr/bin/env python3
"""
Example: tlRender Integration

Demonstrates how to use tlRender for professional-grade playback in Conformity:
- High-performance timeline playback
- Professional format support (EXR, DPX, ProRes, RAW)
- OCIO color management integration
- Hardware-accelerated rendering
- Frame-accurate navigation

Note: This example requires tlRender to be installed.
For installation instructions, see docs/TLRENDER.md
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Check for tlRender availability
try:
    from conformity.playback.tlrender_engine import (
        TLRenderEngine, PlaybackState, PlaybackSpeed, PlaybackInfo
    )
    HAS_TLRENDER = True
except ImportError as e:
    HAS_TLRENDER = False
    print(f"tlRender not available: {e}")

# Check for PyQt6
try:
    from PyQt6.QtWidgets import QApplication
    from conformity.ui_components.tlrender_widget import TLRenderWidget
    HAS_PYQT6 = True
except ImportError:
    HAS_PYQT6 = False


def example_basic_playback():
    """Basic tlRender playback example."""
    print("=" * 60)
    print("EXAMPLE: Basic tlRender Playback")
    print("=" * 60)

    if not HAS_TLRENDER:
        print("\nSkipped: Requires tlRender")
        print("Install tlRender: https://github.com/darbyjohnston/tlRender")
        return

    print("\nBasic playback API:")
    print("""
# Create engine
engine = TLRenderEngine()

# Load media file
engine.load_media(Path("footage.mov"), frame_rate=24.0)

# Playback controls
engine.play()                    # Start playback
engine.pause()                   # Pause playback
engine.stop()                    # Stop and return to start
engine.toggle_play_pause()       # Toggle play/pause

# Navigation
engine.seek(120)                 # Seek to frame 120
engine.step_forward()            # Next frame
engine.step_backward()           # Previous frame
engine.seek_relative(10)         # Jump 10 frames forward

# Speed control
engine.set_speed(1.0)            # Normal speed
engine.set_speed(0.5)            # Half speed
engine.set_speed(2.0)            # Double speed
engine.set_speed(-1.0)           # Reverse playback

# Get current state
frame = engine.get_current_frame()
timecode = engine.get_timecode()
info = engine.get_playback_info()

print(f"Frame: {info.current_frame}/{info.total_frames}")
print(f"Timecode: {info.timecode}")
print(f"State: {info.state.value}")
    """)

    print("\nKey advantages over basic playback:")
    print("  - Hardware-accelerated rendering")
    print("  - Professional format support")
    print("  - Frame-accurate performance")
    print("  - OCIO color management")
    print("  - Optimized for high-resolution media")


def example_timeline_playback():
    """Timeline playback with tlRender."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Timeline Playback")
    print("=" * 60)

    if not HAS_TLRENDER:
        print("\nSkipped: Requires tlRender")
        return

    print("\nLoad and play OTIO timelines:")
    print("""
from conformity.playback.tlrender_engine import TLRenderEngine

# Create engine
engine = TLRenderEngine()

# Load timeline
engine.load_timeline(Path("editorial/my_sequence.otio"))

# Timeline automatically includes:
# - Multiple video/audio tracks
# - Transitions and effects
# - Clip timing and source ranges
# - Media references

# Frame rate is detected from timeline
print(f"Timeline frame rate: {engine.frame_rate} fps")

# Get timeline information
info = engine.get_playback_info()
print(f"Duration: {info.duration:.2f} seconds")
print(f"Total frames: {info.total_frames}")

# Playback respects timeline structure
engine.play()
    """)

    print("\nTimeline features:")
    print("  - Multi-track support")
    print("  - Automatic media linking")
    print("  - Transition rendering")
    print("  - Effect processing")
    print("  - Audio/video synchronization")


def example_image_sequences():
    """Image sequence playback."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Image Sequence Playback")
    print("=" * 60)

    if not HAS_TLRENDER:
        print("\nSkipped: Requires tlRender")
        return

    print("\nPlay image sequences with tlRender:")
    print("""
# tlRender natively handles image sequences
engine = TLRenderEngine()

# Load any frame from the sequence
# tlRender automatically detects and loads the full sequence
engine.load_media(Path("renders/frame.0001.exr"), frame_rate=24.0)

# Supported formats:
# - EXR (OpenEXR) - Industry standard for VFX
# - DPX (Digital Picture Exchange)
# - TIFF (Tagged Image File Format)
# - PNG, JPEG (for proxies)

# Pattern detection is automatic:
# frame.0001.exr -> finds frame.0001.exr, frame.0002.exr, etc.
# shot_001.1001.dpx -> finds shot_001.1001.dpx, shot_001.1002.dpx, etc.

# Playback performance:
# - Hardware-accelerated decoding
# - Efficient caching
# - Smooth playback even at high resolutions (4K+)
    """)

    print("\nImage sequence advantages:")
    print("  - Frame-accurate access")
    print("  - No compression artifacts")
    print("  - Industry-standard formats")
    print("  - High bit-depth support (16-bit, 32-bit float)")


def example_ocio_color_management():
    """OCIO color management with tlRender."""
    print("\n" + "=" * 60)
    print("EXAMPLE: OCIO Color Management")
    print("=" * 60)

    if not HAS_TLRENDER:
        print("\nSkipped: Requires tlRender")
        return

    print("\nIntegrate OCIO color management:")
    print("""
from conformity.playback.tlrender_engine import TLRenderEngine

engine = TLRenderEngine()

# Load OCIO configuration
engine.set_ocio_config(Path("aces_1.2/config.ocio"))

# Set display and view for output transform
engine.set_display("ACES", "sRGB")

# Load media - color transform is applied automatically
engine.load_media(Path("footage_aces.exr"))

# Common OCIO workflows:

# 1. ACES workflow
engine.set_display("ACES", "sRGB")
engine.set_display("ACES", "Rec.709")
engine.set_display("ACES", "DCI-P3")

# 2. Log footage review
engine.set_display("sRGB", "Log to sRGB")
engine.set_display("Rec.709", "Log to Rec.709")

# 3. HDR monitoring
engine.set_display("Rec.2020", "ST2084 1000 nits")
engine.set_display("Rec.2020", "HLG")

# Color transform is applied in real-time during playback
# with hardware acceleration
    """)

    print("\nOCIO benefits:")
    print("  - Consistent color across applications")
    print("  - Hardware-accelerated transforms")
    print("  - Industry-standard workflows")
    print("  - Real-time preview")


def example_gui_widget():
    """tlRender Qt widget example."""
    print("\n" + "=" * 60)
    print("EXAMPLE: tlRender Qt Widget")
    print("=" * 60)

    if not HAS_PYQT6 or not HAS_TLRENDER:
        print("\nSkipped: Requires PyQt6 and tlRender")
        if not HAS_PYQT6:
            print("  Missing: PyQt6")
        if not HAS_TLRENDER:
            print("  Missing: tlRender")
        return

    print("\nUse tlRender in Qt GUI:")
    print("""
from PyQt6.QtWidgets import QApplication
from conformity.ui_components.tlrender_widget import TLRenderWidget

app = QApplication([])

# Create widget
player = TLRenderWidget()

# Load timeline
player.load_timeline(Path("sequence.otio"))

# Or load media file
player.load_media(Path("footage.mov"), frame_rate=24.0)

# Configure color management
player.set_ocio_config(Path("aces_1.2/config.ocio"))
player.set_display("ACES", "sRGB")

# Connect signals for integration
player.frame_changed.connect(lambda f: print(f"Frame: {f}"))
player.timecode_changed.connect(lambda tc: print(f"TC: {tc}"))
player.state_changed.connect(lambda s: print(f"State: {s}"))

# Show widget
player.show()
app.exec()
    """)

    print("\nWidget features:")
    print("  - Professional playback controls")
    print("  - Timeline scrubber")
    print("  - Speed control")
    print("  - OCIO display/view selection")
    print("  - Keyboard shortcuts")
    print("  - Real-time performance monitoring")


def example_performance_comparison():
    """Performance comparison: tlRender vs basic playback."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Performance Comparison")
    print("=" * 60)

    print("\nWhen to use tlRender vs Qt Multimedia:")

    print("\nUse tlRender for:")
    print("  ✓ Professional formats (EXR, DPX, ProRes 4444, RAW)")
    print("  ✓ High-resolution media (4K, 6K, 8K)")
    print("  ✓ Image sequences")
    print("  ✓ OCIO color management")
    print("  ✓ Timeline playback")
    print("  ✓ Frame-accurate navigation")
    print("  ✓ Production/post-production workflows")

    print("\nUse Qt Multimedia for:")
    print("  ✓ Basic H.264/H.265 playback")
    print("  ✓ Quick review of proxies")
    print("  ✓ When tlRender not available")
    print("  ✓ Simple use cases")

    print("\nPerformance characteristics:")
    print("""
Format                  | tlRender      | Qt Multimedia
------------------------|---------------|---------------
H.264 1080p            | Excellent     | Excellent
ProRes 4444 4K         | Excellent     | Good
EXR Sequence 4K        | Excellent     | Poor/None
DPX Sequence 2K        | Excellent     | None
ACES with OCIO         | Excellent     | None
Timeline with effects  | Excellent     | Limited
    """)


def example_advanced_features():
    """Advanced tlRender features."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Advanced Features")
    print("=" * 60)

    if not HAS_TLRENDER:
        print("\nSkipped: Requires tlRender")
        return

    print("\nAdvanced tlRender capabilities:")
    print("""
# 1. Multiple playback heads (A/B comparison)
engine_a = TLRenderEngine()
engine_b = TLRenderEngine()

engine_a.load_media(Path("source.mov"))
engine_b.load_media(Path("conform.mov"))

# Synchronized playback
engine_a.play()
engine_b.play()

# 2. Performance monitoring
info = engine.get_playback_info()
print(f"Playback FPS: {info.frame_rate}")
print(f"Current speed: {info.speed}x")

# 3. Audio synchronization
# tlRender handles audio/video sync automatically
# even during variable speed playback

# 4. Caching and performance
# tlRender intelligently caches frames for smooth playback
# Cache behavior adapts to available system resources

# 5. Multi-threaded rendering
# tlRender uses multiple CPU/GPU threads for optimal performance
# Automatically scales to available hardware

# 6. Support for industry formats
formats = engine.get_supported_formats()
print(f"Supported formats: {', '.join(formats)}")
    """)


def example_integration_with_conform_review():
    """Integrate tlRender with conform review workflow."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Integration with Conform Review")
    print("=" * 60)

    print("\nUpgrade conform review widget with tlRender:")
    print("""
# Replace basic playback with tlRender in ConformReviewWidget

from conformity.ui_components.tlrender_widget import TLRenderWidget

class ConformReviewTLRender(QWidget):
    def __init__(self):
        super().__init__()

        # Use tlRender widgets instead of basic playback
        self.source_player = TLRenderWidget()
        self.conform_player = TLRenderWidget()

        # Configure OCIO for both players
        ocio_config = Path("aces_1.2/config.ocio")
        self.source_player.set_ocio_config(ocio_config)
        self.conform_player.set_ocio_config(ocio_config)

        # Synchronized playback
        self.source_player.frame_changed.connect(
            lambda f: self.conform_player.seek_to_frame(f)
        )

        # Benefits:
        # - Play high-res masters (4K ProRes, EXR sequences)
        # - Accurate color with OCIO
        # - Frame-accurate comparison
        # - Professional format support
    """)

    print("\nWorkflow improvements:")
    print("  - Review in native resolution")
    print("  - Accurate color representation")
    print("  - Support for all deliverable formats")
    print("  - Professional-grade performance")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("TLRENDER INTEGRATION EXAMPLES")
    print("=" * 60)
    print("\nDemonstrating professional-grade playback with tlRender")

    try:
        example_basic_playback()
        example_timeline_playback()
        example_image_sequences()
        example_ocio_color_management()
        example_gui_widget()
        example_performance_comparison()
        example_advanced_features()
        example_integration_with_conform_review()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        print("\nFor more information, see:")
        print("  - docs/TLRENDER.md")
        print("  - https://github.com/darbyjohnston/tlRender")
        print("  - README.md")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
