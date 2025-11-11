# Xray MCP Server

> A Model Context Protocol (MCP) server providing programmatic access to Xray Cloud's test management capabilities through GraphQL API integration.

[![Production Ready](https://img.shields.io/badge/status-production%20ready-success)](docs/status.md)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/framework-FastMCP-orange)](https://github.com/jlowin/fastmcp)

## What is This?

This MCP server enables AI assistants (Claude, Cursor, etc.) and other MCP clients to interact with Xray Cloud's test management system. Create tests, manage test executions, update test runs, and organize test plans—all through a simple, unified API.

**Perfect for**: Test automation, CI/CD integration, AI-assisted test management, and programmatic test case creation.

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Xray Cloud account with API access
- Xray Client ID and Client Secret ([Get credentials](https://docs.getxray.app/display/XRAYCLOUD/Authentication+-+REST+v2))

### Installation

```bash
# Clone repository
git clone <repository-url>
cd xray-mcp

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Edit .env and add your Xray credentials
```

### Configuration

Edit `.env` file:

```bash
XRAY_CLIENT_ID=your_client_id_here
XRAY_CLIENT_SECRET=your_client_secret_here
```

### Start Server

```bash
python -m src.server
```

## Usage

### For AI Assistants (Claude, Cursor, etc.)

First-time setup:

```
Use the MCP prompt "help" to see the getting started guide
```

Or explore capabilities:

```
Read the MCP resource "xray://capabilities" to see all operations
```

### The Unified Tool

All operations use a single tool: `xray_test(entity, action, **kwargs)`

**Entities**: `test`, `test_execution`, `test_plan`, `test_run`
**Actions**: `create`, `get`, `list`, `search`, `update_status`, `delete`, etc.

### Basic Examples

**List tests in your project:**

```python
xray_test(entity="test", action="list", project_key="DEMO", limit=10)
```

**Create a manual test:**

```python
xray_test(
    entity="test",
    action="create",
    project_key="DEMO",
    summary="Login Test",
    test_type="Manual",
    steps='[{"action": "Open login page", "data": "", "result": "Page loads"}]'
)
```

**Update test run status:**

```python
xray_test(
    entity="test_run",
    action="update_status",
    id="run_id",
    status="PASS",
    comment="All checks passed"
)
```

## ⚠️ Critical: ID Format Requirements

**The Xray GraphQL API requires numeric issue IDs, not JIRA keys.**

✅ **Correct**: `issue_id = "1192649"` (numeric ID)
❌ **Wrong**: `issue_id = "DEMO-123"` (JIRA key - will fail!)

**How to get numeric IDs**: Use `list` operations first to retrieve numeric IDs, then use them for get/update/delete operations.

📖 **Full details**: [ID Format Requirements Guide](docs/id-format-requirements.md)

## Key Features

### Core Entities

| Entity | Description |
|--------|-------------|
| **Tests** | Manual, Generic, and Cucumber test cases |
| **Test Executions** | Test cycles and execution tracking |
| **Test Plans** | Test organization and planning |
| **Test Runs** | Individual test execution instances |

### Operations

- ✅ Full CRUD operations for all entities
- ✅ Relationship management (add/remove tests from executions/plans)
- ✅ Status updates with comments and defects
- ✅ Environment association
- ✅ JQL-based filtering and search
- ✅ Retry logic for Xray Cloud indexing delays

### What Works

- All CRUD operations for Tests, Test Executions, Test Plans, Test Runs
- Authentication and session management
- GraphQL query execution with retry handling
- MCP protocol compliance
- Comprehensive integration test coverage
- Daily workflow validation

### Known Limitations

- Evidence file upload not implemented (requires multipart file handling)
- Xray Cloud indexing delays may affect immediate retrieval (handled with retry logic)
- Maximum 100 items per GraphQL query (Xray Cloud constraint)

📖 **Full status**: [Project Status](docs/status.md)

## Documentation

### Essential Reading

- 📕 **[ID Format Requirements](docs/id-format-requirements.md)** - **START HERE** - Critical information about numeric IDs
- 📘 **[API Examples Guide](docs/api-examples.md)** - Comprehensive examples for all operations
- 📗 **[Functionality Spec](docs/functionality-spec.md)** - Complete API reference

### Additional Guides

- [Use Cases Catalog](docs/use-cases.md) - 310+ real-world examples
- [Step Operations](docs/step-operations.md) - Managing test steps
- [Metadata Updates](docs/metadata-updates.md) - Metadata limitations and workarounds
- [Advanced Retry Strategies](docs/advanced-retry-strategies.md) - Handling indexing delays
- [MCP Resources & Prompts](docs/mcp-resources-prompts.md) - MCP protocol reference

### Project Information

- [Project Status](docs/status.md) - Implementation status and roadmap
- [CLAUDE.md](CLAUDE.md) - Development guidelines
- [Documentation Index](docs/README.md) - Full documentation catalog

## Testing

Run the test suite to verify functionality:

```bash
# All tests
pytest

# Integration tests (requires Xray credentials)
pytest tests/integration/

# Specific test categories
pytest tests/integration/test_qa_fixes_validation.py      # QA validation
pytest tests/integration/test_daily_user_workflows.py     # Workflow tests
pytest tests/integration/test_complete_functionality.py   # Full suite
```

**Integration tests** run against live Xray Cloud instances and validate real-world functionality.

## Architecture

```
src/
├── server.py              # FastMCP server with unified tool
├── tools/
│   └── xray_tool.py      # Unified xray_test tool
├── managers/              # Entity-specific operations
│   ├── test_manager.py
│   ├── execution_manager.py
│   ├── plan_manager.py
│   └── run_manager.py
├── utils/
│   └── graphql_templates.py
├── auth.py                # OAuth 2.0 authentication
├── graphql_client.py      # GraphQL client
└── simple_types.py        # Type definitions
```

**Design principles**:
- Unified tool interface for simplicity
- Entity managers for focused functionality
- GraphQL for efficient API communication
- Async/await for performance

## API Reference

### Entity: `test`

| Action | Description |
|--------|-------------|
| `create` | Create new test (Manual/Generic/Cucumber) |
| `get` | Retrieve test by ID |
| `list` | List tests with filtering |
| `search` | Search tests by text |
| `update_type` | Change test type |
| `update_content` | Update Gherkin content |
| `delete` | Delete test |

### Entity: `test_execution`

| Action | Description |
|--------|-------------|
| `create` | Create test execution |
| `get` | Retrieve execution details |
| `list` | List executions |
| `delete` | Delete execution |
| `add_tests` | Add tests to execution |
| `remove_tests` | Remove tests from execution |
| `add_environments` | Add test environments |
| `remove_environments` | Remove environments |

### Entity: `test_plan`

| Action | Description |
|--------|-------------|
| `create` | Create test plan |
| `get` | Retrieve plan details |
| `list` | List plans |
| `delete` | Delete plan |
| `add_tests` | Add tests to plan |
| `remove_tests` | Remove tests from plan |
| `add_executions` | Add executions to plan |
| `remove_executions` | Remove executions from plan |

### Entity: `test_run`

| Action | Description |
|--------|-------------|
| `get` | Retrieve test run details |
| `list` | List test runs |
| `update_status` | Update run status (PASS/FAIL/etc.) |
| `update_comment` | Update run comments |
| `add_defects` | Associate defects with run |

📖 **Complete reference**: [Functionality Specification](docs/functionality-spec.md)

## Response Format

All operations return standardized JSON:

```json
{
    "success": true,
    "data": { /* operation-specific data */ },
    "warnings": ["Optional warning messages"],
    "errors": ["Error messages if success=false"]
}
```

## Requirements

Key dependencies (see `requirements.txt` for complete list):

- `fastmcp` - MCP server framework
- `aiohttp` - Async HTTP client
- `pydantic` - Data validation
- `python-dotenv` - Environment management
- `pytest` - Testing framework

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

See [CLAUDE.md](CLAUDE.md) for development guidelines.

## Support

### Getting Help

1. **Check Documentation**: Start with [docs/README.md](docs/README.md)
2. **ID Format Issues**: Read [ID Format Requirements](docs/id-format-requirements.md)
3. **API Examples**: See [API Examples Guide](docs/api-examples.md)
4. **Known Issues**: Check [Project Status](docs/status.md)
5. **Report Issues**: Create an issue in the repository

### Useful Resources

- [Xray Cloud Documentation](https://docs.getxray.app/)
- [Xray GraphQL API Reference](xray-docs/README.md)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)

## License

See [LICENSE.md](LICENSE.md) for details.
