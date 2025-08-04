# updateGherkinTestDefinition

**Category:** Mutations
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updategherkintestdefinition.doc.html

## GraphQL Schema Definition

```graphql

mutation {
    updateGherkinTestDefinition(issueId: "12345", gherkin: "Gherkin definition" ) {
        issueId
        gherkin
    }
}

```

## Example

The mutation below will update the gherkin definition of the Test with id "12345".

```

mutation {
    updateGherkinTestDefinition(issueId: "12345", gherkin: "Gherkin definition" ) {
        issueId
        gherkin
    }
}

```

The mutation below will update the gherkin definition of the version 3 of the Test with id "12345".

```

mutation {
    updateGherkinTestDefinition(issueId: "12345", versionId: 3, gherkin: "Gherkin definition" ) {
        issueId
        gherkin
    }
}

```