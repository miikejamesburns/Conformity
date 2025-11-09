#!/bin/bash
# Complete OpenColorIO installation script for Ubuntu/Debian
# Installs dependencies, builds OpenColorIO from source, and installs Python bindings

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OCIO_VERSION="v2.3.2"  # Stable release
BUILD_DIR="/tmp/OpenColorIO-build-$$"
INSTALL_PREFIX="/usr/local"
PYTHON_EXEC=$(which python3)

echo "======================================================================="
echo "OpenColorIO Installation for Ubuntu/Debian"
echo "======================================================================="
echo ""
echo "This script will:"
echo "  1. Install all required dependencies"
echo "  2. Clone OpenColorIO ${OCIO_VERSION}"
echo "  3. Build OpenColorIO with Python bindings"
echo "  4. Install OpenColorIO system-wide"
echo "  5. Install PyOpenColorIO Python package"
echo ""
echo "Build directory: ${BUILD_DIR}"
echo "Install prefix: ${INSTALL_PREFIX}"
echo "Python: ${PYTHON_EXEC}"
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
echo -e "${BLUE}[1/5] Installing dependencies...${NC}"
echo ""

sudo apt-get update
sudo apt-get install -y \
    build-essential \
    cmake \
    ninja-build \
    git \
    pkg-config \
    python3-dev \
    python3-pip \
    python3-venv \
    libboost-all-dev \
    libyaml-cpp-dev \
    libtinyxml-dev \
    libglew-dev \
    zlib1g-dev

echo ""
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo ""
echo -e "${BLUE}[2/5] Cloning OpenColorIO ${OCIO_VERSION}...${NC}"
echo ""

mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"
git clone --depth 1 --branch "${OCIO_VERSION}" https://github.com/AcademySoftwareFoundation/OpenColorIO.git
cd OpenColorIO

echo ""
echo -e "${GREEN}✓ Repository cloned${NC}"

echo ""
echo -e "${BLUE}[3/5] Configuring build with CMake...${NC}"
echo ""

mkdir build
cd build

cmake -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="${INSTALL_PREFIX}" \
    -DOCIO_BUILD_PYTHON=ON \
    -DPYTHON_EXECUTABLE="${PYTHON_EXEC}" \
    -DOCIO_BUILD_APPS=OFF \
    -DOCIO_BUILD_TESTS=OFF \
    -DOCIO_BUILD_GPU_TESTS=OFF \
    -DOCIO_WARNING_AS_ERROR=OFF \
    ..

echo ""
echo -e "${GREEN}✓ Build configured${NC}"

echo ""
echo -e "${BLUE}[4/5] Building OpenColorIO (this may take several minutes)...${NC}"
echo ""

ninja -j$(nproc)

echo ""
echo -e "${GREEN}✓ Build completed${NC}"

echo ""
echo -e "${BLUE}[5/5] Installing OpenColorIO...${NC}"
echo ""

sudo ninja install
sudo ldconfig  # Update library cache

echo ""
echo -e "${GREEN}✓ OpenColorIO installed${NC}"

echo ""
echo -e "${BLUE}Installing PyOpenColorIO Python package...${NC}"
echo ""

# Try installing from PyPI first (easier)
if pip install PyOpenColorIO>=2.3.0 2>/dev/null; then
    echo -e "${GREEN}✓ PyOpenColorIO installed from PyPI${NC}"
else
    echo -e "${YELLOW}PyPI installation failed, using local build...${NC}"
    # Fall back to building from source
    cd "${BUILD_DIR}/OpenColorIO/build"
    pip install .
    echo -e "${GREEN}✓ PyOpenColorIO installed from source${NC}"
fi

echo ""
echo -e "${BLUE}Verifying installation...${NC}"
echo ""

# Verify installation
if python3 -c "import PyOpenColorIO as ocio; print(f'OCIO version: {ocio.__version__}')" 2>/dev/null; then
    echo ""
    echo -e "${GREEN}=======================================================================${NC}"
    echo -e "${GREEN}✓ Installation completed successfully!${NC}"
    echo -e "${GREEN}=======================================================================${NC}"
    echo ""
    python3 -c "import PyOpenColorIO as ocio; print(f'PyOpenColorIO version: {ocio.__version__}')"
    echo ""
    echo "Library location:"
    python3 -c "import PyOpenColorIO; print(PyOpenColorIO.__file__)"
    echo ""
else
    echo ""
    echo -e "${RED}=======================================================================${NC}"
    echo -e "${RED}✗ Installation verification failed${NC}"
    echo -e "${RED}=======================================================================${NC}"
    echo ""
    echo "Troubleshooting steps:"
    echo "  1. Check library path:"
    echo "     export LD_LIBRARY_PATH=${INSTALL_PREFIX}/lib:\$LD_LIBRARY_PATH"
    echo "  2. Try reinstalling:"
    echo "     pip install --force-reinstall PyOpenColorIO"
    echo "  3. Check logs in: ${BUILD_DIR}/OpenColorIO/build"
    echo ""
    exit 1
fi

echo "Next steps:"
echo "  1. Install Conformity dependencies:"
echo "     cd /path/to/Conformity"
echo "     pip install -r requirements.txt"
echo ""
echo "  2. Verify Conformity can use OCIO:"
echo "     python3 -m conformity.core.dependencies"
echo ""
echo "  3. (Optional) Download OCIO configs:"
echo "     git clone https://github.com/colour-science/OpenColorIO-Configs.git"
echo "     export OCIO=/path/to/OpenColorIO-Configs/aces_1.2/config.ocio"
echo ""
echo "Cleaning up build directory..."
rm -rf "${BUILD_DIR}"
echo ""
echo -e "${GREEN}Done!${NC}"
