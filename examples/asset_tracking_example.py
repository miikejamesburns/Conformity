#!/usr/bin/env python3
"""
Example: Asset Tracking System

Demonstrates how to use the asset tracking system to:
- Create a database
- Scan directories for media files
- Search and filter assets
- Analyze timelines
- Generate reports
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from conformity.asset_tracker.asset_database import AssetDatabase, AssetType, AssetStatus
from conformity.asset_tracker.asset_scanner import AssetScanner

# Optional: Timeline analysis requires opentimelineio
try:
    from conformity.asset_tracker.timeline_analyzer import TimelineAnalyzer
    import opentimelineio as otio
    HAS_OTIO = True
except ImportError:
    HAS_OTIO = False
    print("Note: opentimelineio not installed - timeline analysis examples will be skipped")


def example_basic_asset_tracking():
    """Basic asset tracking workflow."""
    print("=" * 60)
    print("EXAMPLE: Basic Asset Tracking")
    print("=" * 60)

    # Create in-memory database for this example
    # In production, use: db = AssetDatabase(Path("project.db"))
    db = AssetDatabase()

    # Create scanner
    scanner = AssetScanner(db)

    print("\n1. Adding assets manually...")

    # Add some example assets
    asset_id_1 = db.add_asset(
        file_path=Path("/media/footage/clip001.mp4"),
        asset_type=AssetType.VIDEO,
        status=AssetStatus.APPROVED
    )
    print(f"   Added asset ID: {asset_id_1}")

    asset_id_2 = db.add_asset(
        file_path=Path("/media/footage/clip002.mov"),
        asset_type=AssetType.VIDEO,
        status=AssetStatus.PENDING
    )
    print(f"   Added asset ID: {asset_id_2}")

    asset_id_3 = db.add_asset(
        file_path=Path("/media/renders/frame.0001.exr"),
        asset_type=AssetType.IMAGE,
        status=AssetStatus.APPROVED
    )
    print(f"   Added asset ID: {asset_id_3}")

    # Add metadata
    print("\n2. Adding metadata...")
    db.add_metadata(asset_id_1, {
        'width': 1920,
        'height': 1080,
        'frame_rate': 24.0,
        'codec': 'h264',
        'color_space': 'rec709',
        'duration': 120.5
    })
    print(f"   Metadata added for asset {asset_id_1}")

    # Add tags
    print("\n3. Adding tags...")
    db.add_tag(asset_id_1, "dailies")
    db.add_tag(asset_id_1, "approved")
    db.add_tag(asset_id_2, "needs-review")
    print("   Tags added")

    # Search assets
    print("\n4. Searching assets...")

    # Search all approved assets
    approved = db.search_assets(status=AssetStatus.APPROVED)
    print(f"\n   Approved assets: {len(approved)}")
    for asset in approved:
        print(f"   - {asset['file_name']} ({asset['asset_type']})")

    # Search video assets only
    videos = db.search_assets(asset_type=AssetType.VIDEO)
    print(f"\n   Video assets: {len(videos)}")
    for asset in videos:
        print(f"   - {asset['file_name']} - {asset['status']}")

    # Search by tags
    dailies_assets = db.search_assets(tags=["dailies"])
    print(f"\n   Assets tagged 'dailies': {len(dailies_assets)}")
    for asset in dailies_assets:
        print(f"   - {asset['file_name']}")

    # Get statistics
    print("\n5. Database statistics...")
    stats = db.get_statistics()
    print(f"   Total assets: {stats['total_assets']}")
    print(f"   By type:")
    for asset_type, count in stats['by_type'].items():
        print(f"     - {asset_type}: {count}")
    print(f"   By status:")
    for status, count in stats['by_status'].items():
        print(f"     - {status}: {count}")


def example_directory_scanning():
    """Directory scanning workflow."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Directory Scanning")
    print("=" * 60)

    db = AssetDatabase()
    scanner = AssetScanner(db)

    print("\nNote: This example shows the API for directory scanning.")
    print("To actually scan, provide a real directory path.\n")

    print("Example code:")
    print("""
    # Scan directory with progress callback
    def progress_callback(current, total, filename):
        percent = (current / total) * 100
        print(f"Progress: {percent:.1f}% - {filename}")

    results = scanner.scan_directory(
        Path("/media/footage"),
        recursive=True,
        progress_callback=progress_callback
    )

    print(f"Scanning complete!")
    print(f"Added: {results['added']}")
    print(f"Updated: {results['updated']}")
    print(f"Skipped: {results['skipped']}")
    print(f"Errors: {results['errors']}")
    """)


def example_timeline_analysis():
    """Timeline analysis workflow."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Timeline Analysis")
    print("=" * 60)

    if not HAS_OTIO:
        print("\nSkipped: Requires opentimelineio")
        print("Install with: pip install opentimelineio")
        return

    db = AssetDatabase()

    # Create a simple example timeline
    print("\n1. Creating example timeline...")
    timeline = otio.schema.Timeline(name="Example Timeline")
    track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)
    timeline.tracks.append(track)

    # Add clips
    clip1 = otio.schema.Clip(
        name="Clip 1",
        media_reference=otio.schema.ExternalReference(
            target_url="file:///media/footage/clip001.mp4"
        ),
        source_range=otio.opentime.TimeRange(
            start_time=otio.opentime.RationalTime(0, 24),
            duration=otio.opentime.RationalTime(240, 24)
        )
    )
    track.append(clip1)

    clip2 = otio.schema.Clip(
        name="Clip 2",
        media_reference=otio.schema.ExternalReference(
            target_url="file:///media/footage/clip002.mov"
        ),
        source_range=otio.opentime.TimeRange(
            start_time=otio.opentime.RationalTime(0, 24),
            duration=otio.opentime.RationalTime(120, 24)
        )
    )
    track.append(clip2)

    print("   Created timeline with 2 clips")

    # Add assets to database
    print("\n2. Adding referenced assets to database...")
    asset_id_1 = db.add_asset(
        file_path=Path("/media/footage/clip001.mp4"),
        asset_type=AssetType.VIDEO,
        status=AssetStatus.APPROVED
    )
    asset_id_2 = db.add_asset(
        file_path=Path("/media/footage/clip002.mov"),
        asset_type=AssetType.VIDEO,
        status=AssetStatus.APPROVED
    )
    print(f"   Added assets: {asset_id_1}, {asset_id_2}")

    # Analyze timeline
    print("\n3. Analyzing timeline...")
    analyzer = TimelineAnalyzer(db)
    results = analyzer.analyze_timeline(timeline, Path("example.otio"))

    print(f"   Total clips: {results['total_clips']}")
    print(f"   Linked clips: {results['linked_clips']}")
    print(f"   Missing clips: {results['missing_clips']}")

    if results['missing_media']:
        print("\n   Missing media:")
        for media in results['missing_media']:
            print(f"   - {media}")

    # Generate usage report
    print("\n4. Generating usage report...")
    report = analyzer.generate_usage_report()
    print(f"   Total associations: {report['total_associations']}")
    print(f"   Unique timelines: {report['unique_timelines']}")

    if report['most_used']:
        print("\n   Most used assets:")
        for asset in report['most_used'][:3]:
            print(f"   - {asset['file_name']}: {asset['usage_count']} uses")


def example_batch_operations():
    """Batch operations workflow."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Batch Operations")
    print("=" * 60)

    db = AssetDatabase()
    scanner = AssetScanner(db)

    # Add some assets
    print("\n1. Adding assets...")
    asset_ids = []
    for i in range(1, 6):
        asset_id = db.add_asset(
            file_path=Path(f"/media/footage/clip{i:03d}.mp4"),
            asset_type=AssetType.VIDEO,
            status=AssetStatus.PENDING
        )
        asset_ids.append(asset_id)
    print(f"   Added {len(asset_ids)} assets")

    # Batch update status
    print("\n2. Batch update status...")
    count = scanner.batch_update_status(asset_ids[:3], AssetStatus.APPROVED)
    print(f"   Updated {count} assets to APPROVED")

    # Batch add tags
    print("\n3. Batch add tags...")
    count = scanner.batch_add_tags(asset_ids[3:], ["needs-review", "priority"])
    print(f"   Added tags to {count} assets")

    # Verify results
    print("\n4. Verifying results...")
    approved = db.search_assets(status=AssetStatus.APPROVED)
    print(f"   Approved assets: {len(approved)}")

    tagged = db.search_assets(tags=["needs-review"])
    print(f"   Assets tagged 'needs-review': {len(tagged)}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("ASSET TRACKING SYSTEM EXAMPLES")
    print("=" * 60)

    try:
        example_basic_asset_tracking()
        example_directory_scanning()
        example_timeline_analysis()
        example_batch_operations()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        print("\nFor more information, see:")
        print("  - docs/ASSET_TRACKING.md")
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
