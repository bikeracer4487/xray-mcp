# Xray Test Sets - Complete Reference

This document consolidates all Test Set-related GraphQL operations and types for Xray. Test Sets are collections of tests that can be organized for specific testing purposes.

## Table of Contents

1. [Queries](#queries)
   - [getTestSet](#gettestset)
   - [getTestSets](#gettestsets)
2. [Mutations](#mutations)
   - [createTestSet](#createtestset)
   - [deleteTestSet](#deletetestset)
   - [addTestSetsToTest](#addtestsetstotest)
   - [removeTestSetsFromTest](#removetestsetsfromtest)
   - [addTestsToTestSet](#addteststotestset)
   - [removeTestsFromTestSet](#removetestsfromtestset)
3. [Objects](#objects)
   - [TestSet](#testset-object)
   - [TestSetResults](#testsetresults)
   - [AddTestSetsResult](#addtestsetsresult)
   - [CreateTestSetResult](#createtestsetresult)

---

## Queries

### getTestSet

**Category:** Queries  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/gettestset.doc.html

Returns a single Test Set by its issue ID.

**GraphQL Schema Definition:**

```graphql
{
    getTestSet {
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
    getTestSet {
        issueId
        projectId
        jira(fields: ["assignee", "reporter"])
    }
}
```

Query with specific issue ID and tests:
```graphql
{
    getTestSet(issueId: "12345") {
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

### getTestSets

**Category:** Queries  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/gettestsets.doc.html

Returns multiple Test Sets with pagination support.

**GraphQL Schema Definition:**

```graphql
{
    getTestSets(limit: 100) {
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

Get first 100 Test Sets:
```graphql
{
    getTestSets(limit: 100) {
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
    getTestSets(jql: "project = 'PC'", limit: 10) {
        total
        start
        limit
        results {
            issueId
            tests(limit: 10) {
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

### createTestSet

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/createtestset.doc.html

Creates a new Test Set issue.

**GraphQL Schema Definition:**

```graphql
mutation {
    createTestSet(
        testIssueIds: ["54321"]
        jira: {
            fields: { summary: "Test Set for Generic Tests", project: {key: "CALC"} }
        }
    ) {
        testSet {
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
    createTestSet(
        testIssueIds: ["54321"]
        jira: {
            fields: { summary: "Test Set for Generic Tests", project: {key: "CALC"} }
        }
    ) {
        testSet {
            issueId
            jira(fields: ["key"])
        }
        warnings
    }
}
```

### deleteTestSet

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/deletetestset.doc.html

Deletes a Test Set issue.

**GraphQL Schema Definition:**

```graphql
mutation {
    deleteTestSet(issueId: "12345")
}
```

**Example:**

```graphql
mutation {
    deleteTestSet(issueId: "12345")
}
```

### addTestSetsToTest

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/addtestsetstotest.doc.html

Associates Test Sets with a Test.

**GraphQL Schema Definition:**

```graphql
mutation {
    addTestSetsToTest(
        issueId: "12345",
        testSetIssueIds: ["54321"]
    ) {
        addedTestSets
        warning
    }
}
```

**Example:**

```graphql
mutation {
    addTestSetsToTest(
        issueId: "12345",
        testSetIssueIds: ["54321"]
    ) {
        addedTestSets
        warning
    }
}
```

### removeTestSetsFromTest

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/removetestsetsfromtest.doc.html

Removes Test Sets from a Test.

**GraphQL Schema Definition:**

```graphql
mutation {
    removeTestSetsFromTest(issueId: "12345", testSetIssueIds: ["54321", "67890"])
}
```

**Example:**

```graphql
mutation {
    removeTestSetsFromTest(issueId: "12345", testSetIssueIds: ["54321", "67890"])
}
```

### addTestsToTestSet

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/addteststotestset.doc.html

Adds Tests to a Test Set.

**GraphQL Schema Definition:**

```graphql
mutation {
    addTestsToTestSet(
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
    addTestsToTestSet(
        issueId: "12345",
        testIssueIds: ["54321"]
    ) {
        addedTests
        warning
    }
}
```

### removeTestsFromTestSet

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/removetestsfromtestset.doc.html

Removes Tests from a Test Set.

**GraphQL Schema Definition:**

```graphql
mutation {
    removeTestsFromTestSet(issueId: "12345", testIssueIds: ["54321", "67890"])
}
```

**Example:**

```graphql
mutation {
    removeTestsFromTestSet(issueId: "12345", testIssueIds: ["54321", "67890"])
}
```

---

## Objects

### TestSet Object

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testset.doc.html

Represents a Test Set issue type in Xray.

**GraphQL Schema Definition:**

```graphql
type TestSet {
    # Issue id of the Test Set Issue.
    issueId: String

    # Project id of the Test Set Issue.
    projectId: String

    # List of Tests associated with the Test Set Issue.
    # Arguments:
    #   issueIds: Ids of the Tests.
    #   limit: Maximum amount of tests to be returned. The maximum is 100.
    #   start: Index of the first item to return in the page of results (page offset).
    tests(issueIds: [String], limit: Int!, start: Int): TestResults

    # List of Xray History results for the issue
    # Arguments:
    #   limit: the maximum amount of entries to be returned. The maximum is 100.
    #   start: the index of the first item to return in the page of results (page offset).
    history(limit: Int!, start: Int): XrayHistoryResults

    # Extra Jira information of the Test Set Issue.
    # Arguments:
    #   fields: List of the fields to be displayed.
    #   Check the field 'fields' of this Jira endpoint for more information.
    jira(fields: [String]): JSON

    # Date when the test set was last modified.
    lastModified: String
}
```

**Required by:**
- CreateTestSetResult - Create Test Set Result type
- getTestSet
- Query
- TestSetResults - Test Set Results

### TestSetResults

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testsetresults.doc.html

Results type for paginated Test Set queries.

**GraphQL Schema Definition:**

```graphql
type TestSetResults {
    # Total amount of issues.
    total: Int

    # Index of the first item to return in the page of results (page offset).
    start: Int

    # Maximum amount of test sets to be returned. The maximum is 100.
    limit: Int

    # Test Set issue results.
    results: [TestSet]
}
```

**Required by:**
- ExpandedTest - Expanded test issue type
- getTestSets
- Query
- Test - Test issue type

### AddTestSetsResult

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/addtestsetsresult.doc.html

Result type for adding Test Sets to Tests.

**GraphQL Schema Definition:**

```graphql
type AddTestSetsResult {
    # Issue ids of the added Test Set.
    addedTestSets: [String]

    # Warning generated during the operation.
    warning: String
}
```

**Required by:**
- addTestSetsToTest
- Mutation

### CreateTestSetResult

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/createtestsetresult.doc.html

Result type for creating a Test Set.

**GraphQL Schema Definition:**

```graphql
type CreateTestSetResult {
    # Test Set that was created.
    testSet: TestSet

    # Warnings generated during the operation.
    warnings: [String]
}
```

**Required by:**
- createTestSet
- Mutation

---

## Usage Notes

1. **Test Organization**: Test Sets allow organizing tests for specific purposes like regression testing, smoke testing, or feature-specific testing
2. **Multiple Membership**: Unlike folders, tests can belong to multiple Test Sets
3. **Dynamic Collections**: Test Sets can be used to create dynamic groupings of tests across different components or features
4. **Pagination**: Most list operations support pagination with `limit` and `start` parameters
5. **Maximum Limits**: 
   - Tests per Test Set query: 100
   - JQL query results: 100 issues
6. **Bidirectional Relationships**: Tests can be added to Test Sets, and Test Sets can be associated with Tests

## Common Use Cases

1. **Regression Testing**: Create Test Sets for regression test suites
2. **Release Testing**: Organize tests specific to a release or sprint
3. **Feature Testing**: Group tests related to specific features
4. **Cross-Functional Testing**: Create Test Sets that span multiple components
5. **Priority-Based Testing**: Organize tests by priority levels (Critical, High, Medium, Low)

This consolidated reference provides all GraphQL operations and types related to Xray Test Sets in a single document.