# Production Tracker

Comprehensive production tracking system for film/TV post-production workflows. Track shots, sequences, departments, tasks, approvals, and deliverables throughout the entire post-production pipeline.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)
  - [ProductionDatabase](#productiondatabase)
  - [ShotTracker](#shottracker)
- [Workflow Examples](#workflow-examples)
- [Integration](#integration)
- [Best Practices](#best-practices)

## Overview

The Production Tracker provides a complete solution for managing post-production workflows across multiple departments. It uses SQLite for reliable data storage and provides both low-level database access and high-level workflow management.

**Inspired by professional post-production needs**, the system tracks:

- **Projects & Sequences**: Organize shots into sequences and projects
- **Shot-Level Tracking**: Track each shot through all departments
- **Department Workflows**: Independent status tracking for Editorial, VFX, Color, Sound, Finishing, and Delivery
- **Task Management**: Assign and track tasks with priorities and deadlines
- **Review & Approval**: Multi-stage review workflow with feedback
- **Deliverables**: Track all deliverable formats and their status
- **Team Management**: Maintain directory of team members and vendors
- **Progress Reporting**: Real-time statistics and attention flags

## Features

### Core Features

- **Multi-Department Tracking**: Each shot has independent status for all departments
- **Flexible Workflow**: Shots can progress through departments in any order
- **Review System**: Multi-stage review with approval/revision workflows
- **Task Assignment**: Create and track tasks at project or shot level
- **VFX Complexity Tracking**: Categorize VFX shots by complexity (simple/medium/complex)
- **Vendor Management**: Track external vendors and their work
- **Deliverables Checklist**: Comprehensive tracking of all delivery formats
- **Progress Statistics**: Real-time reporting on project progress
- **SQLite Backend**: Reliable, file-based or in-memory database

### Department Types

```python
class Department(Enum):
    EDITORIAL = "editorial"
    VFX = "vfx"
    COLOR = "color"
    SOUND = "sound"
    FINISHING = "finishing"
    DELIVERY = "delivery"
```

### Shot Status Types

```python
class ShotStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    REVISION = "revision"
    APPROVED = "approved"
    FINAL = "final"
    ON_HOLD = "on_hold"
```

## Quick Start

### Basic Project Setup

```python
from pathlib import Path
from conformity.production_tracker.shot_tracker import ShotTracker
from conformity.production_tracker.production_database import (
    Department, VFXComplexity
)

# Create tracker (use Path for persistent, None for in-memory)
tracker = ShotTracker(Path("my_project.db"))

# Create project
project_id = tracker.create_project(
    name="My Film",
    description="Feature film production",
    target_runtime=5400,  # 90 minutes in seconds
    budget=500000.0,
    target_completion="2025-12-31"
)

# Add sequence
seq_id = tracker.add_sequence(
    project_id,
    "SEQ_010",
    "Opening sequence"
)

# Add shot
shot_id = tracker.add_shot(
    sequence_id=seq_id,
    shot_name="010_010",
    description="Wide establishing shot",
    vfx_complexity=VFXComplexity.MEDIUM,
    start_timecode="01:00:00:00",
    duration_frames=120
)
```

### Shot Workflow

```python
# Start VFX work
tracker.start_vfx(shot_id, vendor="VFX Studio Inc")

# Submit for review
tracker.submit_for_review(shot_id, Department.VFX, notes="First pass complete")

# Approve or request revision
review_id = tracker.approve_shot(
    shot_id,
    Department.VFX,
    reviewer="supervisor@studio.com",
    comments="Looks great!"
)

# Or request changes
revision_id = tracker.request_revision(
    shot_id,
    Department.VFX,
    reviewer="director@studio.com",
    feedback="Please adjust sky color"
)
```

### Progress Reporting

```python
# Get project statistics
stats = tracker.get_shot_progress(project_id)
print(f"Total shots: {stats['total_shots']}")
print(f"VFX complete: {stats['vfx_complete']}")

# Get shots needing attention
attention = tracker.get_shots_needing_attention(project_id)
print(f"In review: {len(attention['review'])} shots")
print(f"Need revision: {len(attention['revision'])} shots")
```

## Database Schema

The Production Tracker uses 9 interconnected tables:

### Projects

Stores top-level project information.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | Project name |
| description | TEXT | Project description |
| target_runtime | INTEGER | Target runtime in seconds |
| actual_runtime | INTEGER | Actual runtime in seconds |
| budget | REAL | Project budget |
| spent | REAL | Amount spent |
| start_date | TEXT | ISO format date |
| target_completion | TEXT | ISO format date |
| status | TEXT | active/completed/on_hold |
| notes | TEXT | Additional notes |
| created_at | TEXT | ISO timestamp |
| updated_at | TEXT | ISO timestamp |

### Sequences

Organizes shots into sequences within a project.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| project_id | INTEGER | Foreign key to projects |
| sequence_name | TEXT | Sequence identifier (e.g., "SEQ_010") |
| description | TEXT | Sequence description |
| order_index | INTEGER | Display order |
| created_at | TEXT | ISO timestamp |
| updated_at | TEXT | ISO timestamp |

### Shots

Core shot tracking with per-department status.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| sequence_id | INTEGER | Foreign key to sequences |
| shot_name | TEXT | Shot identifier (e.g., "010_010") |
| description | TEXT | Shot description |
| start_timecode | TEXT | Start timecode |
| end_timecode | TEXT | End timecode |
| duration_frames | INTEGER | Duration in frames |
| frame_rate | REAL | Frame rate (default: 24.0) |
| **editorial_status** | TEXT | Editorial department status |
| **vfx_status** | TEXT | VFX department status |
| **color_status** | TEXT | Color department status |
| **sound_status** | TEXT | Sound department status |
| **finishing_status** | TEXT | Finishing department status |
| **delivery_status** | TEXT | Delivery department status |
| vfx_complexity | TEXT | simple/medium/complex |
| vfx_vendor | TEXT | VFX vendor name |
| colorist | TEXT | Assigned colorist |
| color_notes | TEXT | Color grading notes |
| reference_image | TEXT | Path to reference image |
| director_notes | TEXT | Director's notes |
| camera_info | TEXT | Camera information |
| lens_info | TEXT | Lens information |
| shot_type | TEXT | wide/medium/closeup/etc. |
| movement | TEXT | static/pan/tilt/dolly/etc. |
| is_locked | BOOLEAN | Shot locked status |
| priority | INTEGER | Priority level |
| created_at | TEXT | ISO timestamp |
| updated_at | TEXT | ISO timestamp |

### Tasks

Task assignment and tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| shot_id | INTEGER | Foreign key to shots (optional) |
| project_id | INTEGER | Foreign key to projects (optional) |
| department | TEXT | Department enum value |
| title | TEXT | Task title |
| description | TEXT | Task description |
| assignee | TEXT | Assigned person |
| priority | TEXT | critical/high/medium/low |
| status | TEXT | todo/in_progress/review/completed/blocked |
| due_date | TEXT | ISO format date |
| completed_at | TEXT | ISO timestamp |
| estimated_hours | REAL | Time estimate |
| actual_hours | REAL | Actual time spent |
| created_at | TEXT | ISO timestamp |
| updated_at | TEXT | ISO timestamp |

### Reviews

Review and approval workflow tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| shot_id | INTEGER | Foreign key to shots (optional) |
| deliverable_id | INTEGER | Foreign key to deliverables (optional) |
| department | TEXT | Department enum value |
| reviewer | TEXT | Reviewer identifier |
| status | TEXT | pending/approved/revision_requested/rejected |
| comments | TEXT | Review comments |
| feedback | TEXT | Detailed feedback |
| version | INTEGER | Version number |
| submitted_at | TEXT | ISO timestamp |
| reviewed_at | TEXT | ISO timestamp |

### Deliverables

Delivery format tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| project_id | INTEGER | Foreign key to projects |
| category | TEXT | master/festival/broadcast/marketing/etc. |
| name | TEXT | Deliverable name |
| format | TEXT | File format (MOV/DCP/MP4/etc.) |
| resolution | TEXT | Resolution (e.g., "1920x1080") |
| codec | TEXT | Codec name |
| framerate | REAL | Frame rate |
| file_path | TEXT | Path to delivered file |
| status | TEXT | not_started/in_progress/completed/delivered |
| due_date | TEXT | ISO format date |
| delivered_at | TEXT | ISO timestamp |
| notes | TEXT | Additional notes |
| created_at | TEXT | ISO timestamp |
| updated_at | TEXT | ISO timestamp |

### Team Members

Team and vendor directory.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | Person name |
| role | TEXT | Role/title |
| department | TEXT | Department |
| email | TEXT | Email address |
| phone | TEXT | Phone number |
| company | TEXT | Company name |
| is_vendor | BOOLEAN | External vendor flag |
| notes | TEXT | Additional notes |
| created_at | TEXT | ISO timestamp |

### Milestones

Project milestone tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| project_id | INTEGER | Foreign key to projects |
| name | TEXT | Milestone name |
| description | TEXT | Milestone description |
| target_date | TEXT | ISO format date |
| completed_at | TEXT | ISO timestamp |
| status | TEXT | pending/completed/missed |
| created_at | TEXT | ISO timestamp |

### Notes

General notes and comments.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| project_id | INTEGER | Foreign key to projects (optional) |
| shot_id | INTEGER | Foreign key to shots (optional) |
| author | TEXT | Note author |
| content | TEXT | Note content |
| category | TEXT | Note category |
| created_at | TEXT | ISO timestamp |

## API Reference

### ProductionDatabase

Low-level database interface providing direct access to all tables.

#### Initialization

```python
from conformity.production_tracker.production_database import ProductionDatabase

# File-based database
db = ProductionDatabase(Path("project.db"))

# In-memory database
db = ProductionDatabase()
```

#### Project Management

##### `create_project(name, **kwargs) -> int`

Create a new project.

**Parameters:**
- `name` (str): Project name
- `description` (str, optional): Project description
- `target_runtime` (int, optional): Target runtime in seconds
- `budget` (float, optional): Project budget
- `start_date` (str, optional): ISO format date
- `target_completion` (str, optional): ISO format date
- `status` (str, optional): Project status (default: "active")

**Returns:** Project ID

**Example:**
```python
project_id = db.create_project(
    name="Feature Film",
    description="90-minute feature",
    target_runtime=5400,
    budget=1000000.0,
    target_completion="2025-12-31"
)
```

##### `get_project(project_id) -> Dict`

Get project by ID.

##### `update_project(project_id, **kwargs) -> bool`

Update project fields.

##### `list_projects(status=None) -> List[Dict]`

List all projects, optionally filtered by status.

#### Sequence Management

##### `create_sequence(project_id, sequence_name, description="") -> int`

Create a sequence within a project.

**Example:**
```python
seq_id = db.create_sequence(
    project_id,
    "SEQ_010",
    "Opening sequence"
)
```

##### `get_sequence(sequence_id) -> Dict`

Get sequence by ID.

##### `list_sequences(project_id) -> List[Dict]`

List all sequences in a project.

#### Shot Management

##### `create_shot(sequence_id, shot_name, description="", **kwargs) -> int`

Create a shot within a sequence.

**Parameters:**
- `sequence_id` (int): Parent sequence ID
- `shot_name` (str): Shot identifier
- `description` (str, optional): Shot description
- `start_timecode` (str, optional): Start timecode
- `end_timecode` (str, optional): End timecode
- `duration_frames` (int, optional): Duration in frames
- `frame_rate` (float, optional): Frame rate (default: 24.0)
- `vfx_complexity` (str, optional): simple/medium/complex
- `vfx_vendor` (str, optional): VFX vendor name
- And many more optional fields...

**Returns:** Shot ID

**Example:**
```python
shot_id = db.create_shot(
    sequence_id=seq_id,
    shot_name="010_010",
    description="Wide establishing",
    start_timecode="01:00:00:00",
    duration_frames=120,
    vfx_complexity="medium",
    shot_type="wide"
)
```

##### `get_shot(shot_id) -> Dict`

Get shot by ID.

##### `update_shot(shot_id, **kwargs) -> bool`

Update shot fields.

##### `update_shot_status(shot_id, department, status) -> bool`

Update department status for a shot.

**Parameters:**
- `shot_id` (int): Shot ID
- `department` (Department): Department enum
- `status` (ShotStatus): Status enum

**Example:**
```python
from conformity.production_tracker.production_database import Department, ShotStatus

db.update_shot_status(shot_id, Department.VFX, ShotStatus.IN_PROGRESS)
```

##### `list_shots(sequence_id=None, status=None) -> List[Dict]`

List shots, optionally filtered by sequence or status.

#### Task Management

##### `create_task(title, department, **kwargs) -> int`

Create a task.

**Parameters:**
- `title` (str): Task title
- `department` (Department): Department enum
- `shot_id` (int, optional): Associated shot
- `project_id` (int, optional): Associated project
- `assignee` (str, optional): Assigned person
- `priority` (TaskPriority, optional): Priority enum
- `due_date` (str, optional): ISO format date
- `estimated_hours` (float, optional): Time estimate

**Example:**
```python
from conformity.production_tracker.production_database import TaskPriority

task_id = db.create_task(
    title="Cleanup VFX plate",
    department=Department.VFX,
    shot_id=shot_id,
    assignee="artist@studio.com",
    priority=TaskPriority.HIGH,
    due_date="2025-12-15",
    estimated_hours=8.0
)
```

##### `update_task_status(task_id, status, actual_hours=None) -> bool`

Update task status and optionally record actual time.

##### `list_tasks(project_id=None, shot_id=None, department=None, status=None) -> List[Dict]`

List tasks with optional filters.

#### Review & Approval

##### `create_review(department, reviewer, **kwargs) -> int`

Create a review.

**Parameters:**
- `department` (Department): Department enum
- `reviewer` (str): Reviewer identifier
- `shot_id` (int, optional): Associated shot
- `deliverable_id` (int, optional): Associated deliverable
- `comments` (str, optional): Review comments

**Example:**
```python
review_id = db.create_review(
    department=Department.VFX,
    reviewer="supervisor@studio.com",
    shot_id=shot_id,
    comments="First pass looks good"
)
```

##### `update_review_status(review_id, status, feedback="") -> bool`

Update review status.

**Statuses:** "pending", "approved", "revision_requested", "rejected"

##### `list_reviews(shot_id=None, status=None) -> List[Dict]`

List reviews with optional filters.

#### Deliverables

##### `create_deliverable(project_id, category, name, format, **kwargs) -> int`

Create a deliverable.

**Example:**
```python
deliv_id = db.create_deliverable(
    project_id=project_id,
    category="master",
    name="ProRes Master",
    format="MOV",
    resolution="1920x1080",
    codec="ProRes 422 HQ",
    due_date="2025-12-31"
)
```

##### `update_deliverable_status(deliverable_id, status, file_path=None) -> bool`

Update deliverable status and optionally set file path.

##### `list_deliverables(project_id, category=None, status=None) -> List[Dict]`

List deliverables with optional filters.

#### Team Management

##### `add_team_member(name, role, **kwargs) -> int`

Add team member or vendor.

**Example:**
```python
member_id = db.add_team_member(
    name="John Smith",
    role="VFX Supervisor",
    department="vfx",
    email="john@vfxstudio.com",
    company="VFX Studio Inc",
    is_vendor=True
)
```

##### `list_team_members(department=None, is_vendor=None) -> List[Dict]`

List team members with optional filters.

#### Statistics

##### `get_project_stats(project_id) -> Dict[str, Any]`

Get comprehensive project statistics including department progress and task counts.

### ShotTracker

High-level workflow manager providing simplified interfaces for common operations.

#### Initialization

```python
from conformity.production_tracker.shot_tracker import ShotTracker

tracker = ShotTracker(Path("project.db"))
```

#### Project Setup

##### `create_project(name, **kwargs) -> int`

Wrapper for database `create_project`.

##### `add_sequence(project_id, sequence_name, description="") -> int`

Wrapper for database `create_sequence`.

##### `add_shot(sequence_id, shot_name, description="", vfx_complexity=None, **kwargs) -> int`

Wrapper for database `create_shot` with enum handling.

#### Workflow Management

##### `start_vfx(shot_id, vendor="") -> bool`

Start VFX work on a shot.

**Example:**
```python
tracker.start_vfx(shot_id, vendor="VFX Studio Inc")
```

##### `submit_for_review(shot_id, department, notes="") -> bool`

Submit shot for review.

**Example:**
```python
tracker.submit_for_review(shot_id, Department.VFX, notes="First pass complete")
```

##### `approve_shot(shot_id, department, reviewer, comments="") -> int`

Approve shot for department.

**Returns:** Review ID

**Example:**
```python
review_id = tracker.approve_shot(
    shot_id,
    Department.VFX,
    reviewer="supervisor@studio.com",
    comments="Looks great!"
)
```

##### `request_revision(shot_id, department, reviewer, feedback) -> int`

Request revision on shot.

**Returns:** Review ID

**Example:**
```python
revision_id = tracker.request_revision(
    shot_id,
    Department.VFX,
    reviewer="director@studio.com",
    feedback="Please adjust sky color to match reference"
)
```

#### Reporting

##### `get_shot_progress(project_id) -> Dict[str, Any]`

Get shot progress statistics.

**Returns:**
```python
{
    'total_shots': 10,
    'editorial_complete': 5,
    'vfx_complete': 3,
    'color_complete': 2,
    # ... other departments
    'editorial_status': {'approved': 3, 'final': 2, ...},
    'vfx_status': {'approved': 2, 'in_progress': 1, ...},
    # ... other departments
    'task_status': {'completed': 15, 'in_progress': 5, ...}
}
```

##### `get_shots_needing_attention(project_id) -> Dict[str, List[Dict]]`

Get shots requiring attention.

**Returns:**
```python
{
    'review': [
        {'shot_id': 1, 'shot_name': '010_010', 'department': 'vfx', 'sequence': 'SEQ_010'},
        ...
    ],
    'revision': [
        {'shot_id': 2, 'shot_name': '010_020', 'department': 'color', 'sequence': 'SEQ_010'},
        ...
    ],
    'blocked': []
}
```

## Workflow Examples

### Complete VFX Pipeline

```python
from conformity.production_tracker.shot_tracker import ShotTracker
from conformity.production_tracker.production_database import (
    Department, VFXComplexity, TaskPriority
)

tracker = ShotTracker(Path("production.db"))

# Setup
project_id = tracker.create_project("My Film")
seq_id = tracker.add_sequence(project_id, "SEQ_010", "Opening")
shot_id = tracker.add_shot(
    seq_id,
    "010_010",
    "Hero shot",
    vfx_complexity=VFXComplexity.COMPLEX
)

# Step 1: Start VFX
tracker.start_vfx(shot_id, vendor="VFX Studio Inc")

# Step 2: Create task
task_id = tracker.db.create_task(
    title="Remove wires and markers",
    department=Department.VFX,
    shot_id=shot_id,
    assignee="vfx_artist@studio.com",
    priority=TaskPriority.HIGH,
    estimated_hours=16.0
)

# Step 3: Work in progress
tracker.db.update_task_status(task_id, TaskStatus.IN_PROGRESS)

# Step 4: Submit for review
tracker.submit_for_review(shot_id, Department.VFX)

# Step 5: First review - needs revision
revision_id = tracker.request_revision(
    shot_id,
    Department.VFX,
    reviewer="vfx_supervisor@studio.com",
    feedback="Edge detail needs improvement in frames 50-60"
)

# Step 6: Address feedback, resubmit
tracker.submit_for_review(shot_id, Department.VFX, notes="Addressed edge detail")

# Step 7: Final approval
review_id = tracker.approve_shot(
    shot_id,
    Department.VFX,
    reviewer="vfx_supervisor@studio.com",
    comments="Perfect! Approved for final."
)

# Complete task
tracker.db.update_task_status(task_id, TaskStatus.COMPLETED, actual_hours=18.5)
```

### Multi-Department Workflow

```python
# Shot goes through multiple departments
shot_id = tracker.add_shot(seq_id, "010_020", "Action sequence")

# Editorial
tracker.db.update_shot_status(shot_id, Department.EDITORIAL, ShotStatus.IN_PROGRESS)
tracker.submit_for_review(shot_id, Department.EDITORIAL)
tracker.approve_shot(shot_id, Department.EDITORIAL, "editor@studio.com")

# VFX
tracker.start_vfx(shot_id, vendor="VFX Co")
tracker.submit_for_review(shot_id, Department.VFX)
tracker.approve_shot(shot_id, Department.VFX, "vfx_sup@studio.com")

# Color
tracker.db.update_shot(shot_id, colorist="colorist@studio.com")
tracker.db.update_shot_status(shot_id, Department.COLOR, ShotStatus.IN_PROGRESS)
tracker.submit_for_review(shot_id, Department.COLOR)
tracker.approve_shot(shot_id, Department.COLOR, "director@studio.com")

# Sound
tracker.db.update_shot_status(shot_id, Department.SOUND, ShotStatus.IN_PROGRESS)
tracker.submit_for_review(shot_id, Department.SOUND)
tracker.approve_shot(shot_id, Department.SOUND, "sound_sup@studio.com")

# Finishing
tracker.db.update_shot_status(shot_id, Department.FINISHING, ShotStatus.FINAL)
```

### Deliverables Management

```python
db = tracker.db

# Define deliverables
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
        'category': 'broadcast',
        'name': 'HD Broadcast Master',
        'format': 'MXF',
        'resolution': '1920x1080',
        'codec': 'DNxHD',
        'due_date': '2025-12-20'
    }
]

# Create deliverables
for deliv in deliverables:
    deliv_id = db.create_deliverable(project_id=project_id, **deliv)

# Update status as work progresses
db.update_deliverable_status(
    deliv_id,
    status="completed",
    file_path="/deliverables/prores_master_v1.mov"
)

# List by category
masters = db.list_deliverables(project_id, category='master')
festival = db.list_deliverables(project_id, category='festival')
```

### Team & Vendor Directory

```python
db = tracker.db

# Add internal team
db.add_team_member(
    name="Sarah Johnson",
    role="Post Production Supervisor",
    department="finishing",
    email="sarah@studio.com",
    is_vendor=False
)

# Add vendors
vendors = [
    {
        'name': "VFX Studio Inc",
        'role': "VFX Vendor",
        'department': "vfx",
        'email': "contact@vfxstudio.com",
        'company': "VFX Studio Inc",
        'is_vendor': True
    },
    {
        'name': "Color House",
        'role': "Color Grading",
        'department': "color",
        'email': "info@colorhouse.com",
        'company': "Color House",
        'is_vendor': True
    }
]

for vendor in vendors:
    db.add_team_member(**vendor)

# List all vendors
all_vendors = db.list_team_members(is_vendor=True)

# List by department
vfx_vendors = db.list_team_members(department="vfx", is_vendor=True)
```

## Integration

### With Asset Tracker

The Production Tracker can work alongside the Asset Tracker for complete media management:

```python
from conformity.asset_tracker.asset_database import AssetDatabase
from conformity.production_tracker.shot_tracker import ShotTracker

# Both systems
asset_db = AssetDatabase(Path("assets.db"))
prod_tracker = ShotTracker(Path("production.db"))

# Link assets to shots via metadata
shot_id = prod_tracker.add_shot(seq_id, "010_010", "Hero shot")
asset_id = asset_db.add_asset(
    file_path=Path("/media/shot_010_010_v001.mov"),
    asset_type=AssetType.VIDEO
)

# Store shot reference in asset metadata
asset_db.add_metadata(asset_id, {
    'production_shot_id': shot_id,
    'sequence': 'SEQ_010',
    'shot_name': '010_010'
})
```

### With Timeline Manager

Connect production tracking to OTIO timelines:

```python
from conformity.timeline_manager import TimelineManager
from conformity.production_tracker.shot_tracker import ShotTracker

timeline_mgr = TimelineManager(Path("timeline.otio"))
tracker = ShotTracker(Path("production.db"))

# Extract shots from timeline
timeline = timeline_mgr.load_timeline(Path("edit.otio"))
for clip in timeline.each_clip():
    # Create shot from clip
    shot_id = tracker.add_shot(
        seq_id,
        clip.name,
        description=f"From timeline: {clip.name}",
        start_timecode=str(clip.source_range.start_time),
        duration_frames=int(clip.source_range.duration.value)
    )
```

### With Command Interface

Use natural language to query production status:

```python
from conformity.commands.command_parser import CommandParser, ParsedCommand
from conformity.production_tracker.shot_tracker import ShotTracker

tracker = ShotTracker(Path("production.db"))

# Custom command handler for production queries
def handle_production_query(query: str):
    if "shots in review" in query.lower():
        attention = tracker.get_shots_needing_attention(project_id)
        return attention['review']
    elif "vfx progress" in query.lower():
        stats = tracker.get_shot_progress(project_id)
        return f"VFX: {stats['vfx_complete']}/{stats['total_shots']} shots complete"
```

## Best Practices

### 1. Project Organization

- **Use clear naming conventions**: "SEQ_010", "010_010", etc.
- **Set realistic deadlines**: Allow buffer time for revisions
- **Define complexity early**: VFX complexity affects scheduling
- **Lock shots when approved**: Use `is_locked` flag to prevent changes

### 2. Department Workflow

- **Independent tracking**: Each department progresses independently
- **Clear hand-offs**: Use review system between departments
- **Vendor management**: Always specify vendor for external work
- **Regular status updates**: Keep shot statuses current

### 3. Task Management

- **Break down work**: Create specific, actionable tasks
- **Set priorities**: Use TaskPriority for critical path items
- **Track time**: Use estimated_hours and actual_hours for planning
- **Link to shots**: Associate tasks with specific shots when possible

### 4. Review Workflow

- **Multi-stage reviews**: Use revision workflow for quality control
- **Detailed feedback**: Provide specific, actionable notes
- **Version tracking**: Review system tracks version numbers
- **Department approval**: Each department approves independently

### 5. Deliverables

- **Define early**: Create deliverable list at project start
- **Category organization**: Use categories (master/festival/broadcast/etc.)
- **Track progress**: Update status as formats are created
- **File paths**: Record actual file locations when delivered

### 6. Reporting

- **Regular check-ins**: Use `get_shot_progress()` for status meetings
- **Attention flags**: Review `get_shots_needing_attention()` daily
- **Statistics**: Use `get_project_stats()` for comprehensive overview
- **Team visibility**: Share progress reports with all departments

### 7. Database Management

- **Regular backups**: SQLite files should be backed up regularly
- **Transaction safety**: Database uses transactions for data integrity
- **Connection management**: Always call `close()` when done
- **Testing**: Use in-memory database for testing workflows

### 8. Scalability

- **Indexing**: Database includes indexes on common queries
- **Filtering**: Use list methods with filters for large projects
- **Batch operations**: Group related database operations
- **Archiving**: Move completed projects to archive database

## Performance Tips

### Database Optimization

```python
# Use filtering to reduce query size
shots = db.list_shots(sequence_id=seq_id)  # Better
shots = db.list_shots()  # Avoid on large projects

# Batch operations when possible
for shot_data in shot_list:
    shot_id = db.create_shot(**shot_data)  # Individual inserts
# vs
# Use executemany for bulk inserts if needed

# Close connections when done
tracker.close()
```

### Query Patterns

```python
# Good: Targeted queries
vfx_shots = db.list_shots(sequence_id=seq_id)
in_review = [s for s in vfx_shots if s['vfx_status'] == 'review']

# Better: Use database filtering when available
attention = tracker.get_shots_needing_attention(project_id)
in_review = attention['review']
```

## Troubleshooting

### Common Issues

**Issue: "no such column" error**
- Check database schema version
- Ensure database was created with latest version
- For existing databases, consider migration scripts

**Issue: Foreign key constraint errors**
- Ensure parent records exist (project → sequence → shot)
- Check ON DELETE CASCADE for cleanup
- Verify IDs are correct

**Issue: Shot status not updating**
- Verify department enum value
- Check shot_id is valid
- Ensure database connection is active

### Debug Mode

```python
# Enable SQLite tracing
import sqlite3
sqlite3.enable_callback_tracebacks(True)

# Check database integrity
db.cursor.execute("PRAGMA integrity_check")
print(db.cursor.fetchone())

# View schema
db.cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
for row in db.cursor.fetchall():
    print(row[0])
```

## Future Enhancements

Potential future additions to the Production Tracker:

- **Web Dashboard**: React-based web interface for remote access
- **Real-time Updates**: WebSocket support for live collaboration
- **Advanced Analytics**: Charts and visualizations for progress tracking
- **AI Integration**: LLM-powered status updates and reports
- **Computer Vision**: Automated shot comparison and QC
- **Budget Tracking**: Enhanced financial tracking and forecasting
- **Schedule Integration**: Gantt charts and critical path analysis
- **Email Notifications**: Automated alerts for reviews and deadlines
- **API Server**: REST API for third-party integrations
- **Mobile App**: iOS/Android apps for on-set updates

## See Also

- [Command Interface Documentation](COMMAND_INTERFACE.md) - Natural language queries
- [README.md](../README.md) - Main Conformity documentation
- [examples/production_tracker_example.py](../examples/production_tracker_example.py) - Complete examples

---

**Production Tracker** is part of the Conformity toolkit for professional post-production workflows.
