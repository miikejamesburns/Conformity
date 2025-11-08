# Conformity Deployment Guide

Complete guide for deploying and using the Conformity post-production pipeline management system.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Features Overview](#features-overview)
4. [API Reference](#api-reference)
5. [Developer Guide](#developer-guide)
6. [Troubleshooting](#troubleshooting)
7. [Roadmap](#roadmap)

---

## Installation

### Prerequisites

**Required:**
- Python 3.11 or higher
- pip (Python package manager)
- Git

**Optional:**
- tlRender (for professional playback)
- Display server (for GUI)

### Platform-Specific Requirements

#### macOS
```bash
# Install Python 3.11+
brew install python@3.11

# Install Qt dependencies
brew install qt6
```

#### Linux (Ubuntu/Debian)
```bash
# Install Python 3.11+
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Install Qt dependencies
sudo apt install python3-pyqt6 libqt6widgets6
```

#### Windows
```powershell
# Install Python from python.org
# Ensure "Add Python to PATH" is checked during installation

# Install Visual C++ Build Tools (for some dependencies)
# Download from: https://visualstudio.microsoft.com/downloads/
```

### Installation Steps

#### 1. Clone Repository

```bash
git clone https://github.com/yourusername/conformity.git
cd conformity
```

#### 2. Create Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Note: PyOpenColorIO is optional and may fail to install on some platforms
# See docs/INSTALLATION_TROUBLESHOOTING.md if you encounter errors

# Verify installation
python -c "import conformity; print('Installation successful!')"
```

**Troubleshooting:** If you see errors about PyOpenColorIO:
- This is **normal** on Apple Silicon Macs and some platforms
- PyOpenColorIO is **optional** - core features work without it
- See [Installation Troubleshooting](docs/INSTALLATION_TROUBLESHOOTING.md) for solutions
- Quick fix: Continue without color management (it's optional!)

```bash
# If installation fails, try the automated setup script:
python setup_conformity.py --install
```

#### 4. Verify Installation

```bash
# Run tests to verify everything works
python run_tests.py --quick

# Run demo mode
python -m conformity.demo.demo_mode
```

### Optional: Install tlRender

For professional-grade playback:

```bash
# See docs/TLRENDER.md for detailed instructions
# Repository: https://github.com/darbyjohnston/tlRender
```

---

## Quick Start

### 1. Create Your First Project

```python
from pathlib import Path
from conformity.production_tracker import ShotTracker, Department

# Create production tracker
tracker = ShotTracker(Path("my_project.db"))

# Create project
project_id = tracker.create_project(
    name="My Film",
    target_runtime=5400,  # 90 minutes in seconds
    budget=500000.0
)

# Add sequence
seq_id = tracker.add_sequence(project_id, "SEQ_010", "Opening")

# Add shot
shot_id = tracker.add_shot(
    seq_id,
    "010_001",
    "Wide establishing shot",
    duration_frames=120
)

print(f"Created shot {shot_id}")
```

### 2. Track Assets

```python
from conformity.asset_tracker import AssetDatabase, AssetType, AssetStatus

# Create asset database
asset_db = AssetDatabase(Path("assets.db"))

# Add asset
asset_id = asset_db.add_asset(
    file_path=Path("/media/footage/clip_001.mov"),
    asset_type=AssetType.VIDEO,
    status=AssetStatus.PENDING
)

# Add metadata
asset_db.add_metadata(asset_id, {
    'duration': 150,
    'frame_rate': 24.0,
    'resolution': '1920x1080',
    'color_space': 'rec709'
})

# Add tags
asset_db.add_tags(asset_id, ['footage', 'approved'])

# Search assets
approved_assets = asset_db.search_assets(status=AssetStatus.APPROVED)
print(f"Found {len(approved_assets)} approved assets")
```

### 3. Use Natural Language Commands

```python
from conformity.commands import CommandParser, CommandExecutor

# Create parser and executor
parser = CommandParser()
executor = CommandExecutor(asset_db=asset_db)

# Parse and execute command
cmd = parser.parse("find clips with approved")
result = executor.execute(cmd)

if result.success:
    print(f"Found {len(result.data)} clips")
```

### 4. Run Demo Mode

```bash
# Interactive demo with pre-populated data
python -m conformity.demo.demo_mode
```

---

## Features Overview

### 🎬 Production Tracking

Track shots through the entire post-production pipeline:

**Key Features:**
- Multi-department tracking (Editorial, VFX, Color, Sound, Finishing, Delivery)
- Shot-level status for each department
- Task assignment and management
- Review and approval workflows
- Deliverables checklist
- Team and vendor directory
- Progress statistics

**Example Workflow:**
```python
# Start VFX
tracker.start_vfx(shot_id, vendor="VFX Studio Inc")

# Submit for review
tracker.submit_for_review(shot_id, Department.VFX)

# Approve
tracker.approve_shot(shot_id, Department.VFX, "supervisor@studio.com")

# Get progress
stats = tracker.get_shot_progress(project_id)
print(f"VFX: {stats['vfx_complete']}/{stats['total_shots']}")
```

### 📦 Asset Tracking

Comprehensive media asset management:

**Key Features:**
- Directory scanning and ingestion
- Metadata extraction and storage
- Tag-based organization
- Status tracking
- Timeline-asset linking
- Search and filtering

**Example:**
```python
# Scan directory
from conformity.asset_tracker import AssetScanner

scanner = AssetScanner(asset_db)
results = scanner.scan_directory(Path("/media/footage"), recursive=True)
print(f"Scanned {results['total_scanned']} files")
```

### 💬 Natural Language Commands

Query your project using natural language:

**Supported Commands:**
- `find clips with [keyword]`
- `show assets in [color_space]`
- `list missing media`
- `filter by approved status`
- `count assets by type`

**Features:**
- Pattern-based parsing
- Autocomplete suggestions
- Command history
- Saved queries
- LLM-ready architecture

### 🎨 Color Management

Professional color pipeline with OCIO:

**Key Features:**
- OCIO configuration loading
- Color space transforms
- LUT management (CUBE, 3DL)
- Display transforms
- View transforms

**Example:**
```python
from conformity.color_manager import ColorManager

color_mgr = ColorManager(Path("config.ocio"))

# Get available color spaces
spaces = color_mgr.get_color_spaces()

# Apply transform
processor = color_mgr.get_processor("ACEScg", "sRGB")
```

### 📝 Timeline Management

Industry-standard timeline operations with OTIO:

**Supported Formats:**
- EDL (CMX 3600)
- Final Cut Pro XML
- AAF
- OTIO native

**Example:**
```python
import opentimelineio as otio

# Load timeline
timeline = otio.adapters.read_from_file("edit.xml")

# Access clips
for clip in timeline.each_clip():
    print(f"{clip.name}: {clip.duration()}")

# Export
otio.adapters.write_to_file(timeline, "output.edl")
```

---

## API Reference

### Asset Tracker

#### AssetDatabase

Main interface for asset management.

**Methods:**

```python
# Create
asset_id = db.add_asset(
    file_path: Path,
    asset_type: AssetType,
    status: AssetStatus = AssetStatus.PENDING
) -> int

# Read
asset = db.get_asset(asset_id: int) -> Dict

# Update
db.update_asset_status(asset_id: int, status: AssetStatus) -> bool

# Search
assets = db.search_assets(
    asset_type: AssetType = None,
    status: AssetStatus = None,
    tags: List[str] = None
) -> List[Dict]

# Metadata
db.add_metadata(asset_id: int, metadata: Dict) -> bool
db.get_metadata(asset_id: int) -> Dict

# Tags
db.add_tags(asset_id: int, tags: List[str]) -> bool
db.get_tags(asset_id: int) -> List[str]
```

**Enums:**

```python
class AssetType(Enum):
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"

class AssetStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVIEW = "review"
```

### Production Tracker

#### ShotTracker

High-level interface for production workflows.

**Methods:**

```python
# Project Management
project_id = tracker.create_project(
    name: str,
    target_runtime: int = None,
    budget: float = None,
    target_completion: str = None
) -> int

# Sequence Management
seq_id = tracker.add_sequence(
    project_id: int,
    sequence_name: str,
    description: str = ""
) -> int

# Shot Management
shot_id = tracker.add_shot(
    sequence_id: int,
    shot_name: str,
    description: str = "",
    vfx_complexity: VFXComplexity = None,
    duration_frames: int = None
) -> int

# Workflow Operations
tracker.start_vfx(shot_id: int, vendor: str = "") -> bool
tracker.submit_for_review(shot_id: int, department: Department) -> bool
tracker.approve_shot(shot_id: int, department: Department, reviewer: str) -> int
tracker.request_revision(shot_id: int, department: Department, feedback: str) -> int

# Reporting
stats = tracker.get_shot_progress(project_id: int) -> Dict
attention = tracker.get_shots_needing_attention(project_id: int) -> Dict
```

**Enums:**

```python
class Department(Enum):
    EDITORIAL = "editorial"
    VFX = "vfx"
    COLOR = "color"
    SOUND = "sound"
    FINISHING = "finishing"
    DELIVERY = "delivery"

class VFXComplexity(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
```

### Command Interface

#### CommandParser

Natural language query parser.

```python
parser = CommandParser()

# Parse query
cmd = parser.parse(query: str) -> ParsedCommand

# ParsedCommand properties
cmd.command_type: CommandType  # find, show, list, count, filter
cmd.entity_type: EntityType     # assets, clips, shots, etc.
cmd.filters: Dict[FilterType, Any]
cmd.confidence: float          # 0.0-1.0
```

#### CommandExecutor

Execute parsed commands.

```python
executor = CommandExecutor(
    asset_db: AssetDatabase = None,
    timeline_mgr: TimelineManager = None
)

# Execute command
result = executor.execute(cmd: ParsedCommand) -> ExecutionResult

# ExecutionResult properties
result.success: bool
result.data: Any               # Query results
result.count: int              # Result count
result.error: str              # Error message (if any)
```

---

## Developer Guide

### Extending Conformity

#### Adding New Command Types

1. **Add Pattern to Parser** (`commands/command_parser.py`):

```python
class CommandParser:
    def _extract_command_type(self, query):
        # Add new pattern
        if re.search(r'\b(compare|diff)\b', query):
            return CommandType.COMPARE
        # ...existing patterns
```

2. **Add Handler to Executor** (`commands/command_executor.py`):

```python
class CommandExecutor:
    def execute(self, command):
        if command.command_type == CommandType.COMPARE:
            return self._execute_compare_command(command)
        # ...existing handlers

    def _execute_compare_command(self, command):
        # Implementation
        pass
```

#### Adding Custom UI Widgets

1. **Create Widget** (`ui_components/my_widget.py`):

```python
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal

class MyCustomWidget(QWidget):
    # Define signals
    data_changed = pyqtSignal(dict)

    def __init__(self, backend_service, parent=None):
        super().__init__(parent)
        self.backend = backend_service
        self._setup_ui()

    def _setup_ui(self):
        # Create UI elements
        pass

    def refresh_data(self):
        # Load data from backend
        data = self.backend.get_data()
        self.data_changed.emit(data)
```

2. **Integrate with Main Window**:

```python
# In main window
from .ui_components.my_widget import MyCustomWidget

self.my_widget = MyCustomWidget(backend_service)
self.tab_widget.addTab(self.my_widget, "My Feature")
```

#### Adding New Color Workflows

Update OCIO configuration to add color spaces - no code changes needed:

```yaml
# In config.ocio
colorspaces:
  - !<ColorSpace>
    name: My Custom Space
    family: Custom
    bitdepth: 32f
    to_reference: !<FileTransform> {src: my_lut.cube}
```

#### Preparing for Phase 2 (fiftyone Integration)

Phase 2 will add ML-powered sensory ingest with fiftyone. Prepare by:

1. **Ensure Asset Metadata Complete**: Add all technical metadata
2. **Tag Consistency**: Use consistent tagging scheme
3. **Quality Metrics**: Track quality scores for assets
4. **Performance Baseline**: Benchmark current ingest speed

Example preparation:

```python
# Enhanced metadata for ML
asset_db.add_metadata(asset_id, {
    # Technical
    'duration': 150,
    'frame_rate': 24.0,
    'resolution': '1920x1080',
    'codec': 'ProRes 422',

    # Quality metrics (for Phase 2)
    'sharpness_score': 0.85,
    'noise_level': 0.12,
    'exposure_quality': 0.92,

    # Content tags (for Phase 2 ML)
    'scene_type': 'outdoor',
    'lighting': 'daylight',
    'camera_movement': 'static'
})
```

### Best Practices

#### Database Operations

```python
# Always use transactions for multi-step operations
db.cursor.execute("BEGIN")
try:
    db.create_shot(...)
    db.create_task(...)
    db.conn.commit()
except Exception as e:
    db.conn.rollback()
    raise
```

#### Error Handling

```python
# Use try-except with specific exceptions
try:
    timeline = otio.adapters.read_from_file(path)
except otio.exceptions.UnsupportedSchemaException:
    logger.error(f"Unsupported format: {path}")
except FileNotFoundError:
    logger.error(f"File not found: {path}")
```

#### Testing New Features

```python
# Write tests for new features
import pytest

def test_my_new_feature(asset_db):
    """Test my new feature."""
    # Arrange
    asset_id = asset_db.add_asset(...)

    # Act
    result = my_new_function(asset_id)

    # Assert
    assert result == expected_value
```

---

## Troubleshooting

### Common Issues

#### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'conformity'`

**Solution**:
```bash
# Install in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/conformity/src"
```

#### PyQt6 Not Found

**Problem**: `ModuleNotFoundError: No module named 'PyQt6'`

**Solution**:
```bash
# Install PyQt6
pip install PyQt6

# Linux: May need system packages
sudo apt install python3-pyqt6
```

#### Database Locked

**Problem**: `sqlite3.OperationalError: database is locked`

**Solution**:
```python
# Enable WAL mode for concurrent access
conn.execute("PRAGMA journal_mode=WAL")

# Or increase timeout
conn = sqlite3.connect("db.sqlite", timeout=30.0)
```

#### OTIO Format Not Supported

**Problem**: `UnsupportedSchemaException` when loading timeline

**Solution**:
```bash
# Check installed adapters
python -c "import opentimelineio as otio; print(otio.adapters.available_adapter_names())"

# Install additional adapters if needed
pip install opentimelineio-contrib
```

#### Color Space Not Found

**Problem**: OCIO color space not found

**Solution**:
```python
# Verify OCIO config
config = ocio.Config.CreateFromFile("config.ocio")
for cs in config.getColorSpaces():
    print(cs.getName())

# Update config.ocio to include missing color space
```

### Getting Help

- **Documentation**: Check `docs/` directory
- **Examples**: See `examples/` directory
- **Tests**: Review `tests/` for usage examples
- **Issues**: Open issue on GitHub

---

## Roadmap

### Phase 1: Foundation (COMPLETED ✅)

**Core Pipeline Management**

- ✅ Asset tracking and management
- ✅ Production workflow tracking
- ✅ Timeline management (OTIO)
- ✅ Color management (OCIO)
- ✅ Natural language command interface
- ✅ Professional playback (tlRender)
- ✅ Comprehensive testing (80%+ coverage)
- ✅ Complete documentation

**Key Achievements:**
- 9 major modules
- 50+ Python files (~20,000 lines of code)
- SQLite databases for asset and production tracking
- Multi-department workflow support
- Qt6 GUI components
- Demo mode with sample data
- 35+ comprehensive tests

### Phase 2: Sensory Ingest with ML (PLANNED)

**fiftyone Integration for Intelligent Media Analysis**

**Goals:**
- ML-powered media analysis
- Automated quality assessment
- Scene detection and classification
- Object/face detection
- Shot similarity matching
- Automated metadata extraction

**Planned Features:**

1. **Visual Analysis**
   - Shot detection and segmentation
   - Scene classification (indoor/outdoor, day/night)
   - Object detection (people, vehicles, landmarks)
   - Face detection and recognition
   - Action/activity recognition

2. **Quality Assessment**
   - Sharpness and focus analysis
   - Exposure quality metrics
   - Noise level detection
   - Color balance assessment
   - Technical QC automation

3. **Content Organization**
   - Automated tagging based on content
   - Similarity clustering
   - Duplicate detection
   - Smart search by visual content

4. **Integration Points**
   ```python
   from fiftyone import Dataset
   from conformity.ml import SensoryIngest

   # Analyze media with ML
   ingest = SensoryIngest(asset_db)
   results = ingest.analyze_asset(asset_id)

   # Extract insights
   print(f"Scene type: {results['scene_type']}")
   print(f"Detected objects: {results['objects']}")
   print(f"Quality score: {results['quality_score']}")

   # Auto-tag based on ML
   auto_tags = results['suggested_tags']
   asset_db.add_tags(asset_id, auto_tags)
   ```

**Timeline**: Q2 2026 (estimated)

### Phase 3: LLM-Powered Features (VISION)

**Natural Language Understanding for Post-Production**

**Goals:**
- LLM-enhanced command interface
- Automated workflow suggestions
- Intelligent project planning
- Natural language queries for complex operations

**Planned Features:**

1. **Enhanced Command Interface**
   - Full natural language understanding
   - Context-aware suggestions
   - Multi-step workflow automation
   - Conversational interface

   ```python
   # Natural language workflows
   "Find all shots in SEQ_010 that need VFX revision and create tasks for the VFX team"

   "Show me the color grade status for all outdoor scenes and flag any that don't match the reference"

   "Generate a report of all shots that are behind schedule with their assigned artists"
   ```

2. **Intelligent Automation**
   - Automated shot breakdown from scripts
   - Smart deadline suggestions based on complexity
   - Resource allocation optimization
   - Predictive delay detection

3. **Documentation Generation**
   - Auto-generate technical specs
   - Create delivery documentation
   - Generate client reports
   - Produce project summaries

4. **Integration Architecture**
   ```python
   from conformity.llm import LLMAssistant

   assistant = LLMAssistant(model="gpt-4")

   # Natural language project query
   response = assistant.query(
       "What shots are at risk of missing their delivery date?"
   )

   # Get actionable insights
   for shot in response.at_risk_shots:
       print(f"{shot.name}: {shot.risk_reason}")
       print(f"Suggested action: {shot.recommendation}")
   ```

**Timeline**: 2027+ (vision)

### Version History

- **v1.0.0** (Current): Complete Phase 1 foundation
- **v0.9.0**: Production tracker
- **v0.8.0**: Natural language commands
- **v0.7.0**: tlRender integration
- **v0.6.0**: Media review system
- **v0.5.0**: Asset tracking
- **v0.4.0**: Color management
- **v0.3.0**: Timeline operations
- **v0.2.0**: Core infrastructure
- **v0.1.0**: Initial prototype

---

## Support & Contributing

### Getting Support

- **Documentation**: Check `/docs` directory
- **Examples**: See `/examples` directory
- **Tests**: Review `/tests` for usage patterns

### Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

### License

See LICENSE file for details.

---

**Deployment Guide Version**: 1.0.0
**Last Updated**: 2025-11-08
