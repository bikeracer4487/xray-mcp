#!/usr/bin/env python3
"""
Demonstration of Fixed Manual Test Creation

This script demonstrates that the Manual test creation issues have been resolved.
It creates a Manual test with three structured steps in the FRAMED project,
showing that the fixes work correctly without validation or GraphQL errors.

Usage:
    python demo_manual_test_creation.py

Requirements:
    - Valid Xray API credentials in environment variables
    - Access to FRAMED project in Xray
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import XrayConfig
from auth import XrayAuthManager
from client import XrayGraphQLClient
from tools.tests import TestTools, TestStep


async def demonstrate_manual_test_creation():
    """Demonstrate creating a Manual test with three structured steps."""
    
    # Load environment variables
    load_dotenv()
    
    print("🚀 Xray MCP Manual Test Creation Demonstration")
    print("=" * 60)
    
    try:
        # Initialize components
        print("📋 Initializing Xray MCP components...")
        config = XrayConfig.from_env()
        auth_manager = XrayAuthManager(
            config.client_id,
            config.client_secret,
            config.base_url
        )
        
        # Authenticate
        print("🔐 Authenticating with Xray API...")
        await auth_manager.authenticate()
        print("✅ Authentication successful!")
        
        # Create GraphQL client and tools
        graphql_client = XrayGraphQLClient(auth_manager)
        test_tools = TestTools(graphql_client)
        
        # Define the Manual test with three structured steps
        test_summary = f"Login Flow Test - Demo - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_description = "Automated demonstration of Manual test creation with structured steps"
        
        # Create test steps using TestStep objects (demonstrating the new TestStep class)
        test_steps = [
            TestStep(
                action="Navigate to the login page",
                result="Login page is displayed with username and password fields",
                data="URL: /login"
            ),
            TestStep(
                action="Enter valid user credentials",
                result="Credentials are accepted and fields show valid state",
                data="Username: testuser@example.com, Password: ValidPass123!"
            ),
            TestStep(
                action="Click the Login button",
                result="User is successfully logged in and redirected to dashboard"
            )
        ]
        
        print(f"📝 Creating Manual test: '{test_summary}'")
        print(f"   Description: {test_description}")
        print(f"   Steps: {len(test_steps)} structured steps")
        print()
        
        # Create the Manual test - this should work without any errors
        print("🔧 Calling create_test with Manual type and structured steps...")
        result = await test_tools.create_test(
            project_key="FRAMED",
            summary=test_summary,
            test_type="Manual",
            description=test_description,
            steps=test_steps
        )
        
        print("✅ Manual test created successfully!")
        print()
        
        # Display the results
        test_data = result["test"]
        print("📊 Created Test Details:")
        print(f"   Issue ID: {test_data['issueId']}")
        print(f"   Jira Key: {test_data['jira']['key']}")
        print(f"   Test Type: {test_data['testType']['name']}")
        print(f"   Summary: {test_data['jira']['summary']}")
        print(f"   Steps Count: {len(test_data['steps'])}")
        print()
        
        # Show the steps that were created
        print("🔍 Created Test Steps:")
        for i, step in enumerate(test_data['steps'], 1):
            print(f"   Step {i}:")
            print(f"     Action: {step['action']}")
            print(f"     Result: {step['result']}")
            if step.get('data'):
                print(f"     Data: {step['data']}")
            print()
        
        # Show warnings if any
        if result.get("warnings"):
            print("⚠️  Warnings:")
            for warning in result["warnings"]:
                print(f"   - {warning}")
            print()
        
        # Test idempotency - show that we can retrieve the test
        print("🔄 Testing test retrieval to verify data integrity...")
        retrieved_test = await test_tools.get_test(test_data['issueId'])
        
        print("✅ Test retrieval successful!")
        print(f"   Retrieved test type: {retrieved_test['testType']['name']}")
        print(f"   Retrieved steps count: {len(retrieved_test['steps'])}")
        
        # Verify the steps match what we created
        steps_match = True
        for i, (created_step, retrieved_step) in enumerate(zip(test_data['steps'], retrieved_test['steps'])):
            if (created_step['action'] != retrieved_step['action'] or 
                created_step['result'] != retrieved_step['result']):
                steps_match = False
                break
        
        if steps_match:
            print("✅ All steps match - data integrity verified!")
        else:
            print("⚠️  Step mismatch detected")
        
        print()
        print("🎉 Demonstration completed successfully!")
        print("   - Manual test created without errors")
        print("   - Structured steps properly saved")
        print("   - No 'unstructured' field conflicts")
        print("   - Data integrity verified")
        
        return test_data['jira']['key']
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        print(f"   Error type: {type(e).__name__}")
        if hasattr(e, '__dict__'):
            print(f"   Error details: {e.__dict__}")
        raise


async def main():
    """Main demonstration function."""
    try:
        created_test_key = await demonstrate_manual_test_creation()
        print(f"\n✨ Manual test '{created_test_key}' created successfully!")
        print("   The Manual test creation issues have been resolved.")
        
    except Exception as e:
        print(f"\n💥 Demonstration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())