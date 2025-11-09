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
fi
echo ""

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

    # Find system OpenImageIO package location
    SYSTEM_OIIO=$(python3 -c "import sys; print([p for p in sys.path if 'dist-packages' in p][0])" 2>/dev/null)/OpenImageIO.so

    # Create symlink in venv site-packages
    VENV_SITE_PACKAGES="$VENV_PATH/lib/python${PYTHON_VERSION}/site-packages"

    if [ -f "$SYSTEM_OIIO" ]; then
        ln -sf "$SYSTEM_OIIO" "$VENV_SITE_PACKAGES/OpenImageIO.so"
        echo -e "${GREEN}✓ Symlink created: $VENV_SITE_PACKAGES/OpenImageIO.so${NC}"
    else
        echo -e "${YELLOW}Warning: Could not find system OpenImageIO.so at expected location${NC}"
        echo "You may need to manually link it:"
        echo "  find /usr/lib -name 'OpenImageIO*.so'"
        echo "  ln -s /path/to/OpenImageIO.so $VENV_SITE_PACKAGES/"
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
if $PYTHON_CMD -c "import OpenImageIO as oiio; print(f'OpenImageIO version: {oiio.VERSION_STRING}')" 2>/dev/null; then
    echo ""
    echo -e "${GREEN}=======================================================================${NC}"
    echo -e "${GREEN}✓ Installation completed successfully!${NC}"
    echo -e "${GREEN}=======================================================================${NC}"
    echo ""
    $PYTHON_CMD -c "import OpenImageIO as oiio; print(f'OpenImageIO version: {oiio.VERSION_STRING}')"
    echo ""
    echo "Supported formats:"
    $PYTHON_CMD -c "import OpenImageIO as oiio; print(', '.join(oiio.get_string_attribute('extension_list').split(';')[:10]) + '...')" 2>/dev/null || echo "EXR, DPX, TIFF, PNG, JPEG, and many more"
    echo ""
else
    echo ""
    echo -e "${RED}=======================================================================${NC}"
    echo -e "${RED}✗ Installation verification failed${NC}"
    echo -e "${RED}=======================================================================${NC}"
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
