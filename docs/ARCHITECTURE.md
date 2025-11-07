# Conformity Architecture

## Overview

Conformity follows a layered, modular architecture designed for extensibility and maintainability.

## Architecture Layers

```
┌─────────────────────────────────────────┐
│         User Interface (Qt)             │
│     (main_window, ui_components)        │
├─────────────────────────────────────────┤
│         Application Logic               │
│  (conform_engine, color_manager,        │
│   asset_tracker)                        │
├─────────────────────────────────────────┤
│         Core Services                   │
│    (config, logger)                     │
├─────────────────────────────────────────┤
│      External Libraries                 │
│  (OTIO, OCIO, PyQt6)                    │
└─────────────────────────────────────────┘
```

## Module Details

### Core Layer

The core layer provides foundational services:

**ConfigManager**
- Loads configuration from YAML and environment
- Type-safe config access via Pydantic
- Supports runtime config updates

**Logger**
- Singleton logger instance
- File and console output
- Module-specific loggers

### Application Logic Layer

**Conform Engine**
- `TimelineManager`: CRUD operations for timelines
- `ConformOperations`: Advanced conform operations
- Stateless operations where possible

**Color Manager**
- `OCIOManager`: OCIO config and color space operations
- `ColorPipeline`: Integration with OTIO timelines
- Processor creation for transformations

**Asset Tracker**
- `AssetManager`: Asset registration and tracking
- `Asset`: Dataclass for asset metadata
- Directory scanning and verification

### UI Layer

**Main Window**
- Qt MainWindow with menu system
- Tab-based interface
- Integrates all application components

**Widgets**
- `TimelineWidget`: Timeline visualization
- `AssetBrowserWidget`: Asset management UI
- Reusable, composable components

## Design Patterns

### Singleton
Used for:
- ConfigManager (global configuration)
- Logger (centralized logging)

### Manager Pattern
Used for:
- TimelineManager
- OCIOManager
- AssetManager

Managers provide high-level interfaces to complex subsystems.

### Model-View Pattern
- Asset dataclass as model
- AssetBrowserWidget as view
- Separation of data and presentation

## Data Flow

### Timeline Loading
```
User Action → MainWindow → TimelineManager → OTIO → Timeline Object → TimelineWidget
```

### Asset Scanning
```
User Action → AssetBrowserWidget → AssetManager → Filesystem → Asset Objects → UI Update
```

### Color Management
```
Timeline Clips → ColorPipeline → OCIOManager → OCIO Config → Color Space Assignment
```

## Extension Points

The architecture supports extension through:

1. **New Modules**: Add new managers/services
2. **UI Widgets**: Create new Qt widgets
3. **Conform Operations**: Add to ConformOperations class
4. **Asset Types**: Extend AssetType enum
5. **Configuration**: Add new config fields

## Threading Considerations

Current implementation is single-threaded. Future enhancements:

- Background asset scanning
- Async timeline operations
- Progress reporting for long operations

## Error Handling

- Exceptions propagated to UI layer
- QMessageBox for user-facing errors
- Logging of all errors
- Graceful degradation where possible

## Testing Strategy

- Unit tests for managers and operations
- Integration tests for component interaction
- Qt testing with pytest-qt
- Mock external dependencies (filesystem, OCIO)
