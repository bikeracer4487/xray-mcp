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

The server currently provides 40 MCP tools organized into 12 categories for comprehensive Xray test management. All tools return structured error responses: `{"error": "message", "type": "ErrorType"}`.

📖 **For comprehensive tool documentation with detailed parameters, examples, and usage patterns, see [TOOLSET.md](TOOLSET.md)**

**Note**: 8 tools have been temporarily disabled due to Cursor IDE's 40-tool limit restriction. See the [Disabled Tools](#disabled-tools) section for details.

### 🔗 ID Format Support

All tools that accept `issue_id` parameters support **both Jira keys and numeric IDs** for maximum flexibility:

- **Jira Keys**: Human-readable format like `"PROJ-123"`, `"TEST-456"`
- **Numeric IDs**: Internal Xray IDs like `"1162822"`, `"1163247"`

The server automatically resolves Jira keys to internal IDs using the centralized `IssueIdResolver`, ensuring consistent behavior across all operations. This means you can use whichever format is more convenient for your workflow.

### Test Management Tools (6)

| Tool | Purpose | Parameters | Type | Req? | Notes |
|------|---------|------------|------|------|-------|
| **get_test** | Retrieve single test by ID | `issue_id` | string | ✅ | Returns test with steps, type, Jira info |
| **get_tests** | Query multiple tests with JQL | `jql` | string | ❌ | Optional JQL filter |
| | | `limit` | int | ❌ | Max 100 (default 100) |
| **get_expanded_test** | Detailed test with version support | `issue_id` | string | ✅ | Test ID to retrieve |
| | | `test_version_id` | int | ❌ | Specific version ID |
| **create_test** | Create new test (Manual/Cucumber/Generic) | `project_key` | string | ✅ | Jira project key |
| | | `summary` | string | ✅ | Test title/summary |
| | | `test_type` | string | ❌ | Generic (default), Manual, Cucumber |
| | | `description` | string | ❌ | Test description |
| | | `steps` | List[Dict] | ❌ | Manual test steps (see format below) |
| | | `gherkin` | string | ❌ | Gherkin scenario for Cucumber |
| | | `unstructured` | string | ❌ | Unstructured definition for Generic |
| **delete_test** | Permanently delete test | `issue_id` | string | ✅ | ⚠️ Irreversible operation |
| **update_test_type** | Change test type | `issue_id` | string | ✅ | Test to update |
| | | `test_type` | string | ✅ | New test type |

**Example call:**
```json
{ "tool": "create_test", "arguments": { 
  "project_key": "PROJ", 
  "summary": "Login Test", 
  "test_type": "Manual",
  "steps": [{"action": "Navigate to login", "data": "/login", "result": "Form displayed"}]
}}
```

### Test Execution Management Tools (5)

| Tool | Purpose | Parameters | Type | Req? | Notes |
|------|---------|------------|------|------|-------|
| **get_test_execution** | Retrieve single execution by ID | `issue_id` | string | ✅ | Execution details with associated tests |
| **get_test_executions** | Query multiple executions with JQL | `jql` | string | ❌ | Optional JQL filter |
| | | `limit` | int | ❌ | Max 100 (default 100) |
| **create_test_execution** | Create new test execution | `project_key` | string | ✅ | Jira project key |
| | | `summary` | string | ✅ | Execution title |
| | | `test_issue_ids` | List[string] | ❌ | Tests to include |
| | | `test_environments` | List[string] | ❌ | Test environments |
| | | `description` | string | ❌ | Execution description |
| **add_tests_to_execution** | Add tests to existing execution | `execution_issue_id` | string | ✅ | Target execution |
| | | `test_issue_ids` | List[string] | ✅ | Tests to add |
| **remove_tests_from_execution** | Remove tests from execution | `execution_issue_id` | string | ✅ | Target execution |
| | | `test_issue_ids` | List[string] | ✅ | Tests to remove |

**Example call:**
```json
{ "tool": "create_test_execution", "arguments": {
  "project_key": "PROJ",
  "summary": "Sprint 5 Tests",
  "test_issue_ids": ["PROJ-123", "PROJ-124"],
  "test_environments": ["Chrome", "Firefox"]
}}
```

### Precondition Management Tools (4)

| Tool | Purpose | Parameters | Type | Req? | Notes |
|------|---------|------------|------|------|-------|
| **get_preconditions** | Retrieve test preconditions | `issue_id` | string | ✅ | Test to get preconditions for |
| | | `start` | int | ❌ | Pagination start (default 0) |
| | | `limit` | int | ❌ | Max 100 (default 100) |
| **create_precondition** | Create new precondition | `issue_id` | string | ✅ | Test to add precondition to |
| | | `precondition_input` | Dict | ✅ | Condition data and type info |
| **update_precondition** | Update existing precondition | `precondition_id` | string | ✅ | Precondition to update |
| | | `precondition_input` | Dict | ✅ | Updated precondition data |
| **delete_precondition** | Delete precondition | `precondition_id` | string | ✅ | Precondition to delete |

**Example call:**
```json
{ "tool": "create_precondition", "arguments": {
  "issue_id": "PROJ-123",
  "precondition_input": {"condition": "User logged in", "type": "Manual"}
}}
```

### Test Set Operations (5)

| Tool | Purpose | Parameters | Type | Req? | Notes |
|------|---------|------------|------|------|-------|
| **get_test_set** | Retrieve single test set by ID | `issue_id` | string | ✅ | Test set details with tests |
| **get_test_sets** | Query multiple test sets with JQL | `jql` | string | ❌ | Optional JQL filter |
| | | `limit` | int | ❌ | Max 100 (default 100) |
| **create_test_set** | Create new test set | `project_key` | string | ✅ | Jira project key |
| | | `summary` | string | ✅ | Test set title |
| | | `test_issue_ids` | List[string] | ❌ | Tests to include |
| | | `description` | string | ❌ | Test set description |
| **update_test_set** | Update existing test set | `issue_id` | string | ✅ | Test set to update |
| | | `summary` | string | ✅ | New title |
| | | `description` | string | ❌ | New description |
| **add_tests_to_set** | Add tests to test set | `set_issue_id` | string | ✅ | Target test set |
| | | `test_issue_ids` | List[string] | ✅ | Tests to add |
| **remove_tests_from_set** | Remove tests from test set | `set_issue_id` | string | ✅ | Target test set |
| | | `test_issue_ids` | List[string] | ✅ | Tests to remove |

**Example call:**
```json
{ "tool": "create_test_set", "arguments": {
  "project_key": "PROJ",
  "summary": "UI Tests",
  "test_issue_ids": ["PROJ-100", "PROJ-101"]
}}
```

### Test Plan Operations (5)

| Tool | Purpose | Parameters | Type | Req? | Notes |
|------|---------|------------|------|------|-------|
| **get_test_plan** | Retrieve single test plan by ID | `issue_id` | string | ✅ | Test plan details with tests |
| **get_test_plans** | Query multiple test plans with JQL | `jql` | string | ❌ | Optional JQL filter |
| | | `limit` | int | ❌ | Max 100 (default 100) |
| **create_test_plan** | Create new test plan | `project_key` | string | ✅ | Jira project key |
| | | `summary` | string | ✅ | Test plan title |
| | | `test_issue_ids` | List[string] | ❌ | Tests to include |
| | | `description` | string | ❌ | Test plan description |
| **update_test_plan** | Update existing test plan | `issue_id` | string | ✅ | Test plan to update |
| | | `summary` | string | ✅ | New title |
| | | `description` | string | ❌ | New description |
| **add_tests_to_plan** | Add tests to test plan | `plan_issue_id` | string | ✅ | Target test plan |
| | | `test_issue_ids` | List[string] | ✅ | Tests to add |
| **remove_tests_from_plan** | Remove tests from test plan | `plan_issue_id` | string | ✅ | Target test plan |
| | | `test_issue_ids` | List[string] | ✅ | Tests to remove |

**Example call:**
```json
{ "tool": "create_test_plan", "arguments": {
  "project_key": "PROJ",
  "summary": "Release 1.0 Plan",
  "test_issue_ids": ["PROJ-200", "PROJ-201"]
}}
```

### Test Run Management (3)

| Tool | Purpose | Parameters | Type | Req? | Notes |
|------|---------|------------|------|------|-------|
| **get_test_run** | Retrieve single test run by ID | `issue_id` | string | ✅ | Test run with execution status |
| **get_test_runs** | Query multiple test runs with JQL | `jql` | string | ❌ | Optional JQL filter |
| | | `limit` | int | ❌ | Max 100 (default 100) |
| **create_test_run** | Create new test run | `project_key` | string | ✅ | Jira project key |
| | | `summary` | string | ✅ | Test run title |
| | | `test_environments` | List[string] | ❌ | Test environments |
| | | `description` | string | ❌ | Test run description |

**Example call:**
```json
{ "tool": "create_test_run", "arguments": {
  "project_key": "PROJ",
  "summary": "Nightly Run",
  "test_environments": ["Production"]
}}
```

### Test Versioning (0)

**All test versioning tools are temporarily disabled.** See the [Disabled Tools](#disabled-tools) section for details on re-enabling them.

### Status & Coverage Queries (2)

| Tool | Purpose | Parameters | Type | Req? | Notes |
|------|---------|------------|------|------|-------|
| **get_test_status** | Get test execution status | `issue_id` | string | ✅ | Test to check status for |
| | | `environment` | string | ❌ | Filter by environment |
| | | `version` | string | ❌ | Filter by version |
| | | `test_plan` | string | ❌ | Filter by test plan ID |
| **get_coverable_issues** | Get issues coverable by tests | `jql` | string | ❌ | Optional JQL filter |
| | | `limit` | int | ❌ | Max 100 (default 100) |

**Example call:**
```json
{ "tool": "get_test_status", "arguments": {
  "issue_id": "PROJ-123",
  "environment": "Production"
}}
```

### Xray History & Attachments (3)

| Tool | Purpose | Parameters | Type | Req? | Notes |
|------|---------|------------|------|------|-------|
| **get_xray_history** | Retrieve execution history | `issue_id` | string | ✅ | Test to get history for |
| | | `test_plan_id` | string | ❌ | Filter by test plan |
| | | `test_env_id` | string | ❌ | Filter by environment |
| | | `start` | int | ❌ | Pagination start (default 0) |
| | | `limit` | int | ❌ | Max 100 (default 100) |
| **upload_attachment** | Upload file to test step | `step_id` | string | ✅ | Test step to attach to |
| | | `file` | Dict | ✅ | File info (filename, content, mimeType, description) |
| **delete_attachment** | Delete attachment | `attachment_id` | string | ✅ | Attachment to delete |

**Example call:**
```json
{ "tool": "upload_attachment", "arguments": {
  "step_id": "step-123",
  "file": {"filename": "screenshot.png", "content": "base64data", "mimeType": "image/png"}
}}
```

### Gherkin & Unstructured Updates (1)

| Tool | Purpose | Parameters | Type | Req? | Notes |
|------|---------|------------|------|------|-------|
| **update_gherkin_definition** | Update Gherkin scenario | `issue_id` | string | ✅ | Cucumber test to update |
| | | `gherkin_text` | string | ✅ | New Gherkin scenario content |

**Example call:**
```json
{ "tool": "update_gherkin_definition", "arguments": {
  "issue_id": "PROJ-123",
  "gherkin_text": "Feature: Login\nScenario: Valid login\nGiven user on login page\nWhen enters credentials\nThen logged in"
}}
```

### Folder & Dataset Management (4)

| Tool | Purpose | Parameters | Type | Req? | Notes |
|------|---------|------------|------|------|-------|
| **get_folder_contents** | Retrieve test repository folder | `project_id` | string | ✅ | Numeric project ID (not key) |
| | | `folder_path` | string | ❌ | Path (default "/") |
| **move_test_to_folder** | Move test to different folder | `issue_id` | string | ✅ | Test to move |
| | | `folder_path` | string | ✅ | Destination folder path |
| **get_dataset** | Retrieve dataset for data-driven test | `test_issue_id` | string | ✅ | Test to get dataset for |
| **get_datasets** | Retrieve datasets for multiple tests | `test_issue_ids` | List[string] | ✅ | Tests to get datasets for |

**Example call:**
```json
{ "tool": "move_test_to_folder", "arguments": {
  "issue_id": "PROJ-123",
  "folder_path": "/Component/UI"
}}
```

### Utility Tools (2)

| Tool | Purpose | Parameters | Type | Req? | Notes |
|------|---------|------------|------|------|-------|
| **execute_jql_query** | Custom JQL queries with validation | `jql` | string | ✅ | JQL query string |
| | | `entity_type` | string | ❌ | test (default), testexecution |
| | | `limit` | int | ❌ | Max 100 (default 100) |
| **validate_connection** | Test API connection/auth | None | - | - | Returns connection status |

**Example call:**
```json
{ "tool": "execute_jql_query", "arguments": {
  "jql": "project = 'PROJ' AND labels = 'automated'",
  "entity_type": "test",
  "limit": 50
}}
```

## 🚫 Disabled Tools

The following 8 tools have been temporarily disabled to comply with Cursor IDE's 40-tool limit. The functionality remains fully implemented in the codebase and can be re-enabled by uncommenting the corresponding sections in `main.py`:

### Deletion Tools (4)
| Tool | Purpose | Implementation | Status |
|------|---------|--------------|--------|
| **delete_test_execution** | Delete test execution | `tools/executions.py` | 🔴 Disabled |
| **delete_test_set** | Delete test set | `tools/testsets.py` | 🔴 Disabled |
| **delete_test_plan** | Delete test plan | `tools/plans.py` | 🔴 Disabled |
| **delete_test_run** | Delete test run | `tools/runs.py` | 🔴 Disabled |

### Test Versioning Tools (4)
| Tool | Purpose | Implementation | Status |
|------|---------|--------------|--------|
| **get_test_versions** | Retrieve all versions of a test | `tools/versioning.py` | 🔴 Disabled |
| **archive_test_version** | Archive specific test version | `tools/versioning.py` | 🔴 Disabled |
| **restore_test_version** | Restore archived test version | `tools/versioning.py` | 🔴 Disabled |
| **create_test_version_from** | Create new version from existing | `tools/versioning.py` | 🔴 Disabled |

### Re-enabling Tools

To re-enable any of these tools:

1. **Locate the tool** in `main.py` (search for `# DISABLED:`)
2. **Uncomment the tool registration** by removing the `#` from the `@self.mcp.tool()` decorator and function definition
3. **Remove the disable comment** above the tool
4. **Test the server** to ensure it works with the additional tool

**Example**:
```python
# Before (disabled):
# DISABLED: delete_test_execution tool commented out due to Cursor's 40-tool limit
# @self.mcp.tool()
# async def delete_test_execution(issue_id: str) -> Dict[str, Any]:

# After (enabled):
@self.mcp.tool()
async def delete_test_execution(issue_id: str) -> Dict[str, Any]:
```

**Important**: Keep the total tool count at or below your IDE's limit. If re-enabling tools, you may need to disable others.

## Workflow Examples

### Complete Test Lifecycle
```json
1. { "tool": "create_test", "arguments": {"project_key": "PROJ", "summary": "Login Test", "test_type": "Manual"}}
2. { "tool": "create_test_execution", "arguments": {"project_key": "PROJ", "summary": "Sprint Tests"}}
3. { "tool": "add_tests_to_execution", "arguments": {"execution_issue_id": "PROJ-200", "test_issue_ids": ["PROJ-123"]}}
4. { "tool": "get_test_status", "arguments": {"issue_id": "PROJ-123"}}
```

### Test Organization
```json
1. { "tool": "create_test_set", "arguments": {"project_key": "PROJ", "summary": "UI Tests"}}
2. { "tool": "add_tests_to_set", "arguments": {"set_issue_id": "PROJ-300", "test_issue_ids": ["PROJ-123", "PROJ-124"]}}
3. { "tool": "move_test_to_folder", "arguments": {"issue_id": "PROJ-123", "folder_path": "/UI/Login"}}
```

### Data-Driven Testing
```json
1. { "tool": "create_test", "arguments": {"project_key": "PROJ", "summary": "Parameterized Test", "test_type": "Generic"}}
2. { "tool": "get_dataset", "arguments": {"test_issue_id": "PROJ-400"}}
3. { "tool": "create_test_version_from", "arguments": {"issue_id": "PROJ-400", "source_version_id": 1, "version_name": "v2.0"}}
```

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