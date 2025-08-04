# getIssueLinkTypes

**Category:** Queries
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/getissuelinktypes.doc.html

## GraphQL Schema Definition

```graphql

{
    getIssueLinkTypes {
        issueLinks {
            id
            name
        }
    }
}

```

## Example

The Query below returns all Issue Link Types

```

{
    getIssueLinkTypes {
        issueLinks {
            id
            name
        }
    }
}

```