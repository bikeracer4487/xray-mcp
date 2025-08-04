# getStatuses

**Category:** Queries
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/getstatuses.doc.html

## GraphQL Schema Definition

```graphql

{
    getStatuses {
        name
        description
        final
        color
    }
}

```

## Example

The Query below returns multiple Status

```

{
    getStatuses {
        name
        description
        final
        color
    }
}

```