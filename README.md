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

- Python 3.10 or higher (3.12 recommended)
- Xray Cloud account with API access
- Xray Client ID and Client Secret ([Get credentials](https://docs.getxray.app/display/XRAYCLOUD/Authentication+-+REST+v2))

### ⚡ Automated Installation (Recommended)

The fastest way to get started is using the automated installation script:

```bash
# Clone repository
git clone https://github.com/bikeracer4487/xray-mcp.git
cd xray-mcp

# Run automated installation
./install-server.sh
```

**What the script does:**
- ✅ Detects and configures Python environment (cross-platform: macOS, Linux, WSL)
- ✅ Creates isolated virtual environment
- ✅ Installs all dependencies automatically
- ✅ Prompts for Xray API credentials (interactive setup)
- ✅ Configures Claude Desktop and Cursor IDE integration
- ✅ Validates the complete setup

After installation, restart Claude Desktop or Cursor IDE and the Xray MCP server will be available!

**Script Options:**
- `./install-server.sh` - Full automated setup
- `./install-server.sh --help` - Show all available options
- `./install-server.sh --config` - Display configuration instructions only
- `./install-server.sh --clear-cache` - Clear Python cache (fixes import issues)

### 🛠️ Manual Installation (Alternative)

If you prefer manual setup or the script doesn't work for your environment:

```bash
# Clone repository
git clone <repository-url>
cd xray-mcp

# Create virtual environment
python3 -m venv .xray-mcp_venv
source .xray-mcp_venv/bin/activate  # On Windows: .xray-mcp_venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Edit .env and add your Xray credentials:
# XRAY_CLIENT_ID=your_client_id_here
# XRAY_CLIENT_SECRET=your_client_secret_here
```

**Manual IDE Configuration:**

For Claude Desktop, add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "xray": {
      "command": "/absolute/path/to/.xray-mcp_venv/bin/python",
      "args": ["/absolute/path/to/main.py"]
    }
  }
}
```

For Cursor IDE, add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "xray": {
      "command": "/absolute/path/to/.xray-mcp_venv/bin/python",
      "args": ["/absolute/path/to/main.py"]
    }
  }
}
```

### Testing the Installation

```bash
# Direct execution
python main.py

# Or using FastMCP CLI
fastmcp run main.py:create_mcp
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

### System Requirements

- Python 3.10+ (3.12 recommended for best compatibility)
- macOS, Linux, or Windows (WSL supported)
- Internet connection for Xray Cloud API access

### Key Dependencies

See `requirements.txt` for complete list:

- `fastmcp` - MCP server framework
- `aiohttp` - Async HTTP client
- `pydantic` - Data validation
- `python-dotenv` - Environment management
- `pytest` - Testing framework

## Environment Variables

The server is configured via environment variables in `.env`:

**Required:**
```bash
XRAY_CLIENT_ID=your_client_id_here
XRAY_CLIENT_SECRET=your_client_secret_here
```

**Optional:**
```bash
XRAY_BASE_URL=https://xray.cloud.getxray.app          # Xray Cloud URL (default shown)
XRAY_GRAPHQL_URL=https://xray.cloud.getxray.app/api/v2/graphql  # GraphQL endpoint
MCP_SERVER_NAME=xray-mcp                              # Server name (default: xray-mcp)
MCP_SERVER_VERSION=2.0.0                              # Server version
MCP_LOG_LEVEL=INFO                                    # Logging level (DEBUG|INFO|WARNING|ERROR)
DEFAULT_PROJECT_KEY=YOUR_PROJECT                      # Default Jira project key
```

The `install-server.sh` script automatically creates the `.env` file and prompts for required credentials.

## Contributing

We welcome contributions! Here's how to get started:

### Development Setup

```bash
# Clone and setup
git clone <repository-url>
cd xray-mcp
./install-server.sh

# Activate virtual environment
source .xray-mcp_venv/bin/activate

# Install development dependencies (if any)
pip install -r requirements.txt
```

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests to verify (`pytest` or `pytest tests/integration/`)
5. Update documentation if needed
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Guidelines

See [CLAUDE.md](CLAUDE.md) for comprehensive development guidelines including:
- Project architecture and structure
- Testing practices
- Code style conventions
- Environment setup details

## Troubleshooting

### Installation Issues

**Python version too old:**
```bash
# The server requires Python 3.10+
python3 --version

# Install Python 3.12 (recommended):
# macOS: brew install python@3.12
# Ubuntu/Debian: sudo apt install python3.12 python3.12-venv
```

**Virtual environment creation fails:**
```bash
# Install venv module (Ubuntu/Debian)
sudo apt install python3-venv

# Or recreate the virtual environment
rm -rf .xray-mcp_venv
./install-server.sh
```

**Import errors or module not found:**
```bash
# Clear Python cache and reinstall
./install-server.sh --clear-cache
```

### Runtime Issues

**"Authentication failed" errors:**
- Verify your `XRAY_CLIENT_ID` and `XRAY_CLIENT_SECRET` in `.env`
- Ensure credentials are valid in your Xray Cloud instance
- Check that you're using the correct Xray Cloud URL

**"Failed to retrieve entity" errors:**
- Verify you're using **numeric issue IDs** (not JIRA keys) - see [ID Format Requirements](docs/id-format-requirements.md)
- Check that the entity exists in your Xray instance
- Ensure your API credentials have appropriate permissions

**MCP server not appearing in Claude Desktop/Cursor:**
- Verify the configuration file exists and has correct paths
- Restart the IDE completely (not just reload)
- Check the configuration file syntax (must be valid JSON)
- Run `./install-server.sh --config` to see correct configuration

**Indexing delay issues:**
- Newly created entities may take 1-2 seconds to appear in search results (Xray Cloud limitation)
- The server includes automatic retry logic to handle this
- See [Advanced Retry Strategies](docs/advanced-retry-strategies.md) for details

### Getting Help

If you encounter issues:
1. Check [Project Status](docs/status.md) for known limitations
2. Review [ID Format Requirements](docs/id-format-requirements.md) if you get ID-related errors
3. Check the server logs: `xray_mcp_server.log` in the project directory
4. Create an issue with:
   - Your OS and Python version
   - Complete error message
   - Steps to reproduce
   - Relevant log excerpts

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
