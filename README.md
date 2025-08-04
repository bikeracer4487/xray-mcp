# Jira Xray MCP Server

A Model Context Protocol (MCP) server that provides LLMs with seamless access to Jira Xray's test management capabilities through a standardized interface.

## Overview

This server enables AI assistants to interact with Xray test management directly, supporting automated test creation, execution management, and comprehensive test lifecycle operations. Built with FastMCP and featuring robust authentication, security, and error handling.

## Features

- **🔐 Authentication Management**: Automatic JWT token handling with refresh and race condition protection
- **📝 Test Management**: Create, read, update, and delete tests (Manual, Cucumber, Generic types)
- **🔄 Test Execution Management**: Manage test executions and their associated tests
- **🚀 GraphQL Integration**: Full integration with Xray's GraphQL API
- **🛡️ Security**: JQL injection prevention with whitelist-based validation
- **⚡ Error Handling**: Comprehensive error handling with structured responses
- **🎯 Type Safety**: Full type annotations for better development experience
- **🏗️ Clean Architecture**: Repository patterns, decorators, and dependency injection
- **🧪 Comprehensive Testing**: Mock-based testing with race condition coverage

## Directory Structure

    xray-mcp/
    ├── main.py                     # Main server implementation with FastMCP integration
    ├── example.py                  # Usage examples and demonstrations
    ├── test_server.py              # Comprehensive test suite
    ├── requirements.txt            # Python dependencies
    ├── pytest.ini                 # Test configuration
    ├── install-server.sh           # Installation script for MCP clients
    ├── abstractions/               # Clean architecture patterns
    │   ├── base.py                 # Base classes and interfaces
    │   ├── decorators.py           # Tool decorators for error handling
    │   ├── factory.py              # Tool factory patterns
    │   └── repository.py           # Repository patterns
    ├── auth/                       # Authentication management
    │   └── manager.py              # JWT token lifecycle with race protection
    ├── client/                     # GraphQL client implementation
    │   └── graphql.py              # Xray GraphQL API communication layer
    ├── config/                     # Configuration management
    │   └── settings.py             # Environment variables and validation
    ├── errors/                     # Error handling system
    │   └── handlers.py             # Centralized error handling utilities
    ├── exceptions/                 # Custom exception classes
    │   └── errors.py               # XrayMCPError hierarchy
    ├── tools/                      # MCP tool implementations
    │   ├── tests.py                # Test management operations
    │   ├── executions.py           # Test execution management
    │   ├── plans.py                # Test plan operations (placeholder)
    │   ├── runs.py                 # Test run operations (placeholder)
    │   └── utils.py                # Utility tools and JQL queries
    ├── validators/                 # Input validation and security
    │   └── jql_validator.py        # JQL injection prevention
    ├── tests/                      # Test suite
    │   ├── conftest.py             # Test configuration and fixtures
    │   ├── test_abstractions.py    # Architecture pattern tests
    │   ├── test_auth_race_condition.py # Concurrency tests
    │   ├── test_error_handling.py  # Error handling tests
    │   └── test_*.py               # Additional test modules
    └── docs/                       # Documentation
        └── xray_mcp_debug_log.md   # Development and debugging notes

## Prerequisites

- Python 3.8 or higher
- Jira Xray instance (Cloud or Server/Data Center)
- Valid Xray API credentials (Client ID and Secret)

## Quick Start

### 1. Installation

    pip install -r requirements.txt

### 2. Configuration

Create a `.env` file in the project root:

    XRAY_CLIENT_ID=your_xray_client_id
    XRAY_CLIENT_SECRET=your_xray_client_secret
    XRAY_BASE_URL=https://xray.cloud.getxray.app

**Getting Xray API Credentials:**
1. Log in to your Xray instance
2. Navigate to **Global Settings** → **API Keys**
3. Create a new API Key
4. Copy the Client ID and Client Secret

### 3. Running the Server

**Standalone MCP Server:**

    python main.py

**With FastMCP CLI:**

    fastmcp run main.py:mcp

**For MCP Client Integration:**

    # Use the provided installation script
    ./install-server.sh

### 4. Verification

Test your setup with the validation tool:

    python example.py

## 🛠️ Available Tools

The server provides 14 MCP tools organized into three categories. All tools return structured error responses: `{"error": "message", "type": "ErrorType"}`.

### Test Management Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| **get_test** | Retrieve single test by ID | `issue_id` (required) |
| **get_tests** | Query multiple tests with JQL | `jql`, `limit` (max 100) |
| **get_expanded_test** | Detailed test with version support | `issue_id`, `test_version_id` |
| **create_test** | Create new test (Manual/Cucumber/Generic) | `project_key`, `summary`, `test_type`, `steps`/`gherkin`/`unstructured` |
| **delete_test** | Permanently delete test | `issue_id` (⚠️ irreversible) |
| **update_test_type** | Change test type | `issue_id`, `test_type` |

### Test Execution Management Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| **get_test_execution** | Retrieve single execution | `issue_id` |
| **get_test_executions** | Query multiple executions | `jql`, `limit` |
| **create_test_execution** | Create new execution | `project_key`, `summary`, `test_issue_ids`, `test_environments` |
| **delete_test_execution** | Delete execution | `issue_id` (⚠️ removes test history) |
| **add_tests_to_execution** | Add tests to execution | `execution_issue_id`, `test_issue_ids[]` |
| **remove_tests_from_execution** | Remove tests from execution | `execution_issue_id`, `test_issue_ids[]` |

### Utility Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| **execute_jql_query** | Custom JQL queries with security validation | `jql`, `entity_type`, `limit` |
| **validate_connection** | Test API connection and authentication | None |

## Usage Examples

### Creating a Manual Test

```python
import asyncio
from main import create_server_from_env

async def create_manual_test():
    server = create_server_from_env()
    await server.initialize()
    
    result = await server.test_tools.create_test(
        project_key="PROJ",
        summary="User Login Flow Test",
        test_type="Manual",
        description="Validate user authentication process",
        steps=[
            {
                "action": "Navigate to login page",
                "data": "URL: /login",
                "result": "Login form displayed"
            },
            {
                "action": "Enter valid credentials",
                "data": "user: test@example.com, password: secure123",
                "result": "User successfully authenticated"
            }
        ]
    )
    return result

# Run the example
asyncio.run(create_manual_test())
```

### Creating a Test Execution

```python
async def create_execution():
    server = create_server_from_env()
    await server.initialize()
    
    execution = await server.execution_tools.create_test_execution(
        project_key="PROJ",
        summary="Sprint 5 Regression Tests",
        test_issue_ids=["PROJ-123", "PROJ-124", "PROJ-125"],
        test_environments=["Chrome", "Firefox", "Safari"],
        description="Comprehensive regression testing for Sprint 5 features"
    )
    return execution
```

### Querying with JQL

```python
async def query_tests():
    server = create_server_from_env()
    await server.initialize()
    
    # Find automated tests
    automated_tests = await server.test_tools.get_tests(
        jql="project = 'PROJ' AND labels = 'automated'",
        limit=50
    )
    
    # Find failed executions
    failed_executions = await server.execution_tools.get_test_executions(
        jql="project = 'PROJ' AND status = 'FAIL'",
        limit=25
    )
    
    return automated_tests, failed_executions
```

## Testing

The project includes comprehensive testing with mock-based approaches:

    # Run the complete test suite
    python test_server.py
    
    # Run specific test categories
    python -m pytest tests/test_tools_tests.py -v
    python -m pytest tests/test_auth_race_condition.py -v
    python -m pytest tests/test_error_handling.py -v
    
    # Run with coverage
    python -m pytest --cov=. --cov-report=html

## Development

### Code Quality

The project maintains high code quality standards:

    # Format code
    black .
    isort .
    
    # Lint code
    flake8 .
    
    # Type checking
    mypy .

### Adding New Tools

1. **Implement the tool method** in the appropriate tool class (`tools/`)
2. **Register the tool** in `main.py` `_register_tools()` method
3. **Add comprehensive documentation** with parameter descriptions
4. **Include error handling** with structured responses
5. **Add unit tests** in the `tests/` directory

### Architecture Patterns

The codebase follows clean architecture principles:

- **Dependency Injection**: GraphQL client injected into tool classes
- **Repository Pattern**: Data access abstraction in `abstractions/repository.py`
- **Decorator Pattern**: Error handling and logging in `abstractions/decorators.py`
- **Factory Pattern**: Tool instantiation in `abstractions/factory.py`

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `XRAY_CLIENT_ID` | ✅ | - | Xray API client ID |
| `XRAY_CLIENT_SECRET` | ✅ | - | Xray API client secret |
| `XRAY_BASE_URL` | ❌ | `https://xray.cloud.getxray.app` | Xray instance URL |

### MCP Client Integration

For Claude Desktop or other MCP clients, use the installation script:

    ./install-server.sh

This automatically configures the server in your MCP client settings.

## Security

- **JQL Injection Prevention**: Whitelist-based validation for all JQL queries
- **Token Management**: Secure JWT handling with automatic refresh
- **Input Validation**: Comprehensive parameter validation using Pydantic
- **Error Sanitization**: Structured error responses without sensitive data exposure

## Limitations

- **Query Limits**: JQL queries limited to 100 results (Xray API restriction)
- **Feature Coverage**: Test Plans and Test Runs are placeholder implementations
- **API Dependencies**: Requires active Xray instance with API access

## Troubleshooting

### Common Issues

**Authentication Errors:**
- Verify `XRAY_CLIENT_ID` and `XRAY_CLIENT_SECRET` are correct
- Check network connectivity to Xray instance
- Ensure API credentials have sufficient permissions

**Connection Issues:**
- Use `validate_connection` tool to test API connectivity
- Verify `XRAY_BASE_URL` format (include `https://`)
- Check firewall/proxy settings

**JQL Query Errors:**
- Ensure JQL syntax is valid for your Xray version
- Check project keys and field names exist
- Review query complexity (keep under 100 results)

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Add tests** for new functionality
4. **Ensure** all tests pass (`python test_server.py`)
5. **Run** code quality checks (`black .`, `flake8 .`, `mypy .`)
6. **Commit** changes (`git commit -m 'Add amazing feature'`)
7. **Push** to branch (`git push origin feature/amazing-feature`)
8. **Create** a Pull Request

## Resources

- **Xray API Documentation**: [https://docs.getxray.app/](https://docs.getxray.app/)
- **FastMCP Framework**: [https://gofastmcp.com/](https://gofastmcp.com/)
- **Model Context Protocol**: [https://modelcontextprotocol.io/](https://modelcontextprotocol.io/)
- **Xray GraphQL Schema**: See `xray-docs/` directory for complete API reference

## License

This project is provided as-is for educational and development purposes. See [LICENSE.md](LICENSE.md) for details.

## Support

For support with:
- **Xray API issues**: Consult [Xray documentation](https://docs.getxray.app/) or contact Xray support
- **FastMCP framework**: Check [FastMCP documentation](https://gofastmcp.com/)
- **This MCP server**: Create an issue in this repository

---

*Generated by Claude Code - Enhanced README with comprehensive documentation and examples*