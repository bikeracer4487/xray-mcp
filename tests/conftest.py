"""
Shared pytest configuration and fixtures for Xray MCP integration tests.

Provides common fixtures, utilities, and configuration for all test modules.
"""

import pytest
import pytest_asyncio
import asyncio
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from src.server import create_server
from src.tools.xray_tool import XrayTool
from src.auth import XrayAuth
from src.graphql_client import XrayGraphQLClient
from tests.fixtures.test_data_generators import TestDataGenerator


# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def server():
    """Create a server instance for the entire test session."""
    return create_server()


@pytest.fixture(scope="session")
def xray_client():
    """Create XrayGraphQLClient for testing."""
    client_id = os.getenv('XRAY_CLIENT_ID')
    client_secret = os.getenv('XRAY_CLIENT_SECRET')
    base_url = os.getenv('XRAY_BASE_URL', 'https://xray.cloud.getxray.app')

    if not client_id or not client_secret:
        pytest.skip("Xray credentials not configured (XRAY_CLIENT_ID, XRAY_CLIENT_SECRET)")

    auth = XrayAuth(client_id, client_secret, base_url)
    return XrayGraphQLClient(auth)


@pytest.fixture(scope="session")
def global_tool(xray_client):
    """Create a tool instance for the entire test session."""
    return XrayTool(xray_client)


@pytest.fixture
def tool(xray_client):
    """Create a fresh tool instance for each test."""
    return XrayTool(xray_client)


@pytest.fixture
def unique_prefix():
    """Generate unique prefix for test resources."""
    return f"Test_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"


@pytest.fixture
def project_key():
    """Get project key from environment with validation."""
    key = os.getenv('XRAY_PROJECT_KEY', 'FTEST')
    if not key:
        pytest.skip("XRAY_PROJECT_KEY environment variable not set")
    return key


@pytest.fixture
def test_data_generator(unique_prefix):
    """Create test data generator with unique prefix."""
    return TestDataGenerator(unique_prefix)


@pytest.fixture
def sample_manual_test_data(test_data_generator):
    """Generate sample manual test data."""
    return test_data_generator.generate_manual_test_case("medium")


@pytest.fixture
def sample_bdd_test_data(test_data_generator):
    """Generate sample BDD test data."""
    return test_data_generator.generate_bdd_test_case("web")


@pytest.fixture
def sample_execution_data(test_data_generator):
    """Generate sample test execution data."""
    return test_data_generator.generate_test_execution_data()


@pytest.fixture
def sample_plan_data(test_data_generator):
    """Generate sample test plan data."""
    return test_data_generator.generate_test_plan_data("release")


@pytest.fixture
def multilingual_test_data(test_data_generator):
    """Generate multilingual test data."""
    return test_data_generator.generate_multilingual_test_data()


@pytest.fixture
def edge_case_test_data(test_data_generator):
    """Generate edge case test data."""
    return test_data_generator.generate_edge_case_test_data()


@pytest.fixture
def performance_test_data(test_data_generator):
    """Generate performance test data."""
    return test_data_generator.generate_performance_test_data()


class ResourceManager:
    """Manages test resources and cleanup."""

    def __init__(self):
        self.created_resources = []

    def add_resource(self, resource_type: str, resource_id: str):
        """Add a resource for cleanup."""
        self.created_resources.append((resource_type, resource_id))

    async def cleanup_all(self, tool: XrayTool):
        """Clean up all tracked resources."""
        cleanup_errors = []

        for resource_type, resource_id in reversed(self.created_resources):
            try:
                result = await tool.execute({
                    'entity': resource_type,
                    'action': 'delete',
                    'issue_id': resource_id
                })

                if not result.get('success'):
                    cleanup_errors.append(f"Failed to delete {resource_type} {resource_id}: {result.get('errors', [])}")

            except Exception as e:
                cleanup_errors.append(f"Exception deleting {resource_type} {resource_id}: {str(e)}")

        if cleanup_errors:
            logging.warning(f"Cleanup errors: {cleanup_errors}")

        self.created_resources.clear()


@pytest.fixture
def resource_manager():
    """Provide resource manager for tracking test resources."""
    return ResourceManager()


@pytest_asyncio.fixture
async def auto_cleanup_tool(tool, resource_manager):
    """Tool with automatic resource cleanup."""
    original_execute = tool.execute

    async def execute_with_tracking(*args, **kwargs):
        result = await original_execute(*args, **kwargs)

        # Track successful creations for cleanup
        if result.get('success') and len(args) > 0:
            params = args[0] if args else kwargs
            if params.get('action') == 'create':
                entity = params.get('entity')
                if entity == 'test' and 'test' in result.get('data', {}):
                    resource_id = result['data']['test']['issueId']
                    resource_manager.add_resource('test', resource_id)
                elif entity == 'test_execution' and 'testExecution' in result.get('data', {}):
                    resource_id = result['data']['testExecution']['issueId']
                    resource_manager.add_resource('test_execution', resource_id)
                elif entity == 'test_plan' and 'testPlan' in result.get('data', {}):
                    resource_id = result['data']['testPlan']['issueId']
                    resource_manager.add_resource('test_plan', resource_id)

        return result

    tool.execute = execute_with_tracking
    yield tool

    # Cleanup after test
    await resource_manager.cleanup_all(tool)


@pytest.fixture
def xray_credentials():
    """Get Xray credentials from environment."""
    client_id = os.getenv('XRAY_CLIENT_ID')
    client_secret = os.getenv('XRAY_CLIENT_SECRET')

    if not client_id or not client_secret:
        pytest.skip("Xray credentials not configured (XRAY_CLIENT_ID, XRAY_CLIENT_SECRET)")

    return {
        'client_id': client_id,
        'client_secret': client_secret
    }


@pytest.fixture
def skip_if_no_credentials():
    """Skip test if Xray credentials are not available."""
    client_id = os.getenv('XRAY_CLIENT_ID')
    client_secret = os.getenv('XRAY_CLIENT_SECRET')

    if not client_id or not client_secret:
        pytest.skip("Xray credentials not configured")


@pytest.fixture
def test_timeout():
    """Default timeout for test operations."""
    return 30.0  # 30 seconds


# Utility functions for common test operations

async def create_test_and_track(tool: XrayTool, resource_manager: ResourceManager,
                               test_data: Dict[str, Any], project_key: str) -> str:
    """Create a test and track it for cleanup."""
    test_data['project_key'] = project_key

    result = await tool.execute({
        'entity': 'test',
        'action': 'create',
        **test_data
    })

    if result['success']:
        test_id = result['data']['test']['issueId']
        resource_manager.add_resource('test', test_id)
        return test_id
    else:
        raise Exception(f"Failed to create test: {result.get('errors', [])}")


async def create_execution_and_track(tool: XrayTool, resource_manager: ResourceManager,
                                   execution_data: Dict[str, Any], project_key: str) -> str:
    """Create a test execution and track it for cleanup."""
    execution_data['project_key'] = project_key

    result = await tool.execute({
        'entity': 'test_execution',
        'action': 'create',
        **execution_data
    })

    if result['success']:
        execution_id = result['data']['testExecution']['issueId']
        resource_manager.add_resource('test_execution', execution_id)
        return execution_id
    else:
        raise Exception(f"Failed to create execution: {result.get('errors', [])}")


async def create_plan_and_track(tool: XrayTool, resource_manager: ResourceManager,
                              plan_data: Dict[str, Any], project_key: str) -> str:
    """Create a test plan and track it for cleanup."""
    plan_data['project_key'] = project_key

    result = await tool.execute({
        'entity': 'test_plan',
        'action': 'create',
        **plan_data
    })

    if result['success']:
        plan_id = result['data']['testPlan']['issueId']
        resource_manager.add_resource('test_plan', plan_id)
        return plan_id
    else:
        raise Exception(f"Failed to create plan: {result.get('errors', [])}")


def assert_successful_response(result: Dict[str, Any], operation: str = "operation"):
    """Assert that a response indicates success."""
    assert result is not None, f"{operation} should return a result"
    assert isinstance(result, dict), f"{operation} should return a dictionary"
    assert result.get('success') is True, f"{operation} should succeed: {result.get('errors', [])}"
    assert 'data' in result, f"{operation} should return data"


def assert_failed_response(result: Dict[str, Any], operation: str = "operation"):
    """Assert that a response indicates failure."""
    assert result is not None, f"{operation} should return a result"
    assert isinstance(result, dict), f"{operation} should return a dictionary"
    assert result.get('success') is False, f"{operation} should fail"
    assert 'errors' in result, f"{operation} should return error information"


# Performance testing utilities

class PerformanceTimer:
    """Context manager for timing operations."""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
        self.duration = None

    def __enter__(self):
        import time
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        logging.info(f"{self.operation_name} took {self.duration:.3f} seconds")

    def assert_duration_under(self, max_seconds: float):
        """Assert that the operation completed within the specified time."""
        assert self.duration is not None, "Timer not completed"
        assert self.duration < max_seconds, \
            f"{self.operation_name} took {self.duration:.3f}s, expected < {max_seconds}s"


@pytest.fixture
def performance_timer():
    """Performance timer fixture."""
    return PerformanceTimer


# Test markers for categorization

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "edge_case: marks tests as edge case tests"
    )
    config.addinivalue_line(
        "markers", "error_handling: marks tests as error handling tests"
    )
    config.addinivalue_line(
        "markers", "multilingual: marks tests as multilingual tests"
    )
    config.addinivalue_line(
        "markers", "workflow: marks tests as workflow tests"
    )


# Test data validation utilities

def validate_test_response(response: Dict[str, Any], entity_type: str):
    """Validate the structure of a test response."""
    assert_successful_response(response, f"{entity_type} response")

    data = response['data']
    assert entity_type.replace('_', '') in data, f"Response should contain {entity_type} data"

    entity_data = data[entity_type.replace('_', '')]
    assert 'issueId' in entity_data, f"{entity_type} should have issueId"
    assert 'jira' in entity_data, f"{entity_type} should have jira data"

    jira_data = entity_data['jira']
    assert 'key' in jira_data, f"{entity_type} jira data should have key"
    assert 'summary' in jira_data, f"{entity_type} jira data should have summary"


def validate_gherkin_content(gherkin: str):
    """Validate Gherkin content structure."""
    assert 'Feature:' in gherkin, "Gherkin should contain Feature definition"
    assert any(keyword in gherkin for keyword in ['Scenario:', 'Scenario Outline:']), \
        "Gherkin should contain scenarios"
    assert 'Given' in gherkin, "Gherkin should contain Given steps"
    assert 'When' in gherkin, "Gherkin should contain When steps"
    assert 'Then' in gherkin, "Gherkin should contain Then steps"


def validate_manual_test_steps(steps: List[Dict[str, Any]]):
    """Validate manual test steps structure."""
    assert isinstance(steps, list), "Steps should be a list"
    assert len(steps) > 0, "Should have at least one step"

    for i, step in enumerate(steps):
        assert isinstance(step, dict), f"Step {i+1} should be a dictionary"
        required_fields = ['action', 'data', 'result']
        for field in required_fields:
            assert field in step, f"Step {i+1} should have {field} field"
            assert isinstance(step[field], str), f"Step {i+1} {field} should be a string"
            assert len(step[field]) > 0, f"Step {i+1} {field} should not be empty"