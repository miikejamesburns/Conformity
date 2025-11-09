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
