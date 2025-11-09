#!/bin/bash
# Complete OpenTimelineIO installation script for Ubuntu/Debian
# Builds OTIO from source to avoid library compatibility issues
#
# This script resolves GLIBCXX version conflicts that occur when using
# pre-built wheels with miniconda or other Python distributions.

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OTIO_VERSION="0.16.0"  # Compatible version for this project
BUILD_DIR="/tmp/OpenTimelineIO-build-$$"
PYTHON_EXEC=$(which python3)

# Detect if we're in a virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    PYTHON_EXEC="$VIRTUAL_ENV/bin/python"
    echo -e "${GREEN}Detected virtual environment: $VIRTUAL_ENV${NC}"
fi

echo "======================================================================="
echo "OpenTimelineIO Installation for Ubuntu/Debian"
echo "======================================================================="
echo ""
echo "This script will:"
echo "  1. Install build dependencies"
echo "  2. Clone OpenTimelineIO ${OTIO_VERSION}"
echo "  3. Build OTIO from source with system compiler"
echo "  4. Install into current Python environment"
echo ""
echo "Build directory: ${BUILD_DIR}"
echo "Python: ${PYTHON_EXEC}"
echo ""

# Check Python version
PYTHON_VERSION=$($PYTHON_EXEC --version 2>&1 | awk '{print $2}')
echo "Python version: ${PYTHON_VERSION}"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled."
    exit 1
fi

# Check if running on Ubuntu/Debian
if [ ! -f /etc/debian_version ]; then
    echo -e "${RED}Error: This script is designed for Ubuntu/Debian systems${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}[1/4] Installing build dependencies...${NC}"
echo ""

sudo apt-get update
sudo apt-get install -y \
    build-essential \
    cmake \
    git \
    python3-dev \
    pybind11-dev

echo ""
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo ""
echo -e "${BLUE}[2/4] Cloning OpenTimelineIO ${OTIO_VERSION}...${NC}"
echo ""

mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"
git clone --depth 1 --branch "v${OTIO_VERSION}" https://github.com/AcademySoftwareFoundation/OpenTimelineIO.git
cd OpenTimelineIO

echo ""
echo -e "${GREEN}✓ Repository cloned${NC}"

echo ""
echo -e "${BLUE}[3/4] Building OpenTimelineIO from source...${NC}"
echo ""

# Uninstall any existing OTIO installation
echo "Removing any existing OTIO installation..."
$PYTHON_EXEC -m pip uninstall -y opentimelineio 2>/dev/null || true

# Install build requirements
echo "Installing Python build dependencies..."
$PYTHON_EXEC -m pip install setuptools wheel pybind11

# Build and install
echo "Building OTIO (this may take a few minutes)..."
$PYTHON_EXEC -m pip install -v .

echo ""
echo -e "${GREEN}✓ Build completed${NC}"

echo ""
echo -e "${BLUE}[4/4] Verifying installation...${NC}"
echo ""

# Verify installation
if $PYTHON_EXEC -c "import opentimelineio as otio; print(f'OTIO version: {otio.__version__}')" 2>/dev/null; then
    echo ""
    echo -e "${GREEN}=======================================================================${NC}"
    echo -e "${GREEN}✓ Installation completed successfully!${NC}"
    echo -e "${GREEN}=======================================================================${NC}"
    echo ""
    $PYTHON_EXEC -c "import opentimelineio as otio; print(f'OpenTimelineIO version: {otio.__version__}')"
    echo ""
    echo "Library location:"
    $PYTHON_EXEC -c "import opentimelineio; print(opentimelineio.__file__)"
    echo ""

    # Check adapters
    echo "Available adapters:"
    $PYTHON_EXEC -c "import opentimelineio as otio; print(', '.join([a.name for a in otio.plugins.ActiveManifest().adapters]))" 2>/dev/null || true
    echo ""
else
    echo ""
    echo -e "${RED}=======================================================================${NC}"
    echo -e "${RED}✗ Installation verification failed${NC}"
    echo -e "${RED}=======================================================================${NC}"
    echo ""
    echo "Please check the build logs above for errors."
    echo ""
    exit 1
fi

echo "Cleaning up build directory..."
rm -rf "${BUILD_DIR}"

echo ""
echo -e "${GREEN}Done!${NC}"
echo ""
echo "Next steps:"
echo "  1. Install remaining Conformity dependencies:"
echo "     pip install -r requirements.txt"
echo ""
echo "  2. Verify all dependencies:"
echo "     python -m conformity.core.dependencies"
echo ""
