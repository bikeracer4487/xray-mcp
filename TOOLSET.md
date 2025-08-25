# Xray MCP Server - Tool Reference

This document provides a comprehensive reference for all tools available in the Xray Model Context Protocol (MCP) server. The server provides 40 active tools across 12 categories for complete Jira Xray test management integration.

## Table of Contents

- [Test Management](#test-management)
- [Test Executions](#test-executions)
- [Preconditions](#preconditions)
- [Test Sets](#test-sets)
- [Test Plans](#test-plans)
- [Test Runs](#test-runs)
- [Test Coverage & Status](#test-coverage--status)
- [Execution History](#execution-history)
- [Gherkin & Cucumber](#gherkin--cucumber)
- [Test Organization](#test-organization)
- [Dataset Management](#dataset-management)
- [Utilities](#utilities)

## Test Management

### get_test

Retrieve a single test by issue ID with comprehensive details.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| issue_id | string | Yes | The Jira issue ID or key (e.g., "PROJ-123" or "1162822") |

**Returns:** Test details including steps, type, and Jira metadata

**Example:**
```json
{
  "tool": "get_test",
  "arguments": {
    "issue_id": "PROJ-123"
  }
}
```

### get_tests

Retrieve multiple tests with optional JQL filtering and pagination.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| jql | string | No | JQL query string to filter tests |
| limit | integer | No | Maximum number of tests to return (1-100, default: 100) |

**Returns:** Paginated list of tests with metadata

**Example:**
```json
{
  "tool": "get_tests",
  "arguments": {
    "jql": "project = PROJ AND status = Open",
    "limit": 50
  }
}
```

### get_expanded_test

Retrieve detailed information for a single test with version support.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| issue_id | string | Yes | The Jira issue ID of the test |
| test_version_id | integer | No | Specific version ID of the test |

**Returns:** Detailed test information including all steps and metadata

**Example:**
```json
{
  "tool": "get_expanded_test",
  "arguments": {
    "issue_id": "PROJ-123"
  }
}
```

### create_test

Create a new test in Xray with comprehensive validation.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| project_key | string | Yes | Uppercase Jira project key (e.g., "PROJ", "TEST") |
| summary | string | Yes | Descriptive test title/summary |
| test_type | string | No | Test type: "Manual", "Cucumber", or "Generic" (default) |
| description | string | No | Test description or background information |
| steps | string/array | No | For Manual tests - JSON string or list of steps |
| gherkin | string | No | For Cucumber tests - Gherkin scenario text |
| unstructured | string | No | For Generic tests - Free-form test definition |

**Returns:** Created test information including issue ID and key

**Example:**
```json
{
  "tool": "create_test",
  "arguments": {
    "project_key": "PROJ",
    "summary": "Login functionality test",
    "test_type": "Manual",
    "steps": "[{\"action\": \"Navigate to login page\", \"data\": \"\", \"result\": \"Login page loads\"}]"
  }
}
```

### update_test

Update various aspects of an existing test comprehensively.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| issue_id | string | Yes | Jira issue ID or key |
| test_type | string | No | New test type ("Manual", "Cucumber", "Generic") |
| gherkin | string | No | New Gherkin scenario (for Cucumber tests) |
| unstructured | string | No | New unstructured content (for Generic tests) |
| steps | string/array | No | New test steps (for Manual tests) |
| jira_fields | string/object | No | Jira fields to update |
| version_id | integer | No | Specific test version to update |

**Returns:** Combined update results with success status

**Example:**
```json
{
  "tool": "update_test",
  "arguments": {
    "issue_id": "PROJ-123",
    "test_type": "Manual",
    "steps": "[{\"action\":\"Login\",\"data\":\"\",\"result\":\"Success\"}]"
  }
}
```

### delete_test

Permanently delete a test from Xray.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| issue_id | string | Yes | The Jira issue ID or key of the test to delete |

**Returns:** Confirmation of deletion with status

**Example:**
```json
{
  "tool": "delete_test",
  "arguments": {
    "issue_id": "PROJ-456"
  }
}
```

### update_test_type

Update the test type of an existing test (deprecated - use update_test).

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| issue_id | string | Yes | The Jira issue ID or key of the test |
| test_type | string | Yes | New test type ("Manual", "Cucumber", "Generic") |

**Returns:** Updated test information with new test type

## Test Executions

### get_test_execution

Retrieve a single test execution by issue ID.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| issue_id | string | Yes | The Jira issue ID or key of the test execution |

**Returns:** Test execution details including associated tests and status

**Example:**
```json
{
  "tool": "get_test_execution",
  "arguments": {
    "issue_id": "PROJ-456"
  }
}
```

### get_test_executions

Retrieve multiple test executions with optional JQL filtering.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| jql | string | No | JQL query to filter test executions |
| limit | integer | No | Maximum number of executions to return (1-100, default: 100) |

**Returns:** Paginated list of test executions

**Example:**
```json
{
  "tool": "get_test_executions",
  "arguments": {
    "jql": "project = PROJ AND status = Open",
    "limit": 50
  }
}
```

### create_test_execution

Create a new test execution in Xray.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| project_key | string | Yes | Jira project key where execution will be created |
| summary | string | Yes | Test execution summary/title |
| test_issue_ids | array | No | List of test issue IDs to include |
| test_environments | array | No | List of test environments |
| description | string | No | Test execution description |

**Returns:** Created test execution information

**Example:**
```json
{
  "tool": "create_test_execution",
  "arguments": {
    "project_key": "PROJ",
    "summary": "Sprint 1 Regression Tests",
    "test_issue_ids": ["PROJ-123", "PROJ-456"],
    "test_environments": ["Staging"]
  }
}
```

### add_tests_to_execution

Add tests to an existing test execution.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| execution_issue_id | string | Yes | The Jira issue ID of the test execution |
| test_issue_ids | array | Yes | List of test issue IDs to add |

**Returns:** Information about successfully added tests

**Example:**
```json
{
  "tool": "add_tests_to_execution",
  "arguments": {
    "execution_issue_id": "PROJ-456",
    "test_issue_ids": ["PROJ-123", "PROJ-789"]
  }
}
```

### remove_tests_from_execution

Remove tests from an existing test execution.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| execution_issue_id | string | Yes | The Jira issue ID of the test execution |
| test_issue_ids | array | Yes | List of test issue IDs to remove |

**Returns:** Confirmation of removal with count

**Example:**
```json
{
  "tool": "remove_tests_from_execution",
  "arguments": {
    "execution_issue_id": "PROJ-456",
    "test_issue_ids": ["PROJ-123"]
  }
}
```

## Preconditions

### get_preconditions

Retrieve preconditions for a test with pagination.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| issue_id | string | Yes | The Jira issue ID or key of the test |
| start | integer | No | Starting index for pagination (default: 0) |
| limit | integer | No | Maximum preconditions to return (1-100, default: 100) |

**Returns:** Paginated list of preconditions

**Example:**
```json
{
  "tool": "get_preconditions",
  "arguments": {
    "issue_id": "PROJ-123",
    "limit": 50
  }
}
```

### create_precondition

Create a new precondition for a test.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| issue_id | string | Yes | The Jira issue ID or key of the test |
| precondition_input | object | Yes | Precondition data with 'condition' text and 'type' |

**Returns:** Created precondition information

**Example:**
```json
{
  "tool": "create_precondition",
  "arguments": {
    "issue_id": "PROJ-123",
    "precondition_input": {
      "condition": "User must be logged in",
      "type": "Manual"
    }
  }
}
```

### update_precondition

Update an existing precondition.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| precondition_id | string | Yes | The unique ID of the precondition to update |
| precondition_input | object | Yes | Updated precondition data |

**Returns:** Updated precondition information

**Example:**
```json
{
  "tool": "update_precondition",
  "arguments": {
    "precondition_id": "12345",
    "precondition_input": {
      "condition": "User must have admin rights",
      "type": "Manual"
    }
  }
}
```

### delete_precondition

Permanently delete a precondition.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| precondition_id | string | Yes | The unique ID of the precondition to delete |

**Returns:** Confirmation of deletion

**Example:**
```json
{
  "tool": "delete_precondition",
  "arguments": {
    "precondition_id": "12345"
  }
}
```

## Test Sets

### get_test_set

Retrieve a single test set by issue ID.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| issue_id | string | Yes | The Jira issue ID or key of the test set |

**Returns:** Test set details including associated tests

**Example:**
```json
{
  "tool": "get_test_set",
  "arguments": {
    "issue_id": "PROJ-456"
  }
}
```

### get_test_sets

Retrieve multiple test sets with optional JQL filtering.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| jql | string | No | JQL query to filter test sets |
| limit | integer | No | Maximum number of test sets to return (max 100) |

**Returns:** Paginated list of test sets

**Example:**
```json
{
  "tool": "get_test_sets",
  "arguments": {
    "jql": "project = PROJ AND status = Open",
    "limit": 25
  }
}
```

### create_test_set

Create a new test set in Xray.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| project_key | string | Yes | Jira project key where test set will be created |
| summary | string | Yes | Test set summary/title |
| test_issue_ids | array | No | List of test issue IDs to include |
| description | string | No | Test set description |

**Returns:** Created test set information

**Example:**
```json
{
  "tool": "create_test_set",
  "arguments": {
    "project_key": "PROJ",
    "summary": "Smoke Test Suite",
    "test_issue_ids": ["PROJ-123", "PROJ-456"]
  }
}
```

### update_test_set

Update an existing test set.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| issue_id | string | Yes | The Jira issue ID or key of the test set |
| summary | string | Yes | New test set summary/title |
| description | string | No | New test set description |

**Returns:** Updated test set information

**Example:**
```json
{
  "tool": "update_test_set",
  "arguments": {
    "issue_id": "PROJ-456",
    "summary": "Enhanced Smoke Tests",
    "description": "Updated for v2.0"
  }
}
```

### add_tests_to_set

Add tests to an existing test set.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| set_issue_id | string | Yes | The Jira issue ID of the test set |
| test_issue_ids | array | Yes | List of test issue IDs to add |

**Returns:** Information about added tests and warnings

**Example:**
```json
{
  "tool": "add_tests_to_set",
  "arguments": {
    "set_issue_id": "PROJ-456",
    "test_issue_ids": ["PROJ-789", "PROJ-101"]
  }
}
```

### remove_tests_from_set

Remove tests from an existing test set.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| set_issue_id | string | Yes | The Jira issue ID of the test set |
| test_issue_ids | array | Yes | List of test issue IDs to remove |

**Returns:** Confirmation of removal

**Example:**
```json
{
  "tool": "remove_tests_from_set",
  "arguments": {
    "set_issue_id": "PROJ-456",
    "test_issue_ids": ["PROJ-123"]
  }
}
```

## Test Plans

### get_test_plan

Retrieve a single test plan by issue ID.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| issue_id | string | Yes | The Jira issue ID of the test plan |

**Returns:** Test plan details including associated tests

**Example:**
```json
{
  "tool": "get_test_plan",
  "arguments": {
    "issue_id": "PROJ-789"
  }
}
```

### get_test_plans

Retrieve multiple test plans with optional JQL filtering.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| jql | string | No | JQL query to filter test plans |
| limit | integer | No | Maximum number of test plans to return (max 100) |

**Returns:** Paginated list of test plans

**Example:**
```json
{
  "tool": "get_test_plans",
  "arguments": {
    "jql": "project = PROJ AND created >= -30d"
  }
}
```

### create_test_plan

Create a new test plan in Xray.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| project_key | string | Yes | Jira project key where test plan will be created |
| summary | string | Yes | Test plan summary/title |
| test_issue_ids | array | No | List of test issue IDs to include |
| description | string | No | Test plan description |

**Returns:** Created test plan information

**Example:**
```json
{
  "tool": "create_test_plan",
  "arguments": {
    "project_key": "PROJ",
    "summary": "Release 2.0 Test Plan",
    "test_issue_ids": ["PROJ-123", "PROJ-456"]
  }
}
```

### update_test_plan

Update an existing test plan.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| issue_id | string | Yes | The Jira issue ID of the test plan |
| summary | string | Yes | New test plan summary/title |
| description | string | No | New test plan description |

**Returns:** Updated test plan information

**Example:**
```json
{
  "tool": "update_test_plan",
  "arguments": {
    "issue_id": "PROJ-789",
    "summary": "Updated Release 2.0 Test Plan"
  }
}
```

### add_tests_to_plan

Add tests to an existing test plan.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| plan_issue_id | string | Yes | The Jira issue ID of the test plan |
| test_issue_ids | array | Yes | List of test issue IDs to add |

**Returns:** Information about added tests and warnings

**Example:**
```json
{
  "tool": "add_tests_to_plan",
  "arguments": {
    "plan_issue_id": "PROJ-789",
    "test_issue_ids": ["PROJ-202", "PROJ-303"]
  }
}
```

### remove_tests_from_plan

Remove tests from an existing test plan.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| plan_issue_id | string | Yes | The Jira issue ID of the test plan |
| test_issue_ids | array | Yes | List of test issue IDs to remove |

**Returns:** Confirmation of removal

**Example:**
```json
{
  "tool": "remove_tests_from_plan",
  "arguments": {
    "plan_issue_id": "PROJ-789",
    "test_issue_ids": ["PROJ-123"]
  }
}
```

## Test Runs

### get_test_run

Retrieve a single test run by issue ID.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| issue_id | string | Yes | The Jira issue ID of the test run |

**Returns:** Test run details including associated tests and execution status

**Example:**
```json
{
  "tool": "get_test_run",
  "arguments": {
    "issue_id": "PROJ-404"
  }
}
```

### get_test_runs

Retrieve multiple test runs with optional JQL filtering.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| jql | string | No | JQL query to filter test runs |
| limit | integer | No | Maximum number of test runs to return (max 100) |

**Returns:** Paginated list of test runs

**Example:**
```json
{
  "tool": "get_test_runs",
  "arguments": {
    "jql": "project = PROJ AND status = 'In Progress'"
  }
}
```

### create_test_run

Create a new test run in Xray.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| project_key | string | Yes | Jira project key where test run will be created |
| summary | string | Yes | Test run summary/title |
| test_environments | array | No | List of test environments |
| description | string | No | Test run description |

**Returns:** Created test run information

**Example:**
```json
{
  "tool": "create_test_run",
  "arguments": {
    "project_key": "PROJ",
    "summary": "Nightly Automated Run",
    "test_environments": ["Production", "Staging"]
  }
}
```

## Test Coverage & Status

### get_test_status

Get test execution status for a specific test.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| issue_id | string | Yes | The Jira issue ID of the test |
| environment | string | No | Test environment to filter by |
| version | string | No | Version to filter by |
| test_plan | string | No | Test plan issue ID to filter by |

**Returns:** Test execution status and coverage information

**Example:**
```json
{
  "tool": "get_test_status",
  "arguments": {
    "issue_id": "PROJ-123",
    "environment": "Production"
  }
}
```

### get_coverable_issues

Retrieve issues that can be covered by tests.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| jql | string | No | JQL query to filter coverable issues |
| limit | integer | No | Maximum number of issues to return (max 100) |

**Returns:** Paginated list of coverable issues with coverage information

**Example:**
```json
{
  "tool": "get_coverable_issues",
  "arguments": {
    "jql": "project = PROJ AND status = 'To Do'",
    "limit": 50
  }
}
```

## Execution History

### get_xray_history

Retrieve Xray execution history for a test.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| issue_id | string | Yes | The Jira issue ID of the test |
| test_plan_id | string | No | Test plan issue ID to filter history |
| test_env_id | string | No | Test environment ID to filter history |
| start | integer | No | Starting index for pagination (default: 0) |
| limit | integer | No | Maximum history entries to return (max 100) |

**Returns:** Paginated list of execution history entries

**Example:**
```json
{
  "tool": "get_xray_history",
  "arguments": {
    "issue_id": "PROJ-123",
    "test_plan_id": "PROJ-789",
    "limit": 25
  }
}
```

### upload_attachment

Upload an attachment to a test step.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| step_id | string | Yes | The ID of the test step to attach the file to |
| file | object | Yes | File information (filename, content, mimeType, description) |

**Returns:** Details of the uploaded attachment

**Example:**
```json
{
  "tool": "upload_attachment",
  "arguments": {
    "step_id": "12345",
    "file": {
      "filename": "screenshot.png",
      "content": "base64-encoded-content",
      "mimeType": "image/png"
    }
  }
}
```

### delete_attachment

Delete an attachment from Xray.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| attachment_id | string | Yes | The ID of the attachment to delete |

**Returns:** Confirmation of deletion

**Example:**
```json
{
  "tool": "delete_attachment",
  "arguments": {
    "attachment_id": "67890"
  }
}
```

## Gherkin & Cucumber

### update_gherkin_definition

Update the Gherkin scenario definition for a Cucumber test.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| issue_id | string | Yes | The Jira issue ID of the Cucumber test |
| gherkin_text | string | Yes | The new Gherkin scenario content in standard format |

**Returns:** Updated test information with validation results

**Example:**
```json
{
  "tool": "update_gherkin_definition",
  "arguments": {
    "issue_id": "PROJ-123",
    "gherkin_text": "Feature: Login\nScenario: Successful login\nGiven user is on login page\nWhen user enters valid credentials\nThen user should be logged in"
  }
}
```

## Test Organization

### get_folder_contents

Retrieve contents of a test repository folder.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| project_id | string | Yes | The project ID where the folder exists |
| folder_path | string | No | The path of the folder (defaults to root "/") |

**Returns:** Folder details and contents including tests and subfolders

**Example:**
```json
{
  "tool": "get_folder_contents",
  "arguments": {
    "project_id": "10001",
    "folder_path": "/Component/UI"
  }
}
```

### move_test_to_folder

Move a test to a different folder in the test repository.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| issue_id | string | Yes | The Jira issue ID of the test to move |
| folder_path | string | Yes | The path of the destination folder |

**Returns:** Confirmation of move with previous and new folder information

**Example:**
```json
{
  "tool": "move_test_to_folder",
  "arguments": {
    "issue_id": "PROJ-123",
    "folder_path": "/Component/API"
  }
}
```

## Dataset Management

### get_dataset

Retrieve a specific dataset for data-driven testing.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| test_issue_id | string | Yes | The test issue ID to retrieve dataset for |

**Returns:** Dict with 'dataset' (object or None) and 'found' (boolean)

**Example:**
```json
{
  "tool": "get_dataset",
  "arguments": {
    "test_issue_id": "PROJ-123"
  }
}
```

### get_datasets

Retrieve datasets for multiple tests.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| test_issue_ids | array | Yes | List of test issue IDs to retrieve datasets for |

**Returns:** Dict with 'datasets' key containing list of dataset objects

**Example:**
```json
{
  "tool": "get_datasets",
  "arguments": {
    "test_issue_ids": ["PROJ-123", "PROJ-456", "PROJ-789"]
  }
}
```

## Utilities

### execute_jql_query

Execute a custom JQL query for different Xray entity types.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| jql | string | Yes | JQL query string |
| entity_type | string | No | Type of entity to query ("test" or "testexecution", default: "test") |
| limit | integer | No | Maximum results to return (1-100, default: 100) |

**Returns:** Query results with metadata and pagination info

**Example:**
```json
{
  "tool": "execute_jql_query",
  "arguments": {
    "jql": "project = PROJ AND created >= -30d",
    "entity_type": "test",
    "limit": 50
  }
}
```

### validate_connection

Test connection and authentication with Xray API.

**Parameters:** None

**Returns:** Connection status, authentication information, and API health details

**Example:**
```json
{
  "tool": "validate_connection",
  "arguments": {}
}
```

---

## Configuration

All tools require proper Xray API credentials configured through environment variables:

- `XRAY_CLIENT_ID`: Your Xray API client ID from Global Settings > API Keys
- `XRAY_CLIENT_SECRET`: Your Xray API client secret (keep secure!)
- `XRAY_BASE_URL`: Base URL for Xray instance (defaults to https://xray.cloud.getxray.app)

## Error Handling

All tools return structured error responses when exceptions occur. Common error types include:

- **Authentication Errors**: Invalid or expired credentials
- **Validation Errors**: Invalid parameters or missing required fields
- **API Errors**: Xray service unavailable or rate limiting
- **Not Found Errors**: Requested resources don't exist

## Rate Limits

The Xray API has built-in rate limiting. The MCP server handles this gracefully with automatic retries and exponential backoff for transient failures.

## Support

For issues with specific tools or to request additional functionality, please refer to the project documentation or create an issue in the repository.