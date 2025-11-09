# Asset Preview Feature

## Overview

The Asset Browser now includes a dynamic large preview window on the right side of the UI that displays media assets with automatic format detection and scaling.

## Features

### Media Preview Widget

The `MediaPreviewWidget` provides:

- **Large preview area** with automatic scaling
- **Dynamic updates** when assets are selected
- **Multiple format support**:
  - Image files (JPG, PNG, BMP, TIFF, GIF, WebP)
  - Video files (MP4, MOV, AVI, MKV, MXF, R3D, ARI, BRAW) - placeholder
  - Image sequences (DPX, EXR, CIN) - placeholder
  - Generic file info for other formats

### Layout

The Asset Browser uses a horizontal split layout:

```
┌─────────────────────────────────────────────────────────┐
│  Asset Browser                                          │
├──────────────────┬──────────────────────────────────────┤
│ Left Panel (40%) │ Right Panel (60%)                    │
│                  │                                      │
│ • Statistics     │ ┌────────────────────────────────┐  │
│ • Control Buttons│ │                                │  │
│ • Asset List     │ │   Media Preview                │  │
│ • Quick Info     │ │   (Dynamic Large Display)      │  │
│                  │ │                                │  │
│                  │ └────────────────────────────────┘  │
│                  │ Asset Metadata                      │
└──────────────────┴──────────────────────────────────────┘
```

### Resizable Panels

- The splitter between left and right panels is **draggable**
- Minimum widths:
  - Left panel: 350px
  - Preview panel: 400px
- Default ratio: 40% left, 60% preview

## Supported Media Types

### Images (Full Preview)
- **Formats**: .jpg, .jpeg, .png, .bmp, .tiff, .tif, .gif, .webp
- **Features**:
  - Automatic scaling to fit preview area
  - Maintains aspect ratio
  - Smooth transformation
  - Responsive to window resizing

### Videos (Placeholder)
- **Formats**: .mp4, .mov, .avi, .mkv, .m4v, .mxf, .r3d, .ari, .braw
- **Display**: Shows format info, resolution, and FPS
- **Future**: Video playback integration planned

### Image Sequences (Placeholder)
- **Formats**: .dpx, .exr, .cin
- **Display**: Shows sequence info and resolution
- **Future**: Sequence scrubbing planned

### Other Files
- Shows file type icon and metadata
- Displays file size and basic info

## Visual Indicators

### Status Colors
- **Online assets**: Normal preview with dark background
- **Offline assets**: Red-tinted background with warning icon
- **No selection**: Gray placeholder text

### Information Display
The preview includes:
- Large media display area (scrollable for large images)
- Metadata panel showing:
  - Name
  - Type
  - Status
  - Size
  - Resolution (if available)
  - Frame rate (if available)
  - Color space (if available)
  - Full file path

## Usage

### Basic Usage

1. Select an asset from the list on the left
2. The preview automatically updates on the right
3. For images, the preview scales to fit the available space
4. Resize the window or splitter to adjust the preview size

### Keyboard Navigation

- Use arrow keys to navigate the asset list
- Preview updates automatically as you navigate

### Example Code

```python
from conformity.ui_components.asset_browser import AssetBrowserWidget
from conformity.asset_tracker.asset_manager import AssetManager

# Create asset browser with preview
asset_manager = AssetManager()
browser = AssetBrowserWidget(asset_manager)

# The preview is automatically integrated
# It updates when assets are selected from the list
```

## Implementation Details

### Components

1. **MediaPreviewWidget** (`media_preview_widget.py`)
   - Standalone preview widget
   - Can be used independently
   - Handles all preview rendering logic

2. **AssetBrowserWidget** (`asset_browser.py`)
   - Integrates preview on the right side
   - Uses QSplitter for resizable layout
   - Connects asset selection to preview updates

### Signal Flow

```
User clicks asset in list
  ↓
AssetBrowserWidget._on_asset_selected()
  ↓
MediaPreviewWidget.set_asset(asset)
  ↓
Preview updates automatically
```

## Future Enhancements

### Planned Features
- [ ] Video playback with scrubbing
- [ ] Image sequence playback
- [ ] Color space visualization
- [ ] Metadata overlay toggle
- [ ] Fullscreen preview mode
- [ ] Compare mode (side-by-side)
- [ ] Thumbnail strip for sequences
- [ ] Audio waveform display

### Integration Opportunities
- Integration with `tlRender` for professional playback
- OCIO color management for accurate previews
- Frame-accurate scrubbing
- Render quality settings

## Technical Notes

### Performance
- Images are loaded asynchronously
- Scaling is done with Qt's SmoothTransformation
- Resize events trigger intelligent reloading
- Memory efficient - only current asset loaded

### Styling
- Dark theme optimized
- Consistent with Conformity UI palette
- Responsive to window state changes
- Professional video/post-production aesthetic

## Related Documentation

- See `docs/CONFORM_GUIDE.md` for general conform workflows
- See `docs/EDL_WORKFLOWS.md` for EDL-specific operations
- See source code for detailed API documentation
