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

## Available Tools

### Test Management

- **get_test(issue_id)**: Retrieve a single test by issue ID
- **get_tests(jql, limit)**: Retrieve multiple tests with JQL filtering
- **get_expanded_test(issue_id, test_version_id)**: Get detailed test information
- **create_test(project_key, summary, test_type, ...)**: Create a new test
- **delete_test(issue_id)**: Delete a test
- **update_test_type(issue_id, test_type)**: Update test type

### Test Execution Management

- **get_test_execution(issue_id)**: Retrieve a test execution
- **get_test_executions(jql, limit)**: Retrieve multiple test executions
- **create_test_execution(project_key, summary, ...)**: Create a test execution
- **delete_test_execution(issue_id)**: Delete a test execution
- **add_tests_to_execution(execution_id, test_ids)**: Add tests to execution
- **remove_tests_from_execution(execution_id, test_ids)**: Remove tests from execution

### Utility Tools

- **execute_jql_query(jql, entity_type, limit)**: Execute custom JQL queries
- **validate_connection()**: Test connection and authentication

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

