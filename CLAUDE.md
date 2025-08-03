# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Model Context Protocol (MCP) server for Jira Xray test management, built with FastMCP. It provides LLMs with access to Xray's test management capabilities through a standardized interface, enabling automated test creation, execution management, and JQL queries.

## Common Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment (copy and edit with your credentials)
cp .env.example .env

# Run tests
python test_server.py

# Run the MCP server (two options)
python main.py                    # Direct execution
fastmcp run main.py:mcp          # Using FastMCP CLI

# Test the server functionality
python example.py
```

## High-Level Architecture

The codebase follows a modular architecture with clear separation of concerns:

1. **Authentication Layer** (`auth/manager.py`): Handles JWT token lifecycle with automatic refresh. The XrayAuthManager maintains authentication state and provides valid tokens to the GraphQL client.

2. **GraphQL Client** (`client/graphql.py`): Manages all communication with Xray's GraphQL API. Handles query/mutation execution, error handling, and response parsing.

3. **Tool Classes** (`tools/`): Each tool class encapsulates related functionality:
   - `tests.py`: Test management operations (CRUD operations on tests)
   - `executions.py`: Test execution management (create executions, add/remove tests)
   - `plans.py` & `runs.py`: Placeholder implementations for future features
   - `utils.py`: Utility functions like JQL queries and connection validation

4. **MCP Integration** (`main.py`): The XrayMCPServer class brings everything together, registering tools with FastMCP and handling the server lifecycle.

5. **Configuration** (`config/settings.py`): Manages environment variables and configuration validation using Pydantic.

## Key Design Patterns

- **Dependency Injection**: The GraphQL client is injected into tool classes, making testing and mocking easier.
- **Error Handling**: All exceptions inherit from XrayMCPError, providing structured error responses.
- **Async/Await**: All operations are asynchronous for better performance.
- **Type Safety**: Full type annotations throughout for better development experience.

## Testing Approach

The project uses a mock-based testing approach in `test_server.py`:
- Mock external dependencies (HTTP requests, auth tokens)
- Test each component in isolation
- Verify tool registration and error handling

## Environment Variables

Required:
- `XRAY_CLIENT_ID`: Your Xray API client ID
- `XRAY_CLIENT_SECRET`: Your Xray API client secret

Optional:
- `XRAY_BASE_URL`: Xray instance URL (defaults to `https://xray.cloud.getxray.app`)

## Important Notes

- JQL queries are limited to 100 results due to Xray API restrictions
- Authentication tokens are automatically refreshed when expired
- All tools return structured error responses when exceptions occur
- The server uses stdio transport for MCP communication