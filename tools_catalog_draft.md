## 🛠️ Available Tools

The server currently provides 48 MCP tools organized into 12 categories for comprehensive Xray test management. All tools return structured error responses: `{"error": "message", "type": "ErrorType"}`.

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
| | | `steps` | List[Dict] | ❌ | Manual test steps (action, data, result) |
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

### Test Execution Management Tools (6)

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
| **delete_test_execution** | Delete test execution | `issue_id` | string | ✅ | ⚠️ Removes test history |
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

### Test Set Operations (6)

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
| **delete_test_set** | Delete test set | `issue_id` | string | ✅ | Test set to delete |
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

### Test Plan Operations (6)

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
| **delete_test_plan** | Delete test plan | `issue_id` | string | ✅ | Test plan to delete |
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

### Test Run Management (4)

| Tool | Purpose | Parameters | Type | Req? | Notes |
|------|---------|------------|------|------|-------|
| **get_test_run** | Retrieve single test run by ID | `issue_id` | string | ✅ | Test run with execution status |
| **get_test_runs** | Query multiple test runs with JQL | `jql` | string | ❌ | Optional JQL filter |
| | | `limit` | int | ❌ | Max 100 (default 100) |
| **create_test_run** | Create new test run | `project_key` | string | ✅ | Jira project key |
| | | `summary` | string | ✅ | Test run title |
| | | `test_environments` | List[string] | ❌ | Test environments |
| | | `description` | string | ❌ | Test run description |
| **delete_test_run** | Delete test run | `issue_id` | string | ✅ | Test run to delete |

**Example call:**
```json
{ "tool": "create_test_run", "arguments": {
  "project_key": "PROJ",
  "summary": "Nightly Run",
  "test_environments": ["Production"]
}}
```

### Test Versioning (4)

| Tool | Purpose | Parameters | Type | Req? | Notes |
|------|---------|------------|------|------|-------|
| **get_test_versions** | Retrieve all versions of a test | `issue_id` | string | ✅ | Test to get versions for |
| **archive_test_version** | Archive specific test version | `issue_id` | string | ✅ | Test containing version |
| | | `version_id` | int | ✅ | Version ID to archive (≥1) |
| **restore_test_version** | Restore archived test version | `issue_id` | string | ✅ | Test containing version |
| | | `version_id` | int | ✅ | Version ID to restore (≥1) |
| **create_test_version_from** | Create new version from existing | `issue_id` | string | ✅ | Source test |
| | | `source_version_id` | int | ✅ | Version to copy from (≥1) |
| | | `version_name` | string | ✅ | Name for new version |

**Example call:**
```json
{ "tool": "create_test_version_from", "arguments": {
  "issue_id": "PROJ-123",
  "source_version_id": 1,
  "version_name": "v2.0"
}}
```

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