# Xray MCP Server - Comprehensive Functionality Specification

## Overview

This document defines the complete functionality requirements for the Xray MCP (Model Context Protocol) server. It provides programmatic access to Xray Cloud's test management system via GraphQL API integration.

## Core Entities

### 1. Tests
Primary entity for test case management.

**Test Types:**
- **Manual** - Step-by-step test instructions
- **Generic** - Unstructured test content
- **Cucumber** - Gherkin-based BDD tests

**Required Operations:**
- **Create**: `createTest` mutation with proper test type
- **Get**: `getTest` query by issue ID
- **List**: `getTests` query with JQL filtering and pagination
- **Update Type**: `updateTestType` mutation
- **Update Content**: `updateUnstructuredTestDefinition` for Gherkin
- **Delete**: `deleteTest` mutation

**Data Structures:**
- Test steps with action/data/result fields
- Gherkin content for Cucumber tests
- Test type definitions
- Jira field integration
- Precondition associations

### 2. Test Executions
Containers for organizing test runs in testing cycles.

**Required Operations:**
- **Create**: `createTestExecution` with associated tests
- **Get**: `getTestExecution` with test run details
- **List**: `getTestExecutions` with filtering
- **Delete**: `deleteTestExecution`
- **Add Tests**: `addTestsToTestExecution`
- **Remove Tests**: `removeTestsFromTestExecution`
- **Add Environments**: `addTestEnvironmentsToTestExecution`
- **Remove Environments**: `removeTestEnvironmentsFromTestExecution`

**Data Structures:**
- Test environment associations
- Test associations
- Test run collections
- Execution metadata

### 3. Test Plans
High-level planning and organization of test activities.

**Required Operations:**
- **Create**: `createTestPlan` with test associations
- **Get**: `getTestPlan` with associated tests
- **List**: `getTestPlans` with filtering
- **Delete**: `deleteTestPlan`
- **Add Tests**: `addTestsToTestPlan`
- **Remove Tests**: `removeTestsFromTestPlan`
- **Add Executions**: `addTestExecutionsToTestPlan`
- **Remove Executions**: `removeTestExecutionsFromTestPlan`

**Data Structures:**
- Test associations
- Test execution associations
- Plan metadata
- Folder organization

### 4. Test Runs
Individual test execution instances with results.

**Required Operations:**
- **Get**: `getTestRun` by execution and test ID
- **List**: `getTestRuns` with filtering
- **Update Status**: `updateTestRunStatus` (PASS/FAIL/etc.)
- **Update Comment**: `updateTestRunComment`
- **Add Defects**: `addDefectsToTestRun`
- **Add Evidence**: Document limitation (file upload complexity)

**Data Structures:**
- Status values and colors
- Comments and notes
- Defect associations
- Evidence attachments (limited)
- Execution timestamps

## GraphQL Schema Requirements

### Authentication
- OAuth 2.0 Bearer token authentication
- Token refresh handling
- Error handling for expired tokens

### Correct Field Names (From xray_schema.graphql)

**Test Creation:**
```graphql
mutation createTest(
    jira: JSON!
    testType: UpdateTestTypeInput
    steps: [CreateStepInput]    # NOT manualTestSteps
    gherkin: String
    preconditionIssueIds: [String]
    folderPath: String
) {
    # Return structure
}
```

**Step Input Structure:**
```graphql
input CreateStepInput {    # NOT ManualTestStepInput
    action: String
    data: String
    result: String
    attachments: [AttachmentInput]
    customFields: [CustomStepFieldInput]
    callTestIssueId: String
}
```

**Test Type Input:**
```graphql
input UpdateTestTypeInput {
    name: String!
}
```

### Response Handling
- Standardized error format
- Pagination support (limit: 100 max)
- Field selection optimization
- Warning message handling

### Query Patterns

**Basic Queries:**
- Single entity retrieval by ID
- Multi-entity listing with JQL
- Pagination with start/limit
- Field selection for performance

**Mutation Patterns:**
- Create operations with full data
- Update operations with partial data
- Delete operations by ID
- Association management (add/remove)

## API Integration Constraints

### Xray Cloud Limitations
- Maximum 100 items per GraphQL query
- JQL queries returning >100 issues will error
- Authentication tokens have expiration
- Rate limiting may apply

### Field Selection Requirements
Optimize API calls by selecting only needed fields:
```graphql
{
    getTest(issueId: "123") {
        issueId
        testType { name }
        jira(fields: ["key", "summary"])
        # Only include fields actually needed
    }
}
```

### Error Handling Requirements
- GraphQL error parsing
- HTTP status code handling
- Authentication error recovery
- Rate limit backoff
- Network error retries

## MCP Tool Interface

### Unified Tool Design
Single tool `xray_test` with entity-based dispatch:

```python
async def xray_test(
    entity: Literal["test", "test_execution", "test_plan", "test_run"],
    action: str,
    **kwargs
) -> list[types.TextContent]:
```

### Parameter Validation
- Entity validation against supported types
- Action validation per entity
- Required parameter checking
- Type conversion and validation

### Response Format
Standardized JSON response structure:
```json
{
    "success": true|false,
    "data": {...},
    "errors": ["..."],
    "warnings": ["..."]
}
```

## Implementation Architecture

### Manager Pattern
- `TestManager` - Test CRUD operations
- `ExecutionManager` - Test execution management
- `PlanManager` - Test plan management
- `RunManager` - Test run management

### Template System
- F-string GraphQL templates
- Variable substitution
- Query optimization
- Error-resistant formatting

### Authentication Layer
- Token acquisition and caching
- Automatic refresh handling
- Error recovery mechanisms

## Validation Requirements

### End-to-End Testing
Every operation must be validated against live Xray API:
- Create → Get → Update → Delete cycles
- Relationship management
- Error condition handling
- Pagination functionality

### Integration Test Coverage
- Authentication flow
- All CRUD operations
- All relationship operations
- Error scenarios
- Edge cases (empty results, large datasets)

### Manual Validation Checklist
- [ ] Create Manual test with steps
- [ ] Create Generic test
- [ ] Create Cucumber test with Gherkin
- [ ] Create Test Execution with tests
- [ ] Create Test Plan with tests
- [ ] Update Test Run status
- [ ] Add/remove test associations
- [ ] Handle API errors gracefully

## Known Limitations

### Not Implemented
- **Evidence file upload** - Complex multipart file handling
- **Jira field updates** - Requires REST API integration
- **Complex attachment management** - File handling complexity
- **Test step evidence** - Attachment upload limitations

### Performance Considerations
- Response caching infrastructure (ready, not active)
- Batch operations (not implemented)
- Large dataset handling (basic pagination only)

## Success Criteria

### Functional Requirements
- All CRUD operations work end-to-end
- All relationship management works
- Error handling provides useful feedback
- Authentication works reliably

### Quality Requirements
- 100% test coverage for implemented features
- All GraphQL templates validated against schema
- Performance acceptable for typical usage
- Clear documentation for all limitations

### User Experience Requirements
- Single tool interface is intuitive
- Error messages are actionable
- Response format is consistent
- Setup process is straightforward

This specification serves as the definitive guide for implementation completion and validation.