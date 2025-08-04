# getProjectSettings

**Category:** Queries
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/getprojectsettings.doc.html

## GraphQL Schema Definition

```graphql

{
    getProjectSettings ( projectIdOrKey: "10000" ) {
        projectId,
        testEnvironments,
        testCoverageSettings {
            coverableIssueTypeIds
            epicIssuesRelation
            issueSubTasksRelation
            issueLinkTypeId
            issueLinkTypeDirection
        }
        defectIssueTypes
        testTypeSettings {
            testTypes {
                id
                name
                kind
            }
            defaultTestTypeId
        }
    }
}

```

## Example

The Query below returns multiple Status

```

{
    getProjectSettings ( projectIdOrKey: "10000" ) {
        projectId,
        testEnvironments,
        testCoverageSettings {
            coverableIssueTypeIds
            epicIssuesRelation
            issueSubTasksRelation
            issueLinkTypeId
            issueLinkTypeDirection
        }
        defectIssueTypes
        testTypeSettings {
            testTypes {
                id
                name
                kind
            }
            defaultTestTypeId
        }
    }
}

```