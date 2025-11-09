# Installation Troubleshooting

Common installation issues and solutions for Conformity.

## 🐧 Ubuntu/Debian Users - Start Here!

**If you're on Ubuntu/Debian**, we have a **comprehensive dedicated guide** and **automated installation scripts**:

👉 **[Ubuntu Installation Guide](UBUNTU_INSTALLATION.md)** - Complete step-by-step instructions

### Quick Start (Ubuntu):

```bash
# Automated installation (recommended)
cd /path/to/Conformity
./scripts/install_opencolorio_ubuntu.sh

# Or just install dependencies
./scripts/setup_ubuntu_dependencies.sh
```

The automated scripts handle all the complexity for you. Continue reading below for manual installation or if you encounter issues.

---

## PyOpenColorIO Installation (Required)

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

**This is expected** - PyOpenColorIO is a required dependency that typically requires building from source.

### Solution: Build PyOpenColorIO from Source

**Important:** PyOpenColorIO is **required** for Conformity's color management pipeline. Follow the platform-specific instructions below:

#### Option 1: Build PyOpenColorIO from Source (Standard Method)

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

⚠️ **The commands below are INCOMPLETE and will fail!** See [Ubuntu Installation Guide](UBUNTU_INSTALLATION.md) for the complete solution.

**Quick automated install:**
```bash
cd /path/to/Conformity
./scripts/install_opencolorio_ubuntu.sh
```

**Or manual install with ALL required dependencies:**
```bash
# Install build tools
sudo apt-get update
sudo apt-get install -y build-essential cmake ninja-build git pkg-config

# Install Python development packages (CRITICAL!)
sudo apt-get install -y python3-dev python3-pip

# Install OpenColorIO dependencies (ALL required!)
sudo apt-get install -y \
    libboost-all-dev \
    libyaml-cpp-dev \
    libtinyxml-dev \
    libglew-dev \
    zlib1g-dev

# Now build from source
git clone --depth 1 --branch v2.3.2 https://github.com/AcademySoftwareFoundation/OpenColorIO.git
cd OpenColorIO
mkdir build && cd build
cmake -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DOCIO_BUILD_PYTHON=ON \
    -DPYTHON_EXECUTABLE=$(which python3) \
    ..
ninja -j$(nproc)
sudo ninja install
sudo ldconfig
```

**Common missing dependencies that cause build failures:**
- `build-essential` - C/C++ compiler
- `python3-dev` - Python headers (most common cause of failure!)
- `libboost-all-dev` - Boost C++ libraries
- `libyaml-cpp-dev` - YAML parsing
- `libtinyxml-dev` - XML parsing
- `libglew-dev` - OpenGL libraries

See [Ubuntu Installation Guide](UBUNTU_INSTALLATION.md) for detailed explanations and troubleshooting.

**Windows:**
```powershell
# Install Visual Studio Build Tools first
# Then use vcpkg or build from source

# Using vcpkg
vcpkg install opencolorio

# Set environment variables and pip install
pip install PyOpenColorIO
```

#### Option 3: Use Conda (Alternative)

Conda provides pre-built binaries which may work on some platforms:

```bash
# Create conda environment
conda create -n conformity python=3.11
conda activate conformity

# Install from conda-forge
conda install -c conda-forge opencolorio

# Install other requirements
pip install -r requirements.txt
```

**Note:** If conda installation succeeds, this is the easiest method. However, building from source is more reliable and gives you the latest version.

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

## Quick Start for Development

To get started with development quickly:

```bash
# Clone repository
git clone https://github.com/yourusername/conformity.git
cd conformity

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install PyOpenColorIO first (required - see instructions above)
# For macOS:
brew install opencolorio
pip install PyOpenColorIO

# Install remaining dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Run tests
python run_tests.py --quick

# Run demo
python -m conformity.demo.demo_mode
```

**Optional development tools** (not required for basic usage):
- pytest-xdist (parallel testing)
- black/flake8/mypy (code quality tools)

These can be installed later as needed from requirements.txt.

---

**Last Updated:** 2025-11-08
**Version:** 1.0.0
