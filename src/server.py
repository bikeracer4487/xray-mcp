"""Simplified Xray MCP Server following FastMCP best practices."""

import os
import json
import logging
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

# Setup logger for this module
logger = logging.getLogger(__name__)

# Load environment variables
logger.info("Loading environment variables from .env")
load_dotenv()
logger.info("Environment variables loaded")


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
            # Include warnings in the JSON structure if present
            response_data = result['data'].copy()
            if result.get('warnings'):
                response_data['warnings'] = result['warnings']

            content = {
                "type": "text",
                "text": json.dumps(response_data, indent=2)
            }
        else:
            response_data = {"message": "Operation completed successfully"}
            if result.get('warnings'):
                response_data['warnings'] = result['warnings']

            content = {
                "type": "text",
                "text": json.dumps(response_data, indent=2)
            }

    else:
        # Format error response
        errors = result.get('errors', ['Unknown error occurred'])
        error_text = "Operation failed with the following errors:\n" + \
                    "\n".join(f"- {error}" for error in errors)

        content = {
            "type": "text",
            "text": error_text
        }

    # Return in MCP format: list of content objects (NOT a dict)
    # This is the correct MCP response format, despite any "structured_content must be a dict" messages
    return [content]


def create_server() -> FastMCP:
    """Create simplified FastMCP server with single tool registration.

    Returns:
        FastMCP: Configured server instance following FastMCP best practices

    Raises:
        ValueError: If required environment variables are missing
        Exception: If authentication fails
    """
    logger.info("=" * 60)
    logger.info("create_server() called")
    logger.info("=" * 60)

    # Get required environment variables
    client_id = os.getenv('XRAY_CLIENT_ID')
    client_secret = os.getenv('XRAY_CLIENT_SECRET')
    base_url = os.getenv('XRAY_BASE_URL', 'https://xray.cloud.getxray.app')

    logger.info(f"XRAY_CLIENT_ID present: {bool(client_id)}")
    logger.info(f"XRAY_CLIENT_SECRET present: {bool(client_secret)}")
    logger.info(f"XRAY_BASE_URL: {base_url}")

    if not client_id:
        logger.error("XRAY_CLIENT_ID environment variable is missing")
        raise ValueError("XRAY_CLIENT_ID environment variable is required")
    if not client_secret:
        logger.error("XRAY_CLIENT_SECRET environment variable is missing")
        raise ValueError("XRAY_CLIENT_SECRET environment variable is required")

    # Create FastMCP server instance
    logger.info("Creating FastMCP server instance...")
    try:
        mcp = FastMCP(
            "Xray Test Management",
            instructions="Create and manage Xray Cloud tests, executions, plans, and runs via unified xray_test tool. Use prompt 'help' to get started, or check resource 'xray://documentation' for comprehensive examples."
        )
        logger.info("FastMCP server instance created successfully")
    except Exception as e:
        logger.error(f"Failed to create FastMCP instance: {e}", exc_info=True)
        raise

    # Initialize authentication and GraphQL client
    logger.info("Initializing authentication...")
    try:
        auth = XrayAuth(client_id, client_secret, base_url)
        logger.info("XrayAuth initialized")
    except Exception as e:
        logger.error(f"Failed to initialize XrayAuth: {e}", exc_info=True)
        raise

    logger.info("Initializing GraphQL client...")
    try:
        client = XrayGraphQLClient(auth)
        logger.info("XrayGraphQLClient initialized")
    except Exception as e:
        logger.error(f"Failed to initialize XrayGraphQLClient: {e}", exc_info=True)
        raise

    logger.info("Initializing XrayTool...")
    try:
        xray_tool = XrayTool(client)
        logger.info("XrayTool initialized")
    except Exception as e:
        logger.error(f"Failed to initialize XrayTool: {e}", exc_info=True)
        raise

    # Single tool registration following FastMCP patterns
    logger.info("Registering 'xray_test' tool...")
    @mcp.tool()
    async def xray_test(
        entity: Literal["test", "test_execution", "test_plan", "test_run"],
        action: str,  # Available actions: create, get, update_status, list, delete, search, add_tests, remove_tests, etc.
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
        steps: Optional[Union[str, List[Dict[str, str]]]] = None,
        gherkin: Optional[str] = None,
        status: Optional[str] = None,
        comment: Optional[str] = None,
        test_environments: Optional[List[str]] = None,
        test_execution_id: Optional[str] = None,
        defects: Optional[List[str]] = None,
        environments: Optional[List[str]] = None,
        id: Optional[str] = None,
        retry_on_empty_results: Optional[bool] = None,
        # Search-specific parameters
        text: Optional[str] = None,
        recent_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Unified tool for managing Xray Cloud tests, executions, plans, and runs.

        Use 'entity' and 'action' parameters to specify operations.
        Check the 'help' prompt or xray://documentation resource for detailed examples.

        Args:
            entity: Entity type (test, test_execution, test_plan, test_run)
            action: Action to perform (create, get, list, search, update_status, delete, etc.)

        Returns:
            Operation result with success, data, warnings, and errors
        """
        logger.info(f"xray_test() called: entity={entity}, action={action}")

        # Ensure authentication before executing
        logger.debug("Authenticating with Xray API...")
        try:
            await auth.authenticate()
            logger.debug("Authentication successful")
        except Exception as e:
            logger.error(f"Authentication failed: {e}", exc_info=True)
            return {
                'success': False,
                'data': None,
                'warnings': [],
                'errors': [f"Authentication failed: {str(e)}"]
            }

        # Parse and validate steps parameter if provided
        if steps is not None and (isinstance(steps, list) or (isinstance(steps, str) and steps.strip())):
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

        # Build parameters dictionary - preserve None values for arrays so managers can validate properly
        params = {
            'entity': entity,
            'action': action,
            'issue_id': issue_id,
            'project_key': project_key,
            'summary': summary,
            'test_type': test_type,
            'test_issue_ids': test_issue_ids,  # Preserve None to distinguish from empty array
            'test_issue_id': test_issue_id,  # For test run operations (singular)
            'test_exec_issue_ids': test_exec_issue_ids,  # Preserve None to distinguish from empty array
            'limit': min(limit, 100),
            'start': start,
            'jql': jql,
            'description': description,
            'steps': steps_dict,
            'gherkin': gherkin,
            'status': status,
            'comment': comment,
            'test_environments': test_environments,  # Preserve None to distinguish from empty array
            'test_execution_id': test_execution_id,
            'defects': defects,  # Preserve None to distinguish from empty array
            'environments': environments,  # Preserve None to distinguish from empty array
            'id': id,
            'retry_on_empty_results': retry_on_empty_results,
            # Search parameters
            'text': text,
            'recent_days': recent_days
        }

        # Remove None values to reduce payload, but preserve array parameters that need None distinction
        # These array parameters need to distinguish between None (not provided) and [] (empty array)
        array_params_requiring_none = {
            'test_issue_ids', 'test_exec_issue_ids', 'test_environments',
            'defects', 'environments'
        }
        params = {
            k: v for k, v in params.items()
            if v is not None or k in array_params_requiring_none
        }

        # Security validation and DoS protection
        client_id = "mcp_client"  # In production, derive from actual client context
        is_valid, error_messages = await request_validator.validate_request(client_id, params)

        if not is_valid:
            return {
                'success': False,
                'data': None,
                'warnings': [],
                'errors': [f"Request validation failed: {'; '.join(error_messages)}"]
            }

        # Execute using xray tool
        result = await xray_tool.execute(params)

        # Return result directly - FastMCP handles formatting automatically
        if result.get('success'):
            # For successful operations, return the data with any warnings
            response_data = result['data'].copy()
            if result.get('warnings'):
                response_data['warnings'] = result['warnings']
            return response_data
        else:
            # For errors, let FastMCP handle the error formatting
            error_message = "Operation failed: " + "; ".join(result.get('errors', ['Unknown error']))
            raise Exception(error_message)

    # Simple test tool for diagnostic purposes (no authentication required)
    logger.info("Registering 'test_ping' tool for diagnostics...")
    @mcp.tool()
    async def test_ping(message: str = "Hello") -> str:
        """Simple diagnostic tool that echoes back a message. No authentication required.

        This tool exists to help diagnose MCP integration issues. If clients can see and
        call this tool but not xray_test, the issue is likely with xray_test's complexity
        or authentication requirements.

        Args:
            message: Optional message to echo back (default: "Hello")

        Returns:
            A pong response with the provided message
        """
        logger.info(f"test_ping() called with message='{message}'")
        response = f"Pong! You said: {message}"
        logger.info(f"test_ping() returning: {response}")
        return response

    logger.info("test_ping tool registered successfully")

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

### Adding Tests to Execution:
```
entity: "test_execution"
action: "add_tests"
issue_id: "EXEC-123"
test_issue_ids: ["TEST-456", "TEST-789"]
```

### Creating Test Plan with Tests:
```
entity: "test_plan"
action: "create"
project_key: "YOUR_PROJECT"
summary: "Plan title"
test_issue_ids: ["TEST-123", "TEST-124"]
```

### Available Actions by Entity:
- **test**: create, get, update, delete, list, search, update_type, update_content
- **test_execution**: create, get, delete, list, search, add_tests, remove_tests, add_environments, remove_environments
- **test_plan**: create, get, delete, list, search, add_tests, remove_tests, add_executions, remove_executions
- **test_run**: get, update_status, update_comment, add_defects, remove_defects

### Required Parameters:
- **create operations**: entity, action, project_key, summary
- **get/update/delete**: entity, action, issue_id
- **list operations**: entity, action, project_key (optional: jql, limit, start)
- **search operations**: entity, action, plus at least one filter (text, project_key, test_type, or recent_days)
- **add/remove operations**: entity, action, issue_id, plus specific array parameters

### Array Parameter Format:
Array parameters (test_issue_ids, test_environments, defects, etc.) should be provided as JSON arrays:

**✅ Correct formats:**
- `["FTEST-1298", "FTEST-1299"]` (test IDs)
- `["staging", "production"]` (environments)
- `["BUG-123", "BUG-456"]` (defects)
- `[]` (empty array for optional parameters)

**❌ Incorrect formats:**
- `"FTEST-1298,FTEST-1299"` (comma-separated string)
- `"FTEST-1298"` (single string instead of array)
- `null` (use empty array `[]` instead)

**Example usage:**
```yaml
entity: "test_execution"
action: "create"
project_key: "FTEST"
summary: "Sprint 1 Testing"
test_issue_ids: ["FTEST-100", "FTEST-101"]
test_environments: ["staging", "production"]
```

### Search Operations:
The search action provides user-friendly querying across all entity types with smart JQL generation.

**Search by keyword:**
```yaml
entity: "test"
action: "search"
text: "login"
project_key: "FTEST"
```

**Search recent items:**
```yaml
entity: "test_execution"
action: "search"
project_key: "FTEST"
recent_days: 7
```

**Search with multiple filters:**
```yaml
entity: "test"
action: "search"
text: "authentication"
test_type: "Manual"
project_key: "SECURITY"
recent_days: 14
limit: 10
```

**Search parameters:**
- `text`: Keyword search in titles and descriptions
- `project_key`: Limit to specific project
- `test_type`: For tests only (Manual, Generic, Cucumber)
- `recent_days`: Items updated in last N days
- `limit`: Maximum results (default 20, max 50)

Search returns helpful context including generated JQL and search tips.

### Steps Format:
For Manual tests, provide steps as JSON string:
`'[{"action": "description", "data": "input data", "result": "expected outcome"}]'`

### Known Limitations and Workarounds:

#### 1. Test Metadata Updates (TestManager)
**Limitation**: Cannot update test summary or description via GraphQL API.
**Reason**: Xray Cloud GraphQL API doesn't support metadata-only updates.
**Workarounds**:
- Use Jira's web interface to update metadata manually
- Use Jira's REST API separately (requires additional authentication)
- When updating test content, include metadata changes in the same operation

#### 2. Test Run Creation/Deletion (RunManager)
**Limitation**: Cannot directly create or delete test runs.
**Reason**: Test runs are automatically managed by Xray when tests are added/removed from executions.
**Workarounds**:
- Add tests to executions to create runs: `entity="test_execution", action="add_tests"`
- Remove tests from executions to delete runs: `entity="test_execution", action="remove_tests"`

#### 3. Evidence Upload (RunManager)
**Limitation**: Cannot upload evidence files to test runs.
**Reason**: Requires multipart file upload infrastructure not implemented in this MCP server.
**Workarounds**:
- Upload evidence manually through Jira/Xray web interface
- Use Xray's REST API with proper file upload handling
- Add file paths or URLs in test run comments as references

#### 4. Complex JQL Queries
**Limitation**: Some advanced JQL features may not work with all operations.
**Reason**: GraphQL API has different limitations than Jira's native JQL.
**Workarounds**:
- Use simpler JQL queries with basic operators
- Use search action for user-friendly filtering instead of complex JQL
- Combine multiple simple queries for complex requirements

#### 5. ID Format Requirements
**Limitation**: Must use numeric issue IDs, not JIRA keys.
**Reason**: Xray GraphQL API requires numeric IDs for all operations.
**Workarounds**:
- Use list operations to find numeric IDs for JIRA keys
- Store numeric ID mappings for frequently used entities
- Use search operations to find entities by name/description

### Response Format:
This MCP tool returns responses in the standard MCP format (list of content objects).
Each response contains structured data that can be parsed as JSON for programmatic use.
"""

    @mcp.resource("xray://capabilities")
    async def xray_capabilities() -> str:
        """Complete list of all available operations organized by entity type."""
        return """
# Xray MCP Server Capabilities

## Entity: test

### Actions:
- **create** - Create a new test (Manual, Generic, or Cucumber)
  - Required: project_key, summary, test_type
  - Optional: description, steps (for Manual), gherkin (for Cucumber)

- **get** - Retrieve test details by ID
  - Required: issue_id (numeric ID)

- **list** - List tests with optional filtering
  - Required: project_key
  - Optional: jql, limit, start

- **search** - User-friendly test search
  - Optional: text, project_key, test_type, recent_days
  - At least one filter required

- **update_type** - Change test type
  - Required: issue_id, test_type

- **update_content** - Update Gherkin content for Cucumber tests
  - Required: issue_id, gherkin

- **delete** - Delete a test
  - Required: issue_id

### Example:
```
xray_test(
    entity="test",
    action="create",
    project_key="DEMO",
    summary="Login Test",
    test_type="Manual",
    steps='[{"action": "Navigate", "data": "URL", "result": "Page loads"}]'
)
```

---

## Entity: test_execution

### Actions:
- **create** - Create a new test execution
  - Required: project_key, summary
  - Optional: test_issue_ids, test_environments, description

- **get** - Retrieve execution details
  - Required: issue_id

- **list** - List executions
  - Required: project_key
  - Optional: jql, limit, start

- **search** - Search executions
  - Optional: text, project_key, recent_days
  - At least one filter required

- **delete** - Delete an execution
  - Required: issue_id

- **add_tests** - Add tests to execution
  - Required: issue_id, test_issue_ids (array of numeric IDs)

- **remove_tests** - Remove tests from execution
  - Required: issue_id, test_issue_ids

- **add_environments** - Add test environments
  - Required: issue_id, test_environments (array of strings)

- **remove_environments** - Remove test environments
  - Required: issue_id, test_environments

### Example:
```
xray_test(
    entity="test_execution",
    action="create",
    project_key="DEMO",
    summary="Sprint 10 Tests",
    test_issue_ids=["123", "456"],
    test_environments=["staging", "qa"]
)
```

---

## Entity: test_plan

### Actions:
- **create** - Create a new test plan
  - Required: project_key, summary
  - Optional: test_issue_ids, description

- **get** - Retrieve plan details
  - Required: issue_id

- **list** - List test plans
  - Required: project_key
  - Optional: jql, limit, start

- **search** - Search test plans
  - Optional: text, project_key, recent_days
  - At least one filter required

- **delete** - Delete a test plan
  - Required: issue_id

- **add_tests** - Add tests to plan
  - Required: issue_id, test_issue_ids

- **remove_tests** - Remove tests from plan
  - Required: issue_id, test_issue_ids

- **add_executions** - Add test executions to plan
  - Required: issue_id, test_exec_issue_ids (array of execution IDs)

- **remove_executions** - Remove executions from plan
  - Required: issue_id, test_exec_issue_ids

### Example:
```
xray_test(
    entity="test_plan",
    action="create",
    project_key="DEMO",
    summary="Q1 2024 Test Plan",
    test_issue_ids=["123", "456", "789"]
)
```

---

## Entity: test_run

**Note:** Test runs are automatically created when tests are added to executions.
You cannot directly create or delete test runs - only update their status and details.

### Actions:
- **get** - Retrieve test run details
  - Required: test_execution_id, test_issue_id

- **list** - List test runs
  - Required: test_execution_id
  - Optional: limit, start

- **update_status** - Update test run status
  - Required: test_execution_id, test_issue_id, status
  - Optional: comment
  - Valid statuses: PASS, FAIL, EXECUTING, TODO, ABORTED

- **update_comment** - Update test run comments
  - Required: test_execution_id, test_issue_id, comment

- **add_defects** - Link defects to test run
  - Required: test_execution_id, test_issue_id, defects (array of issue IDs)

- **remove_defects** - Unlink defects from test run
  - Required: test_execution_id, test_issue_id, defects

### Example:
```
xray_test(
    entity="test_run",
    action="update_status",
    test_execution_id="500",
    test_issue_id="123",
    status="PASS",
    comment="All test steps passed successfully"
)
```

---

## Special Parameters

### Array Parameters
All array parameters must be JSON arrays:
- **test_issue_ids**: `["123", "456", "789"]`
- **test_exec_issue_ids**: `["500", "501"]`
- **test_environments**: `["staging", "qa", "production"]`
- **defects**: `["BUG-123", "BUG-456"]`

### Steps Parameter (for Manual tests)
Must be JSON string containing array of step objects:
```
steps='[
    {"action": "Step description", "data": "Input data", "result": "Expected result"},
    {"action": "Next step", "data": "More data", "result": "Next result"}
]'
```

### ID Format
⚠️ **CRITICAL:** Always use numeric issue IDs (e.g., "1192649"), not JIRA keys (e.g., "TEST-123").
Use `list` or `search` operations first to obtain numeric IDs.

---

## Search vs List

**Use `search` when:**
- You want user-friendly keyword search
- You need recent items (recent_days parameter)
- You want automatic JQL generation
- You're not sure of the exact JQL syntax

**Use `list` when:**
- You need precise JQL control
- You want all items in a project
- You have specific JQL requirements

---

## Response Format

All operations return structured JSON:
```json
{
    "success": true,
    "data": {...},
    "warnings": ["Optional warnings about indexing delays, etc."]
}
```

Or on error:
```json
{
    "success": false,
    "errors": ["Error message 1", "Error message 2"]
}
```

---

## Common Workflows

**Workflow 1: Create and Execute Tests**
1. Create tests → Get numeric IDs from response
2. Create execution with test IDs
3. Update test run statuses

**Workflow 2: Sprint Testing**
1. Create test plan for sprint
2. Add tests to plan
3. Create execution for sprint
4. Add execution to plan
5. Execute and update statuses

**Workflow 3: Regression Suite**
1. Search for tests with specific labels
2. Create execution with found tests
3. Update statuses as tests are executed
4. Link defects to failed tests

---

For detailed examples and complete documentation, check resource: `xray://documentation`
For getting started guide, use prompt: `help`
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
    @mcp.prompt("help")
    async def help_prompt() -> str:
        """Get started with Xray MCP Server - shows common operations and examples."""
        return """
# Welcome to Xray MCP Server!

This server provides access to Xray Cloud's test management system through a unified `xray_test` tool.

## Quick Start

### 1. List tests in your project
```
xray_test(
    entity="test",
    action="list",
    project_key="YOUR_PROJECT",
    limit=10
)
```

### 2. Create a simple Manual test
```
xray_test(
    entity="test",
    action="create",
    project_key="YOUR_PROJECT",
    summary="My First Test",
    test_type="Manual",
    steps='[{"action": "Do something", "data": "Test data", "result": "Expected result"}]'
)
```

### 3. Create a test execution
```
xray_test(
    entity="test_execution",
    action="create",
    project_key="YOUR_PROJECT",
    summary="My Test Run",
    test_issue_ids=["123", "456"]  # Numeric IDs from list operation
)
```

### 4. Search for tests
```
xray_test(
    entity="test",
    action="search",
    text="login",
    project_key="YOUR_PROJECT"
)
```

## Available Operations

**Entities:**
- `test` - Test cases (Manual, Generic, Cucumber)
- `test_execution` - Test execution cycles
- `test_plan` - Test planning and organization
- `test_run` - Individual test execution results

**Common Actions:**
- `create` - Create new entity
- `get` - Retrieve by ID
- `list` - List all with optional filtering
- `search` - User-friendly keyword search
- `update_status` - Update test run status
- `delete` - Remove entity
- `add_tests` - Add tests to execution/plan
- `remove_tests` - Remove tests from execution/plan

## Next Steps

📖 **View full documentation:**
   Check the MCP resource: `xray://documentation`

🔍 **See all capabilities:**
   Check the MCP resource: `xray://capabilities`

🎯 **Guided workflows:**
   - Use prompt `create_manual_test` for test creation guidance
   - Use prompt `create_test_execution` for execution setup
   - Use prompt `bdd_converter` for Gherkin/Cucumber tests

⚠️ **Important Note:**
Always use numeric issue IDs (e.g., "1192649") instead of JIRA keys (e.g., "TEST-123") for issue_id parameters.
First use `list` or `search` operations to get numeric IDs, then use them in other operations.

## Common Patterns

**Pattern 1: Create tests, then execute them**
```
1. Create tests with entity="test", action="create"
2. Note the numeric IDs returned
3. Create execution with entity="test_execution", test_issue_ids=[numeric_ids]
4. Update results with entity="test_run", action="update_status"
```

**Pattern 2: Find and run existing tests**
```
1. Search tests with entity="test", action="search"
2. Create execution with found test IDs
3. Execute and update statuses
```

**Pattern 3: Organize tests into plans**
```
1. List tests with entity="test", action="list"
2. Create plan with entity="test_plan", test_issue_ids=[...]
3. Add executions with action="add_executions"
```

Happy testing! 🚀
"""

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

    # Log final server state before returning
    logger.info("=" * 60)
    logger.info("Server configuration complete!")
    logger.info(f"Server name: {mcp.name}")

    # Log registered tools
    if hasattr(mcp, '_tool_manager') and hasattr(mcp._tool_manager, '_tools'):
        tools = mcp._tool_manager._tools
        logger.info(f"Total tools registered: {len(tools)}")
        for tool_name, tool_obj in tools.items():
            logger.info(f"  ✓ Tool: {tool_name}")
    else:
        logger.warning("Could not access tool manager to list tools")

    # Log registered resources
    if hasattr(mcp, '_resource_manager') and hasattr(mcp._resource_manager, '_resources'):
        resources = mcp._resource_manager._resources
        logger.info(f"Total resources registered: {len(resources)}")
        for resource_uri in resources.keys():
            logger.info(f"  ✓ Resource: {resource_uri}")
    else:
        logger.warning("Could not access resource manager to list resources")

    # Log registered prompts
    if hasattr(mcp, '_prompt_manager') and hasattr(mcp._prompt_manager, '_prompts'):
        prompts = mcp._prompt_manager._prompts
        logger.info(f"Total prompts registered: {len(prompts)}")
        for prompt_name in prompts.keys():
            logger.info(f"  ✓ Prompt: {prompt_name}")
    else:
        logger.warning("Could not access prompt manager to list prompts")

    logger.info("=" * 60)
    logger.info("Returning configured server to caller")

    return mcp


# Alias for any existing references
create_simplified_server = create_server


if __name__ == "__main__":
    # Run the server
    server = create_server()
    # In production, you'd use uvicorn or similar to run this
    print("Simplified Xray MCP Server created successfully!")
    print("Available tools:", [tool.name for tool in server._tool_manager._tools.values()])