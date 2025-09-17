"""Simplified Xray MCP Server following FastMCP best practices."""

import os
import json
from typing import Dict, Any, Literal, List, Optional, Union
from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import ValidationError
from .auth import XrayAuth
from .graphql_client import XrayGraphQLClient
from .tools.xray_tool import XrayTool
from .schemas.models import StepInput
from .security import request_validator
from .config import config

# Load environment variables
load_dotenv()


def _format_mcp_response(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Format tool execution result for MCP protocol.

    Args:
        result: Raw tool execution result from XrayTool

    Returns:
        List of MCP content blocks
    """
    if result.get('success'):
        # Format successful response as text content
        if result.get('data'):
            content = {
                "type": "text",
                "text": json.dumps(result['data'], indent=2)
            }
        else:
            content = {
                "type": "text",
                "text": "Operation completed successfully"
            }

        # Add warnings if present
        if result.get('warnings'):
            warnings_text = "\n\nWarnings:\n" + "\n".join(f"- {w}" for w in result['warnings'])
            content["text"] += warnings_text

    else:
        # Format error response
        errors = result.get('errors', ['Unknown error occurred'])
        error_text = "Operation failed with the following errors:\n" + \
                    "\n".join(f"- {error}" for error in errors)

        content = {
            "type": "text",
            "text": error_text
        }

    return [content]


def create_server() -> FastMCP:
    """Create simplified FastMCP server with single tool registration.

    Returns:
        FastMCP: Configured server instance following FastMCP best practices

    Raises:
        ValueError: If required environment variables are missing
        Exception: If authentication fails
    """
    # Get required environment variables
    client_id = os.getenv('XRAY_CLIENT_ID')
    client_secret = os.getenv('XRAY_CLIENT_SECRET')
    base_url = os.getenv('XRAY_BASE_URL', 'https://xray.cloud.getxray.app')

    if not client_id:
        raise ValueError("XRAY_CLIENT_ID environment variable is required")
    if not client_secret:
        raise ValueError("XRAY_CLIENT_SECRET environment variable is required")

    # Create FastMCP server instance
    mcp = FastMCP("Xray Test Management")

    # Initialize authentication and GraphQL client
    auth = XrayAuth(client_id, client_secret, base_url)
    client = XrayGraphQLClient(auth)
    xray_tool = XrayTool(client)

    # Single tool registration following FastMCP patterns
    @mcp.tool(description="Manage Xray tests, executions, plans, and runs with unified interface")
    async def xray_test(
        entity: Literal["test", "test_execution", "test_plan", "test_run"],
        action: str,
        issue_id: Optional[str] = None,
        project_key: Optional[str] = None,
        summary: Optional[str] = None,
        test_type: Optional[Literal["Manual", "Generic", "Cucumber"]] = None,
        test_issue_ids: Optional[List[str]] = None,
        test_issue_id: Optional[str] = None,  # For test run operations (singular)
        test_exec_issue_ids: Optional[List[str]] = None,  # For plan execution associations
        limit: int = 50,
        start: int = 0,
        jql: Optional[str] = None,
        description: Optional[str] = None,
        steps: Optional[str] = None,
        gherkin: Optional[str] = None,
        status: Optional[str] = None,
        comment: Optional[str] = None,
        test_environments: Optional[List[str]] = None,
        test_execution_id: Optional[str] = None,
        defects: Optional[List[str]] = None,
        environments: Optional[List[str]] = None,
        id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Unified Xray tool for managing all entities with FastMCP simplicity.

        Args:
            entity: Entity type (test, test_execution, test_plan, test_run)
            action: Action to perform (create, get, update_status, list, delete, etc.)
            issue_id: Issue ID for specific operations
            project_key: Jira project key for create/list operations
            summary: Summary/title for create operations
            test_type: Test type for test creation (Manual, Generic, Cucumber)
            test_issue_ids: List of test issue IDs for associations
            test_issue_id: Single test issue ID for test run operations
            test_exec_issue_ids: List of test execution IDs for plan associations
            limit: Maximum results for list operations (max 100)
            start: Starting index for pagination
            jql: Custom JQL query for filtering
            description: Additional description for entities
            steps: JSON string of test steps for Manual tests. Each step must have 'action', 'data', and 'result' fields.
                   Example: '[{"action": "Click login button", "data": "Username: test", "result": "User logged in"}]'
            gherkin: Gherkin script for Cucumber tests
            status: Status for test run updates
            comment: Comment for test run updates
            test_environments: Test environments for executions
            test_execution_id: Test execution ID for test run operations
            defects: Defect list for test run operations

        Returns:
            Operation result with success status, data, warnings, and errors
        """
        # Ensure authentication before executing
        await auth.authenticate()

        # Parse and validate steps parameter if provided
        if steps is not None and steps.strip():
            try:
                # First, try to parse as JSON string (new format)
                if isinstance(steps, str):
                    try:
                        steps_data = json.loads(steps)
                    except json.JSONDecodeError as e:
                        return {
                            'success': False,
                            'errors': [
                                f"Invalid JSON in steps parameter: {str(e)}",
                                "Steps must be a valid JSON string",
                                "Expected format: '[{\"action\": \"text\", \"data\": \"text\", \"result\": \"text\"}]'",
                                "Example: '[{\"action\": \"Click login button\", \"data\": \"Username: test@example.com\", \"result\": \"User logged in successfully\"}]'"
                            ],
                            'data': None,
                            'warnings': []
                        }
                else:
                    # Backwards compatibility: accept list directly (from internal testing)
                    steps_data = steps

                # Validate that parsed data is a list
                if not isinstance(steps_data, list):
                    return {
                        'success': False,
                        'errors': [
                            f"Steps must be an array, got {type(steps_data).__name__}",
                            "Expected format: '[{\"action\": \"text\", \"data\": \"text\", \"result\": \"text\"}]'",
                            "Example: '[{\"action\": \"Click login button\", \"data\": \"Username: test@example.com\", \"result\": \"User logged in successfully\"}]'"
                        ],
                        'data': None,
                        'warnings': []
                    }

                # Validate each step using our StepInput model
                validated_steps = []
                for i, step in enumerate(steps_data):
                    try:
                        if isinstance(step, dict):
                            # Validate using Pydantic model
                            step_input = StepInput(**step)
                            validated_steps.append(step_input.model_dump())
                        else:
                            raise ValueError(f"Step {i+1} must be an object, got {type(step).__name__}")
                    except Exception as step_error:
                        return {
                            'success': False,
                            'errors': [
                                f"Invalid step {i+1}: {str(step_error)}",
                                "Each step must have 'action', 'data', and 'result' fields (all strings)",
                                "Expected format: '[{\"action\": \"text\", \"data\": \"text\", \"result\": \"text\"}]'",
                                "Example: '[{\"action\": \"Click login button\", \"data\": \"Username: test@example.com\", \"result\": \"User logged in successfully\"}]'"
                            ],
                            'data': None,
                            'warnings': []
                        }
                steps_dict = validated_steps
            except Exception as e:
                return {
                    'success': False,
                    'errors': [
                        f"Unexpected error processing steps: {str(e)}",
                        "Steps must be a JSON string containing an array of step objects",
                        "Expected format: '[{\"action\": \"text\", \"data\": \"text\", \"result\": \"text\"}]'",
                        "Example: '[{\"action\": \"Click login button\", \"data\": \"Username: test@example.com\", \"result\": \"User logged in successfully\"}]'"
                    ],
                    'data': None,
                    'warnings': []
                }
        else:
            steps_dict = []

        # Build parameters dictionary - let managers handle validation
        params = {
            'entity': entity,
            'action': action,
            'issue_id': issue_id,
            'project_key': project_key,
            'summary': summary,
            'test_type': test_type,
            'test_issue_ids': test_issue_ids or [],
            'test_issue_id': test_issue_id,  # For test run operations (singular)
            'test_exec_issue_ids': test_exec_issue_ids or [],  # For plan execution associations
            'limit': min(limit, 100),
            'start': start,
            'jql': jql,
            'description': description,
            'steps': steps_dict,
            'gherkin': gherkin,
            'status': status,
            'comment': comment,
            'test_environments': test_environments or [],
            'test_execution_id': test_execution_id,
            'defects': defects or [],
            'environments': environments or [],
            'id': id
        }

        # Remove None values to reduce payload
        params = {k: v for k, v in params.items() if v is not None}

        # Security validation and DoS protection
        client_id = "mcp_client"  # In production, derive from actual client context
        is_valid, error_messages = await request_validator.validate_request(client_id, params)

        if not is_valid:
            return _format_mcp_response({
                'success': False,
                'data': None,
                'warnings': [],
                'errors': [f"Request validation failed: {'; '.join(error_messages)}"]
            })

        # Execute using xray tool
        result = await xray_tool.execute(params)

        # Format result for MCP protocol
        return _format_mcp_response(result)

    # Add resources for read-only data access
    @mcp.resource("xray://documentation")
    async def xray_documentation() -> str:
        """Xray MCP Server documentation and usage examples."""
        return """
# Xray MCP Server Documentation

## Overview
This MCP server provides programmatic access to Xray Cloud's test management system.

## Main Tool: xray_test
Unified interface for all Xray operations.

### Creating a Manual Test with Steps:
```
entity: "test"
action: "create"
project_key: "YOUR_PROJECT"
test_type: "Manual"
summary: "Test title"
steps: '[{"action": "Click login", "data": "username field", "result": "User logged in"}]'
```

### Creating Test Execution:
```
entity: "test_execution"
action: "create"
project_key: "YOUR_PROJECT"
summary: "Execution title"
test_issue_ids: ["TEST-123", "TEST-124"]
```

### Available Actions by Entity:
- **test**: create, get, update, delete, list, update_type, update_content
- **test_execution**: create, get, delete, list, add_tests, remove_tests, add_environments, remove_environments
- **test_plan**: create, get, delete, list, add_tests, remove_tests, add_executions, remove_executions
- **test_run**: get, update_status, update_comment, add_defects, remove_defects

### Required Parameters:
- **create operations**: entity, action, project_key, summary
- **get/update/delete**: entity, action, issue_id
- **list operations**: entity, action, project_key (optional: jql, limit, start)

### Steps Format:
For Manual tests, provide steps as JSON string:
`'[{"action": "description", "data": "input data", "result": "expected outcome"}]'`
"""

    @mcp.resource("xray://project/{project_key}/tests")
    async def project_tests(project_key: str) -> str:
        """List tests in a specific project."""
        # Authenticate first
        await auth.authenticate()

        # Use our tool to get tests
        params = {
            'entity': 'test',
            'action': 'list',
            'project_key': project_key,
            'limit': 50
        }

        result = await xray_tool.execute(params)

        if result['success']:
            tests = result['data'].get('results', [])
            output = f"# Tests in Project {project_key}\n\n"

            if not tests:
                output += "No tests found in this project.\n"
            else:
                output += f"Found {len(tests)} tests:\n\n"
                for test in tests:
                    jira = test.get('jira', {})
                    test_type = test.get('testType', {}).get('name', 'Unknown')
                    output += f"- **{jira.get('key', 'N/A')}**: {jira.get('summary', 'No title')} ({test_type})\n"

            return output
        else:
            return f"Error fetching tests: {', '.join(result['errors'])}"

    @mcp.resource("xray://test/{issue_id}")
    async def test_details(issue_id: str) -> str:
        """Get detailed information about a specific test."""
        # Authenticate first
        await auth.authenticate()

        # Use our tool to get test details
        params = {
            'entity': 'test',
            'action': 'get',
            'issue_id': issue_id
        }

        result = await xray_tool.execute(params)

        if result['success']:
            test = result['data']
            jira = test.get('jira', {})
            test_type = test.get('testType', {}).get('name', 'Unknown')

            output = f"# Test Details: {jira.get('key', issue_id)}\n\n"
            output += f"**Summary**: {jira.get('summary', 'No title')}\n"
            output += f"**Type**: {test_type}\n"
            output += f"**Description**: {jira.get('description', 'No description')}\n"

            # Add steps if it's a manual test
            steps = test.get('steps', [])
            if steps:
                output += f"\n## Test Steps ({len(steps)} steps):\n\n"
                for i, step in enumerate(steps, 1):
                    output += f"### Step {i}\n"
                    output += f"**Action**: {step.get('action', 'N/A')}\n"
                    output += f"**Data**: {step.get('data', 'N/A')}\n"
                    output += f"**Expected Result**: {step.get('result', 'N/A')}\n\n"

            # Add Gherkin if it's a Cucumber test
            gherkin = test.get('gherkin')
            if gherkin:
                output += f"\n## Gherkin Script:\n```gherkin\n{gherkin}\n```\n"

            return output
        else:
            return f"Error fetching test {issue_id}: {', '.join(result['errors'])}"

    # Add prompts for guided workflows
    @mcp.prompt("create_manual_test")
    async def create_manual_test_prompt(
        project_key: Optional[str] = None,
        test_title: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """Interactive prompt to help create a manual test with proper step structure."""
        prompt = "# Create Manual Test Guide\n\n"

        if not project_key:
            prompt += "First, you need to specify the **project key** (e.g., 'FTEST', 'QA', 'PROJ').\n\n"

        if not test_title:
            prompt += "Next, provide a **test title/summary** that describes what this test validates.\n\n"

        if project_key and test_title:
            prompt += f"Creating manual test in project **{project_key}**: \"{test_title}\"\n\n"

            if description:
                prompt += f"Description: {description}\n\n"

            prompt += "## Test Steps Structure\n"
            prompt += "Each step should have three components:\n\n"
            prompt += "1. **Action**: What the tester should do\n"
            prompt += "2. **Data**: Input data or conditions\n"
            prompt += "3. **Result**: Expected outcome\n\n"

            prompt += "### Example Steps:\n"
            prompt += "```json\n"
            prompt += '[\n'
            prompt += '  {\n'
            prompt += '    "action": "Navigate to login page",\n'
            prompt += '    "data": "Open https://app.example.com/login",\n'
            prompt += '    "result": "Login page displays with username and password fields"\n'
            prompt += '  },\n'
            prompt += '  {\n'
            prompt += '    "action": "Enter valid credentials",\n'
            prompt += '    "data": "Username: testuser@example.com, Password: Test123!",\n'
            prompt += '    "result": "User is successfully logged in and redirected to dashboard"\n'
            prompt += '  }\n'
            prompt += ']\n'
            prompt += "```\n\n"

            prompt += "### Tool Call Template:\n"
            prompt += "```\n"
            prompt += "entity: \"test\"\n"
            prompt += "action: \"create\"\n"
            prompt += f"project_key: \"{project_key}\"\n"
            prompt += f"summary: \"{test_title}\"\n"
            prompt += "test_type: \"Manual\"\n"
            if description:
                prompt += f"description: \"{description}\"\n"
            prompt += "steps: '[{\"action\": \"...\", \"data\": \"...\", \"result\": \"...\"}]'\n"
            prompt += "```\n"

        return prompt

    @mcp.prompt("create_test_execution")
    async def create_test_execution_prompt(
        project_key: Optional[str] = None,
        execution_title: Optional[str] = None,
        test_ids: Optional[str] = None
    ) -> str:
        """Guide for creating test executions."""
        prompt = "# Create Test Execution Guide\n\n"

        prompt += "A test execution groups multiple tests to be run together.\n\n"

        if not project_key:
            prompt += "**Step 1**: Specify the project key where tests exist.\n\n"

        if not execution_title:
            prompt += "**Step 2**: Provide an execution title (e.g., 'Sprint 5 Regression Tests').\n\n"

        if not test_ids:
            prompt += "**Step 3**: List the test issue IDs to include (e.g., ['TEST-123', 'TEST-124']).\n\n"

        if project_key and execution_title:
            prompt += f"Creating execution in project **{project_key}**: \"{execution_title}\"\n\n"

            prompt += "### Tool Call Template:\n"
            prompt += "```\n"
            prompt += "entity: \"test_execution\"\n"
            prompt += "action: \"create\"\n"
            prompt += f"project_key: \"{project_key}\"\n"
            prompt += f"summary: \"{execution_title}\"\n"
            if test_ids:
                prompt += f"test_issue_ids: {test_ids}\n"
            else:
                prompt += "test_issue_ids: [\"TEST-123\", \"TEST-124\"]\n"
            prompt += "test_environments: [\"staging\", \"production\"]  # Optional\n"
            prompt += "```\n"

        return prompt

    @mcp.prompt("bdd_converter")
    async def bdd_converter_prompt(requirement: Optional[str] = None) -> str:
        """Convert plain text requirements to Gherkin format for Cucumber tests."""
        prompt = "# BDD/Gherkin Converter\n\n"

        if not requirement:
            prompt += "Provide a plain text requirement or user story to convert to Gherkin format.\n\n"
            prompt += "**Example requirement:**\n"
            prompt += "\"Users should be able to log in with valid credentials and see their dashboard.\"\n\n"
        else:
            prompt += f"**Requirement:** {requirement}\n\n"

            prompt += "## Gherkin Conversion:\n\n"
            prompt += "```gherkin\n"
            prompt += "Feature: User Authentication\n"
            prompt += "  As a registered user\n"
            prompt += "  I want to log in with my credentials\n"
            prompt += "  So that I can access my dashboard\n\n"
            prompt += "Scenario: Successful login with valid credentials\n"
            prompt += "  Given I am on the login page\n"
            prompt += "  When I enter valid username and password\n"
            prompt += "  And I click the login button\n"
            prompt += "  Then I should be logged in successfully\n"
            prompt += "  And I should see my dashboard\n"
            prompt += "```\n\n"

            prompt += "### Tool Call Template:\n"
            prompt += "```\n"
            prompt += "entity: \"test\"\n"
            prompt += "action: \"create\"\n"
            prompt += "project_key: \"YOUR_PROJECT\"\n"
            prompt += "summary: \"User Authentication Test\"\n"
            prompt += "test_type: \"Cucumber\"\n"
            prompt += "description: \"Test user login functionality\"\n"
            prompt += "gherkin: \"Feature: User Authentication...\"  # Full Gherkin script\n"
            prompt += "```\n"

        return prompt

    return mcp


# Alias for any existing references
create_simplified_server = create_server


if __name__ == "__main__":
    # Run the server
    server = create_server()
    # In production, you'd use uvicorn or similar to run this
    print("Simplified Xray MCP Server created successfully!")
    print("Available tools:", [tool.name for tool in server._tool_manager._tools.values()])