#!/usr/bin/env python3
"""
Test Runner for Ultimate Focus Timer
Provides easy testing capabilities with various options
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print the result"""
    print(f"\n🔍 {description}")
    print("=" * 50)

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print("STDERR:", result.stderr)

        if result.returncode != 0:
            print(f"❌ Command failed with return code: {result.returncode}")
            return False
        else:
            print("✅ Command completed successfully")
            return True

    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test runner for Ultimate Focus Timer")

    parser.add_argument('--all', action='store_true',
                       help='Run all tests with coverage')
    parser.add_argument('--unit', action='store_true',
                       help='Run unit tests only')
    parser.add_argument('--coverage', action='store_true',
                       help='Run tests with coverage report')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--file', type=str,
                       help='Run specific test file')
    parser.add_argument('--function', type=str,
                       help='Run specific test function')
    parser.add_argument('--lint', action='store_true',
                       help='Run code linting checks')
    parser.add_argument('--format', action='store_true',
                       help='Format code with black and isort')
    parser.add_argument('--install-deps', action='store_true',
                       help='Install test dependencies')

    args = parser.parse_args()

    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    success = True

    # Install dependencies if requested
    if args.install_deps:
        success &= run_command(
            "pip install -e .[dev]",
            "Installing development dependencies"
        )

    # Format code if requested
    if args.format:
        success &= run_command(
            "black src tests",
            "Formatting code with black"
        )
        success &= run_command(
            "isort src tests",
            "Sorting imports with isort"
        )

    # Run linting if requested
    if args.lint:
        success &= run_command(
            "flake8 src tests",
            "Running flake8 linting"
        )
        success &= run_command(
            "mypy src",
            "Running mypy type checking"
        )
        success &= run_command(
            "bandit -r src",
            "Running security checks with bandit"
        )

    # Prepare pytest command
    pytest_cmd = "python -m pytest"

    if args.verbose:
        pytest_cmd += " -v"

    if args.coverage or args.all:
        pytest_cmd += " --cov=src --cov-report=html --cov-report=term"

    if args.file:
        pytest_cmd += f" tests/{args.file}"
    elif args.function:
        pytest_cmd += f" -k {args.function}"
    else:
        pytest_cmd += " tests/"

    # Run tests
    if args.all:
        # Run comprehensive test suite
        success &= run_command(pytest_cmd, "Running comprehensive test suite")

        if success:
            print("\n📊 Coverage report generated in htmlcov/index.html")

    elif args.unit or not any([args.coverage, args.file, args.function, args.lint, args.format]):
        # Default: run unit tests
        success &= run_command(pytest_cmd, "Running unit tests")

    elif args.coverage:
        success &= run_command(pytest_cmd, "Running tests with coverage")

        if success:
            print("\n📊 Coverage report generated in htmlcov/index.html")

    elif args.file or args.function:
        success &= run_command(pytest_cmd, "Running specific tests")

    # Final status
    print("\n" + "=" * 50)
    if success:
        print("🎉 All operations completed successfully!")
        sys.exit(0)
    else:
        print("❌ Some operations failed. Check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
