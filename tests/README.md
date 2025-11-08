# Conformity Test Suite

Comprehensive testing for the Conformity post-production pipeline management system.

## Quick Start

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
python run_tests.py

# Run quick smoke tests
python run_tests.py --quick
```

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and configuration
├── mock_data_generators.py     # Test data generators
├── test_end_to_end.py         # End-to-end workflow tests
├── test_integration.py        # Integration tests between modules
└── test_data/                 # Sample test data files
    ├── timelines/
    │   └── sample_timeline.edl
    └── ocio/
        └── test_config.ocio
```

## Test Categories

### Smoke Tests (`@pytest.mark.smoke`)

Quick sanity checks - run these first!

```bash
python run_tests.py --quick
```

**Characteristics:**
- Very fast (<10 seconds total)
- Basic functionality only
- Good for pre-commit hooks

### Unit Tests (`@pytest.mark.unit`)

Test individual components in isolation.

```bash
python run_tests.py --unit
```

**Characteristics:**
- Fast (<1s per test)
- No external dependencies
- Mock external services

### Integration Tests (`@pytest.mark.integration`)

Test interactions between modules.

```bash
python run_tests.py --integration
```

**Characteristics:**
- Test module boundaries
- Database interactions
- 1-5s per test

### End-to-End Tests (`@pytest.mark.e2e`)

Test complete workflows.

```bash
python run_tests.py --e2e
```

**Characteristics:**
- Realistic user scenarios
- Multiple systems
- 5-30s per test

## Fixtures

The test suite provides extensive pytest fixtures in `conftest.py`:

### Database Fixtures

- `asset_db` - Empty in-memory asset database
- `asset_db_with_data` - Pre-populated asset database
- `production_tracker` - Empty production tracker
- `production_tracker_with_data` - Pre-populated production tracker
- `integration_context` - All systems initialized and linked

### Directory Fixtures

- `temp_dir` - Temporary directory (auto-cleaned)
- `test_data_dir` - Path to test_data directory
- `mock_project_structure` - Complete mock project tree

### Data Fixtures

- `sample_clip_data` - List of sample clip dictionaries
- `sample_edl` - EDL file content
- `sample_ocio_config` - OCIO configuration
- `sample_timeline_xml` - OTIO timeline as XML

### Utility Fixtures

- `mock_file_creator` - Factory for creating mock files

## Mock Data Generators

Use generators to create test data on the fly:

```python
from tests.mock_data_generators import (
    TimelineGenerator,
    AssetDataGenerator,
    ProductionDataGenerator,
    EDLGenerator
)

# Generate timeline
timeline = TimelineGenerator.generate_simple_timeline(num_clips=10)

# Generate assets
assets = AssetDataGenerator.generate_footage_library(num_clips=50)

# Generate EDL
edl = EDLGenerator.generate_simple_edl(num_events=20)
```

## Writing Tests

### Example Unit Test

```python
import pytest
from conformity.asset_tracker.asset_database import AssetDatabase, AssetType

@pytest.mark.unit
def test_add_asset(asset_db, temp_dir):
    """Test adding asset to database."""
    asset_id = asset_db.add_asset(
        file_path=temp_dir / "test.mov",
        asset_type=AssetType.VIDEO
    )

    assert asset_id > 0

    asset = asset_db.get_asset(asset_id)
    assert asset is not None
    assert asset['asset_type'] == 'video'
```

### Example Integration Test

```python
@pytest.mark.integration
def test_asset_to_shot_link(asset_db, production_tracker):
    """Test linking assets to shots."""
    # Create shot
    project_id = production_tracker.create_project(name="Test")
    seq_id = production_tracker.add_sequence(project_id, "SEQ_001", "Test")
    shot_id = production_tracker.add_shot(seq_id, "001_001", "Test")

    # Create asset
    asset_id = asset_db.add_asset(
        file_path=Path("/test/render.exr"),
        asset_type=AssetType.IMAGE
    )

    # Link them
    asset_db.add_metadata(asset_id, {'shot_id': shot_id})

    # Verify
    asset = asset_db.get_asset(asset_id)
    assert asset['metadata']['shot_id'] == shot_id
```

### Example E2E Test

```python
@pytest.mark.e2e
def test_vfx_pipeline(asset_db, production_tracker, temp_dir):
    """Test complete VFX pipeline workflow."""
    # Setup project
    project_id = production_tracker.create_project(name="VFX Test")
    seq_id = production_tracker.add_sequence(project_id, "SEQ_010", "VFX")
    shot_id = production_tracker.add_shot(seq_id, "010_001", "VFX Shot")

    # Start VFX
    production_tracker.start_vfx(shot_id, vendor="Test VFX")

    # Create render
    asset_id = asset_db.add_asset(
        temp_dir / "render.exr",
        AssetType.IMAGE
    )
    asset_db.add_metadata(asset_id, {'shot_id': shot_id})

    # Review and approve
    production_tracker.submit_for_review(shot_id, Department.VFX)
    production_tracker.approve_shot(shot_id, Department.VFX, "supervisor")
    asset_db.update_asset_status(asset_id, AssetStatus.APPROVED)

    # Verify
    shot = production_tracker.db.get_shot(shot_id)
    assert shot['vfx_status'] == 'approved'

    asset = asset_db.get_asset(asset_id)
    assert asset['status'] == 'approved'
```

## Coverage

Generate coverage reports:

```bash
# HTML report
python run_tests.py --coverage --html

# View report
open htmlcov/index.html
```

**Coverage Goals:**
- Overall: >80%
- Core modules: >90%
- UI components: >60%

## Performance Testing

Run tests marked as slow:

```bash
pytest -m slow
```

Exclude slow tests:

```bash
pytest -m "not slow"
```

Profile test performance:

```bash
pip install pytest-profiling
pytest --profile
```

## Continuous Integration

For CI environments:

```bash
python run_tests.py --ci
```

This excludes:
- Slow tests
- GUI tests
- Tests requiring display

## Troubleshooting

### Import Errors

```bash
# Install in development mode
pip install -e .
```

### Fixture Not Found

Ensure `conftest.py` is in `tests/` directory and pytest can find it.

### Tests Hang

```bash
# Run without parallel execution
pytest --no-cov
```

### Debug Failures

```bash
# Verbose with local variables
pytest -vvl

# Drop into debugger
pytest --pdb

# Show print statements
pytest -s
```

## Best Practices

1. **Test Independence**: Each test should be self-contained
2. **Clear Names**: Use descriptive test function names
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Use Fixtures**: Extract common setup
5. **Parametrize**: Test multiple inputs efficiently

## Resources

- [Full Testing Guide](../docs/TESTING.md)
- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)

---

Happy testing! 🧪
