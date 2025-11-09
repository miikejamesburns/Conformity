# Building Optional Dependencies

This guide covers building and installing PyOpenColorIO and tlRender from your forked repositories.

**Note:** These dependencies are **optional**. Conformity works without them, but they enable advanced features:
- **PyOpenColorIO**: Color management, LUTs, ACES workflows
- **tlRender**: Professional playback, hardware acceleration, image sequences

## Table of Contents

- [PyOpenColorIO](#pyopencolorio)
- [tlRender](#tlrender)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## PyOpenColorIO

PyOpenColorIO provides industry-standard color management through ACES/OpenColorIO.

### Prerequisites

#### macOS
```bash
# Install build tools
xcode-select --install

# Install dependencies via Homebrew
brew install cmake
brew install boost
brew install python@3.11
```

#### Linux (Ubuntu/Debian)
```bash
# Install build tools
sudo apt-get update
sudo apt-get install -y build-essential cmake git

# Install dependencies
sudo apt-get install -y \
    python3-dev \
    libboost-all-dev \
    libyaml-cpp-dev \
    libtinyxml-dev \
    libglew-dev
```

#### Windows
```powershell
# Install Visual Studio 2022 with C++ tools
# Install CMake from https://cmake.org/download/

# Install vcpkg for dependencies
git clone https://github.com/microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat
.\vcpkg integrate install
```

### Building from Your Fork

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/OpenColorIO.git
cd OpenColorIO

# Create build directory
mkdir build
cd build

# Configure (adjust Python version as needed)
cmake -DCMAKE_BUILD_TYPE=Release \
      -DOCIO_BUILD_PYTHON=ON \
      -DPYTHON_EXECUTABLE=$(which python3) \
      ..

# Build (use -j to parallelize)
make -j$(nproc)  # Linux/macOS
# OR on Windows:
# cmake --build . --config Release

# Install
sudo make install  # Linux/macOS
# OR on Windows (run as Administrator):
# cmake --install . --config Release
```

### Installing Python Bindings

After building:

```bash
# Navigate to Python bindings
cd build/src/bindings/python

# Install in development mode (recommended for testing)
pip install -e .

# OR install normally
pip install .
```

### Verify Installation

```bash
python3 -c "import PyOpenColorIO as ocio; print(f'OCIO version: {ocio.__version__}')"
```

### Configuration

Set the `OCIO` environment variable to point to your config:

```bash
# Example: Using ACES config
export OCIO=/path/to/OpenColorIO-Configs/aces_1.2/config.ocio

# Add to your shell profile for persistence
echo 'export OCIO=/path/to/config.ocio' >> ~/.bashrc  # or ~/.zshrc
```

**Download OCIO Configs:**
```bash
git clone https://github.com/colour-science/OpenColorIO-Configs.git
```

---

## tlRender

tlRender provides professional-grade video playback with hardware acceleration.

### Prerequisites

#### macOS
```bash
# Install dependencies
brew install cmake
brew install ffmpeg
brew install openal-soft
brew install freetype
brew install glfw
brew install nlohmann-json
```

#### Linux (Ubuntu/Debian)
```bash
# Install build tools
sudo apt-get update
sudo apt-get install -y build-essential cmake git

# Install dependencies
sudo apt-get install -y \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libopenal-dev \
    libfreetype6-dev \
    libglfw3-dev \
    libglew-dev \
    nlohmann-json3-dev \
    zlib1g-dev
```

#### Windows
Install dependencies via vcpkg:
```powershell
cd vcpkg
.\vcpkg install ffmpeg:x64-windows
.\vcpkg install openal-soft:x64-windows
.\vcpkg install freetype:x64-windows
.\vcpkg install glfw3:x64-windows
.\vcpkg install glew:x64-windows
.\vcpkg install nlohmann-json:x64-windows
```

### Building from Your Fork

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/tlRender.git
cd tlRender

# Create build directory
mkdir build
cd build

# Configure
cmake -DCMAKE_BUILD_TYPE=Release \
      -DTLRENDER_PYTHON=ON \
      -DPYTHON_EXECUTABLE=$(which python3) \
      ..

# Build
make -j$(nproc)  # Linux/macOS
# OR on Windows:
# cmake --build . --config Release

# Install
sudo make install  # Linux/macOS
# OR on Windows (as Administrator):
# cmake --install . --config Release
```

### Installing Python Bindings

```bash
# If tlRender built Python bindings
cd build/python

# Install
pip install -e .  # Development mode
# OR
pip install .
```

**Note:** As of 2024, tlRender's Python bindings may still be in development. Check the repository's Python documentation.

### Verify Installation

```bash
python3 -c "import tlRender as tlr; print('tlRender imported successfully')"
```

---

## Verification

After building both libraries, check their status in Conformity:

```bash
cd /path/to/Conformity

# Check dependency status
python3 -m conformity.core.dependencies

# Expected output:
# ======================================================================
# CONFORMITY DEPENDENCY STATUS
# ======================================================================
#
# Core Dependencies:
# ----------------------------------------------------------------------
#   ✓ opentimelineio         (v0.16.0)
#
# Optional Dependencies:
# ----------------------------------------------------------------------
#   ✓ PyOpenColorIO          (v2.3.0)
#       Features: Color management, LUT application, ACES workflows
#   ✓ tlRender               (v1.0.0)
#       Features: Professional playback, Hardware acceleration, ...
# ======================================================================
```

Or within Python:

```python
from conformity.core.dependencies import DependencyChecker

DependencyChecker.print_dependency_report()
```

---

## Integration with Conformity

Once built and installed, Conformity will automatically detect and use these libraries:

### PyOpenColorIO
```python
from conformity.color_manager.ocio_manager import OCIOManager

# Will work if PyOpenColorIO is installed
ocio_mgr = OCIOManager()
ocio_mgr.load_config(Path("config.ocio"))
color_spaces = ocio_mgr.get_color_spaces()
```

### tlRender
```python
from conformity.playback.tlrender_engine import TLRenderEngine

# Will work if tlRender is installed
player = TLRenderEngine()
player.load_timeline(Path("timeline.otio"))
player.play()
```

---

## Troubleshooting

### PyOpenColorIO Build Issues

**Problem:** CMake can't find Python
```bash
# Specify Python explicitly
cmake -DPYTHON_EXECUTABLE=/usr/bin/python3.11 ..
```

**Problem:** Missing dependencies on macOS
```bash
# Make sure pkg-config can find libraries
export PKG_CONFIG_PATH="/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH"
```

**Problem:** ImportError after installation
```bash
# Check library path
export DYLD_LIBRARY_PATH=/usr/local/lib:$DYLD_LIBRARY_PATH  # macOS
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH      # Linux

# Or reinstall in site-packages
cd build/src/bindings/python
pip install --force-reinstall .
```

### tlRender Build Issues

**Problem:** FFmpeg not found
```bash
# macOS
brew install ffmpeg
export PKG_CONFIG_PATH="/usr/local/opt/ffmpeg/lib/pkgconfig:$PKG_CONFIG_PATH"

# Linux
sudo apt-get install libavcodec-dev libavformat-dev libavutil-dev
```

**Problem:** OpenGL/GLEW issues
```bash
# macOS
brew install glew glfw

# Linux
sudo apt-get install libglew-dev libglfw3-dev
```

**Problem:** Python bindings not building
```bash
# Check CMake output for TLRENDER_PYTHON option
cmake .. -DTLRENDER_PYTHON=ON

# If Python bindings aren't available yet, check tlRender docs
# The C++ library can still be used through ctypes if needed
```

### General Issues

**Check build logs:**
```bash
# Verbose build
cmake --build . --verbose

# Check for linking errors
ldd /usr/local/lib/libOpenColorIO.so  # Linux
otool -L /usr/local/lib/libOpenColorIO.dylib  # macOS
```

**Python import issues:**
```bash
# Check where Python looks for modules
python3 -c "import sys; print('\n'.join(sys.path))"

# Install with user flag if permission issues
pip install --user .
```

**Still having issues?**

1. Check the build logs carefully
2. Ensure all dependencies are installed
3. Try a clean build:
   ```bash
   rm -rf build
   mkdir build
   cd build
   cmake ..
   ```
4. Check the official repositories for known issues:
   - https://github.com/AcademySoftwareFoundation/OpenColorIO/issues
   - https://github.com/darbyjohnston/tlRender/issues

---

## Alternative: Pre-built Packages

If building from source is problematic, some alternatives:

### PyOpenColorIO

**Conda** (easiest):
```bash
conda install -c conda-forge opencolorio
```

**System packages:**
```bash
# macOS
brew install opencolorio
pip install PyOpenColorIO

# Linux (may be outdated)
sudo apt-get install libopencolorio-dev
pip install PyOpenColorIO
```

### tlRender

Currently, tlRender primarily requires building from source. Check the repository for updates on binary distributions.

---

## Next Steps

After successfully building and installing:

1. ✅ Verify dependencies: `python3 -m conformity.core.dependencies`
2. ✅ Try color workflows: See `docs/COLOR_WORKFLOWS.md`
3. ✅ Test playback: See `docs/TLRENDER.md`
4. ✅ Run examples: `python examples/tlrender_example.py`

For more information:
- Color Management: `docs/COLOR_WORKFLOWS.md`
- tlRender Playback: `docs/TLRENDER.md`
- Production Pipeline: `docs/DEPLOYMENT_GUIDE.md`
