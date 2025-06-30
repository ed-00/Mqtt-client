#!/usr/bin/env python3
"""
Test runner script for the MQTT Client project.
Provides convenient commands for running different types of tests.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"\n🔍 {description}")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def run_unit_tests(verbose: bool = False) -> bool:
    """Run unit tests."""
    cmd = ["python", "-m", "pytest", "tests/", "-m", "unit"]
    if verbose:
        cmd.extend(["-v", "--tb=short"])
    cmd.extend(["--cov=Listener", "--cov-report=term-missing"])
    
    return run_command(cmd, "Running unit tests")


def run_integration_tests(verbose: bool = False) -> bool:
    """Run integration tests."""
    cmd = ["python", "-m", "pytest", "tests/", "-m", "integration"]
    if verbose:
        cmd.extend(["-v", "--tb=short"])
    cmd.extend(["--cov=Listener", "--cov-report=term-missing", "--cov-append"])
    
    return run_command(cmd, "Running integration tests")


def run_all_tests(verbose: bool = False) -> bool:
    """Run all tests."""
    cmd = ["python", "-m", "pytest", "tests/"]
    if verbose:
        cmd.extend(["-v", "--tb=short"])
    cmd.extend(["--cov=Listener", "--cov-report=term-missing", "--cov-report=html"])
    
    return run_command(cmd, "Running all tests")


def run_linting() -> bool:
    """Run code linting."""
    success = True
    
    # Run flake8
    cmd = ["python", "-m", "flake8", "Listener/", "tests/", "--max-line-length=127"]
    success &= run_command(cmd, "Running flake8 linting")
    
    return success


def run_security_checks() -> bool:
    """Run security checks."""
    success = True
    
    # Run bandit
    cmd = ["python", "-m", "bandit", "-r", "Listener/"]
    success &= run_command(cmd, "Running bandit security analysis")
    
    # Run safety check
    cmd = ["python", "-m", "safety", "check"]
    success &= run_command(cmd, "Checking dependencies for vulnerabilities")
    
    return success


def run_quick_check() -> bool:
    """Run a quick check (unit tests + linting)."""
    success = True
    success &= run_unit_tests()
    success &= run_linting()
    return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test runner for MQTT Client project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_tests.py unit          # Run unit tests only
  python scripts/run_tests.py integration   # Run integration tests only  
  python scripts/run_tests.py all           # Run all tests
  python scripts/run_tests.py lint          # Run linting only
  python scripts/run_tests.py security      # Run security checks
  python scripts/run_tests.py quick         # Run unit tests + linting
        """
    )
    
    parser.add_argument(
        "command",
        choices=["unit", "integration", "all", "lint", "security", "quick"],
        help="Type of tests/checks to run"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Change to project root directory
    project_root = Path(__file__).parent.parent
    import os
    os.chdir(project_root)
    
    print(f"🚀 Running '{args.command}' tests for MQTT Client project")
    print(f"📁 Working directory: {project_root}")
    
    success = False
    
    if args.command == "unit":
        success = run_unit_tests(args.verbose)
    elif args.command == "integration":
        success = run_integration_tests(args.verbose)
    elif args.command == "all":
        success = run_all_tests(args.verbose)
    elif args.command == "lint":
        success = run_linting()
    elif args.command == "security":
        success = run_security_checks()
    elif args.command == "quick":
        success = run_quick_check()
    
    if success:
        print(f"\n✅ {args.command.title()} tests completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ {args.command.title()} tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 