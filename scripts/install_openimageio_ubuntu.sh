#!/bin/bash
# OpenImageIO installation script for Ubuntu/Debian
# Installs Python bindings for OpenImageIO (OIIO)
#
# OpenImageIO provides support for professional image formats:
# - OpenEXR (.exr) - VFX standard, high dynamic range
# - DPX (.dpx) - Film/cinema workflows
# - TIFF, PNG, JPEG - Standard formats
# - And many more professional formats

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "======================================================================="
echo "OpenImageIO Installation for Ubuntu/Debian"
echo "======================================================================="
echo ""

# Check if running on Ubuntu/Debian
if [ ! -f /etc/debian_version ]; then
    echo -e "${RED}Error: This script is designed for Ubuntu/Debian systems${NC}"
    exit 1
fi

# Detect if we're in a virtual environment
VENV_PATH=""
if [ -n "$VIRTUAL_ENV" ]; then
    VENV_PATH="$VIRTUAL_ENV"
    echo -e "${YELLOW}Detected virtual environment: $VIRTUAL_ENV${NC}"
    echo ""
    echo -e "${YELLOW}Note: Ubuntu packages install system-wide, not in the venv.${NC}"
    echo "We'll create a symlink from the venv to the system package."
    echo ""
fi

echo "This script will:"
echo "  1. Install OpenImageIO from Ubuntu repositories"
echo "  2. Install Python bindings (python3-openimageio)"
if [ -n "$VENV_PATH" ]; then
    echo "  3. Create symlink in your venv to access the package"
    echo "  4. Set up library paths (if using miniconda/anaconda)"
fi
echo ""

# Check if using miniconda/anaconda
USING_CONDA=false
if command -v conda &> /dev/null || [[ "$PATH" == *"miniconda"* ]] || [[ "$PATH" == *"anaconda"* ]]; then
    USING_CONDA=true
    echo -e "${YELLOW}Note: Detected conda/miniconda in your environment.${NC}"
    echo "If you encounter GLIBCXX errors, we'll configure library paths automatically."
    echo ""
fi

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled."
    exit 1
fi

echo ""
echo -e "${BLUE}[1/2] Installing OpenImageIO system packages...${NC}"
echo ""

sudo apt-get update
sudo apt-get install -y \
    python3-openimageio \
    libopenimageio-dev

echo ""
echo -e "${GREEN}✓ System packages installed${NC}"

# If in a venv, create symlink to access system package
if [ -n "$VENV_PATH" ]; then
    echo ""
    echo -e "${BLUE}[2/2] Creating venv symlink...${NC}"
    echo ""

    # Find Python version in venv
    PYTHON_VERSION=$($VENV_PATH/bin/python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

    # Create symlink in venv site-packages
    VENV_SITE_PACKAGES="$VENV_PATH/lib/python${PYTHON_VERSION}/site-packages"

    # Find system OpenImageIO package - try multiple locations and names
    SYSTEM_OIIO=""

    # Try to find via Python import first
    SYSTEM_OIIO=$(python3 -c "import OpenImageIO; print(OpenImageIO.__file__)" 2>/dev/null || echo "")

    # If that fails, search in common locations
    if [ -z "$SYSTEM_OIIO" ] || [ ! -f "$SYSTEM_OIIO" ]; then
        SYSTEM_OIIO=$(find /usr/lib -name "OpenImageIO.so" -o -name "_OpenImageIO*.so" -o -name "OpenImageIO.cpython*.so" 2>/dev/null | head -1)
    fi

    # Also check dist-packages directly
    if [ -z "$SYSTEM_OIIO" ] || [ ! -f "$SYSTEM_OIIO" ]; then
        for distpkg in /usr/lib/python3/dist-packages /usr/lib/python${PYTHON_VERSION}/dist-packages; do
            if [ -f "$distpkg/OpenImageIO.so" ]; then
                SYSTEM_OIIO="$distpkg/OpenImageIO.so"
                break
            fi
        done
    fi

    if [ -n "$SYSTEM_OIIO" ] && [ -f "$SYSTEM_OIIO" ]; then
        # Get just the filename in case it has a python version suffix
        OIIO_FILENAME=$(basename "$SYSTEM_OIIO")
        ln -sf "$SYSTEM_OIIO" "$VENV_SITE_PACKAGES/$OIIO_FILENAME"
        # Also create a generic symlink if the filename has version info
        if [[ "$OIIO_FILENAME" != "OpenImageIO.so" ]]; then
            ln -sf "$SYSTEM_OIIO" "$VENV_SITE_PACKAGES/OpenImageIO.so"
        fi
        echo -e "${GREEN}✓ Symlink created: $VENV_SITE_PACKAGES/OpenImageIO.so -> $SYSTEM_OIIO${NC}"
    else
        echo -e "${YELLOW}Warning: Could not find system OpenImageIO.so${NC}"
        echo "Searched locations:"
        echo "  - /usr/lib/python3/dist-packages"
        echo "  - /usr/lib (recursive)"
        echo ""
        echo "Manual steps:"
        echo "  1. Find the .so file: find /usr/lib -name '*OpenImageIO*.so'"
        echo "  2. Create symlink: ln -s /path/to/file $VENV_SITE_PACKAGES/"
    fi
fi

echo ""
echo -e "${BLUE}Verifying installation...${NC}"
echo ""

# Determine which Python to use
PYTHON_CMD="python3"
if [ -n "$VENV_PATH" ]; then
    PYTHON_CMD="$VENV_PATH/bin/python"
fi

# Verify installation
IMPORT_ERROR=$($PYTHON_CMD -c "import OpenImageIO as oiio; print(f'OpenImageIO version: {oiio.VERSION_STRING}')" 2>&1)
IMPORT_STATUS=$?

if [ $IMPORT_STATUS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=======================================================================${NC}"
    echo -e "${GREEN}✓ Installation completed successfully!${NC}"
    echo -e "${GREEN}=======================================================================${NC}"
    echo ""
    echo "$IMPORT_ERROR"
    echo ""
    echo "Supported formats:"
    $PYTHON_CMD -c "import OpenImageIO as oiio; print(', '.join(oiio.get_string_attribute('extension_list').split(';')[:10]) + '...')" 2>/dev/null || echo "EXR, DPX, TIFF, PNG, JPEG, and many more"
    echo ""
else
    # Check if it's a GLIBCXX error
    if echo "$IMPORT_ERROR" | grep -q "GLIBCXX"; then
        echo ""
        echo -e "${YELLOW}=======================================================================${NC}"
        echo -e "${YELLOW}⚠ GLIBCXX Library Version Issue Detected${NC}"
        echo -e "${YELLOW}=======================================================================${NC}"
        echo ""
        echo "The package is installed but requires a newer libstdc++ than what"
        echo "miniconda/anaconda provides."
        echo ""
        echo -e "${GREEN}SOLUTION: Set up environment to use system libraries${NC}"
        echo ""
        echo "Run this before using OpenImageIO:"
        echo "  ${BLUE}source scripts/setup_ubuntu_environment.sh${NC}"
        echo ""
        echo "Or add to your shell profile (~/.bashrc) for permanent fix:"
        echo "  ${BLUE}export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:\$LD_LIBRARY_PATH${NC}"
        echo ""
        echo "Then verify:"
        echo "  python -c 'import OpenImageIO as oiio; print(oiio.VERSION_STRING)'"
        echo ""
        exit 0  # Not a failure, just needs env setup
    else
        echo ""
        echo -e "${RED}=======================================================================${NC}"
        echo -e "${RED}✗ Installation verification failed${NC}"
        echo -e "${RED}=======================================================================${NC}"
        echo ""
        echo "Error:"
        echo "$IMPORT_ERROR"
        echo ""
        echo "Troubleshooting:"
        echo "  1. Check if package is installed:"
        echo "     dpkg -l | grep openimageio"
        echo ""
        echo "  2. Find the .so file:"
        echo "     find /usr/lib -name 'OpenImageIO*.so'"
        echo ""
        echo "  3. Try importing in system Python:"
        echo "     python3 -c 'import OpenImageIO; print(OpenImageIO.VERSION_STRING)'"
        echo ""

        if [ -n "$VENV_PATH" ]; then
            echo "  4. If system Python works, manually create symlink:"
            echo "     SYSTEM_SO=\$(find /usr/lib -name 'OpenImageIO.so' -o -name 'OpenImageIO.cpython*.so' | head -1)"
            echo "     ln -s \$SYSTEM_SO $VENV_SITE_PACKAGES/"
            echo ""
        fi

        exit 1
    fi
fi

echo "Next steps:"
echo "  1. Verify all dependencies:"
echo "     python -m conformity.core.dependencies"
echo ""
echo "  2. OpenImageIO features are now available for:"
echo "     - Image sequence support (EXR, DPX, TIFF)"
echo "     - High bit-depth image processing"
echo "     - VFX and professional image formats"
echo ""

echo -e "${GREEN}Done!${NC}"
