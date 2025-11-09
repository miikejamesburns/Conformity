#!/usr/bin/env python
"""
Quick EDL analysis tool.

Analyzes an EDL file for duration mismatch issues that can cause
OTIO import failures.

Usage:
    python analyze_edl.py <path_to_edl_file>
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from conformity.conform_engine.edl_utils import (
    analyze_edl_duration_issues,
    print_edl_analysis
)


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_edl.py <edl_file>")
        print("\nExample:")
        print('  python analyze_edl.py "Scene 23 EDL Video 3.edl"')
        sys.exit(1)

    edl_path = Path(sys.argv[1])

    if not edl_path.exists():
        print(f"ERROR: File not found: {edl_path}")
        sys.exit(1)

    print(f"Analyzing: {edl_path}\n")

    # Analyze the EDL
    analysis = analyze_edl_duration_issues(edl_path)

    # Print formatted report
    print_edl_analysis(analysis)

    # Exit with error code if issues found
    if analysis.get('issues'):
        sys.exit(1)


if __name__ == "__main__":
    main()
