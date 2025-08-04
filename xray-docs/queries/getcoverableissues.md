# getCoverableIssues

**Category:** Queries
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/getcoverableissues.doc.html

## GraphQL Schema Definition

```graphql

{
    getCoverableIssues(limit: 10) {
        total
        start
        limit
        results {
            issueId
            jira(fields: ["assignee", "reporter"])
            status {
                name
                description
                color
            }
        }
    }
}

```

## Example

The query below returns 10 coverable issues that match the provided jql.

```

{
    getCoverableIssues(limit: 10) {
        total
        start
        limit
        results {
            issueId
            jira(fields: ["assignee", "reporter"])
            status {
                name
                description
                color
            }
        }
    }
}

```