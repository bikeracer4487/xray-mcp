# Jira Xray MCP Server

A Model Context Protocol (MCP) server for Jira Xray test management, built with FastMCP. This server provides LLMs with access to Xray's test management capabilities through a standardized interface.

## Features

- **Authentication Management**: Automatic JWT token handling with refresh and race condition protection
- **Test Management**: Create, read, update, and delete tests (Manual, Cucumber, Generic types)
- **Test Execution Management**: Manage test executions and their associated tests
- **GraphQL Integration**: Full integration with Xray's GraphQL API
- **Security**: JQL injection prevention with whitelist-based validation
- **Error Handling**: Comprehensive error handling with structured responses
- **Type Safety**: Full type annotations for better development experience
- **Abstractions**: Clean architecture with repository patterns and decorators
- **Testing**: Comprehensive test suite with mock-based testing

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Create a `.env` file in the project root with your Xray credentials:

```env
XRAY_CLIENT_ID=your_xray_client_id
XRAY_CLIENT_SECRET=your_xray_client_secret
XRAY_BASE_URL=https://xray.cloud.getxray.app  # Optional, defaults to cloud instance
```

### Getting Xray API Credentials

1. Log in to your Xray instance
2. Go to **Global Settings** > **API Keys**
3. Create a new API Key
4. Copy the Client ID and Client Secret

## Usage

### Running as an MCP Server

```bash
python main.py
```

This will start the MCP server using the stdio transport, which is the standard way to expose an MCP server to clients.

### Using with FastMCP CLI

```bash
fastmcp run main.py:mcp
```

### Programmatic Usage

```python
import asyncio
from main import create_server

async def example():
    # Create server with credentials
    server = create_server("your_client_id", "your_client_secret")
    
    # Initialize (authenticate)
    await server.initialize()
    
    # Use the tools directly
    tests = await server.test_tools.get_tests(jql="project = 'MYPROJECT'", limit=10)
    print(f"Found {tests['total']} tests")

asyncio.run(example())
```

## 🛠️ Available Tools

The Xray MCP Server provides 14 callable tools organized into three main categories. All tools return structured error responses when exceptions occur: `{"error": "message", "type": "ErrorType"}`.

### Test Management Tools

#### get_test
*Purpose*: Retrieve a single test by issue ID or Jira key with complete information including test type, steps, and Jira fields.

**Parameters** | Type | Required | Default | Notes
-------------- | ---- | -------- | ------- | -----
issue_id | string | ✅ | - | Jira issue ID ("1162822") or key ("TEST-123")

**Returns**: Complete test data including issueId, testType, steps (Manual), gherkin (Cucumber), unstructured (Generic), and jira fields

**Example call**
```json
{ "tool": "get_test", "arguments": { "issue_id": "TEST-123" } }
```

---

#### get_tests
*Purpose*: Retrieve multiple tests with optional JQL filtering and pagination support.

**Parameters** | Type | Required | Default | Notes
-------------- | ---- | -------- | ------- | -----
jql | string | ❌ | null | JQL query (e.g., "project = PROJ AND status = 'In Progress'")
limit | integer | ❌ | 100 | Max results (1-100 due to API restrictions)

**Returns**: Paginated results with total, start, limit, and results array containing test objects

**Example call**
```json
{ "tool": "get_tests", "arguments": { "jql": "project = 'PROJ' AND labels = 'automated'", "limit": 50 } }
```

---

#### get_expanded_test
*Purpose*: Retrieve detailed test information including version support, parent/child relationships, and enhanced metadata.

**Parameters** | Type | Required | Default | Notes
-------------- | ---- | -------- | ------- | -----
issue_id | string | ✅ | - | Jira issue ID or key
test_version_id | integer | ❌ | null | Specific version ID (null = latest)

**Returns**: Expanded test data including versionId, enhanced steps with relationships, and warnings

**Example call**
```json
{ "tool": "get_expanded_test", "arguments": { "issue_id": "TEST-123", "test_version_id": 5 } }
```

---

#### create_test
*Purpose*: Create a new test in Xray supporting Manual (with steps), Cucumber (with Gherkin), or Generic (with unstructured content) types.

**Parameters** | Type | Required | Default | Notes
-------------- | ---- | -------- | ------- | -----
project_key | string | ✅ | - | Jira project key (e.g., "PROJ")
summary | string | ✅ | - | Test title/summary
test_type | string | ❌ | "Generic" | "Manual", "Cucumber", or "Generic"
description | string | ❌ | null | Test description in Jira
steps | array | ❌ | null | For Manual tests: [{"action": "...", "data": "...", "result": "..."}]
gherkin | string | ❌ | null | For Cucumber tests: Gherkin scenario text
unstructured | string | ❌ | null | For Generic tests: free-form content

**Returns**: Created test information with test object and warnings array

**Example call**
```json
{
  "tool": "create_test",
  "arguments": {
    "project_key": "PROJ",
    "summary": "Login functionality test",
    "test_type": "Manual",
    "description": "Test user login flow",
    "steps": [
      {"action": "Navigate to login page", "data": "URL: /login", "result": "Login page displayed"},
      {"action": "Enter credentials", "data": "user: test@example.com", "result": "User authenticated"}
    ]
  }
}
```

---

#### delete_test
*Purpose*: Permanently delete a test and all associated data including steps, execution history, and attachments.

**Parameters** | Type | Required | Default | Notes
-------------- | ---- | -------- | ------- | -----
issue_id | string | ✅ | - | Jira issue ID of test to delete

**Returns**: Deletion result with success boolean and issueId

**Example call**
```json
{ "tool": "delete_test", "arguments": { "issue_id": "TEST-123" } }
```

⚠️ **Warning**: This operation is irreversible.

---

#### update_test_type
*Purpose*: Change the test type while preserving as much content as possible (may result in data loss if new type doesn't support existing content).

**Parameters** | Type | Required | Default | Notes
-------------- | ---- | -------- | ------- | -----
issue_id | string | ✅ | - | Jira issue ID of test to update
test_type | string | ✅ | - | New test type ("Manual", "Cucumber", "Generic")

**Returns**: Updated test object with new type and warnings about potential data loss

**Example call**
```json
{ "tool": "update_test_type", "arguments": { "issue_id": "TEST-123", "test_type": "Manual" } }
```

### Test Execution Management Tools

#### get_test_execution
*Purpose*: Retrieve a single test execution with its associated tests, test types, and Jira fields.

**Parameters** | Type | Required | Default | Notes
-------------- | ---- | -------- | ------- | -----
issue_id | string | ✅ | - | Jira issue ID of test execution

**Returns**: Test execution data with issueId, tests (paginated list), and jira fields

**Example call**
```json
{ "tool": "get_test_execution", "arguments": { "issue_id": "PROJ-200" } }
```

---

#### get_test_executions
*Purpose*: Retrieve multiple test executions with optional JQL filtering and pagination.

**Parameters** | Type | Required | Default | Notes
-------------- | ---- | -------- | ------- | -----
jql | string | ❌ | null | JQL query to filter executions
limit | integer | ❌ | 100 | Max results (1-100)

**Returns**: Paginated results with execution objects including preview of associated tests

**Example call**
```json
{ "tool": "get_test_executions", "arguments": { "jql": "project = 'PROJ' AND fixVersion = '1.0'", "limit": 25 } }
```

---

#### create_test_execution
*Purpose*: Create a new test execution to group and track multiple test runs for a test cycle, sprint, or release.

**Parameters** | Type | Required | Default | Notes
-------------- | ---- | -------- | ------- | -----
project_key | string | ✅ | - | Jira project key
summary | string | ✅ | - | Execution title/summary
test_issue_ids | array | ❌ | null | List of test issue IDs to include
test_environments | array | ❌ | null | Environment names (auto-created if needed)
description | string | ❌ | null | Execution description

**Returns**: Created execution with testExecution object, warnings, and createdTestEnvironments

**Example call**
```json
{
  "tool": "create_test_execution",
  "arguments": {
    "project_key": "PROJ",
    "summary": "Sprint 10 Regression Testing",
    "test_issue_ids": ["PROJ-101", "PROJ-102"],
    "test_environments": ["Chrome", "Firefox"],
    "description": "Regression testing for Sprint 10 features"
  }
}
```

---

#### delete_test_execution
*Purpose*: Permanently delete a test execution and all associated test run data.

**Parameters** | Type | Required | Default | Notes
-------------- | ---- | -------- | ------- | -----
issue_id | string | ✅ | - | Jira issue ID of execution to delete

**Returns**: Deletion result with success boolean and issueId

**Example call**
```json
{ "tool": "delete_test_execution", "arguments": { "issue_id": "PROJ-200" } }
```

⚠️ **Warning**: This operation is irreversible and removes all test run history.

---

#### add_tests_to_execution
*Purpose*: Add one or more tests to an existing test execution for incremental execution building.

**Parameters** | Type | Required | Default | Notes
-------------- | ---- | -------- | ------- | -----
execution_issue_id | string | ✅ | - | Test execution's Jira issue ID
test_issue_ids | array | ✅ | - | List of test issue IDs to add

**Returns**: Operation result with addedTests array and warning message

**Example call**
```json
{ "tool": "add_tests_to_execution", "arguments": { "execution_issue_id": "PROJ-200", "test_issue_ids": ["PROJ-104", "PROJ-105"] } }
```

---

#### remove_tests_from_execution
*Purpose*: Remove one or more tests from an existing test execution (removes execution history for those tests).

**Parameters** | Type | Required | Default | Notes
-------------- | ---- | -------- | ------- | -----
execution_issue_id | string | ✅ | - | Test execution's Jira issue ID
test_issue_ids | array | ✅ | - | List of test issue IDs to remove

**Returns**: Operation result with success boolean and executionId

**Example call**
```json
{ "tool": "remove_tests_from_execution", "arguments": { "execution_issue_id": "PROJ-200", "test_issue_ids": ["PROJ-101", "PROJ-102"] } }
```

### Utility Tools

#### execute_jql_query
*Purpose*: Execute custom JQL queries with security validation for different entity types (tests, test executions).

**Parameters** | Type | Required | Default | Notes
-------------- | ---- | -------- | ------- | -----
jql | string | ✅ | - | JQL query string (validated for security)
entity_type | string | ❌ | "test" | "test" or "testexecution"
limit | integer | ❌ | 100 | Max results (1-100)

**Returns**: Query results with total, start, limit, and results array containing entity objects

**Example call**
```json
{ "tool": "execute_jql_query", "arguments": { "jql": "project = 'PROJ' AND labels = 'automated'", "entity_type": "test", "limit": 50 } }
```

---

#### validate_connection
*Purpose*: Test connection and authentication with Xray API for diagnostics and health checks.

**Parameters** | Type | Required | Default | Notes
-------------- | ---- | -------- | ------- | -----
*None* | - | - | - | No parameters required

**Returns**: Connection status with status, message, and authenticated boolean

**Example call**
```json
{ "tool": "validate_connection", "arguments": {} }
```

### Workflow Examples

#### Complete Test Management Workflow
```json
// 1. Validate connection
{ "tool": "validate_connection", "arguments": {} }

// 2. Create a manual test
{ "tool": "create_test", "arguments": { "project_key": "PROJ", "summary": "User Registration", "test_type": "Manual", "steps": [{"action": "Fill form", "result": "Form submitted"}] } }

// 3. Create test execution
{ "tool": "create_test_execution", "arguments": { "project_key": "PROJ", "summary": "Sprint Testing", "test_issue_ids": ["PROJ-123"] } }

// 4. Query tests by status
{ "tool": "get_tests", "arguments": { "jql": "project = PROJ AND status = 'In Progress'", "limit": 25 } }
```

#### Test Discovery and Analysis
```json
// 1. Find all automated tests
{ "tool": "execute_jql_query", "arguments": { "jql": "project = 'PROJ' AND labels = 'automated'", "entity_type": "test" } }

// 2. Get detailed test information
{ "tool": "get_expanded_test", "arguments": { "issue_id": "PROJ-123" } }

// 3. Find related test executions
{ "tool": "get_test_executions", "arguments": { "jql": "project = 'PROJ' AND fixVersion = '2.0'" } }
```

### Security Notes

- All JQL queries are validated using whitelist-based validation to prevent injection attacks
- Authentication tokens are automatically refreshed with race condition protection
- Input validation is performed on all parameters
- Structured error responses maintain security while providing debugging information

## Examples

### Creating a Manual Test

```python
# Create a manual test with steps
test_data = await server.test_tools.create_test(
    project_key="MYPROJECT",
    summary="Login functionality test",
    test_type="Manual",
    description="Test the login functionality",
    steps=[
        {
            "action": "Navigate to login page",
            "data": "URL: https://example.com/login",
            "result": "Login page is displayed"
        },
        {
            "action": "Enter valid credentials",
            "data": "Username: testuser, Password: testpass",
            "result": "User is logged in successfully"
        }
    ]
)
```

### Creating a Test Execution

```python
# Create a test execution with specific tests
execution = await server.execution_tools.create_test_execution(
    project_key="MYPROJECT",
    summary="Sprint 1 Test Execution",
    test_issue_ids=["MYPROJECT-123", "MYPROJECT-124"],
    test_environments=["staging", "chrome"],
    description="Test execution for Sprint 1 features"
)
```

### Querying Tests with JQL

```python
# Find all tests assigned to a specific user
tests = await server.test_tools.get_tests(
    jql="project = 'MYPROJECT' AND assignee = 'john.doe'",
    limit=50
)

# Find all failed test executions
executions = await server.execution_tools.get_test_executions(
    jql="project = 'MYPROJECT' AND status = 'FAIL'",
    limit=25
)
```

## Error Handling

The server includes comprehensive error handling:

- **AuthenticationError**: Issues with Xray authentication
- **GraphQLError**: GraphQL query/mutation errors
- **ValidationError**: Input validation errors
- **XrayMCPError**: Base exception for all Xray MCP errors

All tools return error information in a structured format when exceptions occur:

```python
{
    "error": "Error message",
    "type": "ErrorType"
}
```

## Architecture

The server is built with a modular architecture:

- **Authentication Manager**: Handles JWT token lifecycle
- **GraphQL Client**: Manages GraphQL communication with Xray
- **Tool Classes**: Organized by functionality (tests, executions, etc.)
- **FastMCP Integration**: Exposes tools through MCP protocol

## Limitations

- JQL queries are limited to 100 results due to Xray API restrictions
- Test Plans and Test Runs tools are placeholder implementations (documented stubs)
- Some advanced Xray features like test cycles may not be fully implemented

## Development

### Running Tests

The project includes a comprehensive test suite:

```bash
# Run the test server
python test_server.py

# Run specific test modules  
python -m pytest tests/test_tools_tests.py
python -m pytest tests/test_auth_race_condition.py
```

### Project Structure

```
xray-mcp/
├── main.py                 # Main server implementation
├── example.py              # Usage examples
├── test_server.py          # Test suite
├── auth/
│   ├── __init__.py
│   └── manager.py         # Authentication management
├── client/
│   ├── __init__.py
│   └── graphql.py         # GraphQL client
├── tools/
│   ├── __init__.py
│   ├── tests.py           # Test management tools
│   ├── executions.py      # Test execution tools
│   ├── plans.py           # Test plan tools (placeholder)
│   ├── runs.py            # Test run tools (placeholder)
│   └── utils.py           # Utility tools
├── config/
│   ├── __init__.py
│   └── settings.py        # Configuration management
├── exceptions/
│   ├── __init__.py
│   └── errors.py          # Custom exceptions
├── validators/
│   ├── __init__.py
│   └── jql_validator.py   # JQL security validation
├── abstractions/
│   ├── __init__.py
│   ├── base.py            # Base classes and interfaces
│   ├── decorators.py      # Tool decorators
│   ├── factory.py         # Tool factory
│   └── repository.py      # Repository patterns
├── errors/
│   ├── __init__.py
│   └── handlers.py        # Error handling utilities
├── tests/                  # Test files
│   ├── __init__.py
│   ├── conftest.py
│   └── test_*.py          # Various test modules
└── requirements.txt       # Dependencies
```

### Adding New Tools

1. Create the tool method in the appropriate tool class
2. Register it as an MCP tool in `main.py`
3. Add proper type annotations and documentation
4. Include error handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is provided as-is for educational and development purposes.

## Support

For issues related to:
- **Xray API**: Consult the [Xray documentation](https://docs.getxray.app/)
- **FastMCP**: Check the [FastMCP documentation](https://gofastmcp.com/)
- **This server**: Create an issue in the project repository

