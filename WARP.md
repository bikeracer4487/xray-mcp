# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a **Model Context Protocol (MCP) server** for Jira Xray test management, built with FastMCP. It provides LLMs with seamless access to Xray's test management capabilities through a standardized interface, enabling automated test creation, execution management, and comprehensive test lifecycle operations.

The server exposes **40 MCP tools** (8 temporarily disabled due to IDE limits) organized into 12 categories for comprehensive Xray test management.

## Prerequisites

- **Python 3.8+** (Python 3.11+ recommended)
- **Jira Xray instance** (Cloud or Server/Data Center) with API access
- **Valid Xray API credentials** (Client ID and Secret from Global Settings > API Keys)

## Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment configuration
cp .env.example .env
# Edit .env with your Xray API credentials
```

### Running the Server
```bash
# Option 1: Direct execution
python main.py

# Option 2: Using FastMCP CLI (preferred)
fastmcp run main.py:mcp

# Test the server functionality
python example.py
```

### Testing
```bash
# Run the complete test suite
python test_server.py

# Run specific test categories
python -m pytest tests/test_tools_tests.py -v
python -m pytest tests/test_auth_race_condition.py -v
python -m pytest tests/test_error_handling.py -v

# Run with coverage
python -m pytest --cov=. --cov-report=html
python -m pytest --cov-fail-under=80

# Run tests by markers
pytest -m unit
pytest -m integration
pytest -m security
pytest -m slow
```

### Code Quality
```bash
# Format code
black .
isort .

# Lint code
flake8 .

# Type checking
mypy .
```

## Environment Setup

### Required Environment Variables
Create a `.env` file in the project root:
```env
XRAY_CLIENT_ID=your_xray_client_id
XRAY_CLIENT_SECRET=your_xray_client_secret
XRAY_BASE_URL=https://xray.cloud.getxray.app  # Optional, defaults to cloud
```

### Configuration Loading
The server uses `python-dotenv` to automatically load environment variables from `.env` files. Configuration is validated using Pydantic models in `config/settings.py`.

## Architecture Overview

The codebase follows a **modular architecture** with clear separation of concerns:

### Core Components

1. **Authentication Layer** (`auth/manager.py`)
   - `XrayAuthManager`: Handles JWT token lifecycle with automatic refresh and race condition protection
   - Manages token expiry and 5-minute refresh buffer

2. **GraphQL Client** (`client/graphql.py`)
   - `XrayGraphQLClient`: Manages all communication with Xray's GraphQL API
   - Handles query/mutation execution, error handling, and response parsing

3. **Tool Classes** (`tools/`)
   - Each tool class encapsulates related functionality (tests, executions, plans, runs, etc.)
   - `TestTools`: Test management operations (CRUD on tests)
   - `TestExecutionTools`: Test execution management (create executions, add/remove tests)
   - `UtilityTools`: JQL queries, connection validation, and utility functions

4. **MCP Integration** (`main.py`)
   - `XrayMCPServer`: Brings everything together, registers tools with FastMCP
   - Handles server lifecycle and MCP protocol communication

5. **Configuration Management** (`config/settings.py`)
   - `XrayConfig`: Manages environment variables and validation using Pydantic

### Call Flow
```
1. Server initialization with config
2. Authentication via initialize() → JWT token
3. Tool registration via _register_tools()
4. Server run via run() or FastMCP CLI
```

## Design Patterns

### Key Architectural Patterns

- **Dependency Injection**: GraphQL client is injected into tool classes, enabling easy testing and mocking
- **Repository Pattern**: Data access abstraction in `abstractions/repository.py`
- **Decorator Pattern**: Error handling and logging decorators in `abstractions/decorators.py`
- **Factory Pattern**: Tool instantiation patterns in `abstractions/factory.py`
- **Async/Await**: All operations are asynchronous for better performance
- **Type Safety**: Full type annotations throughout using Python typing

### Error Handling Strategy
- All exceptions inherit from `XrayMCPError` for structured responses
- Tool methods catch exceptions and return `{"error": str(e), "type": type(e).__name__}`
- Specific exception types: `AuthenticationError`, `GraphQLError`, `ValidationError`

## Directory Structure

```
xray-mcp/
├── main.py                    # Main server with FastMCP integration
├── auth/                      # JWT authentication management
│   └── manager.py             # XrayAuthManager with race condition protection
├── client/                    # GraphQL API communication
│   └── graphql.py             # XrayGraphQLClient for API calls
├── config/                    # Configuration management
│   └── settings.py            # Environment variables and validation
├── tools/                     # MCP tool implementations
│   ├── tests.py               # Test management operations
│   ├── executions.py          # Test execution management
│   ├── plans.py               # Test plan operations
│   ├── runs.py                # Test run operations
│   └── utils.py               # Utility tools and JQL queries
├── exceptions/                # Custom exception hierarchy
│   └── errors.py              # XrayMCPError and subclasses
├── abstractions/              # Clean architecture patterns
│   ├── base.py                # Base classes and interfaces
│   ├── decorators.py          # Tool decorators for error handling
│   ├── factory.py             # Tool factory patterns
│   └── repository.py          # Repository patterns
├── validators/                # Input validation and security
│   └── jql_validator.py       # JQL injection prevention
├── tests/                     # Comprehensive test suite
│   ├── conftest.py            # Test configuration and fixtures
│   └── test_*.py              # Test modules with mock-based approach
└── docs/                      # Documentation and development notes
```

## Testing Approach

### Mock-Based Testing Strategy
The project uses a **mock-based testing approach** to avoid dependencies on external Xray instances:
- Mock external dependencies (HTTP requests, auth tokens)
- Test each component in isolation
- Verify tool registration and error handling
- Race condition testing for authentication

### Test Configuration (`pytest.ini`)
- **Coverage target**: 80% minimum
- **Async support**: Auto-detected with `asyncio_mode = auto`
- **Markers**: `unit`, `integration`, `security`, `slow`
- **Output**: Terminal and HTML coverage reports

### Single Test Execution
```bash
# Run specific test file
pytest tests/test_auth_race_condition.py -v

# Run specific test function
pytest tests/test_tools_tests.py::test_create_test -v

# Run tests matching pattern
pytest -k "auth" -v
```

## Important Implementation Notes

### Tool Limit Constraint
- **40-tool limit** enforced due to Cursor IDE restrictions
- **8 tools currently disabled** (deletion and versioning tools)
- To re-enable: uncomment `@self.mcp.tool()` decorators in `main.py`

### Security Features
- **JQL Injection Prevention**: Whitelist-based validation for all JQL queries
- **Token Management**: Secure JWT handling with automatic refresh
- **Input Validation**: Comprehensive parameter validation using Pydantic

### ID Format Support
All tools accepting `issue_id` parameters support **both Jira keys and numeric IDs**:
- Jira Keys: `"PROJ-123"`, `"TEST-456"`
- Numeric IDs: `"1162822"`, `"1163247"`

### API Limitations
- **Query limits**: JQL queries limited to 100 results (Xray API restriction)
- **Authentication tokens**: Automatically refreshed when expired
- **Error responses**: All tools return structured error responses

## Troubleshooting

### Common Issues

**Authentication Errors:**
```bash
# Test connection
python -c "
from main import create_server_from_env
import asyncio

async def test():
    server = create_server_from_env()
    await server.initialize()
    result = await server.utility_tools.validate_connection()
    print(result)

asyncio.run(test())
"
```

**Import Errors:**
- Ensure you're in the project directory
- Check all dependencies are installed: `pip install -r requirements.txt`

**Environment Variable Issues:**
- Verify `.env` file is in project root
- Check variable names: `XRAY_CLIENT_ID`, `XRAY_CLIENT_SECRET`
- No extra spaces or quotes in values

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### FastMCP CLI Integration
The server supports both execution modes:
- **Direct**: `python main.py` (loads .env automatically)
- **FastMCP**: `fastmcp run main.py:mcp` (exposes `mcp` variable)
