# Xray MCP Server Project Overview

## Project Purpose
This is an Xray MCP (Model Context Protocol) server that provides programmatic access to Xray Cloud's test management system. The server enables Claude and other MCP clients to interact with Xray's GraphQL API for test case management, test execution, and test planning operations.

## Current Status
- **Phase**: Groundup rebuild - most source files have been reset
- **State**: Early development stage
- **Core directories**: src/schemas/ and src/tools/ are currently empty
- **Working components**: Integration tests, authentication framework, documentation

## Tech Stack
- **Framework**: FastMCP (MCP server framework)
- **Language**: Python 3.x with async/await
- **HTTP Client**: aiohttp for async GraphQL requests
- **Validation**: Pydantic for data models and validation
- **Testing**: pytest with pytest-asyncio for async testing
- **Environment**: python-dotenv for configuration management
- **Authentication**: OAuth 2.0 client credentials flow with Xray Cloud

## Architecture Pattern
The project follows the FastMCP framework pattern:
- **Tools**: Individual MCP tools for specific Xray operations (create test, run test, etc.)
- **Schemas**: Pydantic models for request/response validation
- **Authentication**: OAuth 2.0 Bearer token flow with Xray Cloud
- **GraphQL Integration**: Direct GraphQL API calls to Xray Cloud endpoints

## Authentication Flow
1. Exchange client_id/client_secret for Bearer token
2. Include Bearer token in GraphQL requests
3. Token caching and refresh handling

## Key Features (Planned)
- Test case management
- Test execution tracking
- Test planning operations
- Integration with Xray Cloud's complete GraphQL API
- Comprehensive documentation integration