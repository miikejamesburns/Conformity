#!/usr/bin/env python3
"""
Example: Media Review System

Demonstrates how to use the media review system to:
- Play back media files with frame-accurate controls
- Review conforms side-by-side
- Add frame markers
- Display technical metadata
- Export review reports

Note: This requires PyQt6 and a display. For headless environments,
see the example code comments for how to use the API programmatically.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def example_playback_api():
    """Example of playback widget API (without GUI)."""
    print("=" * 60)
    print("EXAMPLE: Playback Widget API")
    print("=" * 60)

    print("\nPlayback Widget Features:")
    print("  - Frame-accurate playback")
    print("  - Timecode display (HH:MM:SS:FF)")
    print("  - Image sequence support")
    print("  - Standard playback controls")

    print("\nBasic usage:")
    print("""
from PyQt6.QtWidgets import QApplication
from conformity.ui_components.playback_widget import PlaybackWidget

# Create application
app = QApplication([])

# Create playback widget
player = PlaybackWidget()

# Load media file
player.load_media(Path("footage.mp4"), frame_rate=24.0)

# Play/pause
player.play_pause()

# Frame navigation
player.frame_forward()  # Next frame
player.frame_back()     # Previous frame

# Seek to specific frame
player.seek_to_frame(120)

# Get current position
frame = player.get_current_frame()
timecode = player.get_timecode()

# Show player
player.show()
app.exec()
    """)

    print("\nKeyboard shortcuts:")
    print("  Space      - Play/Pause")
    print("  Left Arrow - Previous Frame")
    print("  Right Arrow- Next Frame")
    print("  Home       - Jump to Start")
    print("  End        - Jump to End")


def example_conform_review_api():
    """Example of conform review widget API (without GUI)."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Conform Review Widget API")
    print("=" * 60)

    print("\nConform Review Features:")
    print("  - Side-by-side comparison")
    print("  - Synchronized playback")
    print("  - Frame markers (issue, note, approved)")
    print("  - Marker export")
    print("  - Review reports")

    print("\nBasic usage:")
    print("""
from PyQt6.QtWidgets import QApplication
from conformity.ui_components.conform_review_widget import ConformReviewWidget

app = QApplication([])

# Create review widget
review = ConformReviewWidget()

# Load source and conform for comparison
review.load_source_and_conform(
    Path("source/original.mp4"),
    Path("conform/conformed.mp4")
)

# Enable synchronized playback
review.sync_checkbox.setChecked(True)

# Playback controls work on both players simultaneously
# when sync is enabled

# Add markers during review
review._add_marker("issue")      # Red marker for issues
review._add_marker("note")       # Yellow marker for notes
review._add_marker("approved")   # Green marker for approval

# Add review notes
review.notes_text.setPlainText(\"\"\"
Conform Review Notes:
- Color timing matches source
- All edits correctly placed
- Minor audio sync issue at TC 00:05:30:12
\"\"\")

# Export marked frames
review._export_marked_frames()

# Export comprehensive review report
review._export_review_report()

# Get review results
results = review.get_review_results()
print(f"Total markers: {results['total_markers']}")
print(f"Issues: {results['issues']}")
print(f"Notes: {results['notes']}")
print(f"Approved: {results['approved']}")

review.show()
app.exec()
    """)

    print("\nKeyboard shortcuts:")
    print("  I - Add Issue Marker (red)")
    print("  N - Add Note Marker (yellow)")
    print("  A - Add Approved Marker (green)")
    print("  D - Toggle Difference Overlay")
    print("  S - Toggle Synchronized Playback")


def example_review_panel_api():
    """Example of review panel API (without GUI)."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Review Panel API")
    print("=" * 60)

    print("\nReview Panel Features:")
    print("  - Technical metadata display")
    print("  - Color space information")
    print("  - Review status tracking")
    print("  - Review notes")

    print("\nBasic usage:")
    print("""
from PyQt6.QtWidgets import QApplication
from conformity.ui_components.review_panel import ReviewPanel

app = QApplication([])

# Create review panel
panel = ReviewPanel()

# Load file and display metadata
panel.load_file(Path("deliverable.mp4"))

# Metadata automatically displayed:
# - File information (path, name, size)
# - Technical specs (resolution, frame rate, codec)
# - Color information (color space, primaries, transfer)
# - Audio information (codec, channels, sample rate)

# Set review status
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
print(f"File: {data['file_path']}")
print(f"Status: {data['status']}")
print(f"Notes: {data['notes']}")
print(f"Metadata: {data['metadata']}")

panel.show()
app.exec()
    """)


def example_frame_marker_data():
    """Example of frame marker data structure."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Frame Marker Data Structure")
    print("=" * 60)

    try:
        from conformity.ui_components.conform_review_widget import FrameMarker
    except ImportError:
        # Define a simple FrameMarker replacement for demonstration
        from dataclasses import dataclass
        @dataclass
        class FrameMarker:
            frame_number: int
            timecode: str
            note: str
            marker_type: str
            created_date: str

    print("\nCreating frame markers:")

    # Issue marker
    issue = FrameMarker(
        frame_number=120,
        timecode="00:00:05:00",
        note="Color shift visible in background",
        marker_type="issue",
        created_date=datetime.now().isoformat()
    )

    # Note marker
    note = FrameMarker(
        frame_number=240,
        timecode="00:00:10:00",
        note="Check with colorist about this grade",
        marker_type="note",
        created_date=datetime.now().isoformat()
    )

    # Approved marker
    approved = FrameMarker(
        frame_number=360,
        timecode="00:00:15:00",
        note="This section looks perfect",
        marker_type="approved",
        created_date=datetime.now().isoformat()
    )

    print(f"\nIssue marker:")
    print(f"  Frame: {issue.frame_number}")
    print(f"  Timecode: {issue.timecode}")
    print(f"  Type: {issue.marker_type}")
    print(f"  Note: {issue.note}")

    print(f"\nNote marker:")
    print(f"  Frame: {note.frame_number}")
    print(f"  Timecode: {note.timecode}")
    print(f"  Type: {note.marker_type}")
    print(f"  Note: {note.note}")

    print(f"\nApproved marker:")
    print(f"  Frame: {approved.frame_number}")
    print(f"  Timecode: {approved.timecode}")
    print(f"  Type: {approved.marker_type}")
    print(f"  Note: {approved.note}")


def example_timecode_conversion():
    """Example of timecode conversion."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Timecode Conversion")
    print("=" * 60)

    try:
        from conformity.ui_components.playback_widget import PlaybackWidget
    except ImportError:
        # Define simplified timecode conversion for demonstration
        class PlaybackWidget:
            @staticmethod
            def _frames_to_timecode(frames: int, frame_rate: float) -> str:
                total_seconds = frames / frame_rate
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = int(total_seconds % 60)
                frame = int(frames % frame_rate)
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frame:02d}"

    print("\nConverting frames to timecode:")

    test_cases = [
        (0, 24.0),
        (24, 24.0),
        (60, 24.0),
        (1440, 24.0),  # 1 minute
        (86400, 24.0),  # 1 hour
        (30, 30.0),
        (60, 60.0),
        (24, 23.976),
    ]

    for frames, fps in test_cases:
        tc = PlaybackWidget._frames_to_timecode(frames, fps)
        print(f"  {frames:6d} frames @ {fps:7.3f} fps = {tc}")


def example_image_sequence():
    """Example of image sequence playback."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Image Sequence Playback")
    print("=" * 60)

    print("\nImage sequence support:")
    print("  Supported formats: .jpg, .jpeg, .png, .tiff, .tif, .exr, .dpx")

    print("\nUsage:")
    print("""
# Load any frame from the sequence
player.load_media(Path("sequence/frame.0001.exr"), frame_rate=24.0)

# Playback widget automatically:
# - Finds all frames in the directory
# - Sorts them correctly
# - Plays at specified frame rate
# - Provides frame-accurate navigation
    """)

    print("\nExample sequences:")
    print("  render/frame.0001.exr")
    print("  render/frame.0002.exr")
    print("  render/frame.0003.exr")
    print("  ...")


def example_workflow_conform_verification():
    """Example workflow for conform verification."""
    print("\n" + "=" * 60)
    print("EXAMPLE WORKFLOW: Conform Verification")
    print("=" * 60)

    print("""
Step-by-step conform verification workflow:

1. Load source and conform media
   - Open ConformReviewWidget
   - Load source media (original/master)
   - Load conform media (deliverable)

2. Enable synchronized playback
   - Check "Sync Playback" checkbox
   - Both players will stay in sync

3. Review timeline
   - Play through timeline
   - Use Space to play/pause
   - Use Left/Right arrows for frame-by-frame inspection

4. Mark issues and notes
   - Press I to mark issues (red)
   - Press N to add notes (yellow)
   - Press A to mark approved sections (green)
   - Add detailed notes for each marker

5. Add review notes
   - Enter overall review notes in text area
   - Document any patterns or concerns

6. Export review report
   - Click "Export Review Report"
   - Generates comprehensive report with:
     * File paths
     * Marker statistics
     * All frame markers with details
     * Review notes

7. Review results
   - Check total markers
   - Review issues found
   - Verify approved sections
   - Share report with team
    """)


def example_integration_with_asset_tracker():
    """Example of integrating review system with asset tracker."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Integration with Asset Tracker")
    print("=" * 60)

    print("\nIntegrating review panel with asset database:")
    print("""
from conformity.asset_tracker.asset_database import AssetDatabase, AssetStatus
from conformity.ui_components.review_panel import ReviewPanel

# Load asset from database
db = AssetDatabase(Path("project.db"))
asset = db.get_asset_by_id(123)

# Get metadata
metadata = db.get_asset_metadata(asset['id'])

# Create review panel
panel = ReviewPanel()
panel.load_file(Path(asset['file_path']), metadata)

# Perform review...

# Update asset status based on review
review_data = panel.get_review_data()

if review_data['status'] == 'Approved':
    db.update_asset_status(asset['id'], AssetStatus.APPROVED)
elif review_data['status'] == 'Rejected':
    db.update_asset_status(asset['id'], AssetStatus.REJECTED)
    """)


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("MEDIA REVIEW SYSTEM EXAMPLES")
    print("=" * 60)

    try:
        example_playback_api()
        example_conform_review_api()
        example_review_panel_api()
        example_frame_marker_data()
        example_timecode_conversion()
        example_image_sequence()
        example_workflow_conform_verification()
        example_integration_with_asset_tracker()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        print("\nFor more information, see:")
        print("  - docs/MEDIA_REVIEW.md")
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
