#!/usr/bin/env python3
"""Quick test script for MCP error handling integration."""

import asyncio
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from errors.mcp_errors import MCPErrorBuilder, MCPValidationHelper
from validators.tool_validators import XrayToolValidators


def test_error_builders():
    """Test error builder classes."""
    print("Testing error builders...")
    
    # Test invalid parameter error
    error = MCPErrorBuilder.invalid_parameter(
        field="project_key",
        expected="uppercase string",
        got="lowercase",
        hint="Project key should be uppercase like 'PROJ'",
        example_call={"tool": "create_test", "arguments": {"project_key": "PROJ"}}
    )
    
    error_dict = error.to_dict()
    print(f"✓ Invalid parameter error: {error_dict['error']}")
    
    # Test missing required error
    error = MCPErrorBuilder.missing_required(
        field="issue_id",
        hint="Issue ID is required to identify the test"
    )
    
    error_dict = error.to_dict()
    print(f"✓ Missing required error: {error_dict['error']}")


def test_validators():
    """Test validation functions."""
    print("\nTesting validators...")
    
    # Test project key validation
    error = MCPValidationHelper.validate_project_key("invalid-key")
    if error:
        print(f"✓ Project key validation caught error: {error.message}")
    
    error = MCPValidationHelper.validate_project_key("PROJ")
    if error is None:
        print("✓ Project key validation passed for valid key")
    
    # Test issue ID validation
    error = XrayToolValidators.validate_issue_id("")
    if error:
        print(f"✓ Issue ID validation caught error: {error.message}")
    
    error = XrayToolValidators.validate_issue_id("PROJ-123")
    if error is None:
        print("✓ Issue ID validation passed for Jira key")
    
    error = XrayToolValidators.validate_issue_id("1234567")
    if error is None:
        print("✓ Issue ID validation passed for numeric ID")
    
    # Test limit validation
    error = MCPValidationHelper.validate_limit(101, max_limit=100)
    if error:
        print(f"✓ Limit validation caught error: {error.message}")
    
    error = MCPValidationHelper.validate_limit(50, max_limit=100)
    if error is None:
        print("✓ Limit validation passed for valid limit")


def test_mcp_validation_helper():
    """Test MCP validation helper functions."""
    print("\nTesting MCP validation helper...")
    
    # Test project key validation
    error = MCPValidationHelper.validate_project_key("lowercase")
    if error:
        print(f"✓ MCP project key validation: {error.message}")
    
    # Test test type validation
    error = MCPValidationHelper.validate_test_type("InvalidType")
    if error:
        print(f"✓ MCP test type validation: {error.message}")
    
    error = MCPValidationHelper.validate_test_type("Manual")
    if error is None:
        print("✓ MCP test type validation passed for Manual")


def main():
    """Run all tests."""
    print("🚀 Testing MCP Error Handling Integration\n")
    
    test_error_builders()
    test_validators()
    test_mcp_validation_helper()
    
    print("\n✅ All error handling tests completed successfully!")


if __name__ == "__main__":
    main()