# Conformity

A Python-based post-production pipeline management system for professional video workflows.

## Overview

Conformity is a modular application designed to streamline post-production workflows by integrating industry-standard tools for timeline management, color pipeline management, and asset tracking.

### Key Features

- **Automated Conform**: Import/export timelines from multiple formats (EDL, XML, AAF, FCPXML)
  - Parse timeline structure with clips, tracks, transitions, and markers
  - Validate timelines for errors and missing media
  - Match clips to media files automatically
  - Export to different formats with full metadata preservation
- **Timeline Management**: Built on OpenTimelineIO (OTIO) for robust timeline operations
- **Color Management**: Integrated OpenColorIO (OCIO) for professional color pipeline management
- **Asset Tracking**: Comprehensive media asset management and organization
- **Modern UI**: Clean, intuitive interface built with PyQt6

## Architecture

Conformity follows a modular architecture with clear separation of concerns:

```
conformity/
├── src/conformity/
│   ├── core/                 # Core utilities
│   │   ├── config.py        # Configuration management
│   │   └── logger.py        # Logging system
│   ├── conform_engine/      # OTIO timeline operations
│   │   ├── conform_engine.py    # Automated import/export
│   │   ├── timeline_manager.py
│   │   ├── conform_ops.py
│   │   └── exceptions.py
│   ├── color_manager/       # OCIO color management
│   │   ├── ocio_manager.py
│   │   └── color_pipeline.py
│   ├── asset_tracker/       # Asset management
│   │   └── asset_manager.py
│   └── ui_components/       # Qt UI widgets
│       ├── conform_panel.py     # Conform operations UI
│       ├── timeline_widget.py
│       └── asset_browser.py
├── tests/                   # Unit tests
├── config/                  # Configuration files
├── docs/                    # Documentation
└── requirements.txt         # Dependencies
```

### Module Overview

#### Core (`src/conformity/core/`)

Provides foundational services used across the application:

- **config.py**: Configuration management using Pydantic models and YAML
  - Load/save configuration
  - Environment variable overrides
  - Type-safe configuration access

- **logger.py**: Centralized logging system
  - File and console output
  - Configurable log levels
  - Timestamped log files

#### Conform Engine (`src/conformity/conform_engine/`)

Handles all timeline and conform operations using OpenTimelineIO:

- **conform_engine.py**: Automated timeline import/export
  - Import from EDL, XML, AAF, FCPXML formats
  - Parse timeline structure (clips, tracks, transitions, markers)
  - Validate timelines for errors and missing media
  - Export to multiple formats with metadata preservation
  - Error handling with custom exceptions

- **timeline_manager.py**: High-level timeline operations
  - Load/save timelines from various formats
  - Create new timelines
  - Add clips and manage tracks
  - Extract timeline metadata

- **conform_ops.py**: Advanced conform operations
  - Match clips by name
  - Relink media references
  - Generate conform reports
  - Extract clip metadata

- **exceptions.py**: Custom exception classes
  - ImportError, ExportError, MediaNotFoundError
  - InvalidTimecodeError, UnsupportedFeatureError
  - Detailed error reporting

#### Color Manager (`src/conformity/color_manager/`)

Holistic color management system using OpenColorIO:

- **color_manager.py**: Comprehensive color management engine
  - Validate OCIO configurations
  - Track color space assignments across pipeline
  - Auto-detect color spaces from metadata and extensions
  - Generate validation reports with status tracking
  - Pipeline-wide color configuration management

- **ocio_manager.py**: OCIO configuration and operations
  - Load and validate OCIO configs
  - Query color spaces, displays, and views
  - Create color transformation processors
  - Validate color space compatibility

- **color_pipeline.py**: Integration with timelines
  - Assign color spaces to clips with validation
  - Auto-assign based on file types and metadata
  - Generate comprehensive color reports
  - Manage display/view assignments
  - Track color space usage statistics

#### Asset Tracker (`src/conformity/asset_tracker/`)

Tracks and manages media assets:

- **asset_manager.py**: Asset registration and management
  - Register assets with metadata
  - Scan directories for media
  - Verify asset availability
  - Track asset status (online/offline)
  - Generate statistics

#### UI Components (`src/conformity/ui_components/`)

Qt-based user interface widgets:

- **conform_panel.py**: Automated conform operations UI
  - Import timelines from multiple formats
  - Display timeline structure in tree view
  - Show detailed clip information
  - Validate timelines for errors
  - Export to different formats
  - Interactive conform workflow

- **color_space_widget.py**: Color management UI
  - Load and validate OCIO configurations
  - Set pipeline-wide color defaults
  - Visualize color space families and relationships
  - Analyze timelines for color space assignments
  - Manually assign/override color spaces
  - Auto-assign based on rules and metadata
  - Export color space reports

- **timeline_widget.py**: Timeline visualization
  - Display timeline information
  - Browse tracks and clips
  - Show duration and metadata

- **asset_browser.py**: Asset management UI
  - Browse registered assets
  - Scan directories
  - Verify asset status
  - View asset details and statistics

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install from source

1. Clone the repository:
```bash
git clone https://github.com/yourusername/conformity.git
cd conformity
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install in development mode (optional):
```bash
pip install -e .
```

## Running the Application

### Quick Start

Run the application directly:
```bash
python run.py
```

Or if installed:
```bash
conformity
```

### Configuration

The application uses a YAML configuration file located at `config/default_config.yaml`. You can customize:

- Application settings (name, version, log level)
- Project paths (cache, temp directories)
- OCIO settings (config path, default color space)
- OTIO settings (default FPS, resolution)
- UI settings (theme, window size)

### Environment Variables

You can override configuration using environment variables:

- `OCIO`: Path to OCIO configuration file
- `CONFORMITY_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

Example:
```bash
export OCIO=/path/to/config.ocio
export CONFORMITY_LOG_LEVEL=DEBUG
python run.py
```

## Usage Examples

### Automated Conform Operations

```python
from pathlib import Path
from conformity.conform_engine.conform_engine import ConformEngine, TimelineFormat

# Create conform engine
engine = ConformEngine()

# Import timeline from XML
timeline, info = engine.import_timeline(
    Path("project.xml"),
    verify_media=True
)

print(f"Imported: {info.num_clips} clips, {info.num_tracks} tracks")

# Validate timeline
results = engine.validate_timeline(timeline, check_media=True)
if results['valid']:
    print("Timeline is valid!")
else:
    print(f"Errors: {len(results['errors'])}")

# Export to EDL
engine.export_timeline(
    timeline,
    Path("output.edl"),
    format=TimelineFormat.EDL
)
```

### Working with Timelines

```python
from conformity.conform_engine.timeline_manager import TimelineManager

# Create a timeline manager
manager = TimelineManager()

# Create a new timeline
timeline = manager.create_timeline(name="My Project", fps=24.0)

# Load an existing timeline
timeline = manager.load_timeline(Path("timeline.otio"))

# Get timeline information
info = manager.get_timeline_info(timeline)
print(f"Timeline: {info['name']}, Clips: {info['clips']}")

# Save timeline
manager.save_timeline(timeline, Path("output.otio"))
```

### Holistic Color Management

```python
from pathlib import Path
from conformity.color_manager.color_manager import ColorManager

# Create color manager
color_mgr = ColorManager()

# Load and validate OCIO config
color_mgr.load_config(Path("config/ocio/simple_config.ocio"))
valid, errors = color_mgr.validate_config()
print(f"Config valid: {valid}")

# Set pipeline defaults
pipeline = color_mgr.get_pipeline_config()
pipeline.set_defaults(
    working="Linear",
    default_input="CameraRec709",
    display="sRGB",
    view="Standard"
)

# Add auto-detection rules
pipeline.add_rule('.r3d', 'RedWideGamutRGB')
pipeline.add_rule('.ari', 'ARRI_LogC4')
pipeline.add_rule('.braw', 'BMDFilm_Gen5')

# Auto-assign color spaces to timeline
count = color_mgr.auto_assign_color_spaces(timeline, use_defaults=True)
print(f"Assigned color spaces to {count} clips")

# Analyze timeline
result = color_mgr.analyze_timeline(timeline, auto_detect=True)
print(f"Valid: {result.valid_count}, Missing: {result.missing_count}")

# Generate report
report = color_mgr.create_color_space_report(timeline)
print(f"Color spaces used: {list(report['color_spaces_used'].keys())}")
```

### Tracking Assets

```python
from conformity.asset_tracker.asset_manager import AssetManager

# Create asset manager
asset_mgr = AssetManager()

# Scan a directory
count = asset_mgr.scan_directory(
    Path("/path/to/media"),
    recursive=True
)
print(f"Found {count} assets")

# Get statistics
stats = asset_mgr.get_statistics()
print(f"Total assets: {stats['total_assets']}")
print(f"Total size: {stats['total_size_gb']} GB")

# Verify assets
status = asset_mgr.verify_assets()
print(f"Online: {status['online']}, Offline: {status['offline']}")
```

## Development

### Running Tests

Run the test suite with pytest:
```bash
pytest tests/
```

With coverage:
```bash
pytest --cov=src/conformity tests/
```

### Code Style

Format code with black:
```bash
black src/ tests/
```

Lint with flake8:
```bash
flake8 src/ tests/
```

Type checking with mypy:
```bash
mypy src/
```

## Project Structure

```
Conformity/
├── src/
│   └── conformity/
│       ├── __init__.py
│       ├── main.py              # Application entry point
│       ├── main_window.py       # Main Qt window
│       ├── core/                # Core utilities
│       ├── conform_engine/      # Timeline operations
│       ├── color_manager/       # Color management
│       ├── asset_tracker/       # Asset management
│       └── ui_components/       # UI widgets
├── tests/                       # Unit tests
│   ├── __init__.py
│   ├── test_timeline_manager.py
│   └── test_asset_manager.py
├── config/                      # Configuration files
│   └── default_config.yaml
├── docs/                        # Documentation
├── logs/                        # Log files (generated)
├── requirements.txt             # Python dependencies
├── setup.py                     # Package setup
├── run.py                       # Convenience run script
├── .gitignore
└── README.md
```

## Dependencies

### Core Libraries

- **OpenTimelineIO**: Timeline interchange format and operations
- **PyOpenColorIO**: Color management and transformations
- **PyQt6**: GUI framework

### Supporting Libraries

- **PyYAML**: Configuration file parsing
- **Pydantic**: Data validation and settings management
- **python-dotenv**: Environment variable management

### Development Dependencies

- **pytest**: Testing framework
- **pytest-qt**: Qt testing support
- **pytest-cov**: Coverage reporting
- **black**: Code formatting
- **flake8**: Code linting
- **mypy**: Static type checking

## Roadmap

Future enhancements planned:

- [ ] EDL import/export support
- [ ] Advanced timeline editing tools
- [ ] LUT application and management
- [ ] Render queue management
- [ ] Multi-project workspace
- [ ] Plugin architecture
- [ ] REST API for pipeline integration
- [ ] Database backend for asset metadata

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Ensure code passes linting and tests
6. Submit a pull request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Acknowledgments

- Built with [OpenTimelineIO](https://github.com/AcademySoftwareFoundation/OpenTimelineIO)
- Color management by [OpenColorIO](https://github.com/AcademySoftwareFoundation/OpenColorIO)
- UI powered by [Qt for Python](https://www.qt.io/qt-for-python)

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/yourusername/conformity/issues
- Documentation: https://github.com/yourusername/conformity/docs

## Version History

### 0.1.0 (Current)
- Initial prototype release
- Basic timeline management with OTIO
- OCIO integration for color management
- Asset tracking and management
- Qt-based user interface
- Configuration and logging systems
