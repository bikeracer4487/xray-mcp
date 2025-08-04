# XRAY Tests Complete Reference

This document consolidates all test-related GraphQL API documentation for XRAY, including queries, mutations, and object types.

**Last Updated:** August 2025  
**Source:** XRAY Cloud GraphQL API Documentation

## Table of Contents

1. [Queries](#queries)
   - [getTest](#gettest)
   - [getTests](#gettests)
   - [getExpandedTest](#getexpandedtest)
   - [getExpandedTests](#getexpandedtests)
2. [Mutations](#mutations)
   - [createTest](#createtest)
   - [deleteTest](#deletetest)
   - [updateTestType](#updatetesttype)
   - [updateUnstructuredTestDefinition](#updateunstructuredtestdefinition)
3. [Object Types](#object-types)
   - [Test](#test)
   - [ExpandedTest](#expandedtest)
   - [TestResults](#testresults)
   - [ExpandedTestResults](#expandedtestresults)
   - [CreateTestResult](#createtestresult)
   - [TestType](#testtype)
   - [TestStatusType](#teststatustype)
   - [TestVersion](#testversion)
   - [TestVersionResults](#testversionresults)
   - [ProjectSettingsTestType](#projectsettingstesttype)

---

## Queries

### getTest

**Source:** https://us.xray.cloud.getxray.app/doc/graphql/gettest.doc.html

Retrieves a single test by issue ID.

#### GraphQL Schema

```graphql
query {
    getTest(issueId: "12345") {
        issueId
        testType {
            name
        }
        steps {
            action
            data
            result
            attachments {
                id
                filename
            }
        }
        gherkin
        jira(fields: ["key", "assignee", "reporter"])
    }
}
```

#### Example

```graphql
query {
    getTest(issueId: "1000") {
        issueId
        testType {
            name
        }
        steps {
            action
            data
            result
            attachments {
                id
                filename
            }
        }
        gherkin
        jira(fields: ["key", "assignee", "reporter"])
    }
}
```

---

### getTests

**Source:** https://us.xray.cloud.getxray.app/doc/graphql/gettests.doc.html

Retrieves multiple tests with pagination and JQL filtering.

#### GraphQL Schema

```graphql
query GetTests($jql: String, $limit: Int!) {
    getTests(jql: $jql, limit: $limit) {
        total
        start
        limit
        results {
            issueId
            testType {
                name
            }
            steps {
                id
                action
                data
                result
                customFields {
                    id
                    name
                    value
                }
                attachments {
                    id
                    filename
                }
            }
            jira(fields: ["assignee"])
        }
    }
}
```

#### Example with JQL

```graphql
query {
    getTests(jql: "project = 'CALC' and issuetype = 'Test'", limit: 100) {
        total
        start
        limit
        results {
            issueId
            testType {
                name
            }
            steps {
                id
                action
                data
                result
                customFields {
                    id
                    name
                    value
                }
                attachments {
                    id
                    filename
                }
            }
            jira(fields: ["assignee"])
        }
    }
}
```

**Note:** JQL queries returning more than 100 issues will error.

---

### getExpandedTest

**Source:** https://us.xray.cloud.getxray.app/doc/graphql/getexpandedtest.doc.html

Retrieves detailed information for a single test with version support.

#### GraphQL Schema

```graphql
query GetExpandedTest($issueId: String!, $testVersionId: Int) {
    getExpandedTest(issueId: $issueId, testVersionId: $testVersionId) {
        issueId
        versionId
        testType {
            name
        }
        steps {
            id
            action
            data
            result
            parentTestIssueId
            calledTestIssueId
            attachments {
                id
                filename
            }
        }
        warnings
    }
}
```

#### Example

```graphql
query {
    getExpandedTest(issueId: "10000") {
        issueId
        versionId
        testType {
            name
        }
        steps {
            id
            action
            data
            result
            parentTestIssueId
            calledTestIssueId
            attachments {
                id
                filename
            }
        }
        warnings
    }
}
```

---

### getExpandedTests

**Source:** https://us.xray.cloud.getxray.app/doc/graphql/getexpandedtests.doc.html

Retrieves multiple tests with expanded details and version support.

#### GraphQL Schema

```graphql
query {
    getExpandedTests(limit: 100) {
        total
        start
        limit
        results {
            issueId
            versionId
            testType {
                name
            }
            steps {
                id
                action
                data
                result
                customFields {
                    id
                    name
                    value
                }
                attachments {
                    id
                    filename
                }
                parentTestIssueId
                calledTestIssueId
            }
            warnings
        }
    }
}
```

#### Example with Specific Test Versions

```graphql
query {
    getExpandedTests(tests: [
        { issueId: "10000", testVersionId: 1 },
        { issueId: "10001", testVersionId: 2 }
    ]) {
        results {
            issueId
            versionId
            testType {
                name
            }
            steps {
                id
                action
                data
                result
                customFields {
                    id
                    name
                    value
                }
                attachments {
                    id
                    filename
                }
                parentTestIssueId
                calledTestIssueId
            }
            warnings
        }
    }
}
```

---

## Mutations

### createTest

**Source:** https://us.xray.cloud.getxray.app/doc/graphql/createtest.doc.html

Creates a new test issue.

#### GraphQL Schema

```graphql
mutation {
    createTest(
        testType: { name: "Generic" },
        unstructured: "Perform exploratory tests on calculator.",
        jira: {
            fields: { summary:"Exploratory Test", project: {key: "CALC"} }
        }
    ) {
        test {
            issueId
            testType {
                name
            }
            unstructured
            jira(fields: ["key"])
        }
        warnings
    }
}
```

#### Example - Manual Test with Steps

```graphql
mutation {
    createTest(
        testType: { name: "Manual" },
        steps: [
            {
                action: "Create first example step",
                result: "First step was created"
            },
            {
                action: "Create second example step with data",
                data: "Data for the step",
                result: "Second step was created with data"
            }
        ],
        jira: {
            fields: { summary:"Exploratory Test", project: {key: "CALC"} }
        }
    ) {
        test {
            issueId
            testType {
                name
            }
            steps {
                action
                data
                result
            }
            jira(fields: ["key"])
        }
        warnings
    }
}
```

---

### deleteTest

**Source:** https://us.xray.cloud.getxray.app/doc/graphql/deletetest.doc.html

Deletes a test issue.

#### GraphQL Schema

```graphql
mutation {
    deleteTest(issueId: "12345")
}
```

#### Example

```graphql
mutation {
    deleteTest(issueId: "12345")
}
```

---

### updateTestType

**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updatetesttype.doc.html

Updates the test type of an existing test.

#### GraphQL Schema

```graphql
mutation {
    updateTestType(issueId: "12345", testType: {name: "Manual"} ) {
        issueId
        testType {
            name
            kind
        }
    }
}
```

#### Example with Version

```graphql
mutation {
    updateTestType(issueId: "12345", versionId: 3, testType: {name: "Manual"} ) {
        issueId
        testType {
            name
            kind
        }
    }
}
```

---

### updateUnstructuredTestDefinition

**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updateunstructuredtestdefinition.doc.html

Updates the unstructured definition of a generic test.

#### GraphQL Schema

```graphql
mutation {
    updateUnstructuredTestDefinition(issueId: "12345", unstructured: "Generic definition" ) {
        issueId
        unstructured
    }
}
```

#### Example with Version

```graphql
mutation {
    updateUnstructuredTestDefinition(issueId: "12345", versionId: 3, unstructured: "Generic definition" ) {
        issueId
        unstructured
    }
}
```

---

## Object Types

### Test

**Source:** https://us.xray.cloud.getxray.app/doc/graphql/test.doc.html

The basic Test object representing a test issue in XRAY.

#### GraphQL Schema

```graphql
type Test {
    issueId: String
    projectId: String
    testType: TestType
    steps: [TestStep]
    unstructured: String
    gherkin: String
    scenarioType: String
    folder: Folder
    dataset: Dataset
    preconditions(
        start: Int,
        limit: Int = 100
    ): PreconditionResults
    testSets(
        start: Int,
        limit: Int = 100
    ): TestSetResults
    testPlans(
        start: Int,
        limit: Int = 100
    ): TestPlanResults
    testExecutions(
        start: Int,
        limit: Int = 100
    ): TestExecutionResults
    testRuns(
        start: Int,
        limit: Int = 100
    ): TestRunResults
    testVersions(
        includeArchived: Boolean = false,
        filterByTestType: String
    ): TestVersionResults
    status(
        environment: String,
        version: String,
        testPlan: String
    ): String
    jira(fields: [String]): JSON
    lastModified: String
    warnings: [String]
    xrayHistory(
        testPlanId: String,
        testEnvironmentId: String,
        start: Int = 0,
        limit: Int = 100
    ): XrayHistoryResults
}
```

---

### ExpandedTest

**Source:** https://us.xray.cloud.getxray.app/doc/graphql/expandedtest.doc.html

Extended version of Test with additional expanded information.

#### GraphQL Schema

```graphql
type ExpandedTest {
    issueId: String
    versionId: Int
    projectId: String
    testType: TestType
    unstructured: String
    gherkin: String
    scenarioType: String
    folder: Folder
    dataset: Dataset
    steps: [TestStep]
    preconditions(
        start: Int,
        limit: Int = 100
    ): PreconditionResults
    testSets(
        start: Int,
        limit: Int = 100
    ): TestSetResults
    testPlans(
        start: Int,
        limit: Int = 100
    ): TestPlanResults
    testExecutions(
        start: Int,
        limit: Int = 100
    ): TestExecutionResults
    testRuns(
        start: Int,
        limit: Int = 100
    ): TestRunResults
    testVersions(
        includeArchived: Boolean = false,
        filterByTestType: String
    ): TestVersionResults
    coverableIssues(
        jql: String,
        limit: Int = 100
    ): CoverableIssueResults
    status(
        environment: String,
        version: String,
        testPlan: String
    ): String
    jira(fields: [String]): JSON
    lastModified: String
    warnings: [String]
}
```

---

### TestResults

**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testresults.doc.html

Paginated container for basic test results.

#### GraphQL Schema

```graphql
type TestResults {
    total: Int
    start: Int
    limit: Int
    results: [Test]
    warnings: [String]
}
```

**Used by:** CoverableIssue, getTests, Precondition, TestExecution, TestPlan, TestSet

---

### ExpandedTestResults

**Source:** https://us.xray.cloud.getxray.app/doc/graphql/expandedtestresults.doc.html

Paginated container for expanded test results.

#### GraphQL Schema

```graphql
type ExpandedTestResults {
    total: Int
    start: Int
    limit: Int
    results: [ExpandedTest]
}
```

**Maximum limit:** 100

---

### CreateTestResult

**Source:** https://us.xray.cloud.getxray.app/doc/graphql/createtestresult.doc.html

Result object returned by the createTest mutation.

#### GraphQL Schema

```graphql
type CreateTestResult {
    test: Test
    warnings: [String]
}
```

---

### TestType

**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testtype.doc.html

Represents the type of a test.

#### GraphQL Schema

```graphql
type TestType {
    id: String
    name: String
    kind: String
}
```

**Kind values:** "Gherkin", "Steps", or "Unstructured"

---

### TestStatusType

**Source:** https://us.xray.cloud.getxray.app/doc/graphql/teststatustype.doc.html

Represents a test execution status.

#### GraphQL Schema

```graphql
type TestStatusType {
    name: String
    description: String
    final: Boolean
    color: String
}
```

---

### TestVersion

**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testversion.doc.html

Represents a specific version of a test.

#### GraphQL Schema

```graphql
type TestVersion {
    id: Int!
    name: String!
    default: Boolean
    archived: Boolean
    testType: TestType
    steps: [TestStep]
    unstructured: String
    gherkin: String
    scenarioType: String
    lastModified: String
    preconditions(
        start: Int,
        limit: Int = 100
    ): PreconditionResults
    testExecutions(
        start: Int,
        limit: Int = 100
    ): TestExecutionResults
    testRuns(
        start: Int,
        limit: Int = 100
    ): TestRunResults
}
```

---

### TestVersionResults

**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testversionresults.doc.html

Paginated container for test version results.

#### GraphQL Schema

```graphql
type TestVersionResults {
    total: Int
    start: Int
    limit: Int
    results: [TestVersion]
}
```

**Maximum limit:** 100

---

### ProjectSettingsTestType

**Source:** https://us.xray.cloud.getxray.app/doc/graphql/projectsettingstesttype.doc.html

Project-level test type configuration.

#### GraphQL Schema

```graphql
type ProjectSettingsTestType {
    testTypes: [TestType]
    defaultTestTypeId: String
}
```

---

## Usage Guidelines

### Query Selection Guide

| Use Case | Recommended Query |
|----------|------------------|
| Single test retrieval | `getTest` |
| Bulk test retrieval | `getTests` |
| Single test with version details | `getExpandedTest` |
| Bulk tests with full relationships | `getExpandedTests` |

### Common Patterns

1. **Pagination**: All result types support pagination with `start` and `limit` parameters (max 100)
2. **JQL Filtering**: Both `getTests` and `getExpandedTests` support JQL queries (limit: 100 results)
3. **Version Support**: Only expanded queries support test versioning
4. **Relationships**: Expanded types provide access to related entities (preconditions, test sets, etc.)

### Important Limitations

- Maximum 100 items per paginated query
- JQL queries returning >100 issues will error
- Test versions are only accessible through expanded queries
- Some fields may require specific permissions to access