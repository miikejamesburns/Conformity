# Conformity Examples

This directory contains practical examples demonstrating how to use the Conformity post-production pipeline management system.

## Available Examples

### 1. Asset Tracking Example (`asset_tracking_example.py`)

Demonstrates the asset tracking system features:

- Creating and managing an asset database
- Scanning directories for media files
- Searching and filtering assets
- Analyzing timelines and linking clips to assets
- Batch operations (status updates, tagging)
- Generating usage reports

**Run:**
```bash
python examples/asset_tracking_example.py
```

**Key concepts covered:**
- Database CRUD operations
- Metadata extraction
- Timeline analysis
- Tag management
- Asset verification
- Statistics and reporting

### 2. Media Review Example (`media_review_example.py`)

Demonstrates the media review system features:

- Frame-accurate playback controls
- Side-by-side conform comparison
- Frame marker system (issue, note, approved)
- Technical metadata display
- Review status tracking
- Timecode conversion
- Image sequence playback

**Run:**
```bash
python examples/media_review_example.py
```

**Key concepts covered:**
- Playback widget API
- Conform review workflow
- Frame markers
- Review panel
- Keyboard shortcuts
- Integration with asset tracker

**Note:** This example shows API usage. For actual GUI display, you need:
- PyQt6 installed
- Display environment (not headless)

### 3. Integrated Workflow Example (`integrated_workflow_example.py`)

Demonstrates complete real-world scenarios combining multiple systems:

**Scenario 1: Complete Conform Workflow**
- Scan and ingest media library
- Analyze editorial timeline
- Generate conform deliverables
- QC review process
- Update asset status
- Generate final reports

**Scenario 2: Batch Conform Review**
- Multiple episode review
- Automated technical checks
- Batch status updates
- Issue reporting

**Scenario 3: Asset Lifecycle Tracking**
- Track asset from ingest to archive
- Version management
- Status transitions through production pipeline

**Run:**
```bash
python examples/integrated_workflow_example.py
```

**Key concepts covered:**
- End-to-end workflows
- Multi-system integration
- Production best practices
- Automated QC checks
- Asset lifecycle management

## Running Examples

### Prerequisites

All examples require the Conformity package and dependencies:

```bash
# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### Headless Environments

The asset tracking example and integrated workflow example can run in headless environments (no display required).

The media review example demonstrates PyQt6 GUI usage, which requires a display. In headless environments, the example will show the API usage code but won't actually launch the GUI.

### Interactive GUI Examples

To run the actual media review GUI (requires display):

```python
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from conformity.ui_components.playback_widget import PlaybackWidget

app = QApplication([])

player = PlaybackWidget()
player.load_media(Path("your_video.mp4"), frame_rate=24.0)
player.show()

app.exec()
```

## Example Output

### Asset Tracking Example

```
============================================================
ASSET TRACKING SYSTEM EXAMPLES
============================================================

============================================================
EXAMPLE: Basic Asset Tracking
============================================================

1. Adding assets manually...
   Added asset ID: 1
   Added asset ID: 2
   Added asset ID: 3

2. Adding metadata...
   Metadata added for asset 1

3. Adding tags...
   Tags added

4. Searching assets...

   Approved assets: 2
   - clip001.mp4 (VIDEO)
   - frame.0001.exr (IMAGE)

   Video assets: 2
   - clip001.mp4 - APPROVED
   - clip002.mov - PENDING
```

### Integrated Workflow Example

```
================================================================================
SCENARIO: Complete Conform Workflow
================================================================================

================================================================================
STEP 1: Initialize Asset Database
================================================================================

Created asset database for project

================================================================================
STEP 2: Scan and Ingest Media
================================================================================

Scanning media directories...
  Ingested: A001_C001.mov (ID: 1)
  Ingested: A001_C002.mov (ID: 2)
  ...

Total assets ingested: 4
```

## Learning Path

We recommend exploring the examples in this order:

1. **Start with Asset Tracking** - Learn the fundamentals of asset management
   ```bash
   python examples/asset_tracking_example.py
   ```

2. **Explore Media Review** - Understand the review system
   ```bash
   python examples/media_review_example.py
   ```

3. **Study Integrated Workflows** - See how everything works together
   ```bash
   python examples/integrated_workflow_example.py
   ```

## Customizing Examples

All examples use in-memory databases and simulated file paths for demonstration purposes. To adapt for real use:

### Use Real Database Files

```python
# Instead of:
db = AssetDatabase()  # In-memory

# Use:
db = AssetDatabase(Path("my_project.db"))  # Persistent
```

### Use Real Media Paths

```python
# Instead of:
Path("/media/footage/clip001.mp4")  # Simulated

# Use:
Path("/actual/path/to/your/media.mp4")  # Real files
```

### Add Progress Callbacks

```python
def progress_callback(current, total, filename):
    percent = (current / total) * 100
    print(f"Progress: {percent:.1f}% - {filename}")

results = scanner.scan_directory(
    Path("/your/media/directory"),
    recursive=True,
    progress_callback=progress_callback
)
```

## Further Reading

- [Asset Tracking Documentation](../docs/ASSET_TRACKING.md) - Complete API reference
- [Media Review Documentation](../docs/MEDIA_REVIEW.md) - Full feature guide
- [Main README](../README.md) - System overview
- [Quick Start Guide](../docs/QUICKSTART.md) - Getting started

## Common Patterns

### Pattern: Scan → Analyze → Review → Approve

```python
# 1. Scan directory
scanner = AssetScanner(db)
scanner.scan_directory(Path("/media/footage"))

# 2. Analyze timeline
analyzer = TimelineAnalyzer(db)
timeline = otio.adapters.read_from_file("timeline.otio")
analyzer.analyze_timeline(timeline)

# 3. Review (in GUI)
review = ConformReviewWidget()
review.load_source_and_conform(source_path, conform_path)

# 4. Update status based on review
if review_passed:
    db.update_asset_status(asset_id, AssetStatus.APPROVED)
```

### Pattern: Batch Processing

```python
# Get all pending deliverables
pending = db.search_assets(
    asset_type=AssetType.VIDEO,
    status=AssetStatus.PENDING,
    tags=["deliverable"]
)

# Perform automated checks
approved_ids = []
for asset in pending:
    if check_technical_specs(asset):
        approved_ids.append(asset['id'])

# Batch approve
scanner.batch_update_status(approved_ids, AssetStatus.APPROVED)
```

## Support

If you have questions about the examples or encounter issues:

1. Check the documentation in `docs/`
2. Review the test files in `tests/` for more usage examples
3. Open an issue on the project repository

## Contributing Examples

Have a useful example workflow? Contributions are welcome! Examples should:

- Be well-commented and self-contained
- Include clear output showing what the example demonstrates
- Follow the existing example structure
- Work in headless environments when possible
