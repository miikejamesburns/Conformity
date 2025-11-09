# Quick Fix: Ubuntu OpenColorIO Build Errors

**Getting errors when building OpenColorIO on Ubuntu?** This is the quick fix guide.

## TL;DR - The Fast Fix

Run this automated script:

```bash
cd /path/to/Conformity
./scripts/install_opencolorio_ubuntu.sh
```

That's it! The script handles everything. Go grab coffee ☕ for 10-15 minutes.

---

## What Went Wrong?

The commands you found online are **missing critical dependencies**:

### ❌ What Doesn't Work:

```bash
sudo apt-get install cmake ninja-build  # INCOMPLETE!
git clone https://github.com/AcademySoftwareFoundation/OpenColorIO.git
cd OpenColorIO
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release -DOCIO_BUILD_PYTHON=ON ..
make -j$(nproc)
sudo make install
```

### ✅ What You Actually Need:

```bash
# Install build tools
sudo apt-get install -y build-essential cmake ninja-build git pkg-config

# Install Python development (CRITICAL!)
sudo apt-get install -y python3-dev python3-pip

# Install ALL OpenColorIO dependencies
sudo apt-get install -y \
    libboost-all-dev \
    libyaml-cpp-dev \
    libtinyxml-dev \
    libglew-dev \
    zlib1g-dev

# Now build properly
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

---

## Common Errors and Quick Fixes

### Error: "GLIBCXX_3.4.32 not found" (OpenTimelineIO)

**Symptom:** Tests fail with `ImportError: version 'GLIBCXX_3.4.32' not found`

**Root Cause:** You're using a virtual environment based on miniconda/anaconda Python 3.13, and the pre-built OTIO wheel is linking to miniconda's older libstdc++.

**Fix Option 1 - Build OTIO from Source (Recommended):**
```bash
cd /path/to/Conformity
source venv/bin/activate  # Activate your venv
./scripts/install_opentimelineio_ubuntu.sh
```

**Fix Option 2 - Set Library Path:**
```bash
# Add to your shell profile or run before tests
source scripts/setup_ubuntu_environment.sh
```

**Fix Option 3 - Use System Python:**
```bash
# Recreate venv with system Python instead of miniconda
deactivate
rm -rf venv
python3 -m venv venv  # Use system Python 3.11
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "Python.h: No such file or directory"

**Missing:** `python3-dev`

**Fix:**
```bash
sudo apt-get install python3-dev
```

### Error: "Could not find Boost"

**Missing:** `libboost-all-dev`

**Fix:**
```bash
sudo apt-get install libboost-all-dev
```

### Error: "yaml-cpp not found"

**Missing:** `libyaml-cpp-dev`

**Fix:**
```bash
sudo apt-get install libyaml-cpp-dev
```

### Error: "undefined reference to symbol"

**Missing:** `build-essential` (gcc/g++)

**Fix:**
```bash
sudo apt-get install build-essential
```

### Error: "libOpenColorIO.so.2.3: cannot open shared object file"

**Missing:** Library cache update

**Fix:**
```bash
sudo ldconfig
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
```

---

## Why It's Confusing

The official OpenColorIO docs assume you know about these dependencies. Most Ubuntu tutorials online are incomplete. This is frustrating!

**The missing pieces:**
- `build-essential` - You need a C++ compiler!
- `python3-dev` - Required for Python bindings (not just python3!)
- `libboost-all-dev` - OCIO depends on Boost
- `libyaml-cpp-dev` - OCIO configs use YAML
- `libtinyxml-dev` - XML parsing library
- `libglew-dev` - OpenGL support

---

## Just Make It Work!

### Option 1: Fully Automated (Recommended)

```bash
cd /path/to/Conformity
./scripts/install_opencolorio_ubuntu.sh
```

Sit back and relax. The script:
- ✅ Installs ALL dependencies
- ✅ Downloads OpenColorIO v2.3.2
- ✅ Builds with correct settings
- ✅ Installs everything properly
- ✅ Verifies it works

### Option 2: Dependencies Only

If you want to build manually:

```bash
cd /path/to/Conformity
./scripts/setup_ubuntu_dependencies.sh
```

Then build OpenColorIO yourself following the on-screen instructions.

### Option 3: Try pip First (Easy!)

Sometimes this just works:

```bash
pip install opencolorio>=2.3.0
```

If it works, you're done! If not, use Option 1.

---

## Verify It Works

After installation:

```bash
# Test PyOpenColorIO import
python3 -c "import PyOpenColorIO as ocio; print(f'✓ OCIO {ocio.__version__}')"

# Should output: ✓ OCIO 2.3.2 (or similar)
```

If you see the version number, **you're good!** 🎉

---

## Still Having Issues?

1. **Check the build log** - Read the error message carefully
2. **Run diagnostics:**
   ```bash
   python3 -m conformity.core.dependencies
   ```
3. **Read the full guides:**
   - [Ubuntu Installation Guide](UBUNTU_INSTALLATION.md) - Comprehensive
   - [Installation Troubleshooting](INSTALLATION_TROUBLESHOOTING.md) - Common issues
   - [Building Optional Dependencies](BUILDING_OPTIONAL_DEPS.md) - Advanced

4. **Check versions:**
   ```bash
   lsb_release -a     # Ubuntu version
   python3 --version  # Python version
   cmake --version    # CMake version
   gcc --version      # Compiler version
   ```

5. **Clean build and retry:**
   ```bash
   rm -rf /tmp/OpenColorIO
   ./scripts/install_opencolorio_ubuntu.sh
   ```

---

## What About Other Platforms?

### macOS
```bash
brew install opencolorio
pip install PyOpenColorIO
```

### Windows
See [Building Optional Dependencies](BUILDING_OPTIONAL_DEPS.md#windows)

### Other Linux Distros
- **Fedora/RHEL:** Replace `apt-get` with `dnf`, packages have similar names
- **Arch:** `pacman -S opencolorio` (might work!)
- **Conda (any platform):** `conda install -c conda-forge opencolorio`

---

## Next Steps

Once OpenColorIO is installed:

```bash
cd /path/to/Conformity

# Install Conformity
pip install -r requirements.txt
pip install -e .

# Verify everything
python3 -m conformity.core.dependencies

# Run tests
python3 run_tests.py --quick

# Try a demo
python3 -m conformity.demo.demo_mode
```

---

**Last Updated:** 2025-11-09
**Tested On:** Ubuntu 22.04 LTS, 24.04 LTS
**OpenColorIO:** v2.3.2
