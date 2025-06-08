#!/usr/bin/env python3
"""
Test runner script for FastAPI Task Management Service

Usage:
    python scripts/run_tests.py [test_type]

Test types:
    - unit: Run unit tests only
    - integration: Run integration tests only
    - e2e: Run end-to-end tests only
    - performance: Run performance tests only
    - all: Run all tests (default)
    - fast: Run unit and integration tests (skip slow tests)
    - coverage: Run tests with coverage report
"""

import sys
import subprocess
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(command: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(command)}")

    try:
        result = subprocess.run(command, check=True, cwd=project_root)
        print(f"✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED (exit code: {e.returncode})")
        return False


def run_unit_tests():
    """Run unit tests."""
    return run_command(
        ["python", "-m", "pytest", "tests/unit/", "-v", "--tb=short"], "Unit Tests"
    )


def run_integration_tests():
    """Run integration tests."""
    return run_command(
        ["python", "-m", "pytest", "tests/integration/", "-v", "--tb=short"],
        "Integration Tests",
    )


def run_e2e_tests():
    """Run end-to-end tests."""
    return run_command(
        ["python", "-m", "pytest", "tests/e2e/", "-v", "--tb=short"], "End-to-End Tests"
    )


def run_performance_tests():
    """Run performance tests."""
    return run_command(
        [
            "python",
            "-m",
            "pytest",
            "tests/test_performance.py",
            "-v",
            "--tb=short",
            "-s",  # Show print statements for performance metrics
        ],
        "Performance Tests",
    )


def run_all_tests():
    """Run all tests."""
    return run_command(
        ["python", "-m", "pytest", "tests/", "-v", "--tb=short"], "All Tests"
    )


def run_fast_tests():
    """Run fast tests (exclude slow performance tests)."""
    return run_command(
        ["python", "-m", "pytest", "tests/", "-v", "--tb=short", "-m", "not slow"],
        "Fast Tests (excluding slow performance tests)",
    )


def run_coverage_tests():
    """Run tests with coverage report."""
    success = run_command(
        [
            "python",
            "-m",
            "pytest",
            "tests/",
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml",
            "--cov-fail-under=80",
            "-v",
        ],
        "Tests with Coverage Report",
    )

    if success:
        print(f"\n📊 Coverage report generated:")
        print(f"  - Terminal: See above")
        print(f"  - HTML: {project_root}/htmlcov/index.html")
        print(f"  - XML: {project_root}/coverage.xml")

    return success


def run_lint_checks():
    """Run code quality checks."""
    print(f"\n{'='*60}")
    print(f"🔍 Code Quality Checks")
    print(f"{'='*60}")

    checks = []

    # Ruff linting
    checks.append(run_command(["ruff", "check", "app/", "tests/"], "Ruff Linting"))

    # Black formatting check
    checks.append(
        run_command(
            ["black", "--check", "--diff", "app/", "tests/"], "Black Formatting Check"
        )
    )

    # MyPy type checking
    checks.append(run_command(["mypy", "app/"], "MyPy Type Checking"))

    return all(checks)


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(
        description="Run tests for FastAPI Task Management Service"
    )
    parser.add_argument(
        "test_type",
        choices=[
            "unit",
            "integration",
            "e2e",
            "performance",
            "all",
            "fast",
            "coverage",
            "lint",
        ],
        nargs="?",
        default="all",
        help="Type of tests to run (default: all)",
    )
    parser.add_argument(
        "--with-lint", action="store_true", help="Also run linting checks"
    )

    args = parser.parse_args()

    print(f"🚀 FastAPI Task Management Service - Test Runner")
    print(f"📁 Project root: {project_root}")
    print(f"🧪 Running: {args.test_type} tests")

    success = True

    # Run linting first if requested
    if args.with_lint or args.test_type == "lint":
        success &= run_lint_checks()
        if args.test_type == "lint":
            sys.exit(0 if success else 1)

    # Run the specified tests
    if args.test_type == "unit":
        success &= run_unit_tests()
    elif args.test_type == "integration":
        success &= run_integration_tests()
    elif args.test_type == "e2e":
        success &= run_e2e_tests()
    elif args.test_type == "performance":
        success &= run_performance_tests()
    elif args.test_type == "fast":
        success &= run_fast_tests()
    elif args.test_type == "coverage":
        success &= run_coverage_tests()
    elif args.test_type == "all":
        success &= run_unit_tests()
        success &= run_integration_tests()
        success &= run_e2e_tests()
        success &= run_performance_tests()

    # Final summary
    print(f"\n{'='*60}")
    if success:
        print("🎉 All tests completed successfully!")
        print("✅ PASSED")
    else:
        print("💥 Some tests failed!")
        print("❌ FAILED")
    print(f"{'='*60}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
