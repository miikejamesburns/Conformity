# Installation Troubleshooting

Common installation issues and solutions for Conformity.

## PyOpenColorIO Installation Issues

### Issue: "No matching distribution found for PyOpenColorIO"

**Error Message:**
```
ERROR: Could not find a version that satisfies the requirement PyOpenColorIO>=2.3.0
ERROR: No matching distribution found for PyOpenColorIO
```

**Why this happens:**
PyOpenColorIO doesn't provide pre-built wheels (binary packages) for all platforms, especially:
- Apple Silicon (ARM64) Macs
- Some Linux distributions
- Certain Python versions

**Solution Options:**

#### Option 1: Install Core Dependencies Only (Recommended for Getting Started)

PyOpenColorIO is **optional**. Conformity works without it:

```bash
# Install core dependencies (without PyOpenColorIO)
pip install -r requirements.txt

# PyOpenColorIO is already commented out in requirements.txt
# Core features will work fine
```

**What works without PyOpenColorIO:**
- ✅ Timeline management (OTIO)
- ✅ Asset tracking
- ✅ Production tracking
- ✅ Command interface
- ✅ UI components
- ✅ Demo mode

**What requires PyOpenColorIO:**
- ❌ OCIO color space transforms
- ❌ Color management features

#### Option 2: Build PyOpenColorIO from Source

For users who need color management features:

**macOS (with Homebrew):**
```bash
# Install OpenColorIO library first
brew install opencolorio

# Then install Python bindings
pip install PyOpenColorIO
```

**macOS (Apple Silicon specific):**
```bash
# If Homebrew install fails, try building from source
brew install cmake ninja

# Clone OpenColorIO
git clone https://github.com/AcademySoftwareFoundation/OpenColorIO.git
cd OpenColorIO

# Build with Python bindings
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release \
      -DOCIO_BUILD_PYTHON=ON \
      -DPython_EXECUTABLE=$(which python3) \
      ..

make -j8
make install
```

**Linux (Ubuntu/Debian):**
```bash
# Install OpenColorIO library
sudo apt-get update
sudo apt-get install libopencolorio-dev python3-opencolorio

# Or build from source
sudo apt-get install cmake ninja-build
git clone https://github.com/AcademySoftwareFoundation/OpenColorIO.git
cd OpenColorIO
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release -DOCIO_BUILD_PYTHON=ON ..
make -j$(nproc)
sudo make install
```

**Windows:**
```powershell
# Install Visual Studio Build Tools first
# Then use vcpkg or build from source

# Using vcpkg
vcpkg install opencolorio

# Set environment variables and pip install
pip install PyOpenColorIO
```

#### Option 3: Use Conda

Conda provides pre-built binaries:

```bash
# Create conda environment
conda create -n conformity python=3.11
conda activate conformity

# Install from conda-forge
conda install -c conda-forge opencolorio

# Install other requirements
pip install -r requirements.txt
```

#### Option 4: Skip Color Management for Now

You can always install PyOpenColorIO later:

```bash
# Install and use Conformity without color management
pip install -r requirements.txt

# Later, when you need color features:
# See requirements-optional.txt for detailed instructions
pip install PyOpenColorIO  # or follow build instructions above
```

### Verifying PyOpenColorIO Installation

Once installed, verify it works:

```python
# Test import
python -c "import PyOpenColorIO as ocio; print(f'OCIO version: {ocio.__version__}')"

# Should output something like:
# OCIO version: 2.3.0
```

## Other Common Issues

### Issue: Qt Platform Plugin Error

**Error:**
```
qt.qpa.plugin: Could not find the Qt platform plugin
```

**Solutions:**

**macOS:**
```bash
# Reinstall PyQt6
pip uninstall PyQt6 PyQt6-Qt6
pip install PyQt6
```

**Linux:**
```bash
# Install system Qt packages
sudo apt-get install python3-pyqt6 libqt6widgets6

# Or set Qt platform
export QT_QPA_PLATFORM=offscreen  # For headless environments
```

### Issue: ImportError for opentimelineio

**Error:**
```
ModuleNotFoundError: No module named 'opentimelineio'
```

**Solution:**
```bash
# Install in development mode
pip install -e .

# Or ensure package is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/conformity/src"
```

### Issue: SQLite Version Too Old

**Error:**
```
sqlite3.OperationalError: near "RETURNING": syntax error
```

**Solution:**
```bash
# macOS
brew install sqlite3
# Add to PATH

# Linux
sudo apt-get install sqlite3 libsqlite3-dev

# Verify version (need 3.35+)
python -c "import sqlite3; print(sqlite3.sqlite_version)"
```

### Issue: Permission Errors During Installation

**Error:**
```
PermissionError: [Errno 13] Permission denied
```

**Solutions:**

**Don't use sudo with pip!** Instead:

```bash
# Option 1: Use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows
pip install -r requirements.txt

# Option 2: User install
pip install --user -r requirements.txt
```

### Issue: Tests Fail to Run

**Error:**
```
ModuleNotFoundError: No module named 'pytest'
```

**Solution:**
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-xdist

# Or install from requirements
pip install -r requirements.txt
```

### Issue: Memory Error During Installation

**Error:**
```
MemoryError: Unable to allocate array
```

**Solution:**
```bash
# Install packages one at a time
pip install opentimelineio
pip install PyQt6
pip install PyYAML
# etc...

# Or increase pip cache size
pip install --no-cache-dir -r requirements.txt
```

## Platform-Specific Notes

### macOS Apple Silicon (M1/M2/M3)

Some packages may not have ARM64 wheels:

```bash
# Use Rosetta 2 if needed (not recommended)
arch -x86_64 pip install package_name

# Or wait for ARM64 wheels
# Most major packages now support ARM64
```

### Windows Subsystem for Linux (WSL)

GUI applications need X server:

```bash
# Install X server on Windows (e.g., VcXsrv)
# Then in WSL:
export DISPLAY=:0

# Or use headless mode for testing
pytest --no-gui
```

### Linux Server (Headless)

For servers without display:

```bash
# Install headless Qt
export QT_QPA_PLATFORM=offscreen

# Or skip GUI components in tests
pytest -m "not gui"
```

## Getting Help

If you're still having issues:

1. **Check Requirements**
   ```bash
   python --version  # Must be 3.11+
   pip --version
   ```

2. **Verify Installation**
   ```bash
   python setup_conformity.py --check
   ```

3. **Check Logs**
   ```bash
   pip install -r requirements.txt --verbose
   ```

4. **Review Documentation**
   - [Deployment Guide](../DEPLOYMENT_GUIDE.md)
   - [Architecture](ARCHITECTURE.md)
   - [Testing Guide](TESTING.md)

5. **Run Setup Script**
   ```bash
   python setup_conformity.py --install
   ```

6. **Report Issue**
   - Include: OS, Python version, error message
   - Include: Output of `pip list`
   - Include: Output of `python setup_conformity.py --check`

## Quick Start Without Optional Dependencies

To get started immediately without any optional dependencies:

```bash
# Clone repository
git clone https://github.com/yourusername/conformity.git
cd conformity

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install core dependencies only
pip install opentimelineio PyQt6 PyYAML pydantic pytest pytest-cov

# Install in development mode
pip install -e .

# Run tests
python run_tests.py --quick

# Run demo
python -m conformity.demo.demo_mode
```

This installs everything except:
- PyOpenColorIO (color management)
- pytest-xdist (parallel testing)
- black/flake8/mypy (development tools)

You can add these later as needed!

---

**Last Updated:** 2025-11-08
**Version:** 1.0.0
