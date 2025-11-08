#!/usr/bin/env python3
"""
Example: Production Tracker

Demonstrates comprehensive production tracking for film/TV post-production:
- Project and sequence setup
- Shot tracking across departments
- Task management
- Review workflows
- Deliverables tracking
- Progress reporting
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from conformity.production_tracker.production_database import (
    ProductionDatabase, Department, ShotStatus, TaskPriority,
    TaskStatus, VFXComplexity
)
from conformity.production_tracker.shot_tracker import ShotTracker


def example_project_setup():
    """Set up a production project."""
    print("=" * 60)
    print("EXAMPLE: Production Project Setup")
    print("=" * 60)

    tracker = ShotTracker()  # In-memory for example

    # Create project
    print("\n1. Creating project...")
    project_id = tracker.create_project(
        name="Short Film - Festival Cut",
        description="10-minute festival submission",
        target_runtime=600,  # 10 minutes in seconds
        budget=50000.0,
        target_completion="2025-12-31"
    )
    print(f"   Project ID: {project_id}")

    # Create sequences
    print("\n2. Creating sequences...")
    sequences = [
        ("SEQ_010", "Opening - Beach Scene"),
        ("SEQ_020", "Interior - Apartment"),
        ("SEQ_030", "Climax - Rooftop"),
    ]

    seq_ids = {}
    for seq_name, description in sequences:
        seq_id = tracker.add_sequence(project_id, seq_name, description)
        seq_ids[seq_name] = seq_id
        print(f"   {seq_name}: {description}")

    print(f"\n   Created {len(sequences)} sequences")
    return tracker, project_id, seq_ids


def example_shot_tracking(tracker, seq_id):
    """Track shots through departments."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Shot Tracking")
    print("=" * 60)

    # Add shots
    print("\n1. Adding shots to sequence...")
    shots = [
        ("010_010", "Wide establishing beach", VFXComplexity.SIMPLE),
        ("010_020", "Medium actor walking", VFXComplexity.MEDIUM),
        ("010_030", "Close-up dramatic reveal", VFXComplexity.COMPLEX),
    ]

    shot_ids = {}
    for shot_name, description, vfx_complexity in shots:
        shot_id = tracker.add_shot(
            sequence_id=seq_id,
            shot_name=shot_name,
            description=description,
            vfx_complexity=vfx_complexity,
            start_timecode="01:00:00:00",
            duration_frames=120
        )
        shot_ids[shot_name] = shot_id
        print(f"   {shot_name}: {description} (VFX: {vfx_complexity.value})")

    # Start VFX work
    print("\n2. Starting VFX work...")
    for shot_name, shot_id in shot_ids.items():
        tracker.start_vfx(shot_id, vendor="VFX Studio Inc")
        print(f"   Started VFX on {shot_name}")

    # Submit for review
    print("\n3. Submitting shots for review...")
    tracker.submit_for_review(
        shot_ids["010_010"],
        Department.VFX,
        "Initial comp complete"
    )
    print("   Submitted 010_010 for review")

    # Approve shot
    print("\n4. Approving shot...")
    review_id = tracker.approve_shot(
        shot_ids["010_010"],
        Department.VFX,
        reviewer="john@studio.com",
        comments="Looks great, approved!"
    )
    print(f"   Approved 010_010 (Review #{review_id})")

    # Request revision
    print("\n5. Requesting revision...")
    revision_id = tracker.request_revision(
        shot_ids["010_020"],
        Department.VFX,
        reviewer="jane@studio.com",
        feedback="Please adjust sky color to match shot 010"
    )
    print(f"   Requested revision on 010_020 (Review #{revision_id})")

    return shot_ids


def example_task_management(tracker, project_id, shot_ids):
    """Manage tasks and assignments."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Task Management")
    print("=" * 60)

    db = tracker.db

    # Create tasks
    print("\n1. Creating tasks...")
    tasks = [
        {
            'title': "Cleanup wire removal",
            'department': Department.VFX,
            'shot_id': shot_ids["010_020"],
            'assignee': "vfx_artist@studio.com",
            'priority': TaskPriority.HIGH,
            'due_date': "2025-12-15",
            'estimated_hours': 8.0
        },
        {
            'title': "Color grade beach sequence",
            'department': Department.COLOR,
            'shot_id': shot_ids["010_010"],
            'assignee': "colorist@studio.com",
            'priority': TaskPriority.MEDIUM,
            'due_date': "2025-12-20",
            'estimated_hours': 4.0
        },
        {
            'title': "ADR session for actor",
            'department': Department.SOUND,
            'project_id': project_id,
            'assignee': "sound_editor@studio.com",
            'priority': TaskPriority.CRITICAL,
            'due_date': "2025-12-10",
            'estimated_hours': 3.0
        }
    ]

    task_ids = []
    for task_data in tasks:
        task_id = db.create_task(**task_data)
        task_ids.append(task_id)
        print(f"   Task: {task_data['title']}")
        print(f"     Department: {task_data['department'].value}")
        print(f"     Priority: {task_data['priority'].value}")

    # Update task status
    print("\n2. Updating task status...")
    db.update_task_status(task_ids[0], TaskStatus.IN_PROGRESS)
    print(f"   Task #{task_ids[0]}: IN_PROGRESS")

    db.update_task_status(task_ids[1], TaskStatus.COMPLETED, actual_hours=3.5)
    print(f"   Task #{task_ids[1]}: COMPLETED (3.5 hours)")

    # List tasks
    print("\n3. Active tasks by department:")
    for dept in [Department.VFX, Department.COLOR, Department.SOUND]:
        tasks = db.list_tasks(department=dept, status=TaskStatus.IN_PROGRESS)
        print(f"\n   {dept.value.upper()}: {len(tasks)} active tasks")
        for task in tasks:
            print(f"     - {task['title']} (due: {task['due_date']})")


def example_deliverables(tracker, project_id):
    """Track deliverables."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Deliverables Tracking")
    print("=" * 60)

    db = tracker.db

    # Define deliverables
    print("\n1. Creating deliverables...")
    deliverables = [
        {
            'category': 'master',
            'name': 'ProRes Master',
            'format': 'MOV',
            'resolution': '1920x1080',
            'codec': 'ProRes 422 HQ',
            'due_date': '2025-12-31'
        },
        {
            'category': 'festival',
            'name': 'Sundance DCP',
            'format': 'DCP',
            'resolution': '2048x1080',
            'codec': 'JPEG 2000',
            'due_date': '2025-11-15'
        },
        {
            'category': 'marketing',
            'name': 'Trailer Cut',
            'format': 'MP4',
            'resolution': '1920x1080',
            'codec': 'H.264',
            'due_date': '2025-10-30'
        }
    ]

    deliverable_ids = []
    for deliv in deliverables:
        deliv_id = db.create_deliverable(project_id=project_id, **deliv)
        deliverable_ids.append(deliv_id)
        print(f"   {deliv['name']}: {deliv['resolution']} {deliv['codec']}")

    # Update statuses
    print("\n2. Updating deliverable status...")
    db.update_deliverable_status(
        deliverable_ids[2],
        status="completed",
        file_path="/deliverables/trailer_v1.mp4"
    )
    print("   Trailer Cut: COMPLETED")

    db.update_deliverable_status(deliverable_ids[0], status="in_progress")
    print("   ProRes Master: IN_PROGRESS")

    # List by category
    print("\n3. Deliverables by category:")
    for category in ['master', 'festival', 'marketing']:
        delivs = db.list_deliverables(project_id, category=category)
        print(f"\n   {category.upper()}:")
        for deliv in delivs:
            print(f"     - {deliv['name']}: {deliv['status']}")


def example_progress_reporting(tracker, project_id):
    """Generate progress reports."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Progress Reporting")
    print("=" * 60)

    # Get project stats
    print("\n1. Project Statistics:")
    stats = tracker.get_shot_progress(project_id)

    print(f"\n   Total Shots: {stats['total_shots']}")

    print("\n   Department Progress:")
    for dept in Department:
        complete = stats.get(f"{dept.value}_complete", 0)
        total = stats['total_shots']
        percentage = (complete / total * 100) if total > 0 else 0
        print(f"     {dept.value.upper()}: {complete}/{total} ({percentage:.1f}%)")

    # Shots needing attention
    print("\n2. Shots Needing Attention:")
    attention = tracker.get_shots_needing_attention(project_id)

    print(f"\n   In Review: {len(attention['review'])} shots")
    for shot in attention['review']:
        print(f"     - {shot['shot_name']} ({shot['department']})")

    print(f"\n   Needs Revision: {len(attention['revision'])} shots")
    for shot in attention['revision']:
        print(f"     - {shot['shot_name']} ({shot['department']})")

    # Task statistics
    print("\n3. Task Overview:")
    task_stats = stats.get('task_status', {})
    for status, count in task_stats.items():
        print(f"     {status}: {count}")


def example_team_management(tracker):
    """Manage team and vendors."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Team Management")
    print("=" * 60)

    db = tracker.db

    # Add team members
    print("\n1. Adding team members...")
    team = [
        {
            'name': "John Smith",
            'role': "VFX Supervisor",
            'department': "vfx",
            'email': "john@vfxstudio.com",
            'company': "VFX Studio Inc",
            'is_vendor': True
        },
        {
            'name': "Jane Doe",
            'role': "Colorist",
            'department': "color",
            'email': "jane@colorhouse.com",
            'company': "Color House",
            'is_vendor': True
        },
        {
            'name': "Bob Wilson",
            'role': "Sound Designer",
            'department': "sound",
            'email': "bob@soundlab.com",
            'company': "Sound Lab",
            'is_vendor': True
        }
    ]

    for member in team:
        member_id = db.add_team_member(**member)
        print(f"   {member['name']}: {member['role']} ({member['company']})")

    # List vendors
    print("\n2. Vendor Directory:")
    vendors = db.list_team_members(is_vendor=True)
    for vendor in vendors:
        print(f"\n   {vendor['name']}")
        print(f"     Role: {vendor['role']}")
        print(f"     Department: {vendor['department']}")
        print(f"     Email: {vendor['email']}")
        print(f"     Company: {vendor['company']}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("PRODUCTION TRACKER EXAMPLES")
    print("=" * 60)
    print("\nComprehensive production tracking for film/TV post-production")

    try:
        # Setup
        tracker, project_id, seq_ids = example_project_setup()

        # Shot tracking
        shot_ids = example_shot_tracking(tracker, seq_ids["SEQ_010"])

        # Task management
        example_task_management(tracker, project_id, shot_ids)

        # Deliverables
        example_deliverables(tracker, project_id)

        # Progress reporting
        example_progress_reporting(tracker, project_id)

        # Team management
        example_team_management(tracker)

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        print("\nFor more information, see:")
        print("  - docs/PRODUCTION_TRACKER.md")
        print("  - README.md")
        print("=" * 60 + "\n")

        tracker.close()

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
