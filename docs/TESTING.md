## Testing Guide

Comprehensive testing documentation for Conformity.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Types](#test-types)
- [Writing Tests](#writing-tests)
- [Coverage Reports](#coverage-reports)
- [Demo Mode](#demo-mode)
- [Continuous Integration](#continuous-integration)
- [Troubleshooting](#troubleshooting)

## Overview

Conformity includes a comprehensive test suite covering:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Module interaction testing
- **End-to-End Tests**: Complete workflow testing
- **Mock Data Generators**: Synthetic test data creation
- **Demo Mode**: Pre-populated demonstration environment

### Test Statistics

- **Test Files**: 3 main test suites
- **Fixtures**: 30+ reusable pytest fixtures
- **Mock Generators**: 5 data generator classes
- **Coverage Goal**: >80% code coverage

## Test Structure

```
conformity/
├── tests/
│   ├── conftest.py                 # Shared fixtures and configuration
│   ├── mock_data_generators.py     # Test data generators
│   ├── test_end_to_end.py         # E2E workflow tests
│   ├── test_integration.py        # Integration tests
│   └── test_data/                 # Sample test data
│       ├── timelines/
│       │   ├── sample_timeline.edl
│       │   └── sample_timeline.xml (generated)
│       └── ocio/
│           └── test_config.ocio
├── pytest.ini                     # Pytest configuration
├── run_tests.py                   # Test runner script
└── .coveragerc                    # Coverage configuration (in pytest.ini)
```

## Running Tests

### Quick Start

```bash
# Run all tests
python run_tests.py

# Run quick smoke tests
python run_tests.py --quick

# Run with coverage report
python run_tests.py --coverage --html
```

### Test Runner Options

The `run_tests.py` script provides multiple test modes:

```bash
# Test Modes
python run_tests.py --quick         # Smoke tests only (~30 seconds)
python run_tests.py --unit          # Unit tests only
python run_tests.py --integration   # Integration tests
python run_tests.py --e2e           # End-to-end tests
python run_tests.py --ci            # CI-compatible (no GUI/slow tests)

# Options
python run_tests.py --parallel      # Parallel execution
python run_tests.py --failfast      # Stop on first failure
python run_tests.py --html          # Generate HTML coverage report
python run_tests.py --validate      # Validate test environment
```

### Using Pytest Directly

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_end_to_end.py

# Run specific test class
pytest tests/test_integration.py::TestAssetProductionIntegration

# Run specific test
pytest tests/test_end_to_end.py::TestCompleteConformWorkflow::test_simple_conform_workflow

# Run tests with marker
pytest -m smoke                     # Smoke tests
pytest -m integration               # Integration tests
pytest -m "not slow"                # Exclude slow tests
pytest -m "e2e and not gui"         # E2E tests without GUI

# Run with coverage
pytest --cov=src/conformity --cov-report=html

# Run in parallel (requires pytest-xdist)
pytest -n auto

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Show local variables in failures
pytest -l
```

## Test Types

### 1. Unit Tests

Test individual components in isolation.

**Characteristics:**
- Fast execution (<1s per test)
- No external dependencies
- Mock external services
- Focus on single function/method

**Location:** Marked with `@pytest.mark.unit`

**Example:**
```python
@pytest.mark.unit
def test_asset_database_add_asset(asset_db, temp_dir):
    """Test adding asset to database."""
    asset_id = asset_db.add_asset(
        file_path=temp_dir / "test.mov",
        asset_type=AssetType.VIDEO
    )
    assert asset_id > 0
```

### 2. Integration Tests

Test interactions between modules.

**Characteristics:**
- Test module boundaries
- Verify data flow between systems
- Test database interactions
- Typical execution: 1-5s per test

**Location:** `tests/test_integration.py`, marked with `@pytest.mark.integration`

**Example:**
```python
@pytest.mark.integration
def test_link_assets_to_shots(asset_db_with_data, production_tracker_with_data):
    """Test linking assets to production shots."""
    # Get shots and assets from both systems
    shots = production_tracker_with_data.db.list_shots()
    assets = asset_db_with_data.search_assets()

    # Link them
    asset_db_with_data.add_metadata(assets[0]['id'], {
        'shot_id': shots[0]['id']
    })

    # Verify link
    updated_asset = asset_db_with_data.get_asset(assets[0]['id'])
    assert updated_asset['metadata']['shot_id'] == shots[0]['id']
```

### 3. End-to-End Tests

Test complete workflows from start to finish.

**Characteristics:**
- Test realistic user scenarios
- Multiple system interactions
- Complete workflow validation
- Execution: 5-30s per test

**Location:** `tests/test_end_to_end.py`, marked with `@pytest.mark.e2e`

**Example:**
```python
@pytest.mark.e2e
def test_vfx_workflow_complete(asset_db, production_tracker, temp_dir):
    """
    Test complete VFX workflow:
    1. Create project and shots
    2. Link assets to shots
    3. Track through VFX pipeline
    4. Verify deliverables
    """
    # Create project
    project_id = production_tracker.create_project(...)

    # Add shot
    shot_id = production_tracker.add_shot(...)

    # Process through pipeline
    production_tracker.start_vfx(shot_id)
    production_tracker.submit_for_review(shot_id, Department.VFX)
    production_tracker.approve_shot(shot_id, Department.VFX, ...)

    # Verify
    shot = production_tracker.db.get_shot(shot_id)
    assert shot['vfx_status'] == 'approved'
```

### 4. Smoke Tests

Quick sanity checks for basic functionality.

**Characteristics:**
- Very fast (<10s total)
- Basic operations only
- Critical path validation
- Ideal for pre-commit hooks

**Location:** Marked with `@pytest.mark.smoke`

**Example:**
```python
@pytest.mark.smoke
def test_asset_database_basic(asset_db, temp_dir):
    """Basic asset database operations."""
    asset_id = asset_db.add_asset(temp_dir / "test.mov", AssetType.VIDEO)
    assert asset_id > 0

    asset = asset_db.get_asset(asset_id)
    assert asset is not None
```

## Writing Tests

### Test File Naming

- Test files: `test_*.py` or `*_test.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Using Fixtures

Conformity provides extensive pytest fixtures in `conftest.py`:

#### Database Fixtures

```python
def test_with_empty_database(asset_db):
    """Use empty in-memory asset database."""
    # asset_db is fresh AssetDatabase instance

def test_with_populated_database(asset_db_with_data):
    """Use database with sample data."""
    assets = asset_db_with_data.search_assets()
    assert len(assets) > 0

def test_with_production_tracker(production_tracker_with_data):
    """Use production tracker with demo project."""
    project_id = production_tracker_with_data.test_project_id
    stats = production_tracker_with_data.get_shot_progress(project_id)
```

#### Directory Fixtures

```python
def test_with_temp_directory(temp_dir):
    """Use temporary directory (auto-cleaned)."""
    test_file = temp_dir / "test.mov"
    test_file.touch()

def test_with_mock_project(mock_project_structure):
    """Use complete mock project structure."""
    # Directory tree with footage, renders, timelines, etc.
```

#### Data Fixtures

```python
def test_with_sample_data(sample_clip_data, sample_edl, sample_ocio_config):
    """Use pre-made sample data."""
    # sample_clip_data: List of clip dictionaries
    # sample_edl: EDL as string
    # sample_ocio_config: OCIO config as string
```

#### Integration Fixture

```python
def test_all_systems(integration_context):
    """Use all systems initialized and linked."""
    asset_db = integration_context['asset_db']
    tracker = integration_context['production_tracker']
    project_id = integration_context['project_id']
    temp_dir = integration_context['temp_dir']
```

### Mock Data Generators

Use mock data generators for creating test data:

```python
from tests.mock_data_generators import (
    TimelineGenerator,
    AssetDataGenerator,
    ProductionDataGenerator,
    EDLGenerator,
    OCIOConfigGenerator
)

def test_with_generated_timeline():
    """Generate timeline on the fly."""
    timeline = TimelineGenerator.generate_simple_timeline(num_clips=10)
    assert len(list(timeline.each_clip())) == 10

def test_with_generated_assets():
    """Generate asset data."""
    assets = AssetDataGenerator.generate_footage_library(num_clips=50)
    assert len(assets) == 50

def test_with_generated_edl():
    """Generate EDL."""
    edl = EDLGenerator.generate_simple_edl(num_events=20)
    assert "TITLE:" in edl
```

### Test Organization

Organize tests into classes for better structure:

```python
@pytest.mark.integration
class TestAssetProductionIntegration:
    """Test integration between Asset Tracker and Production Tracker."""

    def test_link_assets_to_shots(self, asset_db, production_tracker):
        """Test linking assets to shots."""
        pass

    def test_asset_status_affects_shot(self, asset_db, production_tracker):
        """Test asset approval affects shot readiness."""
        pass
```

### Assertions

Use clear, descriptive assertions:

```python
# Good
assert shot['vfx_status'] == 'approved', f"Expected approved, got {shot['vfx_status']}"
assert len(assets) > 0, "Should have at least one asset"

# Better with pytest's rich comparisons
assert shot['vfx_status'] == 'approved'  # Pytest shows both values on failure

# Even better with helper functions
def assert_shot_approved(shot):
    assert shot['vfx_status'] == 'approved', f"Shot {shot['shot_name']} not approved"
```

## Coverage Reports

### Generating Coverage

```bash
# Terminal report
python run_tests.py --coverage

# HTML report
python run_tests.py --coverage --html

# Open HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Configuration

Coverage is configured in `pytest.ini`:

```ini
[coverage:run]
source = src/conformity
omit =
    */tests/*
    */test_*.py
    */__pycache__/*

[coverage:report]
precision = 2
show_missing = True
```

### Coverage Goals

- **Overall**: >80% coverage
- **Core modules**: >90% coverage
- **UI components**: >60% coverage (GUI testing is harder)
- **Critical paths**: 100% coverage

### Interpreting Coverage

```
Name                                    Stmts   Miss  Cover   Missing
-------------------------------------------------------------------
src/conformity/asset_tracker.py          245     12    95%   34-45
src/conformity/production_tracker.py      310     31    90%   567-589, 601-612
-------------------------------------------------------------------
TOTAL                                    2847    234    92%
```

- **Stmts**: Total statements
- **Miss**: Uncovered statements
- **Cover**: Coverage percentage
- **Missing**: Line numbers not covered

## Demo Mode

### Running Demo Mode

```python
# Interactive demo
python -m conformity.demo.demo_mode

# Programmatic usage
from conformity.demo import DemoProject

# Create and setup demo
demo = DemoProject()
demo.setup()

# Use demo systems
assets = demo.get_all_assets()
shots = demo.get_all_shots()
stats = demo.get_project_stats()

# Print summary
demo.print_summary()

# Cleanup
demo.cleanup()
```

### Demo Project Contents

The demo project includes:

**Assets:**
- 5 video footage clips (ProRes 4444, 4K)
- 5 VFX render sequences (EXR, ACES)
- Various metadata and tags

**Production:**
- 1 feature film project
- 3 sequences (SEQ_010, SEQ_020, SEQ_030)
- 6 shots with various statuses
- 4 tasks in different stages
- 4 deliverables
- 4 team members

**Integrations:**
- Assets linked to shots
- Metadata connections
- Department progress tracking

### Using Demo in Tests

```python
def test_with_demo_project():
    """Test using demo project."""
    demo = DemoProject()
    demo.setup()

    try:
        # Your test code
        stats = demo.get_project_stats()
        assert stats['total_shots'] > 0

    finally:
        demo.cleanup()
```

## Continuous Integration

### GitHub Actions

Example workflow (`.github/workflows/tests.yml`):

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: python run_tests.py --ci

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Pre-commit Hooks

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: python run_tests.py --quick
        language: system
        pass_filenames: false
        always_run: true
```

## Troubleshooting

### Common Issues

**Issue: Tests fail with import errors**

```bash
# Solution: Install in development mode
pip install -e .
```

**Issue: Coverage report empty**

```bash
# Solution: Ensure source is specified
pytest --cov=src/conformity --cov-report=term

# Or check pytest.ini has correct paths
```

**Issue: Tests hang or timeout**

```bash
# Solution: Run without parallel execution
pytest tests/ --no-cov

# Or increase timeout
pytest tests/ --timeout=300
```

**Issue: Fixture not found**

```bash
# Solution: Ensure conftest.py is in tests/ directory
# and contains the fixture definition
```

**Issue: Mock data generators fail**

```bash
# Solution: Install optional dependencies
pip install opentimelineio
```

### Debug Mode

Run tests in debug mode:

```bash
# Verbose with local variables
pytest -vvl

# Drop into debugger on failure
pytest --pdb

# Show print statements
pytest -s

# Show warnings
pytest -W all
```

### Performance Profiling

Profile slow tests:

```bash
# Install pytest-profiling
pip install pytest-profiling

# Profile tests
pytest --profile

# Profile with svg output
pytest --profile-svg
```

## Best Practices

### 1. Test Independence

Each test should be independent and not rely on other tests:

```python
# Good
def test_create_asset(asset_db):
    asset_id = asset_db.add_asset(...)
    assert asset_id > 0

def test_update_asset(asset_db):
    asset_id = asset_db.add_asset(...)  # Create own data
    asset_db.update_asset_status(asset_id, ...)
    assert ...

# Bad
asset_id = None  # Global state

def test_create_asset(asset_db):
    global asset_id
    asset_id = asset_db.add_asset(...)

def test_update_asset(asset_db):
    asset_db.update_asset_status(asset_id, ...)  # Depends on previous test
```

### 2. Clear Test Names

Use descriptive test names:

```python
# Good
def test_asset_status_changes_from_pending_to_approved():
    pass

def test_shot_cannot_be_approved_without_vfx_review():
    pass

# Bad
def test_asset():
    pass

def test_stuff():
    pass
```

### 3. Arrange-Act-Assert

Structure tests clearly:

```python
def test_shot_approval_workflow():
    # Arrange
    shot_id = create_test_shot()

    # Act
    tracker.submit_for_review(shot_id, Department.VFX)
    tracker.approve_shot(shot_id, Department.VFX, "reviewer")

    # Assert
    shot = tracker.db.get_shot(shot_id)
    assert shot['vfx_status'] == 'approved'
```

### 4. Parametrize Similar Tests

Use parametrize for testing multiple inputs:

```python
@pytest.mark.parametrize("complexity,expected_hours", [
    (VFXComplexity.SIMPLE, 8),
    (VFXComplexity.MEDIUM, 24),
    (VFXComplexity.COMPLEX, 80),
])
def test_vfx_complexity_hours(complexity, expected_hours):
    hours = calculate_vfx_hours(complexity)
    assert hours == expected_hours
```

### 5. Use Fixtures for Common Setup

Extract common setup to fixtures:

```python
@pytest.fixture
def populated_shot():
    """Create shot with all departments set up."""
    tracker = ShotTracker()
    project_id = tracker.create_project(...)
    seq_id = tracker.add_sequence(...)
    shot_id = tracker.add_shot(...)
    return tracker, shot_id

def test_shot_workflow(populated_shot):
    tracker, shot_id = populated_shot
    # Test with pre-configured shot
```

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

For questions or issues with testing, please open an issue on GitHub.
