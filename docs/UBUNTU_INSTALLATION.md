# Ubuntu Installation Guide

Complete installation guide for Conformity on Ubuntu/Debian systems.

## Table of Contents

- [Quick Install (Automated)](#quick-install-automated)
- [Manual Installation](#manual-installation)
- [Common Issues](#common-issues)
- [Verification](#verification)
- [Next Steps](#next-steps)

---

## Quick Install (Automated)

### Option 1: Full Automated Installation

This script installs all dependencies, builds OpenColorIO, and sets everything up:

```bash
cd /path/to/Conformity
./scripts/install_opencolorio_ubuntu.sh
```

This will:
- Install all required system dependencies
- Clone and build OpenColorIO v2.3.2
- Install PyOpenColorIO Python bindings
- Verify the installation

**Time:** ~10-15 minutes depending on your system

### Option 2: Dependencies Only

If you want to install dependencies manually but let the script handle system packages:

```bash
cd /path/to/Conformity
./scripts/setup_ubuntu_dependencies.sh
```

Then follow the [Manual Installation](#manual-installation) steps below.

---

## Manual Installation

### Step 1: Install System Dependencies

```bash
# Update package lists
sudo apt-get update

# Install build tools
sudo apt-get install -y \
    build-essential \
    cmake \
    ninja-build \
    git \
    pkg-config

# Install Python development packages
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    python3-venv

# Install OpenColorIO dependencies
sudo apt-get install -y \
    libboost-all-dev \
    libyaml-cpp-dev \
    libtinyxml-dev \
    libglew-dev \
    zlib1g-dev
```

**Why these packages?**
- `build-essential`: C/C++ compiler (gcc, g++, make)
- `cmake` & `ninja-build`: Build system tools
- `python3-dev`: Python headers needed for C++ Python bindings
- `libboost-all-dev`: Boost C++ libraries (required by OCIO)
- `libyaml-cpp-dev`: YAML configuration file parsing
- `libtinyxml-dev`: XML parsing
- `libglew-dev`: OpenGL Extension Wrangler (for GPU support)

### Step 2: Create Virtual Environment (Recommended)

```bash
cd /path/to/Conformity

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Step 3: Build OpenColorIO from Source

OpenColorIO needs to be built from source on Ubuntu to get Python bindings:

```bash
# Navigate to temporary build location
cd /tmp

# Clone OpenColorIO
git clone --depth 1 --branch v2.3.2 https://github.com/AcademySoftwareFoundation/OpenColorIO.git
cd OpenColorIO

# Create build directory
mkdir build
cd build

# Configure with CMake
cmake -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DOCIO_BUILD_PYTHON=ON \
    -DPYTHON_EXECUTABLE=$(which python3) \
    -DOCIO_BUILD_APPS=OFF \
    -DOCIO_BUILD_TESTS=OFF \
    -DOCIO_BUILD_GPU_TESTS=OFF \
    -DOCIO_WARNING_AS_ERROR=OFF \
    ..

# Build (using all CPU cores)
ninja -j$(nproc)

# Install
sudo ninja install

# Update library cache
sudo ldconfig
```

**Build flags explained:**
- `-DCMAKE_BUILD_TYPE=Release`: Optimized build
- `-DOCIO_BUILD_PYTHON=ON`: **Critical** - enables Python bindings
- `-DPYTHON_EXECUTABLE=$(which python3)`: Ensures correct Python version
- `-DOCIO_BUILD_APPS=OFF`: Skip building command-line tools (optional)
- `-DOCIO_BUILD_TESTS=OFF`: Skip building tests to save time

### Step 4: Install PyOpenColorIO

Try installing from PyPI first (easiest):

```bash
pip install PyOpenColorIO>=2.3.0
```

If that fails, install from the build you just created:

```bash
cd /tmp/OpenColorIO/build
pip install .
```

### Step 5: Install Conformity

```bash
cd /path/to/Conformity

# Install core dependencies
pip install -r requirements.txt

# Or install with full optional dependencies
pip install -r requirements-full.txt

# Install in development mode (recommended for development)
pip install -e .
```

### Step 6: Verify Installation

```bash
# Check PyOpenColorIO
python3 -c "import PyOpenColorIO as ocio; print(f'OCIO version: {ocio.__version__}')"

# Check all Conformity dependencies
python3 -m conformity.core.dependencies

# Run a quick test
python3 run_tests.py --quick
```

---

## Additional Optional Dependencies

### OpenTimelineIO (Required - Core Dependency)

OpenTimelineIO is installed via pip in requirements.txt. However, if you're using conda/miniconda Python, you may encounter GLIBCXX library errors. Build from source instead:

```bash
cd /path/to/Conformity
source venv/bin/activate
./scripts/install_opentimelineio_ubuntu.sh
```

### OpenImageIO (Optional - Image Sequence Support)

For professional image format support (EXR, DPX, TIFF):

```bash
cd /path/to/Conformity
source venv/bin/activate
./scripts/install_openimageio_ubuntu.sh
```

This provides support for:
- OpenEXR (.exr) - VFX standard, high dynamic range
- DPX (.dpx) - Film and cinema workflows
- TIFF, PNG, JPEG - Standard image formats

---

## Special Considerations for conda/miniconda Users

**⚠️ Important:** If you have conda or miniconda installed, you may encounter GLIBCXX_3.4.32 library version conflicts.

### Recommended Solution: Use System Python

The best approach is to create your virtual environment with system Python instead of conda's Python:

```bash
cd /path/to/Conformity

# Use the automated script:
./scripts/create_system_venv.sh

# Then install dependencies:
source venv/bin/activate
pip install -r requirements.txt
./scripts/install_opentimelineio_ubuntu.sh
```

### Alternative: Fix Library Paths

If you prefer to keep using conda Python, set up the environment before each session:

```bash
source venv/bin/activate
source scripts/setup_ubuntu_environment.sh
```

Or add to your `~/.bashrc` for a permanent fix:
```bash
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
```

### Why This Happens

Conda Python 3.13 ships with an older libstdc++ that lacks GLIBCXX_3.4.32, which is required by pre-built wheels for OTIO and system packages like OpenImageIO. System Python 3.11 uses the system's libstdc++ which has all required versions.

See [Quick Fix Guide](QUICK_FIX_UBUNTU.md) for detailed troubleshooting.

---

## Common Issues

### Issue 1: "python3-dev not found" or "Python.h not found"

**Error:**
```
fatal error: Python.h: No such file or directory
```

**Solution:**
```bash
sudo apt-get install python3-dev
# Or for specific version:
sudo apt-get install python3.11-dev
```

### Issue 2: "yaml-cpp not found"

**Error:**
```
CMake Error: Could not find a package configuration file provided by "yaml-cpp"
```

**Solution:**
```bash
sudo apt-get install libyaml-cpp-dev
```

### Issue 3: Boost libraries not found

**Error:**
```
CMake Error: Could not find Boost
```

**Solution:**
```bash
sudo apt-get install libboost-all-dev
```

### Issue 4: "ImportError: libOpenColorIO.so.2.3 cannot open shared object file"

**Error:**
```python
ImportError: libOpenColorIO.so.2.3: cannot open shared object file: No such file or directory
```

**Solution:**
```bash
# Update library cache
sudo ldconfig

# If still not working, add to library path
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# Make permanent by adding to ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

### Issue 5: CMake can't find Python

**Error:**
```
Could NOT find Python (missing: Python_LIBRARIES Development Development.Module Development.Embed)
```

**Solution:**
```bash
# Install Python development packages
sudo apt-get install python3-dev

# Explicitly specify Python in cmake
cmake -DPYTHON_EXECUTABLE=/usr/bin/python3 \
      -DPython3_EXECUTABLE=/usr/bin/python3 \
      ...
```

### Issue 6: GLIBCXX_3.4.32 not found (conda/miniconda users)

**Error:**
```python
ImportError: /home/user/miniconda3/lib/libstdc++.so.6: version `GLIBCXX_3.4.32' not found
```

**Root Cause:** Using conda/miniconda Python with packages that require newer libstdc++.

**Solution:**
```bash
# Best solution: Recreate venv with system Python
./scripts/create_system_venv.sh
source venv/bin/activate
pip install -r requirements.txt

# Or: Set library path before running
source scripts/setup_ubuntu_environment.sh
```

See [Special Considerations for conda/miniconda Users](#special-considerations-for-condaminiconda-users) above.

### Issue 7: Ninja build system not found

**Error:**
```
CMake Error: CMake was unable to find a build program corresponding to "Ninja"
```

**Solution:**
```bash
sudo apt-get install ninja-build

# Or use make instead:
cmake -DCMAKE_BUILD_TYPE=Release ...  # (without -G Ninja)
make -j$(nproc)
```

### Issue 8: Out of memory during build

**Error:**
```
c++: fatal error: Killed signal terminated program cc1plus
```

**Solution:**
```bash
# Build with fewer parallel jobs
ninja -j2  # Instead of -j$(nproc)

# Or use make with limited jobs
make -j2
```

---

## Verification

After installation, verify everything works:

### 1. Check PyOpenColorIO

```bash
python3 << EOF
import PyOpenColorIO as ocio
print(f"OCIO version: {ocio.__version__}")
print(f"OCIO location: {ocio.__file__}")

# List available configs
config = ocio.GetCurrentConfig()
print(f"Color spaces: {config.getNumColorSpaces()}")
EOF
```

### 2. Check Conformity Dependencies

```bash
cd /path/to/Conformity
python3 -m conformity.core.dependencies
```

Expected output:
```
======================================================================
CONFORMITY DEPENDENCY STATUS
======================================================================

Core Dependencies:
----------------------------------------------------------------------
  ✓ opentimelineio         (v0.16.0)

Optional Dependencies:
----------------------------------------------------------------------
  ✓ PyOpenColorIO          (v2.3.2)
      Features: Color management, LUT application, ACES workflows
======================================================================
```

### 3. Run Tests

```bash
# Quick test suite
python3 run_tests.py --quick

# Full test suite
pytest tests/

# Test specific module
pytest tests/test_color_manager.py -v
```

### 4. Try a Demo

```bash
# Run the conform demo
python3 -m conformity.demo.demo_mode

# Or try an example
python3 examples/conform_example.py
```

---

## Next Steps

### 1. Download OCIO Configs (Optional)

For professional color management workflows:

```bash
# Download ACES configs
cd ~/Documents
git clone https://github.com/colour-science/OpenColorIO-Configs.git

# Set OCIO environment variable
export OCIO=~/Documents/OpenColorIO-Configs/aces_1.2/config.ocio

# Make permanent
echo 'export OCIO=~/Documents/OpenColorIO-Configs/aces_1.2/config.ocio' >> ~/.bashrc
```

### 2. Install Additional Optional Dependencies

For full professional features:

```bash
# NumPy for numerical operations
pip install numpy>=1.24.0

# PyAV for advanced video format support
pip install av>=10.0.0

# For image sequence support
pip install pillow
```

### 3. Set Up Your Project

```bash
cd /path/to/Conformity

# Run the setup script
python3 setup_conformity.py --check
python3 setup_conformity.py --install

# Configure for your workflow
cp config/default_config.yaml config/my_project_config.yaml
# Edit my_project_config.yaml as needed
```

### 4. Read the Documentation

- [Quick Start Guide](QUICKSTART.md)
- [Color Workflows](COLOR_WORKFLOWS.md)
- [EDL Workflows](EDL_WORKFLOWS.md)
- [Timeline Editing](TIMELINE_EDITING.md)
- [Production Tracker](PRODUCTION_TRACKER.md)

### 5. Try the Examples

```bash
cd examples

# Basic conform workflow
python3 conform_example.py

# Color management
python3 color_workflow_example.py

# Asset tracking
python3 asset_tracking_example.py
```

---

## Ubuntu-Specific Notes

### Ubuntu 22.04 LTS (Recommended)

Fully tested and supported. All dependencies available in standard repos.

### Ubuntu 20.04 LTS

Should work but some packages may be older versions. You may need to:

```bash
# Add newer CMake if needed
sudo apt-get install software-properties-common
sudo add-apt-repository ppa:ubuntu-toolchain-r/test
sudo apt-get update
```

### Ubuntu 24.04 LTS

Latest version, fully supported. All dependencies are current.

### WSL (Windows Subsystem for Linux)

Conformity works on WSL, but GUI features require X server:

```bash
# Install X server on Windows (e.g., VcXsrv, X410)

# In WSL, set display
export DISPLAY=:0

# Or use headless mode for CLI operations
export QT_QPA_PLATFORM=offscreen
```

---

## Performance Tips

### 1. Use Ninja for Faster Builds

Ninja is typically faster than Make:

```bash
sudo apt-get install ninja-build
cmake -G Ninja ...
ninja -j$(nproc)
```

### 2. Use ccache for Repeated Builds

If you're developing/building frequently:

```bash
sudo apt-get install ccache
export PATH="/usr/lib/ccache:$PATH"
```

### 3. Optimize for Your CPU

For maximum performance:

```bash
cmake -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_CXX_FLAGS="-march=native -O3" \
      ...
```

---

## Getting Help

If you encounter issues not covered here:

1. **Check the logs:**
   ```bash
   # CMake configuration log
   cat /tmp/OpenColorIO/build/CMakeFiles/CMakeOutput.log

   # Build errors
   ninja -v  # Verbose output
   ```

2. **Run diagnostics:**
   ```bash
   python3 setup_conformity.py --check
   python3 -m conformity.core.dependencies
   ```

3. **Check system info:**
   ```bash
   lsb_release -a  # Ubuntu version
   python3 --version  # Python version
   cmake --version  # CMake version
   gcc --version  # Compiler version
   ```

4. **Review documentation:**
   - [Installation Troubleshooting](INSTALLATION_TROUBLESHOOTING.md)
   - [Building Optional Dependencies](BUILDING_OPTIONAL_DEPS.md)

5. **Search for similar issues:**
   - [OpenColorIO Issues](https://github.com/AcademySoftwareFoundation/OpenColorIO/issues)
   - [Conformity Issues](https://github.com/yourusername/conformity/issues)

---

**Last Updated:** 2025-11-09
**Tested On:** Ubuntu 22.04 LTS, 24.04 LTS
**OpenColorIO Version:** 2.3.2
