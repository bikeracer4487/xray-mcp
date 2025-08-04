# Xray Folders - Complete Reference

This document consolidates all folder-related GraphQL operations and types for Xray Test Repository.

## Table of Contents

1. [Queries](#queries)
   - [getFolder](#getfolder)
2. [Mutations](#mutations)
   - [createFolder](#createfolder)
   - [deleteFolder](#deletefolder)
   - [renameFolder](#renamefolder)
   - [moveFolder](#movefolder)
   - [addTestsToFolder](#addteststofolder)
   - [addIssuesToFolder](#addissuestofolder)
   - [removeTestsFromFolder](#removetestsfromfolder)
   - [removeIssuesFromFolder](#removeissuesfromfolder)
   - [updateTestFolder](#updatetestfolder)
   - [updatePreconditionFolder](#updatepreconditionfolder)
3. [Objects](#objects)
   - [Folder](#folder-object)
   - [FolderResults](#folderresults)
   - [SimpleFolderResults](#simplefolderresults)
   - [ActionFolderResult](#actionfolderresult)
4. [Input Objects](#input-objects)
   - [FolderSearchInput](#foldersearchinput)
   - [PreconditionFolderSearchInput](#preconditionfoldersearchinput)

---

## Queries

### getFolder

**Category:** Queries  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/getfolder.doc.html

Returns folder information including child folders.

**GraphQL Schema Definition:**

```graphql
{
    getFolder(projectId: "10000", path: "/") {
        name
        path
        testsCount
        folders
    }
}
```

**Examples:**

Get root folder:
```graphql
{
    getFolder(projectId: "10000", path: "/") {
        name
        path
        testsCount
        folders
    }
}
```

Get specific folder:
```graphql
{
    getFolder(projectId: "10000", path: "/generic") {
        name
        path
        testsCount
        folders
    }
}
```

---

## Mutations

### createFolder

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/createfolder.doc.html

Creates a new folder in the Test Repository.

**GraphQL Schema Definition:**

```graphql
mutation {
    createFolder(
        projectId: "10000",
        path: "/generic"
    ) {
        folder {
            name
            path
            testsCount
        }
        warnings
    }
}
```

**Examples:**

Create empty folder:
```graphql
mutation {
    createFolder(
        projectId: "10000",
        path: "/generic"
    ) {
        folder {
            name
            path
            testsCount
        }
        warnings
    }
}
```

Create folder with tests:
```graphql
mutation {
    createFolder(
        projectId: "10000",
        path: "/generic",
        testIssueIds: ["10002","12324","12345"]
    ) {
        folder {
            name
            path
            testsCount
        }
        warnings
    }
}
```

Create folder with tests and/or preconditions:
```graphql
mutation {
    createFolder(
        projectId: "10000",
        path: "/generic",
        issueIds: ["10002","12324","12345"]
    ) {
        folder {
            name
            path
            testsCount
            issuesCount
            preconditionsCount
        }
        warnings
    }
}
```

**Note:** Use createFolder with `testIssueIds` (in which all ids must be from Tests) OR with `issueIds` (which can be either Test ids and/or Precondition ids), but not with both.

### deleteFolder

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/deletefolder.doc.html

Deletes a folder from the Test Repository.

**GraphQL Schema Definition:**

```graphql
mutation {
    deleteFolder(
        projectId: "10000",
        path: "/generic"
    )
}
```

**Example:**

```graphql
mutation {
    deleteFolder(
        projectId: "10000",
        path: "/generic"
    )
}
```

### renameFolder

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/renamefolder.doc.html

Renames an existing folder.

**GraphQL Schema Definition:**

```graphql
mutation {
    renameFolder(
        projectId: "10000",
        path: "/generic",
        newName: "Junit"
    ) {
        folder {
            name
            path
            testsCount
        }
        warnings
    }
}
```

**Example:**

```graphql
mutation {
    renameFolder(
        projectId: "10000",
        path: "/generic",
        newName: "Junit"
    ) {
        folder {
            name
            path
            testsCount
        }
        warnings
    }
}
```

### moveFolder

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/movefolder.doc.html

Moves a folder to a different location in the hierarchy.

**GraphQL Schema Definition:**

```graphql
mutation {
    moveFolder(
        projectId: "10000",
        path: "/generic",
        destinationPath: "/testType"
    ) {
        folder {
            name
            path
            testsCount
        }
        warnings
    }
}
```

**Example:**

```graphql
mutation {
    moveFolder(
        projectId: "10000",
        path: "/generic",
        destinationPath: "/testType"
    ) {
        folder {
            name
            path
            testsCount
        }
        warnings
    }
}
```

### addTestsToFolder

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/addteststofolder.doc.html

Adds tests to an existing folder.

**GraphQL Schema Definition:**

```graphql
mutation {
    addTestsToFolder(
        projectId: "10000",
        path: "/generic",
        testIssueIds: ["10002","12324","12345"]
    ) {
        folder {
            name
            path
            testsCount
        }
        warnings
    }
}
```

**Example:**

```graphql
mutation {
    addTestsToFolder(
        projectId: "10000",
        path: "/generic",
        testIssueIds: ["10002","12324","12345"]
    ) {
        folder {
            name
            path
            testsCount
        }
        warnings
    }
}
```

### addIssuesToFolder

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/addissuestofolder.doc.html

Adds issues (tests and/or preconditions) to an existing folder.

**GraphQL Schema Definition:**

```graphql
mutation {
    addIssuesToFolder(
        projectId: "10000",
        path: "/generic",
        issueIds: ["10002","12324","12345"]
    ) {
        folder {
            name
            path
            issuesCount
        }
        warnings
    }
}
```

**Example:**

```graphql
mutation {
    addIssuesToFolder(
        projectId: "10000",
        path: "/generic",
        issueIds: ["10002","12324","12345"]
    ) {
        folder {
            name
            path
            issuesCount
        }
        warnings
    }
}
```

### removeTestsFromFolder

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/removetestsfromfolder.doc.html

Removes tests from their current folder.

**GraphQL Schema Definition:**

```graphql
mutation {
    removeTestsFromFolder(
        projectId: "10000",
        testIssueIds: ["10002","12324","12345"]
    )
}
```

**Example:**

```graphql
mutation {
    removeTestsFromFolder(
        projectId: "10000",
        testIssueIds: ["10002","12324","12345"]
    )
}
```

### removeIssuesFromFolder

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/removeissuesfromfolder.doc.html

Removes issues (tests and/or preconditions) from their current folder.

**GraphQL Schema Definition:**

```graphql
mutation {
    removeIssuesFromFolder(
        projectId: "10000",
        issueIds: ["10002","12324","12345"]
    )
}
```

**Example:**

```graphql
mutation {
    removeIssuesFromFolder(
        projectId: "10000",
        issueIds: ["10002","12324","12345"]
    )
}
```

### updateTestFolder

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updatetestfolder.doc.html

Moves a specific test to a different folder.

**GraphQL Schema Definition:**

```graphql
mutation {
    updateTestFolder(
        issueId: "12345",
        folderPath: "/Component/UI"
    )
}
```

**Examples:**

Move test to folder:
```graphql
mutation {
    updateTestFolder(
        issueId: "12345",
        folderPath: "/Component/UI"
    )
}
```

Move test to root:
```graphql
mutation {
    updateTestFolder(
        issueId: "12345",
        folderPath: "/"
    )
}
```

### updatePreconditionFolder

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updatepreconditionfolder.doc.html

Moves a specific precondition to a different folder.

**GraphQL Schema Definition:**

```graphql
mutation {
    updatePreconditionFolder(
        issueId: "12345",
        folderPath: "/Component/UI"
    )
}
```

**Examples:**

Move precondition to folder:
```graphql
mutation {
    updatePreconditionFolder(
        issueId: "12345",
        folderPath: "/Component/UI"
    )
}
```

Move precondition to root:
```graphql
mutation {
    updatePreconditionFolder(
        issueId: "12345",
        folderPath: "/"
    )
}
```

---

## Objects

### Folder Object

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/folder.doc.html

Test Repository folder type.

**GraphQL Schema Definition:**

```graphql
type Folder {
    # Folder name
    name: String

    # Folder path
    path: String
}
```

**Required by:**
- ExpandedTest - Expanded test issue type
- Precondition - Precondition issue type
- Test - Test issue type

### FolderResults

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/folderresults.doc.html

Extended folder information with counts and child folders.

**GraphQL Schema Definition:**

```graphql
type FolderResults {
    # Folder name
    name: String

    # Folder path
    path: String

    # Folder issues count
    issuesCount: Int

    # Folder tests count
    testsCount: Int

    # Folder preconditions count
    preconditionsCount: Int

    # Folder children
    folders: JSON
}
```

**Required by:**
- getFolder
- Query
- TestPlan - Test Plan issue type

### SimpleFolderResults

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/simplefolderresults.doc.html

Simplified folder information with counts.

**GraphQL Schema Definition:**

```graphql
type SimpleFolderResults {
    # Folder name
    name: String

    # Folder path
    path: String

    # Folder tests count
    testsCount: Int

    # Folder preconditions count
    preconditionsCount: Int

    # Folder issues count
    issuesCount: Int
}
```

**Required by:**
- ActionFolderResult

### ActionFolderResult

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/actionfolderresult.doc.html

Result type for folder mutations.

**GraphQL Schema Definition:**

```graphql
type ActionFolderResult {
    # Folder updated during the operation.
    folder: SimpleFolderResults

    # Warning generated during the operation.
    warnings: [String]
}
```

**Required by:**
- addIssuesToFolder
- addTestsToFolder
- createFolder
- moveFolder
- Mutation
- renameFolder

---

## Input Objects

### FolderSearchInput

**Category:** Input Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/foldersearchinput.doc.html

Input type for searching folders.

**GraphQL Schema Definition:**

```graphql
input FolderSearchInput {
    # Path of the Folder.
    path: String!

    # Test Plan id of the Folder.
    testPlanId: String

    # Whether descendant folders should be included in the search.
    includeDescendants: Boolean
}
```

**Required by:**
- getExpandedTests
- getTests
- Query

### PreconditionFolderSearchInput

**Category:** Input Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/preconditionfoldersearchinput.doc.html

Input type for searching precondition folders.

**GraphQL Schema Definition:**

```graphql
input PreconditionFolderSearchInput {
    # Path of the Folder.
    path: String!

    # Whether descendant folders should be included in the search.
    includeDescendants: Boolean
}
```

**Required by:**
- getPreconditions
- Query

---

## Usage Notes

1. **Folder Paths**: Always start with "/" for the root folder
2. **Hierarchy**: Folders support nested structures (e.g., "/Component/UI/Forms")
3. **Single Membership**: Each test or precondition can only be in one folder at a time
4. **Issue Types**: Folders can contain both Tests and Preconditions
5. **Batch Operations**: Use `issueIds` to work with mixed issue types, or `testIssueIds` for tests only
6. **Folder Movement**: Moving a folder moves all its contents and subfolders

This consolidated reference provides all GraphQL operations and types related to Xray Test Repository folders in a single document.