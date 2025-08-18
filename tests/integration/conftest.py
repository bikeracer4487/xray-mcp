"""Configuration and fixtures for integration tests.

These tests run against the real Xray API and require valid credentials.
Set environment variables:
- XRAY_CLIENT_ID
- XRAY_CLIENT_SECRET
- XRAY_BASE_URL (optional)

Tests use the FTEST project by default.
"""

import os
import pytest
import asyncio
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.manager import XrayAuthManager
from client.graphql import XrayGraphQLClient
from tools.preconditions import PreconditionTools
from tools.tests import TestTools
from tools.executions import TestExecutionTools


# Integration test configuration
INTEGRATION_PROJECT_KEY = "FTEST"
INTEGRATION_TEST_PREFIX = f"INT_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def pytest_configure(config):
    """Register integration test markers."""
    config.addinivalue_line(
        "markers", 
        "integration: Integration tests that require real Xray API access"
    )
    config.addinivalue_line(
        "markers",
        "cleanup: Tests that create data requiring cleanup"
    )


@pytest.fixture(scope="session")
def integration_enabled():
    """Check if integration tests should run."""
    client_id = os.getenv("XRAY_CLIENT_ID")
    client_secret = os.getenv("XRAY_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        pytest.skip("Integration tests require XRAY_CLIENT_ID and XRAY_CLIENT_SECRET env vars")
    
    return True


@pytest.fixture
async def auth_manager(integration_enabled):
    """Create authenticated auth manager for integration tests."""
    client_id = os.getenv("XRAY_CLIENT_ID")
    client_secret = os.getenv("XRAY_CLIENT_SECRET")
    base_url = os.getenv("XRAY_BASE_URL", "https://xray.cloud.getxray.app")
    
    manager = XrayAuthManager(client_id, client_secret, base_url)
    # Pre-authenticate to validate credentials
    try:
        await manager.authenticate()
    except Exception as e:
        pytest.skip(f"Failed to authenticate with Xray API: {e}")
    
    return manager


@pytest.fixture
async def graphql_client(auth_manager):
    """Create GraphQL client for integration tests."""
    return XrayGraphQLClient(auth_manager)


@pytest.fixture
async def precondition_tools(graphql_client):
    """Create precondition tools for integration tests."""
    return PreconditionTools(graphql_client)


@pytest.fixture
async def test_tools(graphql_client):
    """Create test tools for integration tests."""
    return TestTools(graphql_client)


@pytest.fixture
async def execution_tools(graphql_client):
    """Create execution tools for integration tests."""
    return TestExecutionTools(graphql_client)


@pytest.fixture
def test_data_tracker():
    """Track created test data for cleanup."""
    class TestDataTracker:
        def __init__(self):
            self.created_tests: List[str] = []
            self.created_preconditions: List[str] = []
            self.created_executions: List[str] = []
            self.created_test_sets: List[str] = []
            self.created_test_plans: List[str] = []
        
        def add_test(self, issue_id: str):
            self.created_tests.append(issue_id)
        
        def add_precondition(self, issue_id: str):
            self.created_preconditions.append(issue_id)
        
        def add_execution(self, issue_id: str):
            self.created_executions.append(issue_id)
        
        def add_test_set(self, issue_id: str):
            self.created_test_sets.append(issue_id)
        
        def add_test_plan(self, issue_id: str):
            self.created_test_plans.append(issue_id)
        
        def get_all_created(self) -> Dict[str, List[str]]:
            return {
                "tests": self.created_tests,
                "preconditions": self.created_preconditions,
                "executions": self.created_executions,
                "test_sets": self.created_test_sets,
                "test_plans": self.created_test_plans
            }
    
    return TestDataTracker()


@pytest.fixture
async def cleanup_helper(graphql_client, test_data_tracker):
    """Helper to clean up test data after tests."""
    yield  # Run the test
    
    # Cleanup after test
    created_data = test_data_tracker.get_all_created()
    
    # Delete all created test data
    for test_id in created_data["tests"]:
        try:
            await _delete_test(graphql_client, test_id)
        except Exception as e:
            print(f"Failed to delete test {test_id}: {e}")
    
    for prec_id in created_data["preconditions"]:
        try:
            await _delete_precondition(graphql_client, prec_id)
        except Exception as e:
            print(f"Failed to delete precondition {prec_id}: {e}")
    
    for exec_id in created_data["executions"]:
        try:
            await _delete_test_execution(graphql_client, exec_id)
        except Exception as e:
            print(f"Failed to delete execution {exec_id}: {e}")


async def _delete_test(client: XrayGraphQLClient, issue_id: str):
    """Delete a test via GraphQL."""
    mutation = """
    mutation DeleteTest($issueId: String!) {
        deleteTest(issueId: $issueId)
    }
    """
    await client.execute_query(mutation, {"issueId": issue_id})


async def _delete_precondition(client: XrayGraphQLClient, issue_id: str):
    """Delete a precondition via GraphQL."""
    mutation = """
    mutation DeletePrecondition($issueId: String!) {
        deletePrecondition(issueId: $issueId)
    }
    """
    await client.execute_query(mutation, {"issueId": issue_id})


async def _delete_test_execution(client: XrayGraphQLClient, issue_id: str):
    """Delete a test execution via GraphQL."""
    mutation = """
    mutation DeleteTestExecution($issueId: String!) {
        deleteTestExecution(issueId: $issueId)
    }
    """
    await client.execute_query(mutation, {"issueId": issue_id})


@pytest.fixture
def generate_test_name():
    """Generate unique test names for integration tests."""
    counter = 0
    
    def _generate(prefix: str = "Test") -> str:
        nonlocal counter
        counter += 1
        timestamp = datetime.now().strftime("%H%M%S")
        return f"{INTEGRATION_TEST_PREFIX}_{prefix}_{timestamp}_{counter}"
    
    return _generate


@pytest.fixture
def sample_test_steps():
    """Provide sample test steps for manual tests."""
    return [
        {
            "action": "Open the application",
            "data": "URL: https://example.com",
            "result": "Application loads successfully"
        },
        {
            "action": "Login with test credentials",
            "data": "Username: testuser, Password: ****",
            "result": "User is logged in and dashboard is displayed"
        },
        {
            "action": "Navigate to settings",
            "data": "Click on Settings menu",
            "result": "Settings page is displayed"
        }
    ]


@pytest.fixture
def sample_gherkin_scenario():
    """Provide sample Gherkin scenario for Cucumber tests."""
    return """
Scenario: User login with valid credentials
  Given I am on the login page
  When I enter valid username "testuser"
  And I enter valid password "password123"
  And I click the login button
  Then I should be redirected to the dashboard
  And I should see a welcome message
"""


@pytest.fixture
def sample_precondition_definition():
    """Provide sample precondition definition."""
    return """
1. Test environment is set up and accessible
2. Test user account exists with proper permissions
3. Test data is loaded in the database
4. All dependent services are running
"""


# Helper function to wait for eventual consistency
async def wait_for_consistency(seconds: float = 2.0):
    """Wait for Xray API eventual consistency."""
    await asyncio.sleep(seconds)