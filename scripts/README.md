# Installation Scripts

Automated installation scripts for Conformity dependencies.

## Ubuntu/Debian Scripts

### `install_opencolorio_ubuntu.sh`

**Complete automated installation** of OpenColorIO with Python bindings.

**What it does:**
1. Installs all required system dependencies
2. Clones OpenColorIO v2.3.2 from source
3. Builds with CMake/Ninja
4. Installs OpenColorIO system-wide
5. Installs PyOpenColorIO Python package
6. Verifies installation

**Usage:**
```bash
cd /path/to/Conformity
./scripts/install_opencolorio_ubuntu.sh
```

**Time:** ~10-15 minutes

**Requirements:**
- Ubuntu/Debian Linux
- sudo access
- Internet connection

---

### `setup_ubuntu_dependencies.sh`

**Dependency-only installation** - installs system packages without building OpenColorIO.

**What it does:**
1. Updates package lists
2. Installs build tools (cmake, ninja, gcc, etc.)
3. Installs Python development packages
4. Installs OpenColorIO build dependencies
5. Displays next steps for manual build

**Usage:**
```bash
cd /path/to/Conformity
./scripts/setup_ubuntu_dependencies.sh
```

**Time:** ~2-3 minutes

**Use this if:**
- You want to build OpenColorIO manually
- You're debugging build issues
- You want more control over the build process

---

### `install_opentimelineio_ubuntu.sh`

**Build OpenTimelineIO from source** - fixes GLIBCXX version conflicts with miniconda/anaconda.

**What it does:**
1. Installs build dependencies (build-essential, cmake, pybind11-dev)
2. Clones OpenTimelineIO v0.16.0 from source
3. Builds with system compiler (avoids library version conflicts)
4. Installs into current Python environment
5. Verifies installation and adapters

**Usage:**
```bash
cd /path/to/Conformity
source venv/bin/activate  # Activate your virtual environment
./scripts/install_opentimelineio_ubuntu.sh
```

**Time:** ~5-10 minutes

**Use this if:**
- ✅ You're getting `GLIBCXX_3.4.32 not found` errors
- ✅ You're using miniconda/anaconda Python
- ✅ The pre-built OTIO wheel isn't working
- ✅ You're using Python 3.13

---

### `setup_ubuntu_environment.sh`

**Environment setup** - fixes library path issues with miniconda and system libraries.

**What it does:**
1. Prioritizes system libstdc++ over miniconda's version
2. Sets LD_LIBRARY_PATH to use system libraries first
3. Warns about potential version conflicts
4. Displays available GLIBCXX versions

**Usage:**
```bash
# Run before tests or add to shell profile
source scripts/setup_ubuntu_environment.sh
```

**Use this if:**
- ✅ You're getting library version errors
- ✅ You want to use pre-built wheels with miniconda
- ✅ You don't want to rebuild from source

---

### `create_system_venv.sh`

**Create virtual environment with system Python** - avoids all GLIBCXX issues permanently.

**What it does:**
1. Locates system Python (not conda/miniconda)
2. Removes existing venv if present
3. Creates new venv using system Python
4. Verifies the venv is correctly configured
5. Provides next steps for installation

**Usage:**
```bash
cd /path/to/Conformity
./scripts/create_system_venv.sh
```

**Time:** ~1 minute

**Use this if:**
- ✅ You have conda/miniconda and want to avoid ALL library issues
- ✅ You keep getting GLIBCXX errors despite other fixes
- ✅ You want a clean start with system Python
- ✅ Recommended for Ubuntu users with conda installed

**This is the best long-term solution** - eliminates all library version conflicts at the source by using system Python instead of conda Python.

---

### `install_openimageio_ubuntu.sh`

**Install OpenImageIO** - adds support for professional image formats (EXR, DPX, etc.)

**What it does:**
1. Installs OpenImageIO from Ubuntu repositories
2. Installs Python bindings (python3-openimageio)
3. Creates symlink in venv (if using virtual environment)
4. Verifies installation

**Usage:**
```bash
cd /path/to/Conformity
source venv/bin/activate  # If using venv
./scripts/install_openimageio_ubuntu.sh
```

**Time:** ~2 minutes

**Use this if:**
- ✅ You need image sequence support (EXR, DPX, TIFF)
- ✅ You're working with VFX formats
- ✅ You need high bit-depth image processing

**Enables:**
- OpenEXR (.exr) - VFX standard, HDR
- DPX (.dpx) - Film/cinema workflows
- TIFF, PNG, JPEG - Standard formats
- Many more professional formats

---

## Which Script Should I Use?

### Use `install_opencolorio_ubuntu.sh` if:
- ✅ You want everything done automatically
- ✅ This is your first time installing
- ✅ You just want it to work

### Use `setup_ubuntu_dependencies.sh` if:
- ✅ You only need dependencies installed
- ✅ You want to customize the build process
- ✅ You're troubleshooting build issues
- ✅ You're building from your own OpenColorIO fork

---

## Manual Installation

If you prefer manual installation, see:
- [Ubuntu Installation Guide](../docs/UBUNTU_INSTALLATION.md) - Complete guide
- [Building Optional Dependencies](../docs/BUILDING_OPTIONAL_DEPS.md) - Advanced
- [Installation Troubleshooting](../docs/INSTALLATION_TROUBLESHOOTING.md) - Issues

---

## Common Issues

### Permission Denied

```bash
chmod +x scripts/*.sh
./scripts/install_opencolorio_ubuntu.sh
```

### Script Not Found

Make sure you're in the Conformity directory:
```bash
cd /path/to/Conformity
ls scripts/  # Should show the scripts
./scripts/install_opencolorio_ubuntu.sh
```

### Build Fails

1. Check the error message carefully
2. See [Installation Troubleshooting](../docs/INSTALLATION_TROUBLESHOOTING.md)
3. Try manual installation: [Ubuntu Guide](../docs/UBUNTU_INSTALLATION.md)

---

## After Installation

Verify everything worked:

```bash
# Check PyOpenColorIO
python3 -c "import PyOpenColorIO as ocio; print(f'OCIO: {ocio.__version__}')"

# Check all dependencies
python3 -m conformity.core.dependencies

# Run tests
python3 run_tests.py --quick
```

---

## Adding New Scripts

When adding new platform-specific scripts:

1. Name clearly: `install_<package>_<platform>.sh`
2. Add shebang: `#!/bin/bash`
3. Set exit on error: `set -e`
4. Add colored output for clarity
5. Include verification steps
6. Document in this README
7. Make executable: `chmod +x scripts/<script>.sh`

---

Last Updated: 2025-11-09
