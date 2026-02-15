#!/usr/bin/env python3
"""
Test runner script for StudyPulse backend testing.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py --unit       # Run unit tests only
    python run_tests.py --integration # Run integration tests only
    python run_tests.py --e2e        # Run E2E tests only
    python run_tests.py --coverage   # Run with coverage report
    python run_tests.py --fast       # Skip slow and load tests
"""
import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str]) -> int:
    """Run a command and return exit code."""
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*60}\n")

    result = subprocess.run(cmd)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="StudyPulse Test Runner")

    # Test category flags
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--e2e", action="store_true", help="Run E2E tests only")
    parser.add_argument("--load", action="store_true", help="Run load tests only")

    # Options
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--parallel", "-n", type=int, help="Number of parallel workers")
    parser.add_argument("--failed", action="store_true", help="Re-run only failed tests")

    args = parser.parse_args()

    # Check if we're in the backend directory
    if not Path("tests").exists():
        print("Error: Must run from studypulse/backend directory")
        sys.exit(1)

    # Build pytest command
    cmd = ["pytest"]

    # Select test category
    if args.unit:
        cmd.append("tests/unit")
    elif args.integration:
        cmd.append("tests/integration")
    elif args.e2e:
        cmd.extend(["tests/e2e", "-m", "e2e"])
    elif args.load:
        cmd.extend(["tests/load", "-m", "load"])
    else:
        cmd.append("tests/")

    # Add verbosity
    if args.verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")

    # Add coverage
    if args.coverage:
        cmd.extend([
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml",
        ])

    # Fast mode (skip slow and load tests)
    if args.fast:
        cmd.extend(["-m", "not slow and not load"])

    # Parallel execution
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])

    # Re-run failed tests
    if args.failed:
        cmd.append("--lf")

    # Run tests
    exit_code = run_command(cmd)

    if exit_code == 0:
        print("\n" + "="*60)
        print("✅ All tests passed!")
        print("="*60)

        if args.coverage:
            print("\n📊 Coverage report generated:")
            print("  - HTML: htmlcov/index.html")
            print("  - XML:  coverage.xml")
    else:
        print("\n" + "="*60)
        print("❌ Some tests failed!")
        print("="*60)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
