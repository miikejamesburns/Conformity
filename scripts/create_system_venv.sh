#!/bin/bash
# Create a virtual environment using system Python instead of miniconda/anaconda
# This avoids GLIBCXX library version conflicts

set -e  # Exit on error

# Color output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "======================================================================="
echo "Create Virtual Environment with System Python"
echo "======================================================================="
echo ""

# Find system Python (not conda/miniconda)
SYSTEM_PYTHON=""

# Try common system Python locations
for py in /usr/bin/python3 /usr/local/bin/python3 /bin/python3; do
    if [ -f "$py" ]; then
        # Check if it's NOT from conda
        if ! $py -c "import sys; print(sys.prefix)" 2>/dev/null | grep -q -E "conda|anaconda|miniconda"; then
            SYSTEM_PYTHON="$py"
            break
        fi
    fi
done

if [ -z "$SYSTEM_PYTHON" ]; then
    echo -e "${RED}Error: Could not find system Python${NC}"
    echo "All Python installations appear to be from conda/miniconda"
    echo ""
    echo "Please install system Python:"
    echo "  sudo apt-get install python3 python3-venv"
    exit 1
fi

PYTHON_VERSION=$($SYSTEM_PYTHON --version 2>&1 | awk '{print $2}')
PYTHON_PREFIX=$($SYSTEM_PYTHON -c "import sys; print(sys.prefix)")

echo "Found system Python:"
echo "  Path: $SYSTEM_PYTHON"
echo "  Version: $PYTHON_VERSION"
echo "  Prefix: $PYTHON_PREFIX"
echo ""

# Check if in project directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${YELLOW}Warning: Not in Conformity directory?${NC}"
    echo "Current directory: $(pwd)"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 1
    fi
fi

# Check if venv already exists
if [ -d "venv" ]; then
    echo -e "${YELLOW}A virtual environment already exists at ./venv${NC}"
    echo ""
    read -p "Delete and recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing old venv..."
        rm -rf venv
    else
        echo "Cancelled."
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}Creating virtual environment with system Python...${NC}"
echo ""

$SYSTEM_PYTHON -m venv venv

if [ ! -d "venv" ]; then
    echo -e "${RED}Failed to create virtual environment${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Virtual environment created${NC}"
echo ""

# Verify the venv uses system Python
VENV_PYTHON="./venv/bin/python"
VENV_VERSION=$($VENV_PYTHON --version 2>&1 | awk '{print $2}')

echo "Virtual environment details:"
echo "  Python: $VENV_VERSION"
echo "  Location: ./venv"
echo ""

# Check if it's really using system Python and not conda
if $VENV_PYTHON -c "import sys; print(sys.prefix)" 2>/dev/null | grep -q -E "conda|anaconda|miniconda"; then
    echo -e "${RED}⚠ Warning: venv still appears to be using conda Python${NC}"
    echo "This may cause library version issues."
    echo ""
fi

echo -e "${GREEN}=======================================================================${NC}"
echo -e "${GREEN}Virtual environment created successfully!${NC}"
echo -e "${GREEN}=======================================================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Activate the virtual environment:"
echo "   ${BLUE}source venv/bin/activate${NC}"
echo ""
echo "2. Upgrade pip:"
echo "   ${BLUE}pip install --upgrade pip${NC}"
echo ""
echo "3. Install dependencies:"
echo "   ${BLUE}pip install -r requirements.txt${NC}"
echo ""
echo "4. Build OpenTimelineIO from source (to avoid GLIBCXX errors):"
echo "   ${BLUE}./scripts/install_opentimelineio_ubuntu.sh${NC}"
echo ""
echo "5. Install optional dependencies:"
echo "   ${BLUE}./scripts/install_opencolorio_ubuntu.sh${NC}"
echo "   ${BLUE}./scripts/install_openimageio_ubuntu.sh${NC}"
echo ""
echo "6. Verify everything works:"
echo "   ${BLUE}python -m conformity.core.dependencies${NC}"
echo ""
