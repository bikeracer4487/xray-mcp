# Xray Test Plans - Complete Reference

This document consolidates all Test Plan-related GraphQL operations and types for Xray. Test Plans are used to organize and plan test execution activities for specific releases, versions, or testing cycles.

## Table of Contents

1. [Queries](#queries)
   - [getTestPlan](#gettestplan)
   - [getTestPlans](#gettestplans)
2. [Mutations](#mutations)
   - [createTestPlan](#createtestplan)
   - [deleteTestPlan](#deletetestplan)
   - [addTestPlansToTest](#addtestplanstotest)
   - [removeTestPlansFromTest](#removetestplansfromtest)
   - [addTestsToTestPlan](#addteststotestplan)
   - [removeTestsFromTestPlan](#removetestsfromtestplan)
   - [addTestExecutionsToTestPlan](#addtestexecutionstotestplan)
   - [removeTestExecutionsFromTestPlan](#removetestexecutionsfromtestplan)
3. [Objects](#objects)
   - [TestPlan](#testplan-object)
   - [TestPlanResults](#testplanresults)
   - [AddTestPlansResult](#addtestplansresult)
   - [CreateTestPlanResult](#createtestplanresult)

---

## Queries

### getTestPlan

**Category:** Queries  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/gettestplan.doc.html

Returns a single Test Plan by its issue ID.

**GraphQL Schema Definition:**

```graphql
{
    getTestPlan {
        issueId
        projectId
        jira(fields: ["assignee", "reporter"])
    }
}
```

**Examples:**

Basic query:
```graphql
{
    getTestPlan {
        issueId
        projectId
        jira(fields: ["assignee", "reporter"])
    }
}
```

Query with specific issue ID and tests:
```graphql
{
    getTestPlan(issueId: "12345") {
        issueId
        tests(limit: 100) {
            results {
                issueId
                testType {
                    name
                }
            }
        }
    }
}
```

### getTestPlans

**Category:** Queries  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/gettestplans.doc.html

Returns multiple Test Plans with pagination support.

**GraphQL Schema Definition:**

```graphql
{
    getTestPlans(limit: 100) {
        total
        start
        limit
        results {
            issueId
            jira(fields: ["assignee", "reporter"])
        }
    }
}
```

**Examples:**

Get first 100 Test Plans:
```graphql
{
    getTestPlans(limit: 100) {
        total
        start
        limit
        results {
            issueId
            jira(fields: ["assignee", "reporter"])
        }
    }
}
```

Query with JQL filter and tests:
```graphql
{
    getTestPlans(jql: "project = 'PC'", limit: 10) {
        total
        start
        limit
        results {
            issueId
            tests(limit: 10) {
                total
                start
                limit
                results {
                    issueId
                    testType {
                        name
                    }
                }
            }
            jira(fields: ["assignee", "reporter"])
        }
    }
}
```

**Note:** If the jql returns more than 100 issues an error will be returned asking the user to refine the jql search.

---

## Mutations

### createTestPlan

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/createtestplan.doc.html

Creates a new Test Plan issue.

**GraphQL Schema Definition:**

```graphql
mutation {
    createTestPlan(
        testIssueIds: ["54321"]
        jira: {
            fields: { summary: "Test Plan for v1.0", project: {key: "CALC"} }
        }
    ) {
        testPlan {
            issueId
            jira(fields: ["key"])
        }
        warnings
    }
}
```

**Example:**

```graphql
mutation {
    createTestPlan(
        testIssueIds: ["54321"]
        jira: {
            fields: { summary: "Test Plan for v1.0", project: {key: "CALC"} }
        }
    ) {
        testPlan {
            issueId
            jira(fields: ["key"])
        }
        warnings
    }
}
```

### deleteTestPlan

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/deletetestplan.doc.html

Deletes a Test Plan issue.

**GraphQL Schema Definition:**

```graphql
mutation {
    deleteTestPlan(issueId: "12345")
}
```

**Example:**

```graphql
mutation {
    deleteTestPlan(issueId: "12345")
}
```

### addTestPlansToTest

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/addtestplanstotest.doc.html

Associates Test Plans with a Test.

**GraphQL Schema Definition:**

```graphql
mutation {
    addTestPlansToTest(
        issueId: "12345",
        testPlanIssueIds: ["54321"]
    ) {
        addedTestPlans
        warning
    }
}
```

**Example:**

```graphql
mutation {
    addTestPlansToTest(
        issueId: "12345",
        testPlanIssueIds: ["54321"]
    ) {
        addedTestPlans
        warning
    }
}
```

### removeTestPlansFromTest

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/removetestplansfromtest.doc.html

Removes Test Plans from a Test.

**GraphQL Schema Definition:**

```graphql
mutation {
    removeTestPlansFromTest(issueId: "12345", testPlanIssueIds: ["54321", "67890"])
}
```

**Example:**

```graphql
mutation {
    removeTestPlansFromTest(issueId: "12345", testPlanIssueIds: ["54321", "67890"])
}
```

### addTestsToTestPlan

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/addteststotestplan.doc.html

Adds Tests to a Test Plan.

**GraphQL Schema Definition:**

```graphql
mutation {
    addTestsToTestPlan(
        issueId: "12345",
        testIssueIds: ["54321"]
    ) {
        addedTests
        warning
    }
}
```

**Example:**

```graphql
mutation {
    addTestsToTestPlan(
        issueId: "12345",
        testIssueIds: ["54321"]
    ) {
        addedTests
        warning
    }
}
```

### removeTestsFromTestPlan

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/removetestsfromtestplan.doc.html

Removes Tests from a Test Plan.

**GraphQL Schema Definition:**

```graphql
mutation {
    removeTestsFromTestPlan(issueId: "12345", testIssueIds: ["54321", "67890"])
}
```

**Example:**

```graphql
mutation {
    removeTestsFromTestPlan(issueId: "12345", testIssueIds: ["54321", "67890"])
}
```

### addTestExecutionsToTestPlan

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/addtestexecutionstotestplan.doc.html

Associates Test Executions with a Test Plan.

**GraphQL Schema Definition:**

```graphql
mutation {
    addTestExecutionsToTestPlan(
        issueId: "12345",
        testExecIssueIds: ["54321"]
    ) {
        addedTestExecutions
        warning
    }
}
```

**Example:**

```graphql
mutation {
    addTestExecutionsToTestPlan(
        issueId: "12345",
        testExecIssueIds: ["54321"]
    ) {
        addedTestExecutions
        warning
    }
}
```

### removeTestExecutionsFromTestPlan

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/removetestexecutionsfromtestplan.doc.html

Removes Test Executions from a Test Plan.

**GraphQL Schema Definition:**

```graphql
mutation {
    removeTestExecutionsFromTestPlan(issueId: "12345", testExecIssueIds: ["54321", "67890"])
}
```

**Example:**

```graphql
mutation {
    removeTestExecutionsFromTestPlan(issueId: "12345", testExecIssueIds: ["54321", "67890"])
}
```

---

## Objects

### TestPlan Object

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testplan.doc.html

Represents a Test Plan issue type in Xray.

**GraphQL Schema Definition:**

```graphql
type TestPlan {
    # Id of the Test Plan issue.
    issueId: String

    # Project id of the Test Plan issue.
    projectId: String

    # List of Tests associated with the Test Plan issue.
    # Arguments:
    #   issueIds: the issue ids of the Tests.
    #   limit: the maximum amount of tests to be returned. The maximum is 100.
    #   start: the index of the first item to return in the page of results (page offset).
    tests(issueIds: [String], limit: Int!, start: Int): TestResults

    # List of Test Executions associated with the Test Plan issue.
    # Arguments:
    #   issueIds: issue ids of the Test Executions.
    #   limit: the maximum amount of tests to be returned. The maximum is 100.
    #   start: the index of the first item to return in the page of results (page offset).
    testExecutions(issueIds: [String], limit: Int!, start: Int): TestExecutionResults

    # List of Xray History results for the issue
    # Arguments:
    #   limit: the maximum amount of entries to be returned. The maximum is 100.
    #   start: the index of the first item to return in the page of results (page offset).
    history(limit: Int!, start: Int): XrayHistoryResults

    # Extra Jira information of the Test Plan issue.
    # Arguments:
    #   fields: list of the fields to be displayed.
    #   Check the field 'fields' of this Jira endpoint for more information.
    jira(fields: [String]): JSON

    # Folder structure of the Test Plan.
    folders: FolderResults

    # Date when the test plan was last modified.
    lastModified: String
}
```

**Required by:**
- CreateTestPlanResult - Create Test Plan Result type
- getTestPlan
- Query
- TestPlanResults - Test Plan Results type

### TestPlanResults

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testplanresults.doc.html

Results type for paginated Test Plan queries.

**GraphQL Schema Definition:**

```graphql
type TestPlanResults {
    # Total amount of issues.
    total: Int

    # Index of the first item to return in the page of results (page offset).
    start: Int

    # Maximum amount of Test Plans to be returned. The maximum is 100.
    limit: Int

    # Test Plan issue results.
    results: [TestPlan]

    # Warnings generated during the operation.
    warnings: [String]
}
```

**Required by:**
- ExpandedTest - Expanded test issue type
- getTestPlans
- Query
- Test - Test issue type
- TestExecution - Test Execution issue type

### AddTestPlansResult

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/addtestplansresult.doc.html

Result type for adding Test Plans to Tests.

**GraphQL Schema Definition:**

```graphql
type AddTestPlansResult {
    # Issue ids of the added Test Plans.
    addedTestPlans: [String]

    # Warning generated during the operation.
    warning: String
}
```

**Required by:**
- addTestPlansToTest
- Mutation

### CreateTestPlanResult

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/createtestplanresult.doc.html

Result type for creating a Test Plan.

**GraphQL Schema Definition:**

```graphql
type CreateTestPlanResult {
    # Test Plan that was created.
    testPlan: TestPlan

    # Warnings generated during the operation.
    warnings: [String]
}
```

**Required by:**
- createTestPlan
- Mutation

---

## Usage Notes

1. **Test Planning**: Test Plans organize tests for specific releases, versions, or testing cycles
2. **Test Execution Tracking**: Test Plans can be associated with Test Executions to track testing progress
3. **Folder Support**: Test Plans support folder structures for organizing tests within the plan
4. **Bidirectional Relationships**: 
   - Tests can be added to Test Plans
   - Test Plans can be associated with Tests
   - Test Executions can be linked to Test Plans
5. **Pagination**: Most list operations support pagination with `limit` and `start` parameters
6. **Maximum Limits**: 
   - Tests per Test Plan query: 100
   - Test Executions per Test Plan query: 100
   - JQL query results: 100 issues

## Common Use Cases

1. **Release Planning**: Create Test Plans for each release or version
2. **Sprint Testing**: Organize tests by sprint or iteration
3. **Test Campaign Management**: Group related test executions under a Test Plan
4. **Progress Tracking**: Monitor test execution progress against planned tests
5. **Coverage Analysis**: Ensure all planned tests are executed
6. **Regression Planning**: Create Test Plans for regression test cycles

## Test Plan Workflow

1. **Create Test Plan**: Define the scope and objectives
2. **Add Tests**: Associate relevant tests with the plan
3. **Execute Tests**: Create Test Executions linked to the plan
4. **Track Progress**: Monitor execution status and results
5. **Report Results**: Generate reports on plan completion

This consolidated reference provides all GraphQL operations and types related to Xray Test Plans in a single document.