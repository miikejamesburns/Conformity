#!/usr/bin/env python3
"""
Conformity Test Runner.

Comprehensive test runner with coverage reporting and various test modes.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --quick            # Run only quick tests
    python run_tests.py --integration      # Run integration tests only
    python run_tests.py --e2e              # Run end-to-end tests only
    python run_tests.py --coverage         # Run with coverage report
    python run_tests.py --html             # Generate HTML coverage report
    python run_tests.py --parallel         # Run tests in parallel
"""

import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional


class TestRunner:
    """Test runner for Conformity test suite."""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize test runner.

        Args:
            project_root: Root directory of project. Auto-detected if None.
        """
        if project_root is None:
            self.project_root = Path(__file__).parent
        else:
            self.project_root = Path(project_root)

        self.tests_dir = self.project_root / "tests"
        self.coverage_dir = self.project_root / "htmlcov"

    def run_tests(
        self,
        markers: Optional[List[str]] = None,
        parallel: bool = False,
        coverage: bool = True,
        html_report: bool = False,
        verbose: bool = True,
        failfast: bool = False
    ) -> int:
        """
        Run tests with specified options.

        Args:
            markers: Pytest markers to filter tests (e.g., ['unit', 'integration'])
            parallel: Run tests in parallel using pytest-xdist
            coverage: Generate coverage report
            html_report: Generate HTML coverage report
            verbose: Verbose output
            failfast: Stop on first failure

        Returns:
            Exit code (0 = success, non-zero = failure)
        """
        cmd = ["pytest"]

        # Add test directory
        cmd.append(str(self.tests_dir))

        # Verbosity
        if verbose:
            cmd.append("-v")

        # Fail fast
        if failfast:
            cmd.append("-x")

        # Parallel execution
        if parallel:
            try:
                import xdist  # noqa: F401
                cmd.extend(["-n", "auto"])
            except ImportError:
                print("Warning: pytest-xdist not installed, running sequentially")
                print("Install with: pip install pytest-xdist")

        # Coverage
        if coverage:
            cmd.extend([
                "--cov=src/conformity",
                "--cov-report=term-missing"
            ])

            if html_report:
                cmd.append("--cov-report=html")

        # Markers
        if markers:
            marker_expr = " or ".join(markers)
            cmd.extend(["-m", marker_expr])

        # Run tests
        print(f"Running: {' '.join(cmd)}\n")
        result = subprocess.run(cmd, cwd=self.project_root)

        return result.returncode

    def run_quick_tests(self) -> int:
        """Run quick smoke tests only."""
        print("=" * 60)
        print("RUNNING QUICK TESTS (smoke tests only)")
        print("=" * 60 + "\n")

        return self.run_tests(
            markers=["smoke"],
            coverage=False,
            parallel=False
        )

    def run_unit_tests(self) -> int:
        """Run unit tests only."""
        print("=" * 60)
        print("RUNNING UNIT TESTS")
        print("=" * 60 + "\n")

        return self.run_tests(
            markers=["unit"],
            coverage=True,
            parallel=True
        )

    def run_integration_tests(self) -> int:
        """Run integration tests only."""
        print("=" * 60)
        print("RUNNING INTEGRATION TESTS")
        print("=" * 60 + "\n")

        return self.run_tests(
            markers=["integration"],
            coverage=True,
            parallel=False  # Integration tests may have dependencies
        )

    def run_e2e_tests(self) -> int:
        """Run end-to-end tests only."""
        print("=" * 60)
        print("RUNNING END-TO-END TESTS")
        print("=" * 60 + "\n")

        return self.run_tests(
            markers=["e2e"],
            coverage=True,
            parallel=False
        )

    def run_all_tests(self, html_report: bool = False) -> int:
        """Run complete test suite."""
        print("=" * 60)
        print("RUNNING COMPLETE TEST SUITE")
        print("=" * 60 + "\n")

        return self.run_tests(
            coverage=True,
            html_report=html_report,
            parallel=True
        )

    def run_ci_tests(self) -> int:
        """Run tests suitable for CI environment."""
        print("=" * 60)
        print("RUNNING CI TEST SUITE")
        print("=" * 60 + "\n")

        # Exclude slow and GUI tests
        return self.run_tests(
            markers=["not slow", "not gui"],
            coverage=True,
            html_report=True,
            failfast=False
        )

    def generate_coverage_report(self):
        """Generate detailed coverage report."""
        print("\n" + "=" * 60)
        print("COVERAGE REPORT")
        print("=" * 60 + "\n")

        # Run tests with coverage
        cmd = [
            "pytest",
            str(self.tests_dir),
            "--cov=src/conformity",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=xml",
            "-q"  # Quiet mode
        ]

        subprocess.run(cmd, cwd=self.project_root)

        print(f"\nHTML coverage report generated at: {self.coverage_dir}/index.html")

    def validate_test_environment(self) -> bool:
        """
        Validate test environment is properly configured.

        Returns:
            True if environment is valid, False otherwise
        """
        print("Validating test environment...")

        issues = []

        # Check pytest installed
        try:
            import pytest  # noqa: F401
        except ImportError:
            issues.append("pytest not installed")

        # Check coverage installed
        try:
            import coverage  # noqa: F401
        except ImportError:
            issues.append("pytest-cov not installed")

        # Check test directory exists
        if not self.tests_dir.exists():
            issues.append(f"Tests directory not found: {self.tests_dir}")

        # Check conftest.py exists
        conftest = self.tests_dir / "conftest.py"
        if not conftest.exists():
            issues.append(f"conftest.py not found: {conftest}")

        if issues:
            print("\nTest environment issues found:")
            for issue in issues:
                print(f"  - {issue}")
            print("\nPlease install required packages:")
            print("  pip install pytest pytest-cov")
            return False

        print("Test environment OK\n")
        return True


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(
        description="Run Conformity test suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                     # Run all tests
  %(prog)s --quick             # Quick smoke tests
  %(prog)s --unit              # Unit tests only
  %(prog)s --integration       # Integration tests only
  %(prog)s --e2e               # End-to-end tests only
  %(prog)s --coverage --html   # Full suite with HTML report
  %(prog)s --ci                # CI-compatible test run
        """
    )

    # Test mode selection (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--quick', '-q',
        action='store_true',
        help='Run quick smoke tests only'
    )
    mode_group.add_argument(
        '--unit', '-u',
        action='store_true',
        help='Run unit tests only'
    )
    mode_group.add_argument(
        '--integration', '-i',
        action='store_true',
        help='Run integration tests only'
    )
    mode_group.add_argument(
        '--e2e', '-e',
        action='store_true',
        help='Run end-to-end tests only'
    )
    mode_group.add_argument(
        '--ci',
        action='store_true',
        help='Run CI-compatible tests (excludes slow and GUI tests)'
    )

    # Options
    parser.add_argument(
        '--coverage', '-c',
        action='store_true',
        help='Generate coverage report'
    )
    parser.add_argument(
        '--html',
        action='store_true',
        help='Generate HTML coverage report'
    )
    parser.add_argument(
        '--parallel', '-p',
        action='store_true',
        help='Run tests in parallel (requires pytest-xdist)'
    )
    parser.add_argument(
        '--failfast', '-x',
        action='store_true',
        help='Stop on first test failure'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate test environment and exit'
    )

    args = parser.parse_args()

    # Create test runner
    runner = TestRunner()

    # Validate environment
    if args.validate:
        sys.exit(0 if runner.validate_test_environment() else 1)

    if not runner.validate_test_environment():
        sys.exit(1)

    # Run appropriate tests
    exit_code = 0

    if args.quick:
        exit_code = runner.run_quick_tests()
    elif args.unit:
        exit_code = runner.run_unit_tests()
    elif args.integration:
        exit_code = runner.run_integration_tests()
    elif args.e2e:
        exit_code = runner.run_e2e_tests()
    elif args.ci:
        exit_code = runner.run_ci_tests()
    elif args.coverage and args.html:
        runner.generate_coverage_report()
    else:
        # Default: run all tests
        exit_code = runner.run_all_tests(html_report=args.html)

    # Print summary
    print("\n" + "=" * 60)
    if exit_code == 0:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 60 + "\n")

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
