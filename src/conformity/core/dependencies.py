"""
Optional dependency checking utilities.

This module provides utilities for detecting and handling optional dependencies
like PyOpenColorIO and tlRender.
"""

from typing import Dict, List, Tuple
import sys
from ..core.logger import get_logger

logger = get_logger(__name__)


class DependencyChecker:
    """Check status of optional dependencies."""

    @staticmethod
    def check_pyopencolorio() -> Tuple[bool, str]:
        """
        Check if PyOpenColorIO is available.

        Returns:
            Tuple of (is_available, version_or_error_message)
        """
        try:
            import PyOpenColorIO as ocio
            version = ocio.__version__ if hasattr(ocio, '__version__') else "unknown"
            return (True, version)
        except ImportError as e:
            return (False, str(e))

    @staticmethod
    def check_tlrender() -> Tuple[bool, str]:
        """
        Check if tlRender is available.

        Returns:
            Tuple of (is_available, version_or_error_message)
        """
        try:
            import tlRender as tlr
            version = tlr.__version__ if hasattr(tlr, '__version__') else "unknown"
            return (True, version)
        except ImportError as e:
            return (False, str(e))

    @staticmethod
    def check_opentimelineio() -> Tuple[bool, str]:
        """
        Check if OpenTimelineIO is available.

        Returns:
            Tuple of (is_available, version_or_error_message)
        """
        try:
            import opentimelineio as otio
            version = otio.__version__
            return (True, version)
        except ImportError as e:
            return (False, str(e))

    @staticmethod
    def get_all_dependencies() -> Dict[str, Dict[str, any]]:
        """
        Get status of all dependencies.

        Returns:
            Dictionary with dependency information
        """
        checker = DependencyChecker()

        deps = {}

        # Core dependencies
        deps['opentimelineio'] = {
            'required': True,
            'available': False,
            'version': None,
            'error': None
        }
        available, info = checker.check_opentimelineio()
        deps['opentimelineio']['available'] = available
        if available:
            deps['opentimelineio']['version'] = info
        else:
            deps['opentimelineio']['error'] = info

        # Optional dependencies
        deps['PyOpenColorIO'] = {
            'required': False,
            'available': False,
            'version': None,
            'error': None,
            'features': ['Color management', 'LUT application', 'ACES workflows']
        }
        available, info = checker.check_pyopencolorio()
        deps['PyOpenColorIO']['available'] = available
        if available:
            deps['PyOpenColorIO']['version'] = info
        else:
            deps['PyOpenColorIO']['error'] = info

        deps['tlRender'] = {
            'required': False,
            'available': False,
            'version': None,
            'error': None,
            'features': ['Professional playback', 'Hardware acceleration', 'Image sequences', 'Professional formats']
        }
        available, info = checker.check_tlrender()
        deps['tlRender']['available'] = available
        if available:
            deps['tlRender']['version'] = info
        else:
            deps['tlRender']['error'] = info

        return deps

    @staticmethod
    def print_dependency_report() -> None:
        """Print a formatted dependency status report."""
        deps = DependencyChecker.get_all_dependencies()

        print("\n" + "=" * 70)
        print("CONFORMITY DEPENDENCY STATUS")
        print("=" * 70)

        # Core dependencies
        print("\nCore Dependencies:")
        print("-" * 70)
        for name, info in deps.items():
            if info['required']:
                status = "✓" if info['available'] else "✗"
                version = f"(v{info['version']})" if info['version'] else ""
                print(f"  {status} {name:25} {version}")
                if not info['available']:
                    print(f"      ERROR: {info['error']}")

        # Optional dependencies
        print("\nOptional Dependencies:")
        print("-" * 70)
        for name, info in deps.items():
            if not info['required']:
                status = "✓" if info['available'] else "○"
                version = f"(v{info['version']})" if info['version'] else ""
                print(f"  {status} {name:25} {version}")

                if info['available'] and info.get('features'):
                    print(f"      Features: {', '.join(info['features'])}")
                elif not info['available']:
                    print(f"      Not installed - see DEPLOYMENT_GUIDE.md")
                    if info.get('features'):
                        print(f"      Would enable: {', '.join(info['features'])}")

        print("\n" + "=" * 70)
        print("\nLegend:")
        print("  ✓ = Installed and available")
        print("  ✗ = Required but missing")
        print("  ○ = Optional, not installed")
        print("\n" + "=" * 70)

    @staticmethod
    def validate_core_dependencies() -> List[str]:
        """
        Validate that all core dependencies are available.

        Returns:
            List of missing core dependency names (empty if all present)
        """
        missing = []
        deps = DependencyChecker.get_all_dependencies()

        for name, info in deps.items():
            if info['required'] and not info['available']:
                missing.append(name)

        return missing


def check_dependencies() -> bool:
    """
    Check dependencies and log warnings for missing optional ones.

    Returns:
        True if all core dependencies are available
    """
    deps = DependencyChecker.get_all_dependencies()

    # Check core dependencies
    missing_core = DependencyChecker.validate_core_dependencies()
    if missing_core:
        logger.error(f"Missing core dependencies: {', '.join(missing_core)}")
        return False

    # Log info about optional dependencies
    for name, info in deps.items():
        if not info['required']:
            if info['available']:
                logger.info(f"Optional dependency '{name}' v{info['version']} is available")
            else:
                logger.info(f"Optional dependency '{name}' not installed - some features will be disabled")

    return True


if __name__ == '__main__':
    # When run as script, print dependency report
    DependencyChecker.print_dependency_report()

    missing = DependencyChecker.validate_core_dependencies()
    if missing:
        print(f"\n⚠️  Missing core dependencies: {', '.join(missing)}")
        sys.exit(1)
    else:
        print("\n✓ All core dependencies are installed!")
        sys.exit(0)
