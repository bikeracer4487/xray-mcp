# Xray Preconditions - Complete Reference

This document consolidates all precondition-related GraphQL operations and types for Xray.

## Table of Contents

1. [Queries](#queries)
   - [getPrecondition](#getprecondition)
   - [getPreconditions](#getpreconditions)
2. [Mutations](#mutations)
   - [createPrecondition](#createprecondition)
   - [updatePrecondition](#updateprecondition)
   - [deletePrecondition](#deleteprecondition)
   - [addPreconditionsToTest](#addpreconditionstotest)
   - [removePreconditionsFromTest](#removepreconditionsfromtest)
   - [addTestsToPrecondition](#addteststoprecondition)
   - [removeTestsFromPrecondition](#removetestsfromprecondition)
3. [Objects](#objects)
   - [Precondition](#precondition-object)
4. [Input Objects](#input-objects)
   - [UpdatePreconditionInput](#updatepreconditioninput)
   - [UpdatePreconditionTypeInput](#updatepreconditiontypeinput)

---

## Queries

### getPrecondition

**Category:** Queries  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/getprecondition.doc.html

Returns a single Precondition by its issue ID.

**GraphQL Schema Definition:**

```graphql
{
    getPrecondition {
        issueId
        preconditionType {
            kind
            name
        }
    }
}
```

**Examples:**

Basic query:
```graphql
{
    getPrecondition {
        issueId
        preconditionType {
            kind
            name
        }
    }
}
```

Query with specific issue ID:
```graphql
{
    getPrecondition(issueId: "12345") {
        issueId
        definition
        jira(fields: ["assignee", "reporter"])
    }
}
```

### getPreconditions

**Category:** Queries  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/getpreconditions.doc.html

Returns multiple Preconditions with pagination support.

**GraphQL Schema Definition:**

```graphql
{
    getPreconditions(limit: 100) {
        total
        start
        limit
        results {
            issueId
            preconditionType {
                name
                kind
            }
            definition
            jira(fields: ["assignee", "reporter"])
        }
    }
}
```

**Examples:**

Get first 100 Preconditions:
```graphql
{
    getPreconditions(limit: 100) {
        total
        start
        limit
        results {
            issueId
            preconditionType {
                name
                kind
            }
            definition
            jira(fields: ["assignee", "reporter"])
        }
    }
}
```

Query with JQL filter:
```graphql
{
    getPreconditions(jql: "project = 'PC'", limit: 10) {
        results {
            issueId
            preconditionType {
                name
                kind
            }
            jira(fields: ["assignee", "reporter"])
        }
    }
}
```

**Note:** If the jql returns more than 100 issues an error will be returned asking the user to refine the jql search.

---

## Mutations

### createPrecondition

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/createprecondition.doc.html

Creates a new Precondition issue.

**GraphQL Schema Definition:**

```graphql
mutation {
    createPrecondition(
        preconditionType: { name: "Generic" }
        definition: "Turn on calculator."
        jira: {
            fields: { summary:"Turn on calculator", project: {key: "CALC"} }
        }
    ) {
        precondition {
            issueId
            preconditionType {
                name
            }
            definition
            jira(fields: ["key"])
        }
        warnings
    }
}
```

**Example:**

```graphql
mutation {
    createPrecondition(
        preconditionType: { name: "Generic" }
        definition: "Turn on calculator."
        jira: {
            fields: { summary:"Turn on calculator", project: {key: "CALC"} }
        }
    ) {
        precondition {
            issueId
            preconditionType {
                name
            }
            definition
            jira(fields: ["key"])
        }
        warnings
    }
}
```

### updatePrecondition

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updateprecondition.doc.html

Updates an existing Precondition.

**GraphQL Schema Definition:**

```graphql
mutation {
    updatePrecondition(
        issueId: "49137",
        data: { preconditionType: {name: "Manual" }, definition: "Turn on calculator" }
    ) {
        issueId
        preconditionType {
            kind
            name
        }
        definition
    }
}
```

**Examples:**

Update precondition type and definition:
```graphql
mutation {
    updatePrecondition(
        issueId: "49137",
        data: { preconditionType: {name: "Manual" }, definition: "Turn on calculator" }
    ) {
        issueId
        preconditionType {
            kind
            name
        }
        definition
    }
}
```

Move precondition to folder:
```graphql
mutation {
    updatePrecondition(
        issueId: "12345",
        data: { folderPath: "/generic" }
    ) {
        issueId
        preconditionType {
            kind
            name
        }
        definition
    }
}
```

### deletePrecondition

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/deleteprecondition.doc.html

Deletes a Precondition issue.

**GraphQL Schema Definition:**

```graphql
mutation {
    deletePrecondition(issueId: "12345")
}
```

**Example:**

```graphql
mutation {
    deletePrecondition(issueId: "12345")
}
```

### addPreconditionsToTest

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/addpreconditionstotest.doc.html

Associates Preconditions with a Test.

**GraphQL Schema Definition:**

```graphql
mutation {
    addPreconditionsToTest(
        issueId: "12345",
        preconditionIssueIds: ["54321"]
    ) {
        addedPreconditions
        warning
    }
}
```

**Examples:**

Add precondition to test:
```graphql
mutation {
    addPreconditionsToTest(
        issueId: "12345",
        preconditionIssueIds: ["54321"]
    ) {
        addedPreconditions
        warning
    }
}
```

Add precondition to specific test version:
```graphql
mutation {
    addPreconditionsToTest(
        issueId: "12345",
        versionId: 3,
        preconditionIssueIds: ["54321"]
    ) {
        addedPreconditions
        warning
    }
}
```

### removePreconditionsFromTest

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/removepreconditionsfromtest.doc.html

Removes Preconditions from a Test.

**GraphQL Schema Definition:**

```graphql
mutation {
    removePreconditionsFromTest(issueId: "12345", preconditionIssueIds: ["54321", "67890"])
}
```

**Examples:**

Remove preconditions from test:
```graphql
mutation {
    removePreconditionsFromTest(issueId: "12345", preconditionIssueIds: ["54321", "67890"])
}
```

Remove preconditions from specific test version:
```graphql
mutation {
    removePreconditionsFromTest(issueId: "12345", versionId: 3, preconditionIssueIds: ["54321", "67890"])
}
```

### addTestsToPrecondition

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/addteststoprecondition.doc.html

Associates Tests with a Precondition.

**GraphQL Schema Definition:**

```graphql
mutation {
    addTestsToPrecondition(
        issueId: "12345",
        testIssueIds: ["54321"]
    ) {
        addedTests
        warning
    }
}
```

**Examples:**

Add test to precondition:
```graphql
mutation {
    addTestsToPrecondition(
        issueId: "12345",
        testIssueIds: ["54321"]
    ) {
        addedTests
        warning
    }
}
```

Add specific test versions to precondition:
```graphql
mutation {
    addTestsToPrecondition(
        issueId: "12345",
        tests: [{ issueId: "54321", versionId: 2 }, { issueId: "67890", versionId: 3 }]
    ) {
        addedTests
        warning
    }
}
```

### removeTestsFromPrecondition

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/removetestsfromprecondition.doc.html

Removes Tests from a Precondition.

**GraphQL Schema Definition:**

```graphql
mutation {
    removeTestsFromPrecondition(issueId: "12345", testIssueIds: ["54321", "67890"])
}
```

**Examples:**

Remove tests from precondition:
```graphql
mutation {
    removeTestsFromPrecondition(issueId: "12345", testIssueIds: ["54321", "67890"])
}
```

Remove specific test versions from precondition:
```graphql
mutation {
    removeTestsFromPrecondition(
        issueId: "12345",
        tests: [{ issueId: "54321", versionId: 2 }, { issueId: "67890", versionId: 3 }]
    )
}
```

---

## Objects

### Precondition Object

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/precondition.doc.html

Represents a Precondition issue type in Xray.

**GraphQL Schema Definition:**

```graphql
type Precondition {
    # Id of the Precondition issue.
    issueId: String

    # Project id of the Precondition issue.
    projectId: String

    # Precondition Type of the Precondition issue.
    preconditionType: TestType

    # Definition of the Precondition issue.
    definition: String

    # List of the Tests associated with the Precondition issue.
    # Arguments:
    #   issueIds: the issue ids of the Tests.
    #   limit: the maximum amount of Tests to be returned. The maximum is 100.
    #   start: the index of the first item to return in the page of results (page offset).
    tests(issueIds: [String], limit: Int!, start: Int): TestResults

    # List of the Test versions associated with the Precondition issue.
    # Arguments:
    #   limit: the maximum amount of Test versions to be returned. The maximum is 100.
    #   start: the index of the first item to return in the page of results (page offset).
    #   archived: if should include archived Test versions in the result.
    #   testTypeId: to filter Test versions by Test Type
    testVersions(limit: Int!, start: Int, archived: Boolean, testTypeId: String): TestVersionResults

    # List of Xray History results for the issue
    # Arguments:
    #   limit: the maximum amount of entries to be returned. The maximum is 100.
    #   start: the index of the first item to return in the page of results (page offset).
    history(limit: Int!, start: Int): XrayHistoryResults

    # Extra Jira information of the Precondition Issue.
    # Arguments:
    #   fields: list of the fields to be displayed.
    #   Check the field 'fields' of this Jira endpoint for more information.
    jira(fields: [String]): JSON

    # Date when the precondition was last modified.
    lastModified: String

    # Test Repository folder of the Precondition.
    folder: Folder
}
```

**Required by:**
- CreatePreconditionResult - Create Precondition Response type
- getPrecondition
- Mutation
- PreconditionResults - Precondition Results type
- Query
- TestRunPrecondition - Test Run Precondition type
- updatePrecondition

---

## Input Objects

### UpdatePreconditionInput

**Category:** Input Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updatepreconditioninput.doc.html

Input type for updating a Precondition.

**GraphQL Schema Definition:**

```graphql
input UpdatePreconditionInput {
    # Precondition type of the Precondition Issue.
    preconditionType: UpdatePreconditionTypeInput

    # Definition of the Precondition Issue.
    definition: String

    # the repository path to which the Precondition should be moved to
    folderPath: String
}
```

**Required by:**
- Mutation
- updatePrecondition

### UpdatePreconditionTypeInput

**Category:** Input Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updatepreconditiontypeinput.doc.html

Input type for specifying Precondition Type.

**GraphQL Schema Definition:**

```graphql
input UpdatePreconditionTypeInput {
    # Id of the Precondition Type.
    id: String

    # Name of the Precondition Type.
    name: String
}
```

**Required by:**
- createPrecondition
- Mutation
- UpdatePreconditionInput

---

## Usage Notes

1. **Precondition Types**: Common types include "Generic" and "Manual"
2. **Pagination**: Most list operations support pagination with `limit` and `start` parameters
3. **Maximum Limits**: 
   - Tests per precondition query: 100
   - JQL query results: 100 issues
4. **Versioning**: Both Tests and Preconditions support versioning
5. **Folder Organization**: Preconditions can be organized in folders using the `folderPath` parameter

This consolidated reference provides all GraphQL operations and types related to Xray Preconditions in a single document.