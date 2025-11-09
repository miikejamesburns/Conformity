#!/bin/bash
# Environment setup script for Ubuntu/Debian systems
# Fixes library path issues with miniconda and system libraries
#
# This script ensures that the system's libstdc++ is used instead of
# miniconda's older version, which may lack required GLIBCXX versions.
#
# Usage:
#   source scripts/setup_ubuntu_environment.sh
#
# Or add to your shell profile (~/.bashrc or ~/.zshrc):
#   source /path/to/Conformity/scripts/setup_ubuntu_environment.sh

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Determine system library paths
SYSTEM_LIB_PATHS=(
    "/usr/lib/x86_64-linux-gnu"
    "/lib/x86_64-linux-gnu"
    "/usr/lib"
    "/lib"
)

# Find the system libstdc++
SYSTEM_LIBSTDCXX_PATH=""
for libpath in "${SYSTEM_LIB_PATHS[@]}"; do
    if [ -f "$libpath/libstdc++.so.6" ]; then
        SYSTEM_LIBSTDCXX_PATH="$libpath"
        break
    fi
done

if [ -z "$SYSTEM_LIBSTDCXX_PATH" ]; then
    echo -e "${YELLOW}Warning: Could not find system libstdc++.so.6${NC}"
    echo "This may cause GLIBCXX version errors with OTIO and other libraries."
else
    # Prepend system library path to LD_LIBRARY_PATH
    # This ensures system libraries are used before miniconda or other sources
    if [ -z "$LD_LIBRARY_PATH" ]; then
        export LD_LIBRARY_PATH="$SYSTEM_LIBSTDCXX_PATH"
    else
        # Remove any existing instances of this path first
        LD_LIBRARY_PATH=$(echo "$LD_LIBRARY_PATH" | sed -e "s|$SYSTEM_LIBSTDCXX_PATH:||g" -e "s|:$SYSTEM_LIBSTDCXX_PATH||g")
        # Prepend to the beginning
        export LD_LIBRARY_PATH="$SYSTEM_LIBSTDCXX_PATH:$LD_LIBRARY_PATH"
    fi

    echo -e "${GREEN}✓ Environment configured for Ubuntu${NC}"
    echo "System library path prioritized: $SYSTEM_LIBSTDCXX_PATH"
fi

# Check for miniconda/anaconda in PATH and warn if found
if echo "$PATH" | grep -q "miniconda\|anaconda"; then
    echo ""
    echo -e "${YELLOW}Note: Detected miniconda/anaconda in PATH${NC}"
    echo "If you encounter library version conflicts, consider using"
    echo "the system Python instead:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
fi

# Verify GLIBCXX availability
if [ -n "$SYSTEM_LIBSTDCXX_PATH" ]; then
    GLIBCXX_MAX=$(strings "$SYSTEM_LIBSTDCXX_PATH/libstdc++.so.6" 2>/dev/null | grep "^GLIBCXX_" | sort -V | tail -1)
    if [ -n "$GLIBCXX_MAX" ]; then
        echo "Available GLIBCXX versions up to: $GLIBCXX_MAX"
    fi
fi

echo ""
