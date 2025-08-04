# getStatus

**Category:** Queries
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/getstatus.doc.html

## GraphQL Schema Definition

```graphql

{
    getStatus( name: "PASSED") {
        name
        description
        final
        color
    }
}

```

## Example

The Query below returns a Status

```

{
    getStatus( name: "PASSED") {
        name
        description
        final
        color
    }
}

```