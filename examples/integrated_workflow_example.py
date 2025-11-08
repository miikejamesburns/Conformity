#!/usr/bin/env python3
"""
Example: Integrated Workflow

Demonstrates a complete workflow combining asset tracking and media review:
1. Scan media library and build asset database
2. Analyze timeline to link clips with assets
3. Review conform against source
4. Update asset status based on review
5. Generate final reports

This shows how the different systems work together in a real-world scenario.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from conformity.asset_tracker.asset_database import AssetDatabase, AssetType, AssetStatus
from conformity.asset_tracker.asset_scanner import AssetScanner

# Optional: Frame markers require PyQt6
try:
    from conformity.ui_components.conform_review_widget import FrameMarker
    HAS_PYQT6 = True
except ImportError:
    HAS_PYQT6 = False
    # Define a simple FrameMarker replacement for demonstration
    from dataclasses import dataclass
    @dataclass
    class FrameMarker:
        frame_number: int
        timecode: str
        note: str
        marker_type: str
        created_date: str

# Optional: Timeline analysis requires opentimelineio
try:
    from conformity.asset_tracker.timeline_analyzer import TimelineAnalyzer
    import opentimelineio as otio
    HAS_OTIO = True
except ImportError:
    HAS_OTIO = False


def scenario_complete_conform_workflow():
    """
    Complete conform workflow from ingest to delivery.

    Scenario:
    - Production delivers raw footage
    - Editorial creates timeline
    - Conform department processes deliverables
    - QC reviews conforms
    - Final delivery
    """
    print("=" * 80)
    print("SCENARIO: Complete Conform Workflow")
    print("=" * 80)

    if not HAS_OTIO:
        print("\nSkipped: Requires opentimelineio")
        print("Install with: pip install opentimelineio")
        return

    # Step 1: Initialize database
    print("\n" + "=" * 80)
    print("STEP 1: Initialize Asset Database")
    print("=" * 80)

    db = AssetDatabase()  # In production: AssetDatabase(Path("project.db"))
    scanner = AssetScanner(db)

    print("\nCreated asset database for project")

    # Step 2: Scan and ingest media
    print("\n" + "=" * 80)
    print("STEP 2: Scan and Ingest Media")
    print("=" * 80)

    print("\nScanning media directories...")

    # Simulate adding footage
    footage_paths = [
        "/media/footage/A001_C001.mov",
        "/media/footage/A001_C002.mov",
        "/media/footage/A002_C001.mov",
        "/media/footage/A002_C002.mov",
    ]

    asset_ids = {}
    for path in footage_paths:
        asset_id = db.add_asset(
            file_path=Path(path),
            asset_type=AssetType.VIDEO,
            status=AssetStatus.PENDING
        )
        asset_ids[path] = asset_id
        print(f"  Ingested: {Path(path).name} (ID: {asset_id})")

        # Add metadata
        db.add_metadata(asset_id, {
            'width': 1920,
            'height': 1080,
            'frame_rate': 24.0,
            'codec': 'ProRes 422 HQ',
            'color_space': 'rec709',
            'duration': 300.0
        })

        # Tag raw footage
        db.add_tag(asset_id, "raw-footage")
        db.add_tag(asset_id, "needs-review")

    stats = db.get_statistics()
    print(f"\nTotal assets ingested: {stats['total_assets']}")

    # Step 3: Create and analyze timeline
    print("\n" + "=" * 80)
    print("STEP 3: Analyze Editorial Timeline")
    print("=" * 80)

    print("\nCreating example timeline...")

    timeline = otio.schema.Timeline(name="Episode_01_V1")
    track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)
    timeline.tracks.append(track)

    # Add clips to timeline
    clip1 = otio.schema.Clip(
        name="Scene 1 - Wide",
        media_reference=otio.schema.ExternalReference(
            target_url="file:///media/footage/A001_C001.mov"
        ),
        source_range=otio.opentime.TimeRange(
            start_time=otio.opentime.RationalTime(24, 24),
            duration=otio.opentime.RationalTime(240, 24)
        )
    )
    track.append(clip1)

    clip2 = otio.schema.Clip(
        name="Scene 1 - Close",
        media_reference=otio.schema.ExternalReference(
            target_url="file:///media/footage/A001_C002.mov"
        ),
        source_range=otio.opentime.TimeRange(
            start_time=otio.opentime.RationalTime(48, 24),
            duration=otio.opentime.RationalTime(120, 24)
        )
    )
    track.append(clip2)

    print(f"  Timeline: {timeline.name}")
    print(f"  Total clips: {len(list(track.each_clip()))}")

    # Analyze timeline
    print("\nAnalyzing timeline relationships...")
    analyzer = TimelineAnalyzer(db)
    results = analyzer.analyze_timeline(timeline, Path("editorial/Episode_01_V1.otio"))

    print(f"  Total clips: {results['total_clips']}")
    print(f"  Linked clips: {results['linked_clips']}")
    print(f"  Missing clips: {results['missing_clips']}")

    if results['missing_media']:
        print("\n  WARNING: Missing media:")
        for media in results['missing_media']:
            print(f"    - {media}")
    else:
        print("  All media found!")

    # Step 4: Generate conforms
    print("\n" + "=" * 80)
    print("STEP 4: Generate Conform Deliverables")
    print("=" * 80)

    print("\nGenerating conform deliverables...")

    # Simulate conform generation
    conform_specs = [
        {
            'name': 'ProRes_Master',
            'path': '/deliverables/Episode_01_ProRes_Master.mov',
            'codec': 'ProRes 422 HQ',
            'color_space': 'rec709'
        },
        {
            'name': 'H264_Review',
            'path': '/deliverables/Episode_01_H264_Review.mp4',
            'codec': 'h264',
            'color_space': 'rec709'
        }
    ]

    conform_ids = {}
    for spec in conform_specs:
        asset_id = db.add_asset(
            file_path=Path(spec['path']),
            asset_type=AssetType.VIDEO,
            status=AssetStatus.PENDING
        )
        conform_ids[spec['name']] = asset_id

        db.add_metadata(asset_id, {
            'width': 1920,
            'height': 1080,
            'frame_rate': 24.0,
            'codec': spec['codec'],
            'color_space': spec['color_space'],
            'duration': 360.0
        })

        db.add_tag(asset_id, "deliverable")
        db.add_tag(asset_id, spec['name'])

        print(f"  Created: {spec['name']}")
        print(f"    Path: {spec['path']}")
        print(f"    Codec: {spec['codec']}")

    # Step 5: QC Review
    print("\n" + "=" * 80)
    print("STEP 5: QC Review Process")
    print("=" * 80)

    print("\nPerforming QC review on deliverables...")
    print("\nQC workflow:")
    print("  1. Load source and conform in ConformReviewWidget")
    print("  2. Enable synchronized playback")
    print("  3. Review frame-by-frame")
    print("  4. Add markers for issues")
    print("  5. Document findings")

    # Simulate review process
    print("\nSimulating review of ProRes Master...")

    # Create mock review markers
    markers = [
        FrameMarker(
            frame_number=120,
            timecode="00:00:05:00",
            note="Color looks good, matches source",
            marker_type="approved",
            created_date=datetime.now().isoformat()
        ),
        FrameMarker(
            frame_number=240,
            timecode="00:00:10:00",
            note="Edit cut is clean",
            marker_type="approved",
            created_date=datetime.now().isoformat()
        ),
        FrameMarker(
            frame_number=300,
            timecode="00:00:12:12",
            note="Verify audio sync at this cut",
            marker_type="note",
            created_date=datetime.now().isoformat()
        )
    ]

    print(f"\n  Added {len(markers)} review markers:")
    for marker in markers:
        print(f"    [{marker.marker_type.upper()}] Frame {marker.frame_number} ({marker.timecode})")
        print(f"      Note: {marker.note}")

    # Count marker types
    issues = sum(1 for m in markers if m.marker_type == "issue")
    notes = sum(1 for m in markers if m.marker_type == "note")
    approved = sum(1 for m in markers if m.marker_type == "approved")

    print(f"\n  Review summary:")
    print(f"    Issues: {issues}")
    print(f"    Notes: {notes}")
    print(f"    Approved sections: {approved}")

    # Step 6: Update asset status based on review
    print("\n" + "=" * 80)
    print("STEP 6: Update Asset Status")
    print("=" * 80)

    print("\nUpdating asset status based on QC review...")

    # Approve deliverables if no issues
    if issues == 0:
        for name, asset_id in conform_ids.items():
            db.update_asset_status(asset_id, AssetStatus.APPROVED)
            print(f"  {name}: APPROVED")
    else:
        print(f"  Found {issues} issues - deliverables need revision")

    # Step 7: Generate reports
    print("\n" + "=" * 80)
    print("STEP 7: Generate Final Reports")
    print("=" * 80)

    print("\nGenerating project reports...")

    # Asset statistics
    stats = db.get_statistics()
    print("\nAsset Database Statistics:")
    print(f"  Total assets: {stats['total_assets']}")
    print(f"\n  By type:")
    for asset_type, count in stats['by_type'].items():
        print(f"    {asset_type}: {count}")
    print(f"\n  By status:")
    for status, count in stats['by_status'].items():
        print(f"    {status}: {count}")

    # Timeline usage
    usage_report = analyzer.generate_usage_report()
    print(f"\nTimeline Usage Report:")
    print(f"  Total associations: {usage_report['total_associations']}")
    print(f"  Unique timelines: {usage_report['unique_timelines']}")

    # Deliverables
    deliverables = db.search_assets(tags=["deliverable"])
    print(f"\nDeliverables:")
    for deliverable in deliverables:
        print(f"  {deliverable['file_name']}")
        print(f"    Status: {deliverable['status']}")
        print(f"    Type: {deliverable['asset_type']}")


def scenario_batch_conform_review():
    """
    Batch conform review workflow.

    Scenario:
    - Multiple episodes need QC review
    - Automated checks for technical specs
    - Batch status updates
    """
    print("\n\n" + "=" * 80)
    print("SCENARIO: Batch Conform Review")
    print("=" * 80)

    db = AssetDatabase()
    scanner = AssetScanner(db)

    print("\nBatch review workflow for multiple deliverables...")

    # Add multiple deliverables
    print("\n1. Adding deliverables to database...")
    deliverable_specs = [
        ("Episode_01_Master.mov", "Episode 1"),
        ("Episode_02_Master.mov", "Episode 2"),
        ("Episode_03_Master.mov", "Episode 3"),
        ("Episode_04_Master.mov", "Episode 4"),
    ]

    asset_ids = []
    for filename, episode in deliverable_specs:
        asset_id = db.add_asset(
            file_path=Path(f"/deliverables/{filename}"),
            asset_type=AssetType.VIDEO,
            status=AssetStatus.PENDING
        )
        asset_ids.append(asset_id)

        db.add_metadata(asset_id, {
            'width': 1920,
            'height': 1080,
            'frame_rate': 24.0,
            'codec': 'ProRes 422 HQ',
            'color_space': 'rec709'
        })

        db.add_tag(asset_id, "deliverable")
        db.add_tag(asset_id, episode)

        print(f"  Added: {filename}")

    # Automated technical checks
    print("\n2. Performing automated technical checks...")

    passed_qc = []
    failed_qc = []

    for asset_id in asset_ids:
        asset = db.get_asset_by_id(asset_id)
        metadata = db.get_asset_metadata(asset_id)

        # Check specs
        issues = []
        if metadata.get('width') != 1920:
            issues.append("Incorrect width")
        if metadata.get('height') != 1080:
            issues.append("Incorrect height")
        if metadata.get('frame_rate') != 24.0:
            issues.append("Incorrect frame rate")
        if metadata.get('color_space') != 'rec709':
            issues.append("Incorrect color space")

        if issues:
            failed_qc.append((asset['file_name'], issues))
            print(f"  ✗ {asset['file_name']}: {', '.join(issues)}")
        else:
            passed_qc.append(asset_id)
            print(f"  ✓ {asset['file_name']}: Passed all checks")

    # Batch update approved assets
    print("\n3. Batch updating approved assets...")
    if passed_qc:
        count = scanner.batch_update_status(passed_qc, AssetStatus.APPROVED)
        print(f"  Approved {count} deliverables")

    # Report failures
    if failed_qc:
        print(f"\n4. Technical issues found:")
        for filename, issues in failed_qc:
            print(f"  {filename}:")
            for issue in issues:
                print(f"    - {issue}")

    # Final summary
    print("\n5. Batch review summary:")
    print(f"  Total deliverables: {len(asset_ids)}")
    print(f"  Passed QC: {len(passed_qc)}")
    print(f"  Failed QC: {len(failed_qc)}")


def scenario_asset_lifecycle():
    """
    Complete asset lifecycle tracking.

    Scenario:
    - Track asset from ingest to archive
    - Version management
    - Status transitions
    """
    print("\n\n" + "=" * 80)
    print("SCENARIO: Asset Lifecycle Tracking")
    print("=" * 80)

    db = AssetDatabase()

    print("\nTracking complete lifecycle of an asset...")

    # Initial ingest
    print("\n1. Initial Ingest - RAW FOOTAGE")
    asset_id = db.add_asset(
        file_path=Path("/media/raw/A001_C001.R3D"),
        asset_type=AssetType.VIDEO,
        status=AssetStatus.PENDING
    )
    print(f"  Asset ID: {asset_id}")
    print(f"  Status: PENDING")
    db.add_tag(asset_id, "raw")

    # Transcoding
    print("\n2. Transcoding - CREATE PROXY")
    # Note: Version tracking not yet implemented in database
    # In production, you would create a new asset for the proxy version
    proxy_id = db.add_asset(
        file_path=Path("/media/proxy/A001_C001_proxy.mov"),
        asset_type=AssetType.VIDEO,
        status=AssetStatus.PENDING
    )
    print(f"  Created proxy asset (ID: {proxy_id})")
    db.add_tag(asset_id, "has-proxy")
    db.add_tag(proxy_id, "proxy")

    # Editorial use
    print("\n3. Editorial - IN PROGRESS")
    db.update_asset_status(asset_id, AssetStatus.IN_PROGRESS)
    print(f"  Status: IN_PROGRESS")
    db.add_tag(asset_id, "in-edit")

    # Online conform
    print("\n4. Online Conform - CREATE MASTER")
    # Note: Version tracking not yet implemented in database
    # In production, you would create a new asset for the master version
    master_id = db.add_asset(
        file_path=Path("/media/master/A001_C001_graded.mov"),
        asset_type=AssetType.VIDEO,
        status=AssetStatus.PENDING
    )
    print(f"  Created master asset (ID: {master_id})")
    db.add_tag(master_id, "master")
    db.add_tag(master_id, "color-graded")

    # QC approval
    print("\n5. QC Review - APPROVED")
    db.update_asset_status(asset_id, AssetStatus.APPROVED)
    print(f"  Status: APPROVED")
    db.add_tag(asset_id, "approved")

    # Archive
    print("\n6. Archival - ARCHIVED")
    db.update_asset_status(asset_id, AssetStatus.ARCHIVED)
    print(f"  Status: ARCHIVED")
    db.add_tag(asset_id, "archived")

    # View complete history
    print("\n7. Asset Summary:")
    asset = db.get_asset_by_id(asset_id)

    print(f"\n  Original File: {asset['file_name']}")
    print(f"  Current Status: {asset['status']}")
    print(f"  Asset Type: {asset['asset_type']}")

    # Note: Version tracking via database is not yet implemented
    # In this example, we created separate assets for proxy and master
    print(f"\n  Workflow Complete!")
    print(f"    - RAW → PENDING → IN_PROGRESS → APPROVED → ARCHIVED")
    print(f"\n  Related Assets Created:")
    print(f"    - Proxy: /media/proxy/A001_C001_proxy.mov")
    print(f"    - Master: /media/master/A001_C001_graded.mov")


def main():
    """Run all scenario examples."""
    print("\n" + "=" * 80)
    print("INTEGRATED WORKFLOW EXAMPLES")
    print("=" * 80)
    print("\nDemonstrating how asset tracking and media review work together")
    print("in real-world post-production scenarios.")

    try:
        scenario_complete_conform_workflow()
        scenario_batch_conform_review()
        scenario_asset_lifecycle()

        print("\n\n" + "=" * 80)
        print("All scenario examples completed successfully!")
        print("=" * 80)
        print("\nThese examples demonstrate:")
        print("  - Complete conform workflows")
        print("  - Asset tracking and timeline analysis integration")
        print("  - QC review processes")
        print("  - Batch operations")
        print("  - Asset lifecycle management")
        print("\nFor more information, see:")
        print("  - docs/ASSET_TRACKING.md")
        print("  - docs/MEDIA_REVIEW.md")
        print("  - README.md")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
