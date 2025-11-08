## Asset Tracking System

Comprehensive asset management with SQLite backend for post-production workflows.

## Overview

The asset tracking system provides persistent storage and management for media assets with:

- **SQLite Database Backend**: Lightweight, file-based persistence
- **Metadata Extraction**: Automatic technical metadata from video, image, and audio files
- **Timeline Integration**: Track relationships between timeline clips and physical media
- **Search and Filtering**: Powerful queries across all metadata fields
- **Batch Operations**: Update status, add tags, relocate files for multiple assets
- **Qt UI**: Interactive search, filter, and management interface

## Quick Start

### Basic Asset Management

```python
from pathlib import Path
from conformity.asset_tracker.asset_database import AssetDatabase, AssetType, AssetStatus
from conformity.asset_tracker.asset_scanner import AssetScanner

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
print(f"Errors: {results['errors']}")

# Search for assets
assets = db.search_assets(
    asset_type=AssetType.VIDEO,
    status=AssetStatus.APPROVED
)

for asset in assets:
    print(f"{asset['file_name']}: {asset['status']}")
```

### Timeline Integration

```python
from conformity.asset_tracker.timeline_analyzer import TimelineAnalyzer
import opentimelineio as otio

# Load timeline
timeline = otio.adapters.read_from_file("timeline.otio")

# Analyze timeline and create associations
analyzer = TimelineAnalyzer(db)
results = analyzer.analyze_timeline(timeline)

print(f"Linked clips: {results['linked_clips']}")
print(f"Missing media: {results['missing_clips']}")

# Get all assets used in timeline
assets = analyzer.get_timeline_assets(Path("timeline.otio"))

for asset in assets:
    print(f"{asset['file_name']} used in {asset['clip_name']}")
```

## Database Schema

### Tables

#### assets
Primary asset information table.

```sql
CREATE TABLE assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    file_name TEXT NOT NULL,
    asset_type TEXT NOT NULL,          -- video, image, audio, sequence, other
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, in_progress, approved, needs_review, archived
    file_size INTEGER,
    checksum TEXT,
    created_date TEXT NOT NULL,
    modified_date TEXT NOT NULL,
    last_scanned TEXT,
    is_online INTEGER DEFAULT 1,       -- 1 = online, 0 = offline
    notes TEXT
);
```

#### asset_metadata
Technical metadata for assets.

```sql
CREATE TABLE asset_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    width INTEGER,
    height INTEGER,
    frame_rate REAL,
    duration REAL,
    codec TEXT,
    pixel_format TEXT,
    bit_depth INTEGER,
    color_space TEXT,
    color_primaries TEXT,
    transfer_function TEXT,
    audio_channels INTEGER,
    audio_sample_rate INTEGER,
    metadata_json TEXT,                -- Full metadata as JSON
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
);
```

#### timeline_associations
Links timeline clips to physical assets.

```sql
CREATE TABLE timeline_associations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    timeline_path TEXT NOT NULL,
    clip_name TEXT NOT NULL,
    track_name TEXT,
    source_in REAL,                   -- Source in point (seconds)
    source_out REAL,                  -- Source out point (seconds)
    record_in REAL,                   -- Record in point (seconds)
    record_out REAL,                  -- Record out point (seconds)
    created_date TEXT NOT NULL,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
);
```

#### asset_versions
Version history tracking.

```sql
CREATE TABLE asset_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    created_date TEXT NOT NULL,
    created_by TEXT,
    notes TEXT,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
);
```

#### asset_dependencies
Asset relationship tracking.

```sql
CREATE TABLE asset_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_asset_id INTEGER NOT NULL,
    dependent_asset_id INTEGER NOT NULL,
    dependency_type TEXT NOT NULL,     -- references, derives_from, etc.
    created_date TEXT NOT NULL,
    FOREIGN KEY (source_asset_id) REFERENCES assets(id) ON DELETE CASCADE,
    FOREIGN KEY (dependent_asset_id) REFERENCES assets(id) ON DELETE CASCADE
);
```

#### asset_tags
Asset tagging and organization.

```sql
CREATE TABLE asset_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    tag TEXT NOT NULL,
    created_date TEXT NOT NULL,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
);
```

### Indices

```sql
CREATE INDEX idx_assets_path ON assets(file_path);
CREATE INDEX idx_assets_type ON assets(asset_type);
CREATE INDEX idx_assets_status ON assets(status);
CREATE INDEX idx_timeline_assoc_asset ON timeline_associations(asset_id);
CREATE INDEX idx_timeline_assoc_timeline ON timeline_associations(timeline_path);
CREATE INDEX idx_metadata_colorspace ON asset_metadata(color_space);
CREATE INDEX idx_tags_tag ON asset_tags(tag);
```

## Example Queries

### Find All Video Assets

```python
assets = db.search_assets(asset_type=AssetType.VIDEO)
```

SQL equivalent:
```sql
SELECT * FROM assets WHERE asset_type = 'video';
```

### Find Assets by Status

```python
approved = db.search_assets(status=AssetStatus.APPROVED)
```

SQL equivalent:
```sql
SELECT * FROM assets WHERE status = 'approved';
```

### Find Assets by Color Space

```python
rec709 = db.search_assets(color_space='rec709')
```

SQL equivalent:
```sql
SELECT DISTINCT a.*
FROM assets a
JOIN asset_metadata m ON a.id = m.asset_id
WHERE m.color_space = 'rec709';
```

### Find Offline Assets

```python
offline = db.search_assets(online_only=False)
offline = [a for a in offline if not a['is_online']]
```

SQL equivalent:
```sql
SELECT * FROM assets WHERE is_online = 0;
```

### Find Assets Used in Timeline

```python
analyzer = TimelineAnalyzer(db)
assets = analyzer.get_timeline_assets(Path("project.otio"))
```

SQL equivalent:
```sql
SELECT a.*, ta.clip_name, ta.track_name
FROM assets a
JOIN timeline_associations ta ON a.id = ta.asset_id
WHERE ta.timeline_path = 'project.otio'
ORDER BY ta.record_in;
```

### Find Most Used Assets

```python
report = analyzer.generate_usage_report()
most_used = report['most_used']
```

SQL equivalent:
```sql
SELECT a.id, a.file_name, COUNT(*) as usage_count
FROM assets a
JOIN timeline_associations ta ON a.id = ta.asset_id
GROUP BY a.id
ORDER BY usage_count DESC
LIMIT 10;
```

### Find Unused Assets

```python
# Get all assets
all_assets = db.search_assets(online_only=False)

# Get used asset IDs
used_ids = set()
cursor = db.conn.cursor()
cursor.execute("SELECT DISTINCT asset_id FROM timeline_associations")
used_ids = {row[0] for row in cursor.fetchall()}

# Filter unused
unused = [a for a in all_assets if a['id'] not in used_ids]
```

SQL equivalent:
```sql
SELECT a.*
FROM assets a
LEFT JOIN timeline_associations ta ON a.id = ta.asset_id
WHERE ta.id IS NULL;
```

### Find Assets by Tags

```python
assets = db.search_assets(tags=['important', 'vfx'])
```

SQL equivalent:
```sql
SELECT DISTINCT a.*
FROM assets a
JOIN asset_tags t ON a.id = t.asset_id
WHERE t.tag IN ('important', 'vfx');
```

### Get Asset with Full Metadata

```python
asset = db.get_asset_by_id(asset_id)
metadata = db.get_asset_metadata(asset_id)

print(f"File: {asset['file_path']}")
print(f"Resolution: {metadata['width']}x{metadata['height']}")
print(f"Frame Rate: {metadata['frame_rate']} fps")
print(f"Color Space: {metadata['color_space']}")
```

SQL equivalent:
```sql
SELECT a.*, m.width, m.height, m.frame_rate, m.color_space
FROM assets a
LEFT JOIN asset_metadata m ON a.id = m.asset_id
WHERE a.id = ?;
```

## API Reference

### AssetDatabase

#### Constructor

```python
db = AssetDatabase(db_path=None)
```

Creates or opens database. Use `None` for in-memory database.

#### add_asset

```python
asset_id = db.add_asset(
    file_path: Path,
    asset_type: AssetType,
    status: AssetStatus = AssetStatus.PENDING,
    file_size: Optional[int] = None,
    checksum: Optional[str] = None,
    notes: Optional[str] = None
) -> int
```

Add asset to database. Returns asset ID.

#### add_metadata

```python
metadata_id = db.add_metadata(
    asset_id: int,
    metadata: Dict[str, Any]
) -> int
```

Add technical metadata for asset. Returns metadata ID.

#### search_assets

```python
assets = db.search_assets(
    query: Optional[str] = None,
    asset_type: Optional[AssetType] = None,
    status: Optional[AssetStatus] = None,
    color_space: Optional[str] = None,
    tags: Optional[List[str]] = None,
    online_only: bool = True
) -> List[Dict[str, Any]]
```

Search assets with filters. Returns list of asset dictionaries.

#### update_asset_status

```python
success = db.update_asset_status(
    asset_id: int,
    status: AssetStatus
) -> bool
```

Update asset workflow status.

#### add_tag

```python
success = db.add_tag(
    asset_id: int,
    tag: str
) -> bool
```

Add tag to asset.

### AssetScanner

#### Constructor

```python
scanner = AssetScanner(database: AssetDatabase)
```

Create scanner with database instance.

#### scan_directory

```python
results = scanner.scan_directory(
    directory: Path,
    recursive: bool = True,
    update_existing: bool = False,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> Dict[str, Any]
```

Scan directory for media files and add to database.

Returns:
```python
{
    'total_found': int,
    'added': int,
    'updated': int,
    'skipped': int,
    'errors': int,
    'error_files': List[str],
    'scan_time_seconds': float
}
```

#### verify_assets

```python
results = scanner.verify_assets(
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> Dict[str, Any]
```

Verify all assets are still online. Returns results dictionary.

#### batch_update_status

```python
count = scanner.batch_update_status(
    asset_ids: List[int],
    status: AssetStatus
) -> int
```

Update status for multiple assets. Returns count updated.

#### batch_add_tags

```python
count = scanner.batch_add_tags(
    asset_ids: List[int],
    tags: List[str]
) -> int
```

Add tags to multiple assets. Returns count of tags added.

### TimelineAnalyzer

#### Constructor

```python
analyzer = TimelineAnalyzer(database: AssetDatabase)
```

Create analyzer with database instance.

#### analyze_timeline

```python
results = analyzer.analyze_timeline(
    timeline: otio.schema.Timeline,
    timeline_path: Optional[Path] = None
) -> Dict[str, Any]
```

Analyze timeline and create clip-to-asset associations.

Returns:
```python
{
    'timeline_name': str,
    'total_clips': int,
    'linked_clips': int,
    'missing_clips': int,
    'associations_created': int,
    'missing_media': List[Dict]
}
```

#### get_timeline_assets

```python
assets = analyzer.get_timeline_assets(
    timeline_path: Path
) -> List[Dict[str, Any]]
```

Get all assets used in a timeline.

#### get_asset_timelines

```python
timelines = analyzer.get_asset_timelines(
    asset_id: int
) -> List[Dict[str, Any]]
```

Get all timelines that use an asset.

#### relink_timeline

```python
results = analyzer.relink_timeline(
    timeline: otio.schema.Timeline,
    search_paths: Optional[List[Path]] = None
) -> Dict[str, Any]
```

Attempt to relink missing media using database.

## Workflows

### Initial Project Setup

```python
from pathlib import Path
from conformity.asset_tracker.asset_database import AssetDatabase
from conformity.asset_tracker.asset_scanner import AssetScanner

# Create project database
project_dir = Path("/projects/my_project")
db_path = project_dir / "assets.db"
db = AssetDatabase(db_path)

# Scan media directories
scanner = AssetScanner(db)

media_dirs = [
    project_dir / "footage",
    project_dir / "renders",
    project_dir / "audio"
]

for media_dir in media_dirs:
    results = scanner.scan_directory(media_dir, recursive=True)
    print(f"Scanned {media_dir}: {results['added']} assets added")

# Get statistics
stats = db.get_statistics()
print(f"Total assets: {stats['total_assets']}")
print(f"Total size: {stats['total_size_gb']} GB")
```

### Daily Asset Verification

```python
# Verify all assets are still online
results = scanner.verify_assets()

print(f"Online: {results['online']}")
print(f"Offline: {results['offline']}")

if results['offline'] > 0:
    # Find offline assets
    offline = db.search_assets(online_only=False)
    offline = [a for a in offline if not a['is_online']]

    for asset in offline:
        print(f"Offline: {asset['file_path']}")
```

### Timeline Conforming Workflow

```python
import opentimelineio as otio

# Load timeline
timeline = otio.adapters.read_from_file("edit.otio")

# Analyze timeline
analyzer = TimelineAnalyzer(db)
results = analyzer.analyze_timeline(timeline, Path("edit.otio"))

# Check for missing media
if results['missing_clips'] > 0:
    print(f"Missing media: {results['missing_clips']} clips")

    for missing in results['missing_media']:
        print(f"  - {missing['clip_name']}: {missing['media_path']}")

    # Attempt to relink
    search_paths = [
        Path("/archive/footage"),
        Path("/backup/media")
    ]

    relink_results = analyzer.relink_timeline(timeline, search_paths)
    print(f"Relinked: {relink_results['relinked']} clips")

    # Save relinked timeline
    if relink_results['relinked'] > 0:
        otio.adapters.write_to_file(timeline, "edit_relinked.otio")
```

### Color Space Management

```python
# Find all assets with specific color space
rec709_assets = db.search_assets(color_space='rec709')

print(f"Found {len(rec709_assets)} Rec.709 assets")

# Tag for color grading
for asset in rec709_assets:
    db.add_tag(asset['id'], 'needs_color_grade')
    db.update_asset_status(asset['id'], AssetStatus.NEEDS_REVIEW)
```

### Asset Approval Workflow

```python
# Find pending assets
pending = db.search_assets(status=AssetStatus.PENDING)

for asset in pending:
    # Review asset...
    metadata = db.get_asset_metadata(asset['id'])

    print(f"Review: {asset['file_name']}")
    print(f"  Resolution: {metadata['width']}x{metadata['height']}")
    print(f"  Color Space: {metadata['color_space']}")

    # Approve or mark for review
    if meets_criteria(metadata):
        db.update_asset_status(asset['id'], AssetStatus.APPROVED)
    else:
        db.update_asset_status(asset['id'], AssetStatus.NEEDS_REVIEW)
        db.add_tag(asset['id'], 'quality_issue')
```

### Usage Reports

```python
# Generate usage report
report = analyzer.generate_usage_report()

print(f"Total associations: {report['total_associations']}")
print(f"Unused assets: {report['unused_assets']}")

print("\nMost used assets:")
for asset in report['most_used']:
    print(f"  {asset['file_name']}: {asset['usage_count']} uses")
```

## Qt UI Integration

### Using the Asset Tracker Widget

```python
from PyQt6.QtWidgets import QApplication, QMainWindow
from conformity.asset_tracker.asset_database import AssetDatabase
from conformity.ui_components.asset_tracker_widget import AssetTrackerWidget

app = QApplication([])
window = QMainWindow()

# Create database
db = AssetDatabase(Path("project.db"))

# Create widget
tracker = AssetTrackerWidget(db)
window.setCentralWidget(tracker)

window.show()
app.exec()
```

### Features

- **Text Search**: Search file paths and notes
- **Filters**: Filter by type, status, color space
- **Sorting**: Click column headers to sort
- **Batch Operations**: Select multiple assets and update status
- **Directory Scanning**: Scan new media with progress bar
- **Asset Verification**: Check online/offline status
- **Double-Click**: View detailed asset information

## Best Practices

### Database Management

1. **Use File-Based Database**: Store database in project directory
2. **Regular Backups**: Backup `.db` file regularly
3. **Verify Regularly**: Run verification daily to catch offline media
4. **Index Optimization**: Database indices are auto-created for performance

### Scanning

1. **Initial Scan**: Full recursive scan when starting project
2. **Incremental Updates**: Use `update_existing=True` when re-scanning
3. **Progress Callbacks**: Use callbacks for UI feedback on large scans
4. **Error Handling**: Review `error_files` list after scanning

### Timeline Integration

1. **Analyze Early**: Analyze timelines before starting work
2. **Track Associations**: Create associations to enable relinking
3. **Relink First**: Attempt automatic relinking before manual intervention
4. **Update Regularly**: Re-analyze timelines after major changes

### Workflow

1. **Use Status**: Track workflow stages (pending → in_progress → approved)
2. **Tag Liberally**: Use tags for flexible organization
3. **Document**: Use notes field for important information
4. **Clean Up**: Archive or remove unused assets periodically

## Related Documentation

- [Color Workflows](COLOR_WORKFLOWS.md) - Color space management
- [Timeline Editing](TIMELINE_EDITING.md) - Timeline operations
- [EDL Workflows](EDL_WORKFLOWS.md) - EDL import/export
- [README](../README.md) - Main documentation
