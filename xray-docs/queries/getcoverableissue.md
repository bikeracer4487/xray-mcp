# getCoverableIssue

**Category:** Queries
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/getcoverableissue.doc.html

## GraphQL Schema Definition

```graphql

{
    getCoverableIssue {
        issueId
        jira(fields: ["assignee", "reporter"])
        status {
            name
            description
            color
        }
    }
}

```

## Example

The query below returns a Coverable Issue.

```

{
    getCoverableIssue {
        issueId
        jira(fields: ["assignee", "reporter"])
        status {
            name
            description
            color
        }
    }
}

```

The query below returns the Coverable Issue with issue id12345.

```

{
    getCoverableIssue(issueId: "12345") {
        issueId
    }
}

```