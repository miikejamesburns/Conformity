#!/usr/bin/env python3
"""
Conformity Setup Script

Automated setup and dependency checker for Conformity.

Usage:
    python setup_conformity.py              # Interactive setup
    python setup_conformity.py --check      # Check dependencies only
    python setup_conformity.py --install    # Install dependencies
    python setup_conformity.py --demo       # Run demo mode after setup
"""

import sys
import subprocess
import platform
from pathlib import Path
from typing import List, Tuple, Optional


class SetupChecker:
    """Check and setup Conformity environment."""

    def __init__(self):
        self.python_version = sys.version_info
        self.platform = platform.system()
        self.issues = []
        self.warnings = []

    def check_python_version(self) -> bool:
        """Check Python version >= 3.11."""
        print("Checking Python version...")

        if self.python_version >= (3, 11):
            print(f"✓ Python {self.python_version.major}.{self.python_version.minor} OK")
            return True
        else:
            self.issues.append(
                f"Python 3.11+ required (found {self.python_version.major}.{self.python_version.minor})"
            )
            print(f"✗ Python version too old")
            return False

    def check_pip(self) -> bool:
        """Check if pip is available."""
        print("\nChecking pip...")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print(f"✓ pip available")
                return True
            else:
                self.issues.append("pip not found")
                print("✗ pip not available")
                return False

        except Exception as e:
            self.issues.append(f"pip check failed: {e}")
            print("✗ pip not available")
            return False

    def check_dependencies(self) -> Tuple[List[str], List[str]]:
        """
        Check if required packages are installed.

        Returns:
            Tuple of (installed, missing) package names
        """
        print("\nChecking core dependencies...")

        # Core requirements (must have)
        requirements = [
            "opentimelineio",
            "PyQt6",
            "PyYAML",
            "pydantic",
            "pytest",
            "pytest-cov"
        ]

        installed = []
        missing = []

        for package in requirements:
            try:
                __import__(package.lower().replace("-", "_"))
                installed.append(package)
                print(f"✓ {package}")
            except ImportError:
                missing.append(package)
                print(f"✗ {package} not found")

        return installed, missing

    def check_optional_dependencies(self) -> List[str]:
        """
        Check optional dependencies.

        Returns:
            List of missing optional dependencies
        """
        print("\nChecking optional dependencies...")

        # Optional dependencies with installation notes
        optional = {
            "PyOpenColorIO": "Color management (see requirements-optional.txt)",
            "pytest-xdist": "Parallel test execution",
            "black": "Code formatting",
            "flake8": "Linting",
            "mypy": "Type checking"
        }

        missing = []

        for package, description in optional.items():
            try:
                # Special handling for PyOpenColorIO
                if package == "PyOpenColorIO":
                    import PyOpenColorIO as ocio
                    print(f"✓ {package} (v{ocio.__version__})")
                else:
                    __import__(package.lower().replace("-", "_"))
                    print(f"✓ {package}")
            except ImportError:
                missing.append(package)
                print(f"○ {package} (optional) - {description}")

        # Special note for PyOpenColorIO if missing
        if "PyOpenColorIO" in missing:
            print("\n  ℹ️  PyOpenColorIO note:")
            print("     Color management is optional. System will work without it.")
            print("     For installation help: see requirements-optional.txt")
            print(f"     Platform detected: {self.platform}")

        if missing and len(missing) > 1:
            self.warnings.append(
                f"Optional packages not installed: {', '.join(missing)}"
            )

        return missing

    def check_directory_structure(self) -> bool:
        """Check if directory structure is correct."""
        print("\nChecking directory structure...")

        required_dirs = [
            "src/conformity",
            "tests",
            "docs",
            "examples"
        ]

        all_present = True
        for dir_path in required_dirs:
            path = Path(dir_path)
            if path.exists():
                print(f"✓ {dir_path}/")
            else:
                print(f"✗ {dir_path}/ not found")
                self.issues.append(f"Directory not found: {dir_path}")
                all_present = False

        return all_present

    def install_dependencies(self) -> bool:
        """Install dependencies from requirements.txt."""
        print("\nInstalling dependencies...")

        requirements_file = Path("requirements.txt")

        if not requirements_file.exists():
            print("✗ requirements.txt not found")
            return False

        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                check=True
            )
            print("✓ Dependencies installed successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"✗ Installation failed: {e}")
            return False

    def install_dev_mode(self) -> bool:
        """Install package in development mode."""
        print("\nInstalling Conformity in development mode...")

        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-e", "."],
                check=True
            )
            print("✓ Conformity installed successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"✗ Installation failed: {e}")
            return False

    def run_tests(self) -> bool:
        """Run smoke tests to verify installation."""
        print("\nRunning verification tests...")

        try:
            result = subprocess.run(
                [sys.executable, "run_tests.py", "--quick"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                print("✓ All tests passed")
                return True
            else:
                print("✗ Some tests failed")
                print(result.stdout[-500:] if result.stdout else "")
                return False

        except subprocess.TimeoutExpired:
            print("✗ Tests timed out")
            return False
        except Exception as e:
            print(f"✗ Test execution failed: {e}")
            return False

    def run_demo(self) -> bool:
        """Run demo mode."""
        print("\nLaunching demo mode...")

        try:
            subprocess.run(
                [sys.executable, "-m", "conformity.demo.demo_mode"],
                check=True
            )
            return True

        except subprocess.CalledProcessError as e:
            print(f"✗ Demo failed: {e}")
            return False
        except KeyboardInterrupt:
            print("\nDemo interrupted by user")
            return True

    def print_summary(self):
        """Print setup summary."""
        print("\n" + "=" * 60)
        print("SETUP SUMMARY")
        print("=" * 60)

        if self.issues:
            print("\n❌ ISSUES FOUND:")
            for issue in self.issues:
                print(f"  - {issue}")

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")

        if not self.issues:
            print("\n✓ All critical checks passed!")
            print("\nConformity is ready to use.")
            print("\nNext steps:")
            print("  - Review documentation: docs/")
            print("  - Try examples: python examples/production_tracker_example.py")
            print("  - Run demo: python -m conformity.demo.demo_mode")
            print("  - Run tests: python run_tests.py")

        print("\n" + "=" * 60)

    def platform_specific_help(self):
        """Print platform-specific installation help."""
        print("\n" + "=" * 60)
        print("PLATFORM-SPECIFIC HELP")
        print("=" * 60)

        if self.platform == "Darwin":  # macOS
            print("\nmacOS Setup:")
            print("  brew install python@3.11")
            print("  brew install qt6")

        elif self.platform == "Linux":
            print("\nLinux (Ubuntu/Debian) Setup:")
            print("  sudo apt update")
            print("  sudo apt install python3.11 python3.11-venv")
            print("  sudo apt install python3-pyqt6")

        elif self.platform == "Windows":
            print("\nWindows Setup:")
            print("  1. Download Python 3.11+ from python.org")
            print("  2. Install with 'Add Python to PATH' checked")
            print("  3. Install Visual C++ Build Tools if needed")

        print()


def main():
    """Main setup routine."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Setup Conformity environment",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--check',
        action='store_true',
        help='Check dependencies only (no installation)'
    )

    parser.add_argument(
        '--install',
        action='store_true',
        help='Install dependencies automatically'
    )

    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run demo mode after setup'
    )

    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Skip verification tests'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("CONFORMITY SETUP")
    print("=" * 60)
    print()

    checker = SetupChecker()

    # Check Python version
    if not checker.check_python_version():
        checker.platform_specific_help()
        checker.print_summary()
        sys.exit(1)

    # Check pip
    if not checker.check_pip():
        print("\nInstall pip:")
        print("  python -m ensurepip --upgrade")
        sys.exit(1)

    # Check directory structure
    checker.check_directory_structure()

    # Check dependencies
    installed, missing = checker.check_dependencies()

    # Check optional dependencies
    optional_missing = checker.check_optional_dependencies()

    # Install if requested or missing dependencies
    if args.install or (missing and not args.check):
        if missing:
            print(f"\nMissing {len(missing)} required packages")

            if args.install or input("\nInstall missing packages? (y/n): ").lower() == 'y':
                if checker.install_dependencies():
                    print("✓ Installation successful")

                    # Install in dev mode
                    if input("\nInstall Conformity in development mode? (y/n): ").lower() == 'y':
                        checker.install_dev_mode()
                else:
                    print("✗ Installation failed")
                    checker.print_summary()
                    sys.exit(1)

    # Run tests unless skipped
    if not args.skip_tests and not args.check:
        if not missing:  # Only run if dependencies are installed
            if input("\nRun verification tests? (y/n): ").lower() == 'y':
                checker.run_tests()

    # Run demo if requested
    if args.demo:
        checker.run_demo()

    # Print summary
    checker.print_summary()

    # Exit with appropriate code
    sys.exit(1 if checker.issues else 0)


if __name__ == '__main__':
    main()
