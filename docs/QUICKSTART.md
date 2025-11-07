# Conformity Quick Start Guide

## Installation

### 1. Prerequisites

Ensure you have Python 3.8+ installed:
```bash
python --version
```

### 2. Get the Code

```bash
git clone https://github.com/yourusername/conformity.git
cd conformity
```

### 3. Setup Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## Running Conformity

### Launch the Application

```bash
python run.py
```

The main window will open with three tabs:
- **Timeline**: Timeline management
- **Assets**: Asset browser
- **Color Management**: OCIO configuration

## Basic Workflows

### Working with Timelines

#### Create a New Timeline

1. Click **File → New Timeline** (or Ctrl+N)
2. A new empty timeline is created
3. Timeline info is displayed in the Timeline tab

#### Open an Existing Timeline

1. Click **File → Open Timeline** (or Ctrl+O)
2. Browse to an `.otio` file
3. Timeline loads and displays tracks and clips

#### Save a Timeline

1. Click **File → Save Timeline** (or Ctrl+S)
2. Choose location and filename
3. Timeline saved in OTIO format

### Managing Assets

#### Scan for Assets

1. Switch to the **Assets** tab
2. Click **Scan Directory**
3. Select a folder containing media files
4. Assets are registered and displayed

#### Verify Assets

1. Click **Verify Assets**
2. Asset status updates (online/offline)
3. Statistics refresh

### Color Management

#### Load OCIO Config

1. Click **Color → Load OCIO Config**
2. Select an OCIO config file (`.ocio`)
3. Config loads and color spaces become available

#### View Color Spaces

1. Click **Color → Show Color Spaces**
2. List of available color spaces displays

## Configuration

### Config File Location

Default configuration: `config/default_config.yaml`

### Key Settings

```yaml
# Logging
log_level: "INFO"  # DEBUG, INFO, WARNING, ERROR

# OCIO
ocio_config_path: null  # Path to OCIO config or use $OCIO

# Timeline defaults
default_fps: 24.0
default_resolution: [1920, 1080]

# UI
theme: "dark"  # dark or light
window_width: 1280
window_height: 720
```

### Environment Variables

Override settings with environment variables:

```bash
# Set OCIO config
export OCIO=/path/to/config.ocio

# Set log level
export CONFORMITY_LOG_LEVEL=DEBUG

# Run application
python run.py
```

## Using the API

### Timeline Operations

```python
from pathlib import Path
from conformity.conform_engine.timeline_manager import TimelineManager

# Create manager
manager = TimelineManager()

# Create timeline
timeline = manager.create_timeline("My Project", fps=24.0)

# Add a clip
manager.add_clip(
    media_path=Path("/path/to/video.mov"),
    track_index=0,
    name="Clip 1"
)

# Save timeline
manager.save_timeline(timeline, Path("project.otio"))
```

### Asset Management

```python
from pathlib import Path
from conformity.asset_tracker.asset_manager import AssetManager

# Create manager
asset_mgr = AssetManager()

# Scan directory
count = asset_mgr.scan_directory(Path("/media"), recursive=True)

# Get statistics
stats = asset_mgr.get_statistics()
print(f"Found {stats['total_assets']} assets")

# Verify online/offline status
status = asset_mgr.verify_assets()
```

### Color Pipeline

```python
from pathlib import Path
from conformity.color_manager.ocio_manager import OCIOManager
from conformity.color_manager.color_pipeline import ColorPipeline

# Setup OCIO
ocio_mgr = OCIOManager()
ocio_mgr.load_config(Path("config.ocio"))

# Create color pipeline
color_pipe = ColorPipeline(ocio_mgr)

# Assign color space to clip
color_pipe.assign_color_space_to_clip(clip, "ACEScg")

# Auto-assign based on file types
color_pipe.auto_assign_color_spaces(timeline)
```

## Troubleshooting

### Application Won't Start

1. Check Python version: `python --version`
2. Verify dependencies: `pip list`
3. Check logs: `logs/conformity_*.log`

### OCIO Errors

1. Ensure OCIO config is valid
2. Check `$OCIO` environment variable
3. Verify color space names match config

### Timeline Load Fails

1. Check file format is supported by OTIO
2. Verify file is not corrupted
3. Check logs for specific error

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Review main [README.md](../README.md) for full documentation
- Explore example scripts in `examples/` (coming soon)
- Check tests in `tests/` for usage examples

## Getting Help

- Check logs in `logs/` directory
- Review error messages in UI dialogs
- Consult OTIO/OCIO documentation for library-specific issues
- Open an issue on GitHub
