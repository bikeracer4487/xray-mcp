# TestExecution Complete Reference

This document consolidates all TestExecution-related operations, objects, and types from the XRAY GraphQL API.

## Table of Contents

1. [Queries](#queries)
   - [getTestExecution](#gettestexecution)
   - [getTestExecutions](#gettestexecutions)
2. [Mutations](#mutations)
   - [createTestExecution](#createtestexecution)
   - [deleteTestExecution](#deletetestexecution)
   - [addTestsToTestExecution](#addteststotestexecution)
   - [removeTestsFromTestExecution](#removetestsfromtestexecution)
   - [addTestExecutionsToTest](#addtestexecutionstotest)
   - [removeTestExecutionsFromTest](#removetestexecutionsfromtest)
   - [addTestEnvironmentsToTestExecution](#addtestenvironmentstotestexecution)
   - [removeTestEnvironmentsFromTestExecution](#removetestenvironmentsfromtestexecution)
3. [Objects](#objects)
   - [TestExecution](#testexecution-object)
   - [TestExecutionResults](#testexecutionresults)
   - [CreateTestExecutionResult](#createtestexecutionresult)
   - [AddTestExecutionsResult](#addtestexecutionsresult)

---

## Queries

### getTestExecution

**Category:** Queries  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/gettestexecution.doc.html

Returns a Test Execution, optionally by its issue ID.

```graphql
{
    getTestExecution {
        issueId
        projectId
        jira(fields: ["assignee", "reporter"])
    }
}
```

**Example with specific issue ID:**
```graphql
{
    getTestExecution(issueId: "12345") {
        issueId
        tests(limit: 100) {
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
    }
}
```

### getTestExecutions

**Category:** Queries  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/gettestexecutions.doc.html

Returns multiple Test Executions with pagination support.

```graphql
{
    getTestExecutions(limit: 100) {
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

**Example with JQL filter:**
```graphql
{
    getTestExecutions(jql: "project = 'PC'", limit: 10) {
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

**Note:** If the jql returns more than 100 issues, an error will be returned asking the user to refine the jql search.

---

## Mutations

### createTestExecution

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/createtestexecution.doc.html

Creates a new Test Execution.

```graphql
mutation {
    createTestExecution(
        testIssueIds: ["54321"]
        testEnvironments: ["android"]
        jira: {
            fields: { summary: "Test Execution for CALC-123", project: {key: "CALC"} }
        }
    ) {
        testExecution {
            issueId
            jira(fields: ["key"])
        }
        warnings
        createdTestEnvironments
    }
}
```

### deleteTestExecution

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/deletetestexecution.doc.html

Deletes a Test Execution.

```graphql
mutation {
    deleteTestExecution(issueId: "12345")
}
```

### addTestsToTestExecution

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/addteststotestexecution.doc.html

Associates Tests with a Test Execution.

```graphql
mutation {
    addTestsToTestExecution(
        issueId: "12345",
        testIssueIds: ["54321"]
    ) {
        addedTests
        warning
    }
}
```

### removeTestsFromTestExecution

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/removetestsfromtestexecution.doc.html

Removes Tests from a Test Execution.

```graphql
mutation {
    removeTestsFromTestExecution(issueId: "12345", testIssueIds: ["54321", "67890"])
}
```

### addTestExecutionsToTest

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/addtestexecutionstotest.doc.html

Associates Test Executions with a Test.

```graphql
mutation {
    addTestExecutionsToTest(
        issueId: "12345",
        testExecIssueIds: ["54321"]
    ) {
        addedTestExecutions
        warning
    }
}
```

**Adding to a specific test version:**
```graphql
mutation {
    addTestExecutionsToTest(
        issueId: "12345",
        versionId: 3,
        testExecIssueIds: ["54321"]
    ) {
        addedTestExecutions
        warning
    }
}
```

### removeTestExecutionsFromTest

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/removetestexecutionsfromtest.doc.html

Removes Test Executions from a Test.

```graphql
mutation {
    removeTestExecutionsFromTest(issueId: "12345", testExecIssueIds: ["54321", "67890"])
}
```

### addTestEnvironmentsToTestExecution

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/addtestenvironmentstotestexecution.doc.html

Adds Test Environments to a Test Execution.

```graphql
mutation {
    addTestEnvironmentsToTestExecution(
        issueId: "12345",
        testEnvironments: ["android", "ios"]
    ) {
        associatedTestEnvironments
        createdTestEnvironments
        warning
    }
}
```

### removeTestEnvironmentsFromTestExecution

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/removetestenvironmentsfromtestexecution.doc.html

Removes Test Environments from a Test Execution.

```graphql
mutation {
    removeTestEnvironmentsFromTestExecution(
        issueId: "12345",
        testEnvironments: ["android", "ios"]
    )
}
```

---

## Objects

### TestExecution Object

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testexecution.doc.html

Test Execution issue type definition.

```graphql
type TestExecution {
    # Id of the Test Execution issue.
    issueId: String 
    
    # Project id of the Test Execution issue.
    projectId: String 
    
    # Test Environments of the Test Execution.
    testEnvironments: [String] 
    
    # List of Tests associated with the Test Execution Issue.
    # Arguments:
    #   issueIds: the issue ids of the Tests.
    #   limit: the maximum amount of tests to be returned. The maximum is 100.
    #   start: the index of the first item to return in the page of results (page offset).
    tests(issueIds: [String], limit: Int!, start: Int): TestResults 
    
    # List of Test Plans associated with the Test Execution Issue.
    # Arguments:
    #   issueIds: Ids of the Test Plans.
    #   limit: the maximum amount of Test Plans to be returned. The maximum is 100.
    #   start: the index of the first item to return in the page of results (page offset).
    testPlans(issueIds: [String], limit: Int!, start: Int): TestPlanResults 
    
    # List of Test Runs for the Test Execution Issue.
    # Arguments:
    #   limit: the maximum amount of tests to be returned. The maximum is 100.
    #   start: the index of the first item to return in the page of results (page offset).
    testRuns(limit: Int!, start: Int): TestRunResults 
    
    # List of Xray History results for the issue
    # Arguments:
    #   limit: the maximum amount of entries to be returned. The maximum is 100.
    #   start: the index of the first item to return in the page of results (page offset).
    history(limit: Int!, start: Int): XrayHistoryResults 
    
    # Extra Jira information of the Test Execution Issue.
    # Arguments:
    #   fields: List of the fields to be displayed.
    #   Check the field 'fields' of this Jira endpoint for more information.
    jira(fields: [String]): JSON 
    
    # Date when the test exec was last modified.
    lastModified: String 
}
```

### TestExecutionResults

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testexecutionresults.doc.html

Test Execution Results Type for paginated queries.

```graphql
type TestExecutionResults {
    # Total amount of issues.
    total: Int 
    
    # Index of the first item to return in the page of results (page offset).
    start: Int 
    
    # Maximum amount of Test Executions to be returned. The maximum is 100.
    limit: Int 
    
    # Test Execution issue results.
    results: [TestExecution] 
}
```

### CreateTestExecutionResult

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/createtestexecutionresult.doc.html

Create Test Execution Result type.

```graphql
type CreateTestExecutionResult {
    # Test Execution that was created.
    testExecution: TestExecution 
    
    # Test Environments that were created.
    createdTestEnvironments: [String] 
    
    # Warnings generated during the operation.
    warnings: [String] 
}
```

### AddTestExecutionsResult

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/addtestexecutionsresult.doc.html

Add Test Executions Result type.

```graphql
type AddTestExecutionsResult {
    # Issue ids of the added Test Executions.
    addedTestExecutions: [String] 
    
    # Warning generated during the operation.
    warning: String 
}
```