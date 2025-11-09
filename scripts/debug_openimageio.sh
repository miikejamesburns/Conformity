#!/bin/bash
# Debug script to diagnose OpenImageIO installation issues

# Color output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "======================================================================="
echo "OpenImageIO Installation Diagnostic"
echo "======================================================================="
echo ""

# Check which Python is being used
echo -e "${BLUE}[1] Python Environment${NC}"
echo "Python executable: $(which python)"
echo "Python version: $(python --version)"
echo "Virtual environment: ${VIRTUAL_ENV:-Not in a venv}"
echo ""

# Check if package is installed system-wide
echo -e "${BLUE}[2] System Package Status${NC}"
if dpkg -l | grep -q python3-openimageio; then
    echo -e "${GREEN}✓ python3-openimageio package is installed${NC}"
    dpkg -l | grep openimageio
else
    echo -e "${RED}✗ python3-openimageio package is NOT installed${NC}"
    echo "Run: sudo apt-get install python3-openimageio"
fi
echo ""

# Find OpenImageIO .so files
echo -e "${BLUE}[3] OpenImageIO Library Files${NC}"
OIIO_FILES=$(find /usr/lib -name "*OpenImageIO*" 2>/dev/null)
if [ -n "$OIIO_FILES" ]; then
    echo -e "${GREEN}Found OpenImageIO library files:${NC}"
    echo "$OIIO_FILES"
else
    echo -e "${RED}No OpenImageIO library files found in /usr/lib${NC}"
fi
echo ""

# Check Python import
echo -e "${BLUE}[4] Python Import Test${NC}"
if python -c "import OpenImageIO as oiio; print(f'✓ OpenImageIO version: {oiio.VERSION_STRING}')" 2>/dev/null; then
    python -c "import OpenImageIO as oiio; print(f'✓ OpenImageIO version: {oiio.VERSION_STRING}')"
else
    echo -e "${RED}✗ Cannot import OpenImageIO${NC}"
    echo ""
    echo "Error details:"
    python -c "import OpenImageIO" 2>&1 || true
fi
echo ""

# Check Python path
echo -e "${BLUE}[5] Python Module Search Paths${NC}"
python -c "import sys; [print(p) for p in sys.path]"
echo ""

# If in venv, check for symlink
if [ -n "$VIRTUAL_ENV" ]; then
    echo -e "${BLUE}[6] Virtual Environment Symlink${NC}"
    PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    VENV_SITE_PACKAGES="$VIRTUAL_ENV/lib/python${PYTHON_VERSION}/site-packages"

    if [ -f "$VENV_SITE_PACKAGES/OpenImageIO.so" ] || [ -L "$VENV_SITE_PACKAGES/OpenImageIO.so" ]; then
        echo -e "${GREEN}✓ OpenImageIO symlink exists in venv${NC}"
        ls -la "$VENV_SITE_PACKAGES/OpenImageIO"* 2>/dev/null
    else
        echo -e "${RED}✗ No OpenImageIO symlink in venv${NC}"
        echo ""
        echo "To create symlink manually:"
        SYSTEM_OIIO=$(find /usr/lib -name "OpenImageIO*.so" -o -name "_OpenImageIO*.so" 2>/dev/null | head -1)
        if [ -n "$SYSTEM_OIIO" ]; then
            echo "  ln -s $SYSTEM_OIIO $VENV_SITE_PACKAGES/"
        else
            echo "  First find the .so file: find /usr/lib -name '*OpenImageIO*.so'"
            echo "  Then create symlink: ln -s /path/to/file $VENV_SITE_PACKAGES/"
        fi
    fi
    echo ""
fi

# Check system Python (outside venv)
echo -e "${BLUE}[7] System Python Test${NC}"
if /usr/bin/python3 -c "import OpenImageIO as oiio; print(f'✓ System Python can import OpenImageIO: {oiio.VERSION_STRING}')" 2>/dev/null; then
    /usr/bin/python3 -c "import OpenImageIO as oiio; print(f'✓ System Python can import OpenImageIO: {oiio.VERSION_STRING}')"
else
    echo -e "${YELLOW}System Python cannot import OpenImageIO${NC}"
fi
echo ""

echo "======================================================================="
echo -e "${BLUE}Recommendations:${NC}"
echo "======================================================================="
echo ""

# Give recommendations
if ! dpkg -l | grep -q python3-openimageio; then
    echo "1. Install the package:"
    echo "   sudo apt-get install python3-openimageio"
    echo ""
fi

if [ -n "$VIRTUAL_ENV" ]; then
    echo "2. You're in a virtual environment. After installing the package,"
    echo "   create a symlink to make it available in your venv:"
    echo "   ./scripts/install_openimageio_ubuntu.sh"
    echo ""
fi

echo "3. Verify the installation:"
echo "   python -c 'import OpenImageIO as oiio; print(oiio.VERSION_STRING)'"
echo ""
