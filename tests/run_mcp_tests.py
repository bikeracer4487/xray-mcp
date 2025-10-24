#!/usr/bin/env python3
"""
Comprehensive MCP test runner.

This script runs all MCP protocol tests and provides detailed reporting
on protocol compliance and functionality.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_test_suite(test_category: str = "all", verbose: bool = False,
                  fail_fast: bool = False, parallel: bool = False) -> bool:
    """Run MCP test suite with specified options."""

    # Base pytest command
    cmd = ["python", "-m", "pytest"]

    # Add verbosity
    if verbose:
        cmd.extend(["-v", "-s"])

    # Add fail fast
    if fail_fast:
        cmd.append("-x")

    # Add parallel execution if requested
    if parallel:
        try:
            import pytest_xdist
            cmd.extend(["-n", "auto"])
        except ImportError:
            print("Warning: pytest-xdist not installed, running sequentially")

    # Test category selection
    test_paths = []
    markers = []

    if test_category == "all":
        test_paths.extend([
            "tests/mcp_protocol/",
            "tests/mcp_integration/",
            "tests/mcp_compliance/"
        ])
    elif test_category == "protocol":
        test_paths.append("tests/mcp_protocol/")
        markers.append("mcp_protocol")
    elif test_category == "integration":
        test_paths.append("tests/mcp_integration/")
        markers.append("mcp_integration")
    elif test_category == "compliance":
        test_paths.append("tests/mcp_compliance/")
        markers.append("mcp_compliance")
    elif test_category == "client":
        markers.append("mcp_client")
    elif test_category == "subprocess":
        markers.append("mcp_subprocess")
    elif test_category == "performance":
        markers.append("performance")
    elif test_category == "error_handling":
        markers.append("error_handling")
    else:
        print(f"Unknown test category: {test_category}")
        return False

    # Add test paths
    cmd.extend(test_paths)

    # Add markers
    if markers:
        cmd.extend(["-m", " and ".join(markers)])

    # Add output formatting
    cmd.extend([
        "--tb=short",
        "--show-capture=no",
        "--color=yes"
    ])

    print(f"Running MCP tests: {' '.join(cmd)}")
    print("=" * 80)

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        return False
    except Exception as e:
        print(f"Error running tests: {e}")
        return False


def run_quick_smoke_test() -> bool:
    """Run quick smoke test to verify basic functionality."""
    print("Running quick smoke test...")
    print("=" * 40)

    cmd = [
        "python", "-m", "pytest",
        "tests/mcp_protocol/test_initialization.py::TestMCPInitialization::test_server_starts_successfully",
        "tests/mcp_protocol/test_tool_discovery.py::TestMCPToolDiscovery::test_list_tools_basic",
        "-v"
    ]

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running smoke test: {e}")
        return False


def run_coverage_report() -> bool:
    """Run tests with coverage reporting."""
    print("Running tests with coverage...")
    print("=" * 40)

    try:
        import coverage
    except ImportError:
        print("Coverage not installed. Install with: pip install coverage")
        return False

    cmd = [
        "python", "-m", "coverage", "run", "-m", "pytest",
        "tests/mcp_protocol/",
        "tests/mcp_integration/",
        "tests/mcp_compliance/",
        "--quiet"
    ]

    try:
        # Run tests with coverage
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)

        if result.returncode == 0:
            # Generate coverage report
            subprocess.run([
                "python", "-m", "coverage", "report",
                "--show-missing",
                "--include=src/*"
            ], cwd=Path(__file__).parent.parent)

            # Generate HTML report
            subprocess.run([
                "python", "-m", "coverage", "html",
                "--include=src/*"
            ], cwd=Path(__file__).parent.parent)

            print("\nHTML coverage report generated in htmlcov/")

        return result.returncode == 0

    except Exception as e:
        print(f"Error running coverage: {e}")
        return False


def run_compliance_check() -> bool:
    """Run comprehensive compliance check."""
    print("Running MCP protocol compliance check...")
    print("=" * 50)

    cmd = [
        "python", "-m", "pytest",
        "tests/mcp_compliance/",
        "-v",
        "--tb=short",
        "-m", "mcp_compliance"
    ]

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)

        if result.returncode == 0:
            print("\n✅ MCP protocol compliance check PASSED")
        else:
            print("\n❌ MCP protocol compliance check FAILED")

        return result.returncode == 0

    except Exception as e:
        print(f"Error running compliance check: {e}")
        return False


def print_test_categories():
    """Print available test categories."""
    categories = {
        "all": "Run all MCP tests",
        "protocol": "MCP protocol tests (initialization, tool discovery, etc.)",
        "integration": "Integration tests with mocked APIs",
        "compliance": "MCP and JSON-RPC specification compliance tests",
        "client": "Tests using FastMCP Client",
        "subprocess": "Tests using subprocess communication",
        "performance": "Performance and load tests",
        "error_handling": "Error handling and edge case tests"
    }

    print("Available test categories:")
    for category, description in categories.items():
        print(f"  {category:15} - {description}")


def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(
        description="MCP Server Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run all tests
  %(prog)s --category protocol # Run protocol tests only
  %(prog)s --smoke            # Quick smoke test
  %(prog)s --compliance       # Compliance check only
  %(prog)s --coverage         # Run with coverage report
  %(prog)s --verbose --fail-fast  # Verbose output, stop on first failure
        """
    )

    parser.add_argument(
        "--category", "-c",
        default="all",
        help="Test category to run (default: all)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    parser.add_argument(
        "--fail-fast", "-x",
        action="store_true",
        help="Stop on first failure"
    )

    parser.add_argument(
        "--parallel", "-n",
        action="store_true",
        help="Run tests in parallel (requires pytest-xdist)"
    )

    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run quick smoke test only"
    )

    parser.add_argument(
        "--compliance",
        action="store_true",
        help="Run compliance check only"
    )

    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage reporting"
    )

    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List available test categories"
    )

    args = parser.parse_args()

    if args.list_categories:
        print_test_categories()
        return 0

    # Change to repository root
    repo_root = Path(__file__).parent.parent
    print(f"Repository root: {repo_root}")

    success = True

    if args.smoke:
        success = run_quick_smoke_test()
    elif args.compliance:
        success = run_compliance_check()
    elif args.coverage:
        success = run_coverage_report()
    else:
        success = run_test_suite(
            test_category=args.category,
            verbose=args.verbose,
            fail_fast=args.fail_fast,
            parallel=args.parallel
        )

    if success:
        print("\n✅ All tests completed successfully!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())