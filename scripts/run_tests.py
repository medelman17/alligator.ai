#!/usr/bin/env python3
"""
Test runner script for citation graph platform.
Provides easy commands to run different types of tests.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
os.chdir(PROJECT_ROOT)


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✅ {description} completed successfully!")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with exit code {e.returncode}")
        return e.returncode
    except KeyboardInterrupt:
        print(f"\n⚠️  {description} interrupted by user")
        return 130


def install_test_dependencies():
    """Install test dependencies."""
    cmd = ["poetry", "install", "--with", "test"]
    return run_command(cmd, "Installing test dependencies")


def run_unit_tests(verbose=False, coverage=True):
    """Run unit tests only."""
    cmd = ["poetry", "run", "pytest", "-m", "unit"]
    
    if verbose:
        cmd.append("-v")
    if coverage:
        cmd.extend(["--cov=shared", "--cov=services"])
    
    return run_command(cmd, "Running unit tests")


def run_integration_tests(verbose=False):
    """Run integration tests."""
    cmd = ["poetry", "run", "pytest", "-m", "integration"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "Running integration tests")


def run_agent_tests(verbose=False):
    """Run agent workflow tests."""
    cmd = ["poetry", "run", "pytest", "-m", "agent"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "Running agent workflow tests")


def run_performance_tests(verbose=False):
    """Run performance tests."""
    cmd = ["poetry", "run", "pytest", "-m", "performance", "--benchmark-only"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "Running performance tests")


def run_all_tests(exclude_slow=False, parallel=False, verbose=False):
    """Run all tests."""
    cmd = ["poetry", "run", "pytest"]
    
    if exclude_slow:
        cmd.extend(["-m", "not slow"])
    
    if parallel:
        cmd.extend(["-n", "auto"])  # Use all available CPU cores
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "Running all tests")


def run_quick_tests():
    """Run quick test suite (unit tests only, no coverage)."""
    cmd = ["poetry", "run", "pytest", "-m", "unit", "--no-cov", "-q"]
    return run_command(cmd, "Running quick test suite")


def run_accuracy_tests():
    """Run legal accuracy validation tests."""
    cmd = ["poetry", "run", "pytest", "-m", "accuracy", "-v"]
    return run_command(cmd, "Running legal accuracy tests")


def run_specific_test(test_path, verbose=False):
    """Run a specific test file or test function."""
    cmd = ["poetry", "run", "pytest", test_path]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, f"Running specific test: {test_path}")


def generate_coverage_report():
    """Generate comprehensive coverage report."""
    cmd = ["poetry", "run", "pytest", "--cov=shared", "--cov=services", "--cov=api", 
           "--cov-report=html", "--cov-report=xml", "--cov-report=term"]
    return run_command(cmd, "Generating coverage report")


def lint_and_format():
    """Run linting and formatting checks."""
    print("\n🔄 Running code quality checks...")
    
    # Run ruff linting
    lint_result = run_command(
        ["poetry", "run", "ruff", "check", "."],
        "Running ruff linting"
    )
    
    # Run ruff formatting
    format_result = run_command(
        ["poetry", "run", "ruff", "format", "--check", "."],
        "Checking code formatting"
    )
    
    # Run mypy type checking
    type_result = run_command(
        ["poetry", "run", "mypy", "shared", "services"],
        "Running type checking"
    )
    
    return max(lint_result, format_result, type_result)


def check_databases():
    """Check if required databases are available for integration tests."""
    print("\n🔄 Checking database availability...")
    
    import socket
    
    services = [
        ("Neo4j", "localhost", 7687),
        ("ChromaDB", "localhost", 8000),
        ("PostgreSQL", "localhost", 5432),
        ("Redis", "localhost", 6379)
    ]
    
    all_available = True
    
    for name, host, port in services:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"✅ {name} is available at {host}:{port}")
            else:
                print(f"❌ {name} is NOT available at {host}:{port}")
                all_available = False
        except Exception as e:
            print(f"❌ Error checking {name}: {e}")
            all_available = False
    
    if all_available:
        print("\n✅ All databases are available for integration testing")
    else:
        print("\n⚠️  Some databases are unavailable. Integration tests may be skipped.")
        print("💡 Run 'docker compose up -d' to start all required services.")
    
    return all_available


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Test runner for citation graph platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_tests.py --all                    # Run all tests
  python scripts/run_tests.py --unit                   # Run unit tests only
  python scripts/run_tests.py --integration            # Run integration tests
  python scripts/run_tests.py --agents                 # Run agent tests
  python scripts/run_tests.py --quick                  # Quick test suite
  python scripts/run_tests.py --performance            # Performance tests
  python scripts/run_tests.py --accuracy               # Legal accuracy tests
  python scripts/run_tests.py --specific tests/unit/test_legal_entities.py
  python scripts/run_tests.py --coverage               # Generate coverage report
  python scripts/run_tests.py --lint                   # Run code quality checks
  python scripts/run_tests.py --check-db               # Check database availability
        """
    )
    
    # Test type selection (mutually exclusive)
    test_group = parser.add_mutually_exclusive_group(required=True)
    test_group.add_argument("--all", action="store_true", help="Run all tests")
    test_group.add_argument("--unit", action="store_true", help="Run unit tests only")
    test_group.add_argument("--integration", action="store_true", help="Run integration tests")
    test_group.add_argument("--agents", action="store_true", help="Run agent workflow tests")
    test_group.add_argument("--performance", action="store_true", help="Run performance tests")
    test_group.add_argument("--accuracy", action="store_true", help="Run legal accuracy tests")
    test_group.add_argument("--quick", action="store_true", help="Run quick test suite")
    test_group.add_argument("--specific", type=str, help="Run specific test file or function")
    test_group.add_argument("--coverage", action="store_true", help="Generate coverage report")
    test_group.add_argument("--lint", action="store_true", help="Run linting and formatting checks")
    test_group.add_argument("--check-db", action="store_true", help="Check database availability")
    test_group.add_argument("--install", action="store_true", help="Install test dependencies")
    
    # Test options
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--no-slow", action="store_true", help="Exclude slow tests")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--no-cov", action="store_true", help="Disable coverage reporting")
    
    args = parser.parse_args()
    
    # Header
    print("🧪 Citation Graph Platform Test Runner")
    print(f"Project: {PROJECT_ROOT}")
    
    # Route to appropriate test runner
    exit_code = 0
    
    if args.install:
        exit_code = install_test_dependencies()
    elif args.check_db:
        check_databases()
    elif args.lint:
        exit_code = lint_and_format()
    elif args.coverage:
        exit_code = generate_coverage_report()
    elif args.unit:
        exit_code = run_unit_tests(verbose=args.verbose, coverage=not args.no_cov)
    elif args.integration:
        exit_code = run_integration_tests(verbose=args.verbose)
    elif args.agents:
        exit_code = run_agent_tests(verbose=args.verbose)
    elif args.performance:
        exit_code = run_performance_tests(verbose=args.verbose)
    elif args.accuracy:
        exit_code = run_accuracy_tests()
    elif args.quick:
        exit_code = run_quick_tests()
    elif args.specific:
        exit_code = run_specific_test(args.specific, verbose=args.verbose)
    elif args.all:
        exit_code = run_all_tests(
            exclude_slow=args.no_slow,
            parallel=args.parallel,
            verbose=args.verbose
        )
    
    # Summary
    if exit_code == 0:
        print(f"\n🎉 Test execution completed successfully!")
    else:
        print(f"\n💥 Test execution failed with exit code {exit_code}")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()