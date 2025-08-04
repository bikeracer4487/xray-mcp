# updateIterationStatus

**Category:** Mutations
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updateiterationstatus.doc.html

## GraphQL Schema Definition

```graphql

mutation {
    updateIterationStatus(
        testRunId: "5e8489c05f200f3cd45bbaf0",
        iterationRank: "0",
        status: "PASSED"
    ) {
        warnings
    }
}

```

## Example

The mutation below updates the status of a Test Run iteration.

```

mutation {
    updateIterationStatus(
        testRunId: "5e8489c05f200f3cd45bbaf0",
        iterationRank: "0",
        status: "PASSED"
    ) {
        warnings
    }
}

```