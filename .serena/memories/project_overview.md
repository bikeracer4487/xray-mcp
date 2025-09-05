# Project Overview

## Purpose
This is a **Jira Xray MCP Server** - a Model Context Protocol (MCP) server that provides LLMs with seamless access to Jira Xray's test management capabilities through a standardized interface. It enables AI assistants to interact with Xray test management directly, supporting automated test creation, execution management, and comprehensive test lifecycle operations.

## Key Features
- **Authentication Management**: Automatic JWT token handling with refresh and race condition protection
- **Test Management**: Create, read, update, and delete tests (Manual, Cucumber, Generic types)  
- **Test Execution Management**: Manage test executions and their associated tests
- **GraphQL Integration**: Full integration with Xray's GraphQL API
- **Security**: JQL injection prevention with whitelist-based validation
- **Error Handling**: Comprehensive error handling with structured responses
- **Type Safety**: Full type annotations for better development experience
- **Clean Architecture**: Repository patterns, decorators, and dependency injection

## Target Use Cases
- Automated test creation and management by AI assistants
- Test execution workflow automation
- Xray test lifecycle management through conversational interfaces
- Integration of test management into AI-powered development workflows

## Current Status
- 40+ MCP tools available (8 temporarily disabled due to IDE limits)
- Comprehensive test coverage with mock-based testing
- Production-ready with robust error handling and security features
- Built with FastMCP framework for MCP compliance