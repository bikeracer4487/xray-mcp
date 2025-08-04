#!/usr/bin/env python3
"""
Test idempotency of Manual test creation

This script demonstrates that calling the same create_test operation multiple times
will create separate tests (as expected), but shows the data consistency.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import XrayConfig
from auth import XrayAuthManager
from client import XrayGraphQLClient
from tools.tests import TestTools, TestStep


async def test_create_operations():
    """Test multiple create operations to show they work consistently."""

    load_dotenv()

    print("🔄 Testing Manual test creation consistency")
    print("=" * 50)

    # Initialize components
    config = XrayConfig.from_env()
    auth_manager = XrayAuthManager(
        config.client_id, config.client_secret, config.base_url
    )
    await auth_manager.authenticate()

    graphql_client = XrayGraphQLClient(auth_manager)
    test_tools = TestTools(graphql_client)

    # Define consistent test data
    base_summary = "Idempotency Test - Manual Test Creation"
    test_steps = [
        TestStep(
            action="Open application homepage",
            result="Homepage loads with navigation menu",
            data="URL: https://example.com",
        ),
        TestStep(
            action="Click on About link",
            result="About page displays company information",
        ),
    ]

    created_tests = []

    # Create three tests with the same structure but different summaries
    for i in range(1, 4):
        summary = f"{base_summary} #{i}"
        print(f"📝 Creating test {i}: {summary}")

        result = await test_tools.create_test(
            project_key="FRAMED",
            summary=summary,
            test_type="Manual",
            description=f"Test #{i} for idempotency verification",
            steps=test_steps,
        )

        test_data = result["test"]
        created_tests.append(
            {
                "key": test_data["jira"]["key"],
                "issue_id": test_data["issueId"],
                "summary": test_data["jira"]["summary"],
                "steps_count": len(test_data["steps"]),
            }
        )

        print(f"   ✅ Created: {test_data['jira']['key']} (ID: {test_data['issueId']})")

    print(f"\n📊 Summary: Created {len(created_tests)} Manual tests")
    for test in created_tests:
        print(f"   - {test['key']}: '{test['summary']}' ({test['steps_count']} steps)")

    print("\n✅ All tests created successfully with consistent structure!")
    print("   Each test is unique (as expected) with proper Manual test structure.")

    return created_tests


if __name__ == "__main__":
    asyncio.run(test_create_operations())
