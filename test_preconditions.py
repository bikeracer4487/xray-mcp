#!/usr/bin/env python3
"""Test script for verifying precondition operations work correctly."""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()

# Import required modules
from config.settings import XrayConfig
from auth.manager import XrayAuthManager
from client.graphql import XrayGraphQLClient
from tools.preconditions import PreconditionTools
from tools.tests import TestTools

async def test_preconditions():
    """Test precondition creation, update, and deletion.
    
    This comprehensive test function validates the complete lifecycle of preconditions
    in Xray, including:
    - Test creation (prerequisite for precondition association)
    - Precondition creation with different types (Generic, Manual)
    - Precondition retrieval and validation
    - Cleanup operations
    
    Test Flow:
        1. Initialize Xray MCP connection with authentication
        2. Create a test to associate preconditions with
        3. Create a Generic precondition with definition
        4. Create a Manual precondition with step-by-step instructions
        5. Retrieve and validate all preconditions for the test
        6. Clean up by deleting the test (cascades to preconditions)
    
    Complexity: O(1) - Fixed number of API operations regardless of data size
    
    Dependencies:
        - Requires valid Xray API credentials in environment variables
        - Needs access to a test project (default: "FTEST")
        - Depends on auth.manager, client.graphql, and tools.preconditions
    
    Error Handling:
        - All API operations are wrapped in try-catch blocks
        - Continues execution on non-critical failures
        - Provides detailed error messages for debugging
    
    Example Output:
        🔧 Initializing Xray MCP connection...
        ✅ Connection initialized
        📝 Creating a test to associate preconditions with...
        ✅ Created test: FTEST-123 (ID: 456789)
        🔨 Creating a precondition...
        ✅ Created precondition: FTEST-124 (ID: 456790)
        ...
        ✨ Precondition testing complete!
    """
    
    print("🔧 Initializing Xray MCP connection...")
    
    # Initialize settings and authentication
    # Load configuration from environment variables (XRAY_CLIENT_ID, XRAY_CLIENT_SECRET, XRAY_BASE_URL)
    settings = XrayConfig.from_env()
    auth_manager = XrayAuthManager(
        client_id=settings.client_id,
        client_secret=settings.client_secret,
        base_url=settings.base_url,
    )
    
    # Initialize GraphQL client with JWT authentication
    # The client will automatically handle token refresh when needed
    client = XrayGraphQLClient(auth_manager=auth_manager)
    
    # Initialize tools with dependency injection pattern
    # Both tools share the same GraphQL client for consistency
    precondition_tools = PreconditionTools(client)
    test_tools = TestTools(client)
    
    print("✅ Connection initialized\n")
    
    # Step 1: Create a test first (preconditions need to be associated with tests)
    # Preconditions in Xray must be linked to specific tests, so we create a test first
    print("📝 Creating a test to associate preconditions with...")
    test_result = await test_tools.create_test(
        project_key="FTEST",  # Test project key - update if using different project
        summary="Test for Precondition Testing",
        test_type="Manual",  # Manual test type allows for step-by-step execution
        description="Test created to verify precondition functionality",
        steps=[
            {
                "action": "Execute test step 1",  # What the tester should do
                "data": "Test data 1",           # Input data for the step
                "result": "Expected result 1"     # Expected outcome
            }
        ]
    )
    
    # Extract test identifiers from the response for subsequent operations
    # issueId is the internal Xray ID, key is the human-readable Jira key (e.g., FTEST-123)
    test_id = test_result.get("test", {}).get("issueId")
    test_key = test_result.get("test", {}).get("jira", {}).get("key")
    print(f"✅ Created test: {test_key} (ID: {test_id})\n")
    
    # Step 2: Create a precondition
    # Preconditions define setup requirements that must be met before test execution
    print("🔨 Creating a precondition...")
    try:
        # Generic precondition structure - most flexible type for simple text definitions
        precondition_input = {
            "preconditionType": "Generic",  # Can be "Generic", "Manual", or "Cucumber"
            "definition": "System must be in test mode with all dependencies started",
            "jira": {
                "fields": {
                    "summary": "System Test Mode Precondition",  # Displayed in Jira UI
                    "project": {"key": "FTEST"}                    # Must match test project
                }
            }
        }
        
        precondition_result = await precondition_tools.create_precondition(
            issue_id=test_id,
            precondition_input=precondition_input
        )
        
        # Parse and validate the precondition creation response
        if "precondition" in precondition_result:
            precondition_id = precondition_result["precondition"].get("issueId")
            precondition_key = precondition_result["precondition"].get("jira", {}).get("key")
            print(f"✅ Created precondition: {precondition_key} (ID: {precondition_id})")
            print(f"   Type: {precondition_result['precondition'].get('preconditionType', {}).get('name')}")
            print(f"   Definition: {precondition_result['precondition'].get('definition')}")
            
            # Verify the precondition was successfully linked to the test
            if "addedToTest" in precondition_result:
                print(f"   Associated with test: {test_key}")
        else:
            # Log unexpected response format for debugging
            print(f"⚠️ Precondition created but response format unexpected: {precondition_result}")
            
    except Exception as e:
        print(f"❌ Failed to create precondition: {e}")
        print(f"   Error details: {str(e)}")
        
    # Step 3: Try creating another precondition with different type
    # Manual preconditions provide step-by-step instructions for human testers
    print("\n🔨 Creating a Manual precondition...")
    try:
        # Manual precondition with structured step-by-step format
        manual_precondition_input = {
            "preconditionType": {"name": "Manual"},  # Using object format (alternative to string)
            "definition": "1. Open the application\n2. Login with test credentials\n3. Navigate to test section",
            "jira": {
                "fields": {
                    "summary": "Manual Setup Precondition",
                    "project": {"key": "FTEST"},
                    "description": "Manual steps to prepare the test environment"  # Additional context
                }
            }
        }
        
        manual_result = await precondition_tools.create_precondition(
            issue_id=test_id,
            precondition_input=manual_precondition_input
        )
        
        # Validate manual precondition creation response
        if "precondition" in manual_result:
            manual_id = manual_result["precondition"].get("issueId")
            manual_key = manual_result["precondition"].get("jira", {}).get("key")
            print(f"✅ Created manual precondition: {manual_key} (ID: {manual_id})")
        else:
            # Log unexpected response for debugging API changes
            print(f"⚠️ Manual precondition created but response format unexpected: {manual_result}")
            
    except Exception as e:
        print(f"❌ Failed to create manual precondition: {e}")
        
    # Step 4: Get preconditions for the test
    # Verify that both preconditions were successfully created and associated
    print(f"\n📋 Retrieving preconditions for test {test_key}...")
    try:
        # Query all preconditions associated with the test
        preconditions = await precondition_tools.get_preconditions(test_id)
        if preconditions and "results" in preconditions:
            print(f"✅ Found {preconditions.get('total', 0)} preconditions:")
            # Iterate through and display each precondition's details
            for pc in preconditions["results"]:
                pc_key = pc.get("jira", {}).get("key", "Unknown")
                pc_type = pc.get("preconditionType", {}).get("name", "Unknown")
                print(f"   - {pc_key}: Type={pc_type}")
        else:
            print("⚠️ No preconditions found or unexpected response format")
    except Exception as e:
        print(f"❌ Failed to retrieve preconditions: {e}")
    
    # Step 5: Clean up - delete the test
    # Deleting the test will cascade delete associated preconditions in Xray
    print(f"\n🧹 Cleaning up - deleting test {test_key}...")
    try:
        await test_tools.delete_test(test_id)
        print(f"✅ Deleted test {test_key}")
        # Note: Associated preconditions are automatically deleted with the test
    except Exception as e:
        print(f"⚠️ Failed to delete test: {e}")
        # Non-critical failure - test may need manual cleanup in Jira
    
    print("\n✨ Precondition testing complete!")

if __name__ == "__main__":
    """Entry point for direct script execution.
    
    Runs the comprehensive precondition test when script is executed directly.
    Uses asyncio.run() to handle the async test function properly.
    
    Usage:
        python test_preconditions.py
    
    Prerequisites:
        - .env file with XRAY_CLIENT_ID and XRAY_CLIENT_SECRET
        - Access to a test project (default: "FTEST")
        - Network connectivity to Xray API endpoint
    """
    asyncio.run(test_preconditions())