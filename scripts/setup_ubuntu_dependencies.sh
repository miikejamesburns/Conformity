#!/bin/bash
# Ubuntu/Debian dependency installation script for Conformity
# This script installs all required dependencies for building PyOpenColorIO from source

set -e  # Exit on error

echo "======================================================================="
echo "Conformity - Ubuntu Dependency Installation"
echo "======================================================================="
echo ""

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Ubuntu/Debian
if [ ! -f /etc/debian_version ]; then
    echo -e "${RED}Error: This script is designed for Ubuntu/Debian systems${NC}"
    exit 1
fi

echo -e "${YELLOW}Updating package lists...${NC}"
sudo apt-get update

echo ""
echo -e "${YELLOW}Installing build tools...${NC}"
sudo apt-get install -y \
    build-essential \
    cmake \
    ninja-build \
    git \
    pkg-config

echo ""
echo -e "${YELLOW}Installing Python development dependencies...${NC}"
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    python3-venv

echo ""
echo -e "${YELLOW}Installing OpenColorIO build dependencies...${NC}"
sudo apt-get install -y \
    libboost-all-dev \
    libyaml-cpp-dev \
    libtinyxml-dev \
    libglew-dev \
    zlib1g-dev

echo ""
echo -e "${GREEN}✓ All dependencies installed successfully!${NC}"
echo ""
echo "======================================================================="
echo "Next Steps:"
echo "======================================================================="
echo ""
echo "1. Build OpenColorIO from source:"
echo "   cd /tmp"
echo "   git clone https://github.com/AcademySoftwareFoundation/OpenColorIO.git"
echo "   cd OpenColorIO"
echo "   mkdir build && cd build"
echo "   cmake -DCMAKE_BUILD_TYPE=Release \\"
echo "         -DOCIO_BUILD_PYTHON=ON \\"
echo "         -DPYTHON_EXECUTABLE=\$(which python3) \\"
echo "         .."
echo "   make -j\$(nproc)"
echo "   sudo make install"
echo ""
echo "2. Install Python bindings:"
echo "   cd /tmp/OpenColorIO/build"
echo "   sudo ldconfig  # Update library cache"
echo "   pip install PyOpenColorIO"
echo ""
echo "3. Verify installation:"
echo "   python3 -c \"import PyOpenColorIO as ocio; print(f'OCIO version: {ocio.__version__}')\""
echo ""
echo "For more information, see:"
echo "  - docs/BUILDING_OPTIONAL_DEPS.md"
echo "  - docs/INSTALLATION_TROUBLESHOOTING.md"
echo ""
