# Project Structure

## Root Directory
```
xray-mcp/
├── main.py                     # Main server implementation with FastMCP integration
├── example.py                  # Usage examples and demonstrations
├── test_server.py              # Comprehensive test suite
├── requirements.txt            # Python dependencies
├── pytest.ini                 # Test configuration
├── install-server.sh           # Installation script for MCP clients
├── .env.example               # Environment template
├── CLAUDE.md                  # Project instructions for Claude Code
└── README.md                  # Project documentation
```

## Core Directories

### `/tools/` - MCP Tool Implementations
- **tests.py**: Test management operations (CRUD)
- **executions.py**: Test execution management  
- **plans.py**: Test plan operations
- **runs.py**: Test run operations
- **testsets.py**: Test set management
- **preconditions.py**: Test precondition management
- **versioning.py**: Test versioning (disabled)
- **utils.py**: Utility tools and JQL queries
- **coverage.py**: Coverage and status queries
- **history.py**: Xray history and attachments
- **gherkin.py**: Gherkin/unstructured updates
- **organization.py**: Folder and dataset management

### `/auth/` - Authentication Management
- **manager.py**: JWT token lifecycle with race protection

### `/client/` - GraphQL Client
- **graphql.py**: Xray GraphQL API communication layer

### `/config/` - Configuration Management
- **settings.py**: Environment variables and validation (XrayConfig class)

### `/exceptions/` - Error Handling
- **errors.py**: XrayMCPError hierarchy and custom exceptions

### `/validators/` - Input Validation
- **tool_validators.py**: Input validation for tools
- **jql_validator.py**: JQL injection prevention

### `/security/` - Security Features  
- Security-related utilities and credential management

### `/tests/` - Test Suite
- **conftest.py**: Test configuration and fixtures
- **e2e/**: End-to-end tests
- Various test modules for different components

## Key Files
- **main.py**: Entry point with XrayMCPServer class and tool registration
- **TOOLSET.md**: Comprehensive tool documentation
- **SECURITY.md**: Security guidelines and features
- **KNOWN_ISSUES.md**: Known issues and limitations

## Architecture Flow
1. **main.py** initializes XrayMCPServer
2. **config/settings.py** loads environment variables
3. **auth/manager.py** handles authentication
4. **client/graphql.py** communicates with Xray API
5. **tools/*.py** implement MCP tool functionality
6. **validators/*.py** validate inputs and prevent injections

## Build Artifacts
- **.ruff_cache/**: Linting cache
- **__pycache__/**: Python bytecode cache
- **htmlcov/**: Coverage reports (generated)