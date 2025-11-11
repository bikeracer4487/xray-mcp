# Xray MCP Server Resources and Prompts

This document describes the resources and prompts available in the Xray MCP server.

## Overview

The Xray MCP server now provides:
- **1 Tool**: `xray_test` (unified interface for all operations)
- **3 Resources**: Read-only access to Xray data
- **3 Prompts**: Guided workflows for common tasks

## 🛠️ Tools

### `xray_test`
Unified tool for managing all Xray entities and operations.

**Parameters:**
- `entity`: "test", "test_execution", "test_plan", or "test_run"
- `action`: Operation to perform (create, get, update, delete, list, etc.)
- Plus entity-specific parameters

**Key Fix**: Steps parameter now accepts JSON string format:
```json
steps: '[{"action": "Click button", "data": "Input data", "result": "Expected outcome"}]'
```

## 📚 Resources

Resources provide read-only access to Xray data without executing operations.

### 1. `xray://documentation`
**Description**: Complete documentation and usage examples for the Xray MCP server.

**Content includes:**
- Tool usage examples
- Parameter formats (including the fixed steps JSON format)
- Available actions by entity type
- Required parameters for each operation

### 2. `xray://project/{project_key}/tests`
**Description**: List all tests in a specific project.

**Example**: `xray://project/FTEST/tests`

**Returns**: Formatted list of tests with:
- Issue keys
- Test summaries
- Test types (Manual, Generic, Cucumber)

### 3. `xray://test/{issue_id}`
**Description**: Detailed information about a specific test.

**Example**: `xray://test/FTEST-123`

**Returns**: Complete test details including:
- Basic test information
- Test steps (for Manual tests)
- Gherkin scripts (for Cucumber tests)
- Formatted in readable Markdown

## 💬 Prompts

Prompts provide guided workflows and templates for common operations.

### 1. `create_manual_test`
**Description**: Interactive guide for creating manual tests with proper step structure.

**Parameters:**
- `project_key` (optional): Target project
- `test_title` (optional): Test summary
- `description` (optional): Test description

**Features:**
- Step-by-step guidance
- JSON format examples for steps
- Ready-to-use tool call templates
- Explains the three-part step structure (action, data, result)

### 2. `create_test_execution`
**Description**: Guide for creating test executions to group multiple tests.

**Parameters:**
- `project_key` (optional): Target project
- `execution_title` (optional): Execution summary
- `test_ids` (optional): List of test IDs to include

**Features:**
- Explains test execution concepts
- Provides parameter templates
- Shows how to include multiple tests
- Optional environment configuration

### 3. `bdd_converter`
**Description**: Convert plain text requirements to Gherkin format for Cucumber tests.

**Parameters:**
- `requirement` (optional): Plain text requirement to convert

**Features:**
- Converts user stories to Gherkin
- Provides Given-When-Then structure
- Shows complete Cucumber test creation
- Template for Gherkin scripts

## Usage Examples

### Using Resources
```javascript
// Get documentation
await mcp.readResource("xray://documentation")

// List tests in FTEST project
await mcp.readResource("xray://project/FTEST/tests")

// Get specific test details
await mcp.readResource("xray://test/FTEST-123")
```

### Using Prompts
```javascript
// Get manual test creation guide
await mcp.getPrompt("create_manual_test")

// Get customized guide for specific project
await mcp.getPrompt("create_manual_test", {
  project_key: "FTEST",
  test_title: "Login Functionality Test"
})

// Convert requirement to Gherkin
await mcp.getPrompt("bdd_converter", {
  requirement: "Users should be able to log in with valid credentials"
})
```

## Benefits

### Resources:
- **Read-only access** to test data without modifying anything
- **Browseable** test hierarchies and details
- **Self-documenting** API with examples and formats
- **Cacheable** responses for better performance

### Prompts:
- **Guided workflows** for complex operations
- **Template generation** with correct formats
- **Interactive assistance** for test creation
- **Educational** content about best practices

## Testing

Comprehensive tests verify:
- Resource registration and accessibility
- Prompt functionality with parameters
- Content accuracy and formatting
- Error handling for invalid requests

Run tests with:
```bash
pytest tests/integration/test_resources_and_prompts.py -v
```

## Integration

The server automatically exposes these resources and prompts when loaded. No additional configuration is required. MCP clients will see:

- 1 tool: `xray_test`
- 3 resources: documentation, project tests, test details
- 3 prompts: manual test creation, execution creation, BDD conversion

This enhanced functionality makes the Xray MCP server much more discoverable and user-friendly for both new and experienced users.